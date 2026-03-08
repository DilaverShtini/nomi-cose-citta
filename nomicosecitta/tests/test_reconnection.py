import json
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, call

import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir    = os.path.dirname(current_dir)
sys.path.insert(0, root_dir)

from src.client.reconnection_manager import ReconnectionManager
from src.common.message import Message, MessageType

"""
Tests for the ReconnectionManager module.
"""

def _make_config(servers, max_retries=2, delay=0.0) -> dict:
    return {
        "servers": servers,
        "reconnection": {
            "max_retries_per_server": max_retries,
            "retry_delay_seconds": delay,
        }
    }


def _write_config(data: dict) -> str:
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(data, tmp)
    tmp.close()
    return tmp.name


def _mock_handler_factory(connect_results: list):
    results = list(connect_results)

    def factory(host: str, port: int):
        handler = MagicMock()
        rv = results.pop(0) if results else False
        handler.connect = AsyncMock(return_value=rv)
        handler.host = host
        handler.port = port
        return handler

    return factory

class TestConfigLoading(unittest.TestCase):
    """ReconnectionManager correctly reads / falls back from config.json."""

    def test_valid_config_servers_parsed(self):
        cfg  = _make_config(["10.0.0.1:5000", "10.0.0.2:5001"], max_retries=4, delay=1.5)
        path = _write_config(cfg)
        try:
            mgr = ReconnectionManager(config_path=path)
            self.assertEqual(mgr.servers, [("10.0.0.1", 5000), ("10.0.0.2", 5001)])
            self.assertEqual(mgr.max_retries, 4)
            self.assertAlmostEqual(mgr.retry_delay, 1.5)
        finally:
            os.unlink(path)

    def test_missing_config_uses_defaults(self):
        mgr = ReconnectionManager(config_path="/nonexistent/path/config.json")
        self.assertEqual(mgr.servers, [("127.0.0.1", 5000)])
        self.assertEqual(mgr.max_retries, 3)

    def test_malformed_json_uses_defaults(self):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8")
        tmp.write("{ this is not json }")
        tmp.close()
        try:
            mgr = ReconnectionManager(config_path=tmp.name)
            self.assertEqual(mgr.servers, [("127.0.0.1", 5000)])
        finally:
            os.unlink(tmp.name)

    def test_config_without_reconnection_section_uses_defaults(self):
        cfg  = {"servers": ["192.168.1.10:5000"]}
        path = _write_config(cfg)
        try:
            mgr = ReconnectionManager(config_path=path)
            self.assertEqual(mgr.max_retries, 3)
            self.assertAlmostEqual(mgr.retry_delay, 2.0)
        finally:
            os.unlink(path)


class TestAddressParsing(unittest.TestCase):
    """_parse_address handles edge cases."""

    def test_standard_host_port(self):
        self.assertEqual(
            ReconnectionManager._parse_address("192.168.1.5:6000"),
            ("192.168.1.5", 6000))

    def test_missing_port_defaults_to_5000(self):
        self.assertEqual(
            ReconnectionManager._parse_address("localhost"),
            ("localhost", 5000))

    def test_whitespace_stripped(self):
        self.assertEqual(
            ReconnectionManager._parse_address("  10.0.0.1:5001  "),
            ("10.0.0.1", 5001))


class TestServerRotation(unittest.TestCase):
    """Circular server rotation API."""

    def setUp(self):
        cfg        = _make_config(["A:5000", "B:5001", "C:5002"])
        path       = _write_config(cfg)
        self.mgr   = ReconnectionManager(config_path=path)
        self._path = path

    def tearDown(self):
        os.unlink(self._path)

    def test_get_initial_server(self):
        self.assertEqual(self.mgr.get_initial_server(), ("A", 5000))

    def test_advance_wraps_around(self):
        self.mgr.advance()
        self.mgr.advance()
        next_srv = self.mgr.advance()   # wraps back to A
        self.assertEqual(next_srv, ("A", 5000))

    def test_reset_rotation_returns_to_start(self):
        self.mgr.advance()
        self.mgr.advance()
        self.mgr.reset_rotation()
        self.assertEqual(self.mgr.get_current_server(), ("A", 5000))

    def test_server_list_property(self):
        self.assertEqual(self.mgr.server_list, ["A:5000", "B:5001", "C:5002"])


class TestReconnectLoop(unittest.IsolatedAsyncioTestCase):
    """Async reconnection logic of ReconnectionManager."""

    def _make_mgr(self, servers, max_retries=2):
        cfg        = _make_config(servers, max_retries=max_retries, delay=0.0)
        path       = _write_config(cfg)
        self._path = path
        return ReconnectionManager(config_path=path)

    def tearDown(self):
        if hasattr(self, "_path") and os.path.isfile(self._path):
            os.unlink(self._path)

    async def test_success_on_first_attempt(self):
        mgr     = self._make_mgr(["S1:5000", "S2:5001"])
        factory = _mock_handler_factory([True])
        result  = await mgr.reconnect(network_factory=factory, username="U", p2p_port=9000)
        self.assertIsNotNone(result)
        result.connect.assert_awaited_once()
        self.assertFalse(mgr.is_active)

    async def test_success_after_initial_failures(self):
        mgr     = self._make_mgr(["S1:5000", "S2:5001", "S3:5002"], max_retries=1)
        factory = _mock_handler_factory([False, False, True])
        result  = await mgr.reconnect(network_factory=factory, username="P", p2p_port=8080)
        self.assertIsNotNone(result)

    async def test_returns_none_when_all_fail(self):
        mgr     = self._make_mgr(["S1:5000", "S2:5001"], max_retries=2)
        factory = _mock_handler_factory([False] * 4)
        result  = await mgr.reconnect(network_factory=factory, username="P", p2p_port=9000)
        self.assertIsNone(result)
        self.assertFalse(mgr.is_active)

    async def test_concurrent_reconnect_ignored(self):
        mgr       = self._make_mgr(["S1:5000"])
        mgr._active = True   # simulate in-progress reconnect
        factory   = _mock_handler_factory([True])
        result    = await mgr.reconnect(network_factory=factory, username="P", p2p_port=0)
        self.assertIsNone(result)

    async def test_status_callback_called_on_each_attempt(self):
        mgr      = self._make_mgr(["S1:5000", "S2:5001"], max_retries=1)
        factory  = _mock_handler_factory([False, True])
        statuses: list[str] = []
        await mgr.reconnect(
            network_factory=factory, username="X", p2p_port=0,
            on_status=statuses.append)
        self.assertGreaterEqual(len(statuses), 2)
        self.assertTrue(any("Reconnecting" in s for s in statuses))
        self.assertTrue(any("successfully" in s for s in statuses))

    async def test_status_callback_exhaustion_message(self):
        mgr      = self._make_mgr(["S1:5000"], max_retries=1)
        factory  = _mock_handler_factory([False])
        statuses: list[str] = []
        await mgr.reconnect(
            network_factory=factory, username="X", p2p_port=0,
            on_status=statuses.append)
        self.assertTrue(any("exhausted" in s.lower() or "✗" in s for s in statuses))

    async def test_is_active_false_after_success(self):
        mgr    = self._make_mgr(["S1:5000"])
        factory = _mock_handler_factory([True])
        await mgr.reconnect(network_factory=factory, username="U", p2p_port=0)
        self.assertFalse(mgr.is_active)

    async def test_is_active_false_after_failure(self):
        mgr     = self._make_mgr(["S1:5000"], max_retries=1)
        factory = _mock_handler_factory([False])
        await mgr.reconnect(network_factory=factory, username="U", p2p_port=0)
        self.assertFalse(mgr.is_active)

class _FakeController:
    """
    Minimal stand-in for ClientController.
    Exercises only the reconnection-relevant logic without needing a display.
    """

    def __init__(self, mgr: ReconnectionManager):
        self.reconnection_manager    = mgr
        self.username                = "TestPlayer"
        self.p2p_port                = 9001
        self._reconnecting           = False
        self._intentional_disconnect = False
        self.network                 = None
        self.status_messages: list[str] = []
        self.failed_called           = False
        self.success_called: list    = []

    def _update_reconnection_status(self, msg: str):
        self.status_messages.append(msg)

    def _on_reconnection_success(self, host: str, port: int):
        self.success_called.append((host, port))

    def _on_reconnection_failed(self):
        self.failed_called = True

    def handle_disconnection(self, reason: str):
        """Mirrors ClientController.handle_disconnection."""
        if self._intentional_disconnect:
            return
        if self._reconnecting:
            return
        self._reconnecting = True

    def _build_handler(self, host: str, port: int):
        h = MagicMock()
        h.host, h.port  = host, port
        h.connect       = AsyncMock(return_value=False)
        h.send          = AsyncMock(return_value=True)
        h.on_message    = None
        h.on_disconnect = None
        return h

    async def _async_reconnect(self):
        """Mirrors ClientController._async_reconnect."""
        new_handler = await self.reconnection_manager.reconnect(
            network_factory=self._build_handler,
            username=self.username,
            p2p_port=self.p2p_port,
            on_status=self._update_reconnection_status,
        )
        self._reconnecting = False
        if new_handler is None:
            self._on_reconnection_failed()
            return
        self.network = new_handler
        host, port   = self.reconnection_manager.get_current_server()
        await self.network.send(Message(
            type=MessageType.CMD_JOIN,
            sender=self.username,
            payload={"username": self.username, "p2p_port": self.p2p_port},
        ))
        self._on_reconnection_success(host, port)


class TestClientControllerReconnection(unittest.IsolatedAsyncioTestCase):
    """Controller-level reconnection behaviour (no Tkinter needed)."""

    def _make_ctrl(self, servers, max_retries=2) -> _FakeController:
        cfg  = _make_config(servers, max_retries=max_retries, delay=0.0)
        path = _write_config(cfg)
        self._tmp = path
        return _FakeController(ReconnectionManager(config_path=path))

    def tearDown(self):
        if hasattr(self, "_tmp") and os.path.isfile(self._tmp):
            os.unlink(self._tmp)

    def test_intentional_disconnect_skips_reconnect(self):
        ctrl = self._make_ctrl(["127.0.0.1:5000"])
        ctrl._intentional_disconnect = True
        ctrl.handle_disconnection("clean exit")
        self.assertFalse(ctrl._reconnecting)

    def test_duplicate_disconnection_signal_ignored(self):
        ctrl = self._make_ctrl(["127.0.0.1:5000"])
        ctrl._reconnecting = True
        ctrl.handle_disconnection("second signal")
        self.assertTrue(ctrl._reconnecting)

    async def test_cmd_join_sent_with_correct_payload_on_success(self):
        ctrl = self._make_ctrl(["127.0.0.1:5000"], max_retries=1)
        good = MagicMock()
        good.connect = AsyncMock(return_value=True)
        good.send    = AsyncMock(return_value=True)
        good.on_message = good.on_disconnect = None
        ctrl._build_handler = MagicMock(return_value=good)

        await ctrl._async_reconnect()

        good.send.assert_awaited_once()
        msg = good.send.call_args[0][0]
        self.assertEqual(msg.type, MessageType.CMD_JOIN)
        self.assertEqual(msg.payload["username"], "TestPlayer")
        self.assertEqual(msg.payload["p2p_port"], 9001)
        self.assertTrue(ctrl.success_called)
        self.assertFalse(ctrl._reconnecting)

    async def test_failed_callback_on_exhaustion(self):
        ctrl = self._make_ctrl(["127.0.0.1:5000"], max_retries=1)
        await ctrl._async_reconnect()
        self.assertTrue(ctrl.failed_called)
        self.assertFalse(ctrl._reconnecting)

    async def test_all_servers_tried_circularly(self):
        """2 servers × 2 retries = 4 connect() calls before giving up."""
        ctrl = self._make_ctrl(["S1:5000", "S2:5001"], max_retries=2)
        calls: list = []

        def factory(host, port):
            h = MagicMock()
            h.connect = AsyncMock(side_effect=lambda: calls.append((host, port)) or False)
            return h

        ctrl._build_handler = factory
        await ctrl._async_reconnect()

        self.assertEqual(len(calls), 4)
        self.assertTrue(ctrl.failed_called)

    async def test_status_updates_during_reconnect(self):
        ctrl = self._make_ctrl(["S1:5000", "S2:5001"], max_retries=1)
        results = [False, True]

        def factory(host, port):
            h = MagicMock()
            rv = results.pop(0) if results else False
            h.connect    = AsyncMock(return_value=rv)
            h.send       = AsyncMock(return_value=True)
            h.on_message = h.on_disconnect = None
            return h

        ctrl._build_handler = factory
        await ctrl._async_reconnect()

        self.assertTrue(len(ctrl.status_messages) >= 2)
        self.assertFalse(ctrl.failed_called)
        self.assertTrue(ctrl.success_called)


if __name__ == "__main__":
    unittest.main(verbosity=2)