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

## 5. How to Use

1. Enter a peer name and an available port, then click **Start Peer**.
2. To connect to another peer, enter its IP address and listening port, then click **Connect**.
3. Select a peer in the **Connected Peers** list before sending a text message or file.
4. To transfer a file, click **Choose File & Send** and select the file. The receiving peer saves it in the `downloads/` folder.

For peers on the same computer, use `127.0.0.1` and the other peer's port. For peers on different computers, use the other computer's LAN IP address and the peer's listening port.

## 6. How It Works

**TCP connections:** Each peer listens for incoming connections and can also initiate a connection to another peer. Threads are used to accept and handle peer connections.

**Peer identification:** After a connection is established, peers exchange `hello` and `hello_ack` messages containing the peer ID, name, and port.

**Text and file transfer:** Control messages are encoded as JSON with a four-byte length header. For file transfers, the sender sends file metadata followed by the file's binary data in 64 KB chunks. The receiver writes the data to its `downloads/` folder.

## 7. Testing and Screenshots

The application was tested using two physical devices connected to the same local network: Device 1 runs Windows, and Device 2 runs macOS. The screenshots show different stages of testing; they do not necessarily represent one simultaneous run of every peer.

| Device | Operating system | Peer | Port |
|---|---|---|---:|
| Device 1 | Windows | Faiza | 5000 |
| Device 1 | Windows | Esha | 5001 |
| Device 2 | macOS | Momo | 6000 |
| Device 2 | macOS | Qirat | 6001 |

### 7.1 Peer Startup

This screenshot shows the successful startup of a peer node with its assigned peer name and listening port.

![Peer startup](screenshots/01_peer_startup.png)

*Figure 1. Faiza and Esha started on separate ports on the Windows device.*

### 7.2 Local Text Messaging and File Transfer

It demonstrates text messaging between locally connected peers and the successful transfer of files.

![Local text and file test](screenshots/02_local_text_and_file_test.png)

*Figure 2. Text messaging and image/PDF file-transfer activity between local peers.*

### 7.3 Multi-Peer Connections and Audio Transfer

This illustrates communication between multiple connected peers and the transfer of an audio file through the P2P network.

![Multi-peer and audio transfer](screenshots/03_multi_peer_and_audio_transfer.png)

*Figure 3. Multiple peer connections and audio/file-transfer activity.*

### 7.4 Multi-Peer Network and File Transfer

This screenshot presents a four-peer network setup using their IP, demonstrating multiple peer instances from multiple devices communicating and the files are automatically saved in `downloads/` folder.

![Four-peer network](screenshots/04_four_peer_network.png)

*Figure 4. Peer connections and file-transfer activity in the multi-peer setup.*


![Qirat cross-device communication](screenshots/05_qirat_cross_device_communication.png)

*Figure 5. Qirat connected to a peer using a LAN address, with text/file-transfer activity visible.*

## 8. Error Handling

The application reports errors for invalid port input, connection failures, attempts to send without selecting a peer, and file-transfer problems. When a peer disconnects, it is removed from the connected-peer list. An incomplete received file is deleted if a transfer is interrupted.

![Error handling](screenshots/06_error_handling.png)

*Figure 6. The application displays an error when Send is pressed without selecting a peer.*

## 9. Scope

This project demonstrates direct peer-to-peer communication using TCP sockets, text messaging, file transfer, and multiple peer connections. It does not implement a blockchain or cryptocurrency.
