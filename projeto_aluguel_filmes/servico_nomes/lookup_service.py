import os
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer


class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
	pass


class LookupService:
	def __init__(self) -> None:
		self._registry: dict[str, dict] = {}

	def register(self, service_name: str, host: str, port: int) -> dict:
		self._registry[service_name] = {
			"host": host,
			"port": int(port),
		}
		return {
			"ok": True,
			"mensagem": f"Serviço '{service_name}' registrado em {host}:{port}",
		}

	def lookup(self, service_name: str) -> dict:
		entry = self._registry.get(service_name)
		if not entry:
			return {
				"ok": False,
				"mensagem": f"Serviço '{service_name}' não encontrado.",
			}
		return {"ok": True, "service": entry}

	def heartbeat(self, service_name: str) -> bool:
		return service_name in self._registry


def main() -> None:
	host = os.getenv("LOOKUP_HOST", "127.0.0.1")
	port = int(os.getenv("LOOKUP_PORT", "9000"))

	service = LookupService()
	with ThreadedXMLRPCServer((host, port), allow_none=True, logRequests=True) as server:
		server.register_introspection_functions()
		server.register_instance(service)
		print(f"[LOOKUP] Serviço de nomes ativo em {host}:{port}")
		server.serve_forever()


if __name__ == "__main__":
	main()

