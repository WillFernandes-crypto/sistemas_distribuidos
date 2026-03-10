import os
from xmlrpc.client import ServerProxy


def obter_proxy_servidor() -> ServerProxy:
	lookup_host = os.getenv("LOOKUP_HOST", "127.0.0.1")
	lookup_port = int(os.getenv("LOOKUP_PORT", "9000"))
	service_name = os.getenv("SERVICE_NAME", "filmes_rpc")

	lookup = ServerProxy(f"http://{lookup_host}:{lookup_port}", allow_none=True)
	resposta = lookup.lookup(service_name)
	if not resposta.get("ok"):
		raise RuntimeError(
			"Não foi possível localizar o servidor de aluguel. "
			"Verifique se o lookup e o servidor estão em execução."
		)

	service = resposta["service"]
	host = service["host"]
	port = service["port"]
	return ServerProxy(f"http://{host}:{port}", allow_none=True)


def mostrar_filmes(proxy: ServerProxy) -> None:
	filmes = proxy.listar_filmes()
	print("\n=== Catálogo de Filmes ===")
	for filme in filmes:
		print(f"{filme['id']:>2} - {filme['titulo']} (disponíveis: {filme['disponiveis']})")


def alugar(proxy: ServerProxy) -> None:
	try:
		filme_id = int(input("Informe o ID do filme: ").strip())
	except ValueError:
		print("ID inválido.")
		return

	cliente = input("Seu nome: ").strip() or "Cliente Anônimo"
	resposta = proxy.alugar_filme(filme_id, cliente)
	print(resposta.get("mensagem", "Sem mensagem retornada."))


def devolver(proxy: ServerProxy) -> None:
	try:
		filme_id = int(input("Informe o ID do filme para devolver: ").strip())
	except ValueError:
		print("ID inválido.")
		return

	cliente = input("Seu nome: ").strip() or "Cliente Anônimo"
	resposta = proxy.devolver_filme(filme_id, cliente)
	print(resposta.get("mensagem", "Sem mensagem retornada."))


def mostrar_historico(proxy: ServerProxy) -> None:
	historico = proxy.historico_alugueis()
	print("\n=== Histórico de Aluguéis ===")
	if not historico:
		print("Nenhum aluguel registrado.")
		return

	for item in historico:
		print(
			f"#{item['id']} | {item['data_hora']} | "
			f"{item['cliente']} alugou '{item['titulo']}'"
		)


def main() -> None:
	print("Cliente de Aluguel de Filmes (RPC)")
	try:
		proxy = obter_proxy_servidor()
	except Exception as exc:
		print(f"Erro ao conectar: {exc}")
		return

	while True:
		print("\n1) Listar filmes")
		print("2) Alugar filme")
		print("3) Devolver filme")
		print("4) Ver histórico")
		print("0) Sair")
		opcao = input("Escolha: ").strip()

		if opcao == "1":
			mostrar_filmes(proxy)
		elif opcao == "2":
			alugar(proxy)
		elif opcao == "3":
			devolver(proxy)
		elif opcao == "4":
			mostrar_historico(proxy)
		elif opcao == "0":
			print("Encerrando cliente.")
			break
		else:
			print("Opção inválida.")


if __name__ == "__main__":
	main()

