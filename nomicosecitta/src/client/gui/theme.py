"""
Design system per Nomi Cose Città.
Stile quaderno scolastico: carta rigata, colori vivaci, font scritto a mano.
"""
import platform

# Palette
BG_PAGE      = "#f7f4ed"   
BG_SURFACE   = "#eeeade"
LINE_COLOR   = "#b8cfe8"
LINE_DARK    = "#7aacd4"
MARGIN_RED   = "#e8706a"

INK          = "#1a1a2e"
INK_LIGHT    = "#4a4a6a"

GREEN_INK    = "#2e9e5b"
RED_INK      = "#d93a3a"
BLUE_INK     = "#2b6cb0"
ORANGE_INK   = "#d97706"
YELLOW_HL    = "#f8ee9e"

TITLE_N      = "#e53e3e"
TITLE_C1     = "#2b6cb0"
TITLE_C2     = "#2e9e5b"

# Font scritto a mano
_os = platform.system()
if _os == "Windows":
    HAND_FONT = "Segoe Print"
    ALT_FONT  = "Segoe UI"
elif _os == "Darwin":
    HAND_FONT = "Chalkboard SE"
    ALT_FONT  = "Helvetica Neue"
else:
    HAND_FONT = "URW Chancery L"
    ALT_FONT  = "Ubuntu"

FONT_TITLE   = (HAND_FONT, 26, "bold")
FONT_HEADING = (HAND_FONT, 14, "bold")
FONT_BODY    = (HAND_FONT, 12)
FONT_SMALL   = (HAND_FONT, 10)
FONT_LABEL   = (HAND_FONT, 12, "bold")
FONT_TIMER   = (HAND_FONT, 30, "bold")
FONT_LETTER  = (HAND_FONT, 52, "bold")
FONT_MONO    = (ALT_FONT, 10)
FONT_FAMILY  = HAND_FONT

# Spacing
PAD_XS = 4
PAD_SM = 8
PAD_MD = 14
PAD_LG = 22
PAD_XL = 32

# Widget helpers

def configure_root(root):
    root.configure(bg=BG_PAGE)

def style_button(btn, variant="primary"):
    palettes = {
        "primary": dict(bg=BLUE_INK,   fg="#ffffff", activebackground="#1a4e8a", activeforeground="#ffffff"),
        "warning": dict(bg=ORANGE_INK, fg="#ffffff", activebackground="#b45309", activeforeground="#ffffff"),
        "success": dict(bg=GREEN_INK,  fg="#ffffff", activebackground="#1e7a47", activeforeground="#ffffff"),
        "danger":  dict(bg=RED_INK,    fg="#ffffff", activebackground="#a82a2a", activeforeground="#ffffff"),
        "ghost":   dict(bg=BG_SURFACE, fg=INK,       activebackground=LINE_COLOR, activeforeground=INK),
    }
    p = palettes.get(variant, palettes["primary"])
    btn.configure(
        relief="flat", cursor="hand2",
        padx=16, pady=7,
        font=(HAND_FONT, 11, "bold"),
        bd=0, overrelief="flat",
        **p,
    )

def style_entry(entry):
    entry.configure(
        bg=BG_PAGE,
        fg=GREEN_INK,
        insertbackground=GREEN_INK,
        relief="flat",
        font=(HAND_FONT, 12),
        highlightthickness=2,
        highlightbackground=LINE_COLOR,
        highlightcolor=BLUE_INK,
    )

def style_listbox(lb):
    lb.configure(
        bg=BG_PAGE,
        fg=INK,
        selectbackground=YELLOW_HL,
        selectforeground=INK,
        relief="flat",
        highlightthickness=1,
        highlightbackground=LINE_COLOR,
        font=(HAND_FONT, 11),
        borderwidth=0,
        activestyle="none",
    )

def style_scrolled_text(st):
    st.configure(
        bg=BG_PAGE,
        fg=INK,
        insertbackground=INK,
        relief="flat",
        borderwidth=0,
        selectbackground=YELLOW_HL,
        selectforeground=INK,
        font=(ALT_FONT, 10),
    )

def separator(parent, color=None, **kw):
    import tkinter as tk
    return tk.Frame(parent, height=2, bg=color or LINE_COLOR, **kw)