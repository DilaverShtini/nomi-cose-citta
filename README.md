# 🎮 Nomi, Cose, Città - Distributed Multiplayer Game

A real-time, distributed implementation of the classic Italian word game "Nomi, Cose, Città" (Names, Things, Cities) built with Python.

## 📝 Project Overview

This project reimagines the traditional pen-and-paper game as a modern multiplayer experience where players compete in real-time to find words matching specific categories and starting letters. The game features a distributed architecture with both client-server and peer-to-peer communication, ensuring robust gameplay with fault tolerance and consistency across all nodes.

## ✨ Features

### Core Gameplay
- **Real-time multiplayer**: Multiple players can join shared game
- **Category-based challenges**: Write words matching given letters and categories
- **Collaborative validation**: Players vote to accept or reject each other's answers
- **Point system**: First player to reach the target score wins
- **Live chat**: Communicate with other players during the game

### Technical Features
- **Hybrid architecture**: Central server with P2P client communication
- **Fault Tolerance**: Automatic recovery from disconnections and crashes
- **State consistency**: Synchronized game state across all nodes
- **Lightweight GUI**: User-friendly interface for seamless interaction

## 🏗️ System Architecture

### Components

#### Central Server
- Manages game sessions
- Coordinates game rounds and timing
- Handles player synchronization
- Maintains authoritative game state
- Manages player connections and reconnections

#### Client Nodes
- Peer-to-peer communication for chat and voting
- Local game state caching
- Automatic reconnection handling
- GUI for player interaction

#### Communication Protocol
- **Client-Server**: Game state updates, round management, scoring
- **Peer-to-Peer**: Real-time chat, distributed voting mechanism

## 🎯 How to Play

1. **Join the game**: Connect to the server
2. **Lobby & Configuration**: The administrator configures the game mode, then starts
   the match for all participants in the lobby.
3. **Game Round**: 
   - A random letter are presented
   - Write words starting with that letter for each category
   - Submit your answers before time runs out
4. **Validation Phase**:
   - Review other players' answers
   - Vote to accept or reject each answer
   - Chat with other players to discuss answers
5. **Scoring**: Points are awarded for validated answers
6. **Victory**: First player to reach the target score wins!

## 🛡️ Fault Tolerance

### Server Recovery
- Session state persistance
- Automatic state restoration after crashes
- Client reconnection handling

### Client Recovery
- Automatic reconnection to server
- P2P connection re-establishment
- Local state caching for seamless recovery

## 📊 Game State Consistency

The system ensures consistency through:
- **Event ordering**: Total ordering of game events via server timestamps
- **State synchronization**: Regular state snapshots from server to clients
- **Conflict resolution**: Server acts as authoritative source for disputes
- **Eventual consistency**: P2P communications converge to consistent state

## 👥 Team

- **Chiara Giangiulli** - chiara.giangiulli@studio.unibo.it
- **Giovanni Pisoni** - giovanni.pisoni@studio.unibo.it
- **Dilaver Shtini** - dilaver.shtini@studio.unibo.it

## 📄 License

This project is licensed under the GPL-3.0 license - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the classic Italian game "Nomi, Cose, Città"
- Built as part of the Distributed Systems course at University of Bologna

**Happy Gaming! 🎉**

## 📄 Report

For a more in-depth analysis of the architecture, networking, and fault-tolerance mechanisms, please read our [official project report](https://github.com/ChiaraGiangiulli/ds-report).
