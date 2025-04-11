import socket
import ssl
import threading
import sqlite3

# Configuration
HOST = '127.0.0.1'
PORT = 5001
CERTFILE = "server.crt"
KEYFILE = "server.key"

# Handle client connection
def handle_client(connstream, addr):
    print(f"Connected by {addr}")
    try:
        while True:
            data = connstream.recv(1024).decode()
            if not data:
                break
            print(f"Received from {addr}: {data}")
            response = process_request(data)
            connstream.sendall(response.encode())
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        connstream.close()

# Protocol logic for handling commands
def process_request(data):
    try:
        command, *params = data.strip().split("|")
        if command == "VOTE":
            user_id, photo_id = params
            return record_vote(user_id, photo_id)
        elif command == "LEADERBOARD":
            return get_leaderboard()
        else:
            return "ERROR|Unknown command"
    except Exception as e:
        return f"ERROR|{str(e)}"

# Store vote in database securely
def record_vote(user_id, photo_id):
    conn = sqlite3.connect("voting_system.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM vote WHERE user_id=?", (user_id,))
    if cur.fetchone():
        conn.close()
        return "ERROR|Already voted"
    cur.execute("INSERT INTO vote (user_id, photo_id, encrypted_vote) VALUES (?, ?, ?)", (user_id, photo_id, f"encrypted_{photo_id}"))
    conn.commit()
    conn.close()
    return "SUCCESS|Vote recorded"

# Retrieve vote counts
def get_leaderboard():
    conn = sqlite3.connect("voting_system.db")
    cur = conn.cursor()
    cur.execute("SELECT photo_id, COUNT(*) FROM vote GROUP BY photo_id")
    results = cur.fetchall()
    conn.close()
    return "LEADERBOARD|" + ";".join([f"{row[0]}:{row[1]}" for row in results])

# Start server with SSL
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind((HOST, PORT))
    server.listen()
    print(f"Socket Server listening on {HOST}:{PORT}")

    while True:
        client_sock, addr = server.accept()
        connstream = context.wrap_socket(client_sock, server_side=True)
        threading.Thread(target=handle_client, args=(connstream, addr)).start()
