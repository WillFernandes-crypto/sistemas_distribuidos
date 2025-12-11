import socket
import sys


HOST = "127.0.0.1"
PORT = 8000


def request(message: str, host: str = HOST, port: int = PORT) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(message.encode("utf-8"))
        data = s.recv(1024)
    return data.decode("utf-8", errors="replace")


if __name__ == "__main__":
    # Usage:
    #   python client.py                -> sends default string
    #   python client.py TIME           -> asks server time
    #   python client.py "custom text"  -> sends custom text
    msg = "Olá Mundo Distribuído"
    if len(sys.argv) > 1:
        msg = sys.argv[1]
    resp = request(msg)
    print(f"Resposta do servidor: {resp}")
