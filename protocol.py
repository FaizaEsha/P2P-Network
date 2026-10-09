"""
protocol.py - application-level protocol helpers.

Wire format of every control message:

    [4-byte big-endian length][JSON payload (UTF-8)]

File transfer = a "file" JSON message (metadata) followed by exactly
`filesize` raw bytes of the file (sent in chunks, NOT length-prefixed).
"""
import json
import struct

HEADER = struct.Struct("!I")        # 4-byte unsigned int, network byte order
CHUNK_SIZE = 64 * 1024              # 64 KB per file chunk
MAX_MESSAGE_SIZE = 10 * 1024 * 1024 # sanity limit for a JSON message

# message types
HELLO = "hello"
HELLO_ACK = "hello_ack"
TEXT = "text"
FILE = "file"


def recv_exact(sock, n):
    """Read exactly n bytes from the socket (recv may return fewer)."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Peer disconnected")
        buf.extend(chunk)
    return bytes(buf)


def send_json(sock, obj):
    """Frame and send a dict as [4-byte length][JSON]."""
    payload = json.dumps(obj).encode("utf-8")
    sock.sendall(HEADER.pack(len(payload)) + payload)


def recv_json(sock):
    """Receive one framed JSON message and return it as a dict."""
    (length,) = HEADER.unpack(recv_exact(sock, HEADER.size))
    if length <= 0 or length > MAX_MESSAGE_SIZE:
        raise ValueError(f"Invalid message length: {length}")
    return json.loads(recv_exact(sock, length).decode("utf-8"))


def make_hello(kind, peer_id, name, port):
    return {"type": kind, "peer_id": peer_id, "peer_name": name, "port": port}


def make_text(peer_id, name, message):
    return {"type": TEXT, "sender_id": peer_id, "sender_name": name,
            "message": message}


def make_file_meta(peer_id, name, filename, filesize):
    return {"type": FILE, "sender_id": peer_id, "sender_name": name,
            "filename": filename, "filesize": filesize}
