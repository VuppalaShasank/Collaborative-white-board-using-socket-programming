import os
import socket
import threading
import logging
logging.basicConfig(level=logging.DEBUG)

HOST = "0.0.0.0"  # Listen on all interfaces, or replace with your IP for testing
PORT = 5555
BUFFER_SIZE = 1024

clients = {}
shapes = []  # To track drawn shapes

def handle_client(client_socket, address):
    print(f"New connection from {address}")
    try:
        while True:
            message_length = int.from_bytes(client_socket.recv(4), 'big')
            data = client_socket.recv(message_length).decode()
            if not data:
                break
            print(f"Received from {address}: {data}")  # Debug print
            broadcast(data, client_socket)
    except Exception as e:
        print(f"Error handling client {address}: {e}")
    finally:
        client_socket.close()
        del clients[client_socket]

def broadcast(message, sender_socket):
    for client_socket in clients:
        if client_socket != sender_socket:
            try:
                client_socket.sendall(len(message.encode()).to_bytes(4, 'big'))
                client_socket.sendall(message.encode())
            except Exception as e:
                print(f"Error broadcasting to {clients[client_socket]}: {e}")

def start_whiteboard_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server started on {HOST}:{PORT}")
    try:
        while True:
            try:
                client_socket, address = server_socket.accept()
                clients[client_socket] = address
                client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
                client_thread.start()
            except Exception as e:
                logging.error(f"Error accepting connection: {e}")
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        server_socket.close()

def start_whiteboard_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server started on {HOST}:{PORT}")
    try:
        while True:
            client_socket, address = server_socket.accept()
            clients[client_socket] = address
            client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
            client_thread.start()
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        server_socket.close()

def main():
    start_whiteboard_server()

if __name__ == "__main__":
    main()
