# Peer-to-Peer Network Communication and File Sharing

| | |
|---|---|
| **University** | University of Asia Pacific, Department of Computer Science and Engineering |
| **Course** | CSE 433 – Blockchain & Distributed Security Lab |
| **Assignment** | Peer-to-Peer Network Communication and File Sharing |
| **Student** | Faiza Ahmed Esha |
| **Student ID** | 22201121 |
| **Section** | AB2 |
| **Language** | Python |

## 1. Project Description

This project is a Python-based peer-to-peer (P2P) application that allows peers to connect directly over TCP sockets, exchange text messages, and transfer files without a central server. Each running application instance can accept incoming connections and connect to other peers.

## 2. Requirements

- Python 3.9 or later, with Tkinter support.
- Windows or macOS for the tested setup.
- For communication between devices, both computers must be reachable on the same local network, and the connection must be allowed by the firewall.
- No third-party Python packages are required.

## 3. Project Structure

```text
22201121_AB2_P2P_Assignment/
├── main.py            # Graphical user interface
├── p2p_node.py        # Peer connections, messaging, and file transfer
├── protocol.py        # Message formatting and parsing
├── requirements.txt
├── README.md
├── downloads/         # Received files are saved here
└── screenshots/       # Assignment screenshots
```

### File Responsibilities

| File / Folder | Description |
| :--- | :--- |
| `main.py` | Creates the Tkinter GUI for user interaction. |
| `p2p_node.py` | Manages peer connections, threads, and data transfer. |
| `protocol.py` | Defines the communication message types. |
| `requirements.txt` | Lists dependencies. No external packages are needed. |
| `downloads/` | Saves received files. |
| `README.md` | Contains setup steps and project details. |

## 4. Setup and How to Run

1. Extract the project ZIP file.
2. Open a terminal in the project folder.
3. Check that Python is installed:

   ```bash
   python --version
   ```

4. Start the application:

   ```bash
   python main.py
   ```

Each application instance runs one peer. To run another peer on the same computer, open another terminal and run `python main.py` again with a different listening port.

## 5. System Overview

Each node works as both a **server and a client**, allowing two-way communication.

### Accepting Connections (Server)

Uses `socket()`, `bind()`, `listen()`, and `accept()` to receive connection requests from other nodes.

### Establishing Connections (Client)

Uses `socket()` and `connect()` to initiate communication with another node.

This dual functionality enables direct peer-to-peer communication without a central server.


## 6. How to Use

### Step 1: Start a Peer
1. Run `python main.py`.
2. Enter a peer name and an available port.
3. Click **Start Peer**.

### Step 2: Connect Two Peers

**On the Same Computer:**
1. Open two terminals and run `python main.py` in each.
2. Start **Peer1** on port `5000` and **Peer2** on port `5001`.
3. In Peer2's window, enter:
   - Remote IP: `127.0.0.1`
   - Remote Port: `5000`
4. Click **Connect**.

**On Different Computers (Same Wi-Fi/LAN):**
1. Start a peer on each computer.
2. Find Computer A's LAN IP (e.g., `192.168.1.10`).
3. On Computer B, enter Computer A's IP and listening port (`5000`).
4. Click **Connect**.

### Step 3: Send Messages and Files
1. Select a peer from the **Connected Peers** list.
2. Type a message and click **Send**.
3. To share a file, click **Choose File & Send** and select a file.
4. Received files are automatically saved in the `downloads/` folder.

## 7. How It Works

**TCP connections:** Each peer listens for incoming connections and can also initiate a connection to another peer. Threads are used to accept and handle peer connections.

**Peer identification:** After a connection is established, peers exchange `hello` and `hello_ack` messages containing the peer ID, name, and port.

**Text and file transfer:** Control messages are encoded as JSON with a four-byte length header. For file transfers, the sender sends file metadata followed by the file's binary data in 64 KB chunks. The receiver writes the data to its `downloads/` folder.

## 8. Testing and Screenshots

The application was tested using two physical devices connected to the same local network: Device 1 runs Windows, and Device 2 runs macOS. The screenshots show different stages of testing; they do not necessarily represent one simultaneous run of every peer.

| Device | Operating system | Peer | Port |
|---|---|---|---:|
| Device 1 | Windows | Faiza | 5000 |
| Device 1 | Windows | Esha | 5001 |
| Device 2 | macOS | Momo | 6000 |
| Device 2 | macOS | Qirat | 6001 |

### 8.1 Peer Startup

This screenshot shows the successful startup of a peer node with its assigned peer name and listening port.

![Peer startup](screenshots/01_peer_startup.png)

*Figure 1. Faiza and Esha started on separate ports on the Windows device.*

### 8.2 Local Text Messaging and File Transfer

It demonstrates text messaging between locally connected peers and the successful transfer of files.

![Local text and file test](screenshots/02_local_text_and_file_test.png)

*Figure 2. Text messaging and image/PDF file-transfer activity between local peers.*

### 8.3 Multi-Peer Connections and Audio Transfer

This illustrates communication between multiple connected peers and the transfer of an audio file through the P2P network.

![Multi-peer and audio transfer](screenshots/03_multi_peer_and_audio_transfer.png)

*Figure 3. Multiple peer connections and audio/file-transfer activity.*

### 8.4 Multi-Peer Network and File Transfer

This screenshot presents a four-peer network setup using their IP, demonstrating multiple peer instances from multiple devices communicating and the files are automatically saved in `downloads/` folder.

![Four-peer network](screenshots/04_four_peer_network.png)

*Figure 4. Peer connections and file-transfer activity in the multi-peer setup.*


![Qirat cross-device communication](screenshots/05_qirat_cross_device_communication.png)

*Figure 5. Qirat connected to a peer using a LAN address, with text/file-transfer activity visible.*

## 9. Error Handling

The application reports errors for invalid port input, connection failures, attempts to send without selecting a peer, and file-transfer problems. When a peer disconnects, it is removed from the connected-peer list. An incomplete received file is deleted if a transfer is interrupted.

![Error handling](screenshots/06_error_handling.png)

*Figure 6. The application displays an error when Send is pressed without selecting a peer.*

## 10. Scope

This project demonstrates direct peer-to-peer communication using TCP sockets, text messaging, file transfer, and multiple peer connections. It does not implement a blockchain or cryptocurrency.

The application is designed for local network communication and does not provide encryption or internet-wide peer discovery.
