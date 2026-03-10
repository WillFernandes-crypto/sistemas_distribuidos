# Projeto: Aplicação Distribuída de Aluguel de Filmes

Este projeto implementa uma aplicação distribuída em Python para aluguel de filmes, com comunicação via RPC e separação em camadas.

## Objetivo acadêmico

Exercitar conceitos de Sistemas Distribuídos, incluindo:

- Descoberta de serviços (Service Discovery)
- Transparência de localização
- Concorrência com múltiplos clientes
- Sincronização para evitar condição de corrida
- Separação de responsabilidades em arquitetura em camadas

## Arquitetura

Estrutura do projeto:

- `cliente/app_cliente.py`: camada de apresentação (CLI)
- `cliente/app_cliente_gui.py`: camada de apresentação (GUI com cards e animacoes)
- `servico_nomes/lookup_service.py`: nó de nomes (registro e busca de serviços)
- `servidor/servidor_rpc.py`: servidor de negócio (RPC multithread)
- `servidor/sincronizacao.py`: exclusão mútua por recurso
- `database/persistencia.py`: persistência com SQLite
- `requirements.txt`: dependências externas da interface/infra

Fluxo principal:

1. O `lookup_service.py` sobe e espera registros de serviços.
2. O `servidor_rpc.py` inicia e se registra no lookup (`register`).
3. O `app_cliente.py` consulta o lookup (`lookup`) para descobrir endereço do servidor.
4. O cliente invoca métodos remotos do servidor para listar e alugar filmes.

## Tecnologias usadas

- Python 3.10+
- `xmlrpc.server` e `xmlrpc.client` (RPC)
- `socketserver.ThreadingMixIn` (atendimento concorrente)
- `sqlite3` (persistência local)
- `threading.Lock` (sincronização)
- `Pillow` (renderização de capas de filmes na interface GUI)

## Funcionalidades implementadas

### Serviço de nomes (`lookup_service.py`)

- `register(service_name, host, port)`: registra um serviço no diretório
- `lookup(service_name)`: retorna host/porta do serviço
- `heartbeat(service_name)`: verifica se o serviço está registrado

### Servidor RPC (`servidor_rpc.py`)

- Registro automático no serviço de nomes ao iniciar
- `listar_filmes()`: retorna catálogo com cópias disponíveis
- `alugar_filme(filme_id, cliente)`: efetiva aluguel com lock por filme
- `devolver_filme(filme_id, cliente)`: registra devolução e reestabelece estoque
- `historico_alugueis()`: retorna histórico de aluguéis
- Suporte a múltiplas requisições simultâneas (multithread)

### Persistência (`persistencia.py`)

- Criação automática de banco SQLite (`database/catalogo_filmes.db`)
- Criação das tabelas `filmes` e `alugueis`
- Carga inicial (seed) do catálogo na primeira execução
- Migração automática da coluna de devolução para bases já existentes

### Sincronização (`sincronizacao.py`)

- Lock por recurso (`filme:<id>`) para garantir exclusão mútua
- Evita duas locações simultâneas da mesma última cópia

### Cliente (`app_cliente.py`)

- Interface CLI com menu:
  - Listar filmes
  - Alugar filme
  - Devolver filme
  - Ver histórico
- Descoberta automática do servidor via lookup

### Cliente GUI (`app_cliente_gui.py`)

- Catálogo visual em grade com capas de filmes (ícones)
- Nome do filme exibido logo abaixo de cada capa
- Busca por título com filtro instantâneo no catálogo
- Seleção por clique na capa para aluguel/devolução
- Carregamento assincrono para evitar travamentos da interface
- Feedback visual com notificacoes animadas (toast)
- Janela dedicada para historico com status (`ativo`/`devolvido`)
- Descoberta automatica do servidor via lookup (mesmo fluxo RPC do CLI)

## Como executar

> Execute os comandos **a partir da pasta `projeto_aluguel_filmes`**.

### 1) Subir o serviço de nomes

```bash
python servico_nomes/lookup_service.py
```

### 2) Subir o servidor de aluguel

Em outro terminal:

```bash
python servidor/servidor_rpc.py
```

### 3) Executar o cliente

Em outro terminal:

```bash
python cliente/app_cliente.py
```

### 4) (Opcional) Executar a interface grafica

Em outro terminal:

```bash
python cliente/app_cliente_gui.py
```

## Variáveis de ambiente opcionais

Se quiser mudar portas/host sem alterar código:

- `LOOKUP_HOST` (default: `127.0.0.1`)
- `LOOKUP_PORT` (default: `9000`)
- `SERVER_HOST` (default: `127.0.0.1`)
- `SERVER_PORT` (default: `9100`)
- `SERVICE_NAME` (default: `filmes_rpc`)

Exemplo (PowerShell):

```powershell
$env:LOOKUP_PORT="9001"
python servico_nomes/lookup_service.py
```

## Cenário de demonstração (apresentação)

1. Inicie lookup, servidor e cliente.
2. No cliente, liste o catálogo.
3. Abra um segundo cliente e tente alugar o mesmo filme com apenas 1 cópia.
4. Mostre que apenas um aluguel é confirmado quando acabar o estoque.
5. Faça a devolução do filme e confirme o retorno do estoque.
6. Exiba o histórico para comprovar operações ativas e devolvidas.

## Observações

- A GUI usa `Pillow` para leitura e redimensionamento das capas.
- O banco SQLite é criado automaticamente na primeira execução.
- Para reiniciar o estado inicial, remova o arquivo `database/catalogo_filmes.db`.
