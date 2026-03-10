import os
import sys
from pathlib import Path
from socketserver import ThreadingMixIn
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database.persistencia import RepositorioFilmes
from servidor.sincronizacao import GerenciadorLocks


class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
	pass


class ServidorAluguel:
	def __init__(self) -> None:
		db_path = str(Path(__file__).resolve().parents[1] / "database" / "catalogo_filmes.db")
		self.repositorio = RepositorioFilmes(db_path=db_path)
		self.locks = GerenciadorLocks()

	def ping(self) -> str:
		return "pong"

	def listar_filmes(self) -> list:
		return self.repositorio.listar_filmes()

	def alugar_filme(self, filme_id: int, cliente: str) -> dict:
		chave_recurso = f"filme:{filme_id}"
		with self.locks.lock_recurso(chave_recurso):
			return self.repositorio.alugar_filme(filme_id=int(filme_id), cliente=cliente)

	def devolver_filme(self, filme_id: int, cliente: str) -> dict:
		chave_recurso = f"filme:{filme_id}"
		with self.locks.lock_recurso(chave_recurso):
			return self.repositorio.devolver_filme(filme_id=int(filme_id), cliente=cliente)

	def historico_alugueis(self) -> list:
		return self.repositorio.historico_alugueis()


def registrar_no_lookup(lookup_url: str, service_name: str, host: str, port: int) -> None:
	proxy = ServerProxy(lookup_url, allow_none=True)
	resposta = proxy.register(service_name, host, port)
	if not resposta.get("ok"):
		raise RuntimeError(f"Falha ao registrar no lookup: {resposta}")


def main() -> None:
	host = os.getenv("SERVER_HOST", "127.0.0.1")
	port = int(os.getenv("SERVER_PORT", "9100"))
	service_name = os.getenv("SERVICE_NAME", "filmes_rpc")
	lookup_host = os.getenv("LOOKUP_HOST", "127.0.0.1")
	lookup_port = int(os.getenv("LOOKUP_PORT", "9000"))
	lookup_url = f"http://{lookup_host}:{lookup_port}"

	servidor = ServidorAluguel()
	registrar_no_lookup(lookup_url, service_name, host, port)

	with ThreadedXMLRPCServer((host, port), allow_none=True, logRequests=True) as rpc_server:
		rpc_server.register_introspection_functions()
		rpc_server.register_instance(servidor)
		print(f"[SERVIDOR] Serviço de aluguel ativo em {host}:{port}")
		print(f"[SERVIDOR] Registrado no lookup em {lookup_url} como '{service_name}'")
		rpc_server.serve_forever()


if __name__ == "__main__":
	main()

