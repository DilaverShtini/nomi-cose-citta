import tkinter as tk
from tkinter import messagebox, scrolledtext

class ClientGUI:
    def __init__(self, master, on_connect_callback, on_send_callback):
        self.root = master
        self.root.title("Nomi Cose Città - Client Test")
        self.root.geometry("500x400")

        self.on_connect = on_connect_callback
        self.on_send = on_send_callback

        self.username_var = tk.StringVar()
        self.ip_var = tk.StringVar(value="127.0.0.1")
        self.msg_var = tk.StringVar()

        self.login_frame = tk.Frame(self.root, padx=20, pady=20)
        self.game_frame = tk.Frame(self.root, padx=10, pady=10)

        self._setup_login()
        self._setup_game()

        self.show_login()

    def _setup_login(self):
        tk.Label(self.login_frame, text="Username:", font=("Arial", 12)).pack(anchor="w")
        tk.Entry(self.login_frame, textvariable=self.username_var).pack(fill="x", pady=5)

        tk.Label(self.login_frame, text="Server IP:", font=("Arial", 12)).pack(anchor="w")
        tk.Entry(self.login_frame, textvariable=self.ip_var).pack(fill="x", pady=5)

        tk.Button(self.login_frame, text="CONNETTI", bg="lightblue", 
                  command=self._handle_connect_click).pack(fill="x", pady=20)

    def _setup_game(self):
        self.log_area = scrolledtext.ScrolledText(self.game_frame, state='disabled', height=15)
        self.log_area.pack(fill="both", expand=True, pady=5)

        input_frame = tk.Frame(self.game_frame)
        input_frame.pack(fill="x", pady=5)

        tk.Entry(input_frame, textvariable=self.msg_var).pack(side="left", fill="x", expand=True)
        tk.Button(input_frame, text="Invia", command=self._handle_send_click).pack(side="right", padx=5)

    def _handle_connect_click(self):
        user = self.username_var.get()
        ip = self.ip_var.get()
        if user and ip:
            self.on_connect(ip, user)
        else:
            messagebox.showerror("Errore", "Inserisci tutti i dati")

    def _handle_send_click(self):
        msg = self.msg_var.get()
        if msg:
            self.on_send(msg)
            self.msg_var.set("")

    def show_login(self):
        self.game_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def show_game(self):
        self.login_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)

    def append_log(self, text):
        """Scrive un messaggio nell'area di testo"""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
