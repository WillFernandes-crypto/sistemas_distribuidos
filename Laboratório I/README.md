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