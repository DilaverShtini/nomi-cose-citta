import tkinter as tk
from tkinter import messagebox, scrolledtext

class ClientGUI:
    def __init__(self, master, on_connect_callback, on_send_callback):
        self.root = master
        self.root.title("Nomi Cose Città - Client")
        self.root.geometry("600x450")
        
        self.on_connect = on_connect_callback
        self.on_send = on_send_callback

        self.username_var = tk.StringVar()
        self.ip_var = tk.StringVar(value="127.0.0.1")
        self.msg_var = tk.StringVar()

        self.login_frame = tk.Frame(self.root, padx=20, pady=20)
        self._setup_login()

        self.lobby_frame = tk.Frame(self.root, padx=10, pady=10)
        self._setup_lobby()

        self.show_login()

    def _setup_login(self):
        tk.Label(self.login_frame, text="BENVENUTO", font=("Arial", 20, "bold")).pack(pady=20)
        
        tk.Label(self.login_frame, text="Username:", font=("Arial", 12)).pack(anchor="w")
        tk.Entry(self.login_frame, textvariable=self.username_var).pack(fill="x", pady=5)

        tk.Label(self.login_frame, text="Server IP:", font=("Arial", 12)).pack(anchor="w")
        tk.Entry(self.login_frame, textvariable=self.ip_var).pack(fill="x", pady=5)
        
        tk.Button(self.login_frame, text="ENTRA IN LOBBY", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
                  command=self._handle_connect_click).pack(fill="x", pady=30)

    def _setup_lobby(self):
        header = tk.Frame(self.lobby_frame)
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="Sala d'Attesa", font=("Arial", 16, "bold")).pack(side="left")

        content = tk.Frame(self.lobby_frame)
        content.pack(fill="both", expand=True)

        left_panel = tk.Frame(content, width=150)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(left_panel, text="Giocatori Connessi:", font=("Arial", 10, "bold")).pack(anchor="w")

        self.players_list = tk.Listbox(left_panel, height=15, width=20, bg="#f0f0f0")
        self.players_list.pack(fill="both", expand=True)

        right_panel = tk.Frame(content)
        right_panel.pack(side="right", fill="both", expand=True)

        tk.Label(right_panel, text="Chat di Lobby:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.log_area = scrolledtext.ScrolledText(right_panel, state='disabled', height=15)
        self.log_area.pack(fill="both", expand=True, pady=5)

        input_frame = tk.Frame(right_panel)
        input_frame.pack(fill="x", pady=5)
        
        tk.Entry(input_frame, textvariable=self.msg_var).pack(side="left", fill="x", expand=True)
        tk.Button(input_frame, text="Invia", command=self._handle_send_click).pack(side="right", padx=5)

    def _handle_connect_click(self):
        user = self.username_var.get()
        ip = self.ip_var.get()
        if user and ip:
            self.on_connect(ip, user)
        else:
            messagebox.showerror("Errore", "Dati mancanti")

    def _handle_send_click(self):
        msg = self.msg_var.get()
        if msg:
            self.on_send(msg)
            self.msg_var.set("")

    def show_login(self):
        self.lobby_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def show_lobby(self):
        self.login_frame.pack_forget()
        self.lobby_frame.pack(fill="both", expand=True)

    def append_log(self, text):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def update_player_list(self, players_list):
        self.players_list.delete(0, tk.END)
        for player in players_list:
            self.players_list.insert(tk.END, f"👤 {player}")
