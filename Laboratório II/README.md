# Laboratório II — RPC com RPyC (Python)

## Descrição
- Servidor RPC expõe o método `get_time()` que retorna o horário atual.
- Cliente conecta via RPyC, solicita o horário e encerra.

## Requisitos
- Python 3.8+
- Dependência: `rpyc`

## Instalação
```powershell
python -m pip install -r ".\Laboratório II\requirements.txt"
```

## Como executar

1. Iniciar o servidor (a partir de `Sistemas Distribuídos`):
```powershell
python ".\Laboratório II\server.py"
```

2. Executar o cliente:
```powershell
python ".\Laboratório II\client.py"
```

## Observações
- O servidor usa `ThreadedServer` na porta `8001`.
- O cliente invoca `conn.root.get_time()`.
# Laboratório I — Modelo Cliente/Servidor com Sockets (Python)

## Descrição
- Servidor TCP multithread escutando em `8000`.
- Atende um pedido por conexão: se recebe `TIME`, retorna o horário atual; caso contrário, reverte a string recebida e envia de volta.
- Cliente envia uma string (por padrão `Olá Mundo Distribuído`) e encerra após receber a resposta.

## Requisitos
- Python 3.8+
- Sistema: Windows (testado), mas funciona em outros SOs.

## Como executar

Abra dois terminais PowerShell.

1. Iniciar o servidor (execute a partir de `Sistemas Distribuídos`):
```powershell
python ".\Laboratório I\server.py"
```

2. Executar o cliente com a mensagem padrão (string será revertida):
```powershell
python ".\Laboratório I\client.py"
```

3. Solicitar horário atual do servidor:
```powershell
python ".\Laboratório I\client.py" TIME
```

4. Enviar uma string customizada:
```powershell
python ".\Laboratório I\client.py" "Sua mensagem aqui"
```

## Observações
- Cada conexão trata apenas um pedido e é encerrada.
- O servidor cria uma thread por conexão (`daemon=True`).
- Porta e host podem ser ajustados editando constantes em `server.py` e `client.py`.

# Laboratório II — Modelo RPC com RPyC

## Descrição
- Servidor RPyC que expõe um único método remoto: retornar o horário atual.
- Cliente solicita o horário ao servidor e encerra.

## Requisitos
- Python 3.8+
- Biblioteca RPyC

## Como executar

1. Instalar dependência:
```powershell
pip install rpyc
```

2. Iniciar o servidor:
```powershell
python ".\Laboratório I\server_rpc.py"
```

3. Executar o cliente:
```powershell
python ".\Laboratório I\client_rpc.py"
```

## Observações
- Porta padrão: `18812` (padrão do RPyC).
- Host e porta podem ser ajustados em `server_rpc.py` e `client_rpc.py`.