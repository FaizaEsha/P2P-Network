"""
p2p_node.py - the peer: TCP server + TCP client in one object.

The node knows nothing about the GUI. It reports what happens through two
callbacks:  on_log(text)  and  on_peers_changed().
"""
import os
import socket
import threading
import uuid

import protocol as proto


def get_local_ip():
    """Return this computer's LAN (Wi-Fi) IP address, e.g. 192.168.1.10."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))   # no data is sent; only picks the interface
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def _close_socket(sock):
    """shutdown() first so blocked recv() calls wake up and the remote sees EOF."""
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        sock.close()
    except OSError:
        pass


class Peer:
    """A remote peer we are currently connected to."""

    def __init__(self, peer_id, name, ip, port, sock):
        self.peer_id = peer_id
        self.name = name
        self.ip = ip
        self.port = port          # the peer's LISTENING port (from HELLO)
        self.sock = sock
        self.send_lock = threading.Lock()  # never interleave text/file bytes

    def label(self):
        return f"{self.name} [{self.peer_id}] {self.ip}:{self.port}"


class P2PNode:
    def __init__(self, name, port, download_dir="downloads",
                 on_log=None, on_peers_changed=None):
        self.name = name
        self.port = port
        self.peer_id = uuid.uuid4().hex[:8]
        self.ip = get_local_ip()
        self.download_dir = download_dir
        self.on_log = on_log or (lambda msg: None)
        self.on_peers_changed = on_peers_changed or (lambda: None)

        self.server_socket = None
        self.running = False
        self.peers = {}                    # peer_id -> Peer
        self.peers_lock = threading.Lock()
        os.makedirs(self.download_dir, exist_ok=True)

    # ------------------------------------------------------------ server
    def start(self):
        """Create the listening socket and start accepting peers."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if os.name != "nt":   # on Windows SO_REUSEADDR would let two peers share one port
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.port))   # may raise OSError
        self.server_socket.listen()
        self.running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
            except OSError:
                break                       # server socket closed by stop()
            threading.Thread(target=self._handle_incoming,
                             args=(conn, addr), daemon=True).start()

    def _handle_incoming(self, conn, addr):
        """We are the server side: wait for HELLO, answer HELLO_ACK."""
        try:
            conn.settimeout(10)
            hello = proto.recv_json(conn)
            if hello.get("type") != proto.HELLO:
                raise ValueError("Expected HELLO")
            proto.send_json(conn, proto.make_hello(
                proto.HELLO_ACK, self.peer_id, self.name, self.port))
            conn.settimeout(None)
            peer = self._register(hello, addr[0], conn)
            if peer:
                self._receive_loop(peer)
            else:
                conn.close()
        except Exception as e:
            self.on_log(f"[ERROR] Incoming connection from {addr[0]} failed: {e}")
            try:
                conn.close()
            except OSError:
                pass

    # ------------------------------------------------------------ client
    def connect(self, ip, port):
        """Connect to another peer (client role). Raises on failure."""
        if not self.running:
            raise RuntimeError("Start your peer first")
        if port == self.port and ip in ("127.0.0.1", "localhost", "0.0.0.0", self.ip):
            raise ValueError("You cannot connect to yourself")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(5)
            sock.connect((ip, port))
            proto.send_json(sock, proto.make_hello(
                proto.HELLO, self.peer_id, self.name, self.port))
            ack = proto.recv_json(sock)
            if ack.get("type") != proto.HELLO_ACK:
                raise ValueError("Expected HELLO_ACK")
            sock.settimeout(None)
        except Exception:
            sock.close()
            raise
        peer = self._register(ack, ip, sock, remote_port=port)
        if peer is None:
            sock.close()
            raise ValueError("Already connected to this peer")
        threading.Thread(target=self._receive_loop, args=(peer,),
                         daemon=True).start()
        return peer

    # ------------------------------------------------------ peer registry
    def _register(self, info, ip, sock, remote_port=None):
        pid = info["peer_id"]
        with self.peers_lock:
            if pid == self.peer_id or pid in self.peers:
                return None
            peer = Peer(pid, info["peer_name"], ip,
                        remote_port or info["port"], sock)
            self.peers[pid] = peer
        self.on_log(f"[SYSTEM] Connected to {peer.name} ({peer.ip}:{peer.port})")
        self.on_peers_changed()
        return peer

    def _remove(self, peer, reason):
        with self.peers_lock:
            removed = self.peers.pop(peer.peer_id, None)
        _close_socket(peer.sock)
        if removed:
            self.on_log(f"[SYSTEM] {peer.name} disconnected ({reason})")
            self.on_peers_changed()

    def get_peers(self):
        with self.peers_lock:
            return list(self.peers.values())

    # --------------------------------------------------------- receiving
    def _receive_loop(self, peer):
        try:
            while self.running:
                msg = proto.recv_json(peer.sock)
                kind = msg.get("type")
                if kind == proto.TEXT:
                    self.on_log(f"{peer.name} -> You: {msg['message']}")
                elif kind == proto.FILE:
                    self._receive_file(peer, msg)
                else:
                    self.on_log(f"[ERROR] Unknown message type from {peer.name}")
        except (ConnectionError, OSError):
            self._remove(peer, "connection closed")
        except Exception as e:
            self._remove(peer, f"protocol error: {e}")

    def _receive_file(self, peer, meta):
        filesize = meta.get("filesize")
        if not isinstance(filesize, int) or filesize < 0:
            raise ValueError("Invalid file size")
        # basename() prevents a malicious name like ../../x from escaping
        filename = os.path.basename(meta.get("filename", "")) or "received_file"
        path = self._unique_path(filename)
        remaining = filesize
        try:
            with open(path, "wb") as f:
                while remaining > 0:
                    chunk = peer.sock.recv(min(proto.CHUNK_SIZE, remaining))
                    if not chunk:
                        raise ConnectionError("Disconnected during file transfer")
                    f.write(chunk)
                    remaining -= len(chunk)
        except Exception:
            if os.path.exists(path):
                os.remove(path)             # discard partial file
            raise
        self.on_log(f"{peer.name} -> You: File received: "
                    f"{os.path.basename(path)} ({filesize} bytes) "
                    f"saved to {path}")

    def _unique_path(self, filename):
        path = os.path.join(self.download_dir, filename)
        base, ext = os.path.splitext(filename)
        n = 1
        while os.path.exists(path):
            path = os.path.join(self.download_dir, f"{base}_{n}{ext}")
            n += 1
        return path

    # ----------------------------------------------------------- sending
    def _get_peer(self, peer_id):
        with self.peers_lock:
            peer = self.peers.get(peer_id)
        if peer is None:
            raise ValueError("Peer is not connected")
        return peer

    def send_text(self, peer_id, message):
        peer = self._get_peer(peer_id)
        try:
            with peer.send_lock:
                proto.send_json(peer.sock, proto.make_text(
                    self.peer_id, self.name, message))
        except OSError as e:
            self._remove(peer, str(e))
            raise ConnectionError(f"Send failed: {e}")
        self.on_log(f"You -> {peer.name}: {message}")

    def send_file(self, peer_id, filepath):
        peer = self._get_peer(peer_id)
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File does not exist: {filepath}")
        filesize = os.path.getsize(filepath)
        filename = os.path.basename(filepath)
        try:
            with peer.send_lock:            # metadata + bytes stay together
                proto.send_json(peer.sock, proto.make_file_meta(
                    self.peer_id, self.name, filename, filesize))
                with open(filepath, "rb") as f:
                    while True:
                        chunk = f.read(proto.CHUNK_SIZE)
                        if not chunk:
                            break
                        peer.sock.sendall(chunk)
        except OSError as e:
            self._remove(peer, str(e))
            raise ConnectionError(f"File send failed: {e}")
        self.on_log(f"You -> {peer.name}: File sent: {filename} ({filesize} bytes)")

    # -------------------------------------------------------------- stop
    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
        for peer in self.get_peers():
            _close_socket(peer.sock)
        with self.peers_lock:
            self.peers.clear()
        self.on_peers_changed()
        self.on_log("[SYSTEM] Peer stopped")
