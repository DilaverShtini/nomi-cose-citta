"""
Utility functions for the GUI components.
"""

def bind_mousewheel(canvas):
    """
    Bind mouse wheel scrolling to a canvas.
    Works on Windows, MacOS, and Linux.
    """
    def _on_mousewheel(event):
        # Windows and MacOS
        if hasattr(event, 'delta') and event.delta:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # Linux
        elif hasattr(event, 'num'):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

    def _bind_wheel(event=None):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

    def _unbind_wheel(event=None):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    canvas.bind("<Enter>", _bind_wheel)
    canvas.bind("<Leave>", _unbind_wheel)