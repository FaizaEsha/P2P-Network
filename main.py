"""
main.py - Tkinter user interface for the P2P network.  Run:  python main.py
"""
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from p2p_node import P2PNode

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")


class App:
    def __init__(self, root):
        self.root = root
        root.title("UAP P2P Network")
        root.geometry("900x620")
        self.node = None
        self.listed_ids = []            # peer_ids in the same order as listbox
        self.events = queue.Queue()     # worker threads -> GUI thread
        self._build_ui()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self._poll_events)

    # ------------------------------------------------------------- layout
    def _build_ui(self):
        pad = {"padx": 6, "pady": 4}

        f = ttk.LabelFrame(self.root, text="My Peer")
        f.pack(fill="x", padx=8, pady=4)
        ttk.Label(f, text="Name:").grid(row=0, column=0, **pad)
        self.name_var = tk.StringVar(value="Alice")
        self.name_entry = ttk.Entry(f, textvariable=self.name_var, width=16)
        self.name_entry.grid(row=0, column=1, **pad)
        ttk.Label(f, text="Port:").grid(row=0, column=2, **pad)
        self.port_var = tk.StringVar(value="5000")
        self.port_entry = ttk.Entry(f, textvariable=self.port_var, width=8)
        self.port_entry.grid(row=0, column=3, **pad)
        self.start_btn = ttk.Button(f, text="Start Peer", command=self.start_peer)
        self.start_btn.grid(row=0, column=4, **pad)
        self.stop_btn = ttk.Button(f, text="Stop", command=self.stop_peer,
                                   state="disabled")
        self.stop_btn.grid(row=0, column=5, **pad)
        self.info_var = tk.StringVar(value="Not running")
        ttk.Label(f, textvariable=self.info_var).grid(row=1, column=0,
                                                       columnspan=6, sticky="w", **pad)

        f = ttk.LabelFrame(self.root, text="Connect to Another Peer")
        f.pack(fill="x", padx=8, pady=4)
        ttk.Label(f, text="IP:").grid(row=0, column=0, **pad)
        self.ip_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(f, textvariable=self.ip_var, width=18).grid(row=0, column=1, **pad)
        ttk.Label(f, text="Port:").grid(row=0, column=2, **pad)
        self.rport_var = tk.StringVar(value="5000")
        ttk.Entry(f, textvariable=self.rport_var, width=8).grid(row=0, column=3, **pad)
        self.connect_btn = ttk.Button(f, text="Connect", command=self.connect_peer,
                                      state="disabled")
        self.connect_btn.grid(row=0, column=4, **pad)

        mid = ttk.Frame(self.root)
        mid.pack(fill="both", expand=True, padx=8, pady=4)
        left = ttk.LabelFrame(mid, text="Connected Peers")
        left.pack(side="left", fill="y")
        self.peer_list = tk.Listbox(left, width=34, exportselection=False)
        self.peer_list.pack(fill="both", expand=True, padx=4, pady=4)
        right = ttk.LabelFrame(mid, text="Messages / Events")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.log = tk.Text(right, state="disabled", wrap="word",
                           font=("Consolas", 10))
        sb = ttk.Scrollbar(right, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True, padx=4, pady=4)
        self.log.tag_config("error", foreground="#c0392b")
        self.log.tag_config("system", foreground="#2c7a3f")

        f = ttk.LabelFrame(self.root, text="Send Text")
        f.pack(fill="x", padx=8, pady=4)
        self.msg_var = tk.StringVar()
        entry = ttk.Entry(f, textvariable=self.msg_var)
        entry.pack(side="left", fill="x", expand=True, padx=6, pady=6)
        entry.bind("<Return>", lambda e: self.send_text())
        ttk.Button(f, text="Send", command=self.send_text).pack(side="right", padx=6)

        f = ttk.LabelFrame(self.root, text="Send File")
        f.pack(fill="x", padx=8, pady=4)
        ttk.Label(f, text="Text, image, audio, video, PDF, ZIP, etc.").pack(
            side="left", padx=6, pady=6)
        ttk.Button(f, text="Choose File & Send",
                   command=self.send_file).pack(side="right", padx=6)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status_var, relief="sunken",
                  anchor="w").pack(fill="x", side="bottom")

    # ---------------------------------------------------- thread-safe glue
    def _on_log(self, text):            # called from any thread
        self.events.put(("log", text))

    def _on_peers_changed(self):        # called from any thread
        self.events.put(("peers", None))

    def _poll_events(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "log":
                    self._append_log(data)
                elif kind == "peers":
                    self._refresh_peers()
                elif kind == "status":
                    self.status_var.set(data)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _append_log(self, text):
        tag = "error" if text.startswith("[ERROR]") else \
              "system" if text.startswith("[SYSTEM]") else None
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")
        self.status_var.set(text[:120])

    def _refresh_peers(self):
        selected = self._selected_id()
        self.peer_list.delete(0, "end")
        self.listed_ids = []
        if self.node:
            for p in self.node.get_peers():
                self.peer_list.insert("end", p.label())
                self.listed_ids.append(p.peer_id)
        if selected in self.listed_ids:
            self.peer_list.selection_set(self.listed_ids.index(selected))

    def _selected_id(self):
        sel = self.peer_list.curselection()
        return self.listed_ids[sel[0]] if sel else None

    # ------------------------------------------------------------ actions
    def start_peer(self):
        name = self.name_var.get().strip()
        if not name:
            return messagebox.showerror("Error", "Enter a peer name")
        try:
            port = int(self.port_var.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            return messagebox.showerror("Error", "Port must be 1-65535")
        node = P2PNode(name, port, DOWNLOAD_DIR, self._on_log,
                       self._on_peers_changed)
        try:
            node.start()
        except OSError as e:
            return self._on_log(f"[ERROR] Cannot start peer on port {port}. "
                                f"The port is already in use - choose a different port. ({e})")
        self.node = node
        self.info_var.set(f"{name} | ID: {node.peer_id} | IP: {node.ip} | Port: {port}")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.connect_btn.config(state="normal")
        self.name_entry.config(state="disabled")   # change name/port only after Stop
        self.port_entry.config(state="disabled")
        self._on_log(f"[SYSTEM] Peer started: {name} [{node.peer_id}] on {node.ip}:{port}")

    def stop_peer(self):
        if self.node:
            self.node.stop()
            self.node = None
        self.info_var.set("Not running")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.connect_btn.config(state="disabled")
        self.name_entry.config(state="normal")
        self.port_entry.config(state="normal")

    def connect_peer(self):
        ip = self.ip_var.get().strip()
        if not ip:
            return self._on_log("[ERROR] Invalid IP address")
        try:
            port = int(self.rport_var.get())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            return self._on_log("[ERROR] Invalid port")
        node = self.node

        def work():                     # keep the GUI responsive
            try:
                node.connect(ip, port)
            except Exception as e:
                self._on_log(f"[ERROR] Connection failed: {e}")
        threading.Thread(target=work, daemon=True).start()

    def send_text(self):
        if not self.node:
            return self._on_log("[ERROR] Start your peer first")
        pid = self._selected_id()
        if not pid:
            return self._on_log("[ERROR] Select a peer from the list first")
        msg = self.msg_var.get().strip()
        if not msg:
            return
        try:
            self.node.send_text(pid, msg)
            self.msg_var.set("")
        except Exception as e:
            self._on_log(f"[ERROR] {e}")

    def send_file(self):
        if not self.node:
            return self._on_log("[ERROR] Start your peer first")
        pid = self._selected_id()
        if not pid:
            return self._on_log("[ERROR] Select a peer from the list first")
        path = filedialog.askopenfilename(title="Choose a file to send")
        if not path:
            return
        node = self.node

        def work():                     # large files must not freeze the GUI
            self.events.put(("status", f"Sending {os.path.basename(path)} ..."))
            try:
                node.send_file(pid, path)
            except Exception as e:
                self._on_log(f"[ERROR] {e}")
        threading.Thread(target=work, daemon=True).start()

    def on_close(self):
        if self.node:
            self.node.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
