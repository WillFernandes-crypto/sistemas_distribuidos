import socket
import threading
from datetime import datetime


HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 8000        # Fixed port as requested


def handle_client(conn: socket.socket, addr):
    try:
        data = conn.recv(1024)
        if not data:
            return

        message = data.decode("utf-8", errors="replace").strip()

        # If client asks for time, return current timestamp; otherwise reverse string
        if message.upper() == "TIME":
            response = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            response = message[::-1]

        conn.sendall(response.encode("utf-8"))
    finally:
        conn.close()


def start_server(host: str = HOST, port: int = PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        print(f"Servidor escutando em {host}:{port}")

        while True:
            conn, addr = s.accept()
            print(f"Conexão de {addr}")
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()


if __name__ == "__main__":
    start_server()
