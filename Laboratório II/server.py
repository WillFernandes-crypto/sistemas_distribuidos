import rpyc
from rpyc.utils.server import ThreadedServer
from datetime import datetime


class TimeService(rpyc.Service):
    def exposed_get_time(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    server = ThreadedServer(TimeService, port=8001, protocol_config={"allow_public_attrs": True})
    print("Servidor RPyC escutando na porta 8001")
    server.start()


if __name__ == "__main__":
    main()
