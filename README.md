# EuroQuiz

Trabalho Prático da disciplina **DIN6920 - Sistemas Distribuídos** (Bacharelado em Ciência da Computação — Universidade Estadual de Maringá - UEM), ministrada pelo Prof. Dr. Alisson Renan Svaigen.

---

## Especificações Técnicas

- **Tema do Quiz:** Eurovision Song Contest (48 perguntas cadastradas no banco: 12 fáceis, 12 médias, 12 difíceis e 12 finais).
- **Linguagem de Programação:** **Python 3.12+** (containers Docker utilizam a imagem oficial `python:3.12-slim`).
- **Estratégia de Comunicação Cliente-Servidor:** **RPC (XML-RPC)** utilizando os módulos nativos `xmlrpc.client` e `xmlrpc.server` sobre HTTP/HTTPS.
- **Balanceamento de Carga:** Algoritmo **Round-Robin (RR) clássico** implementado manualmente em Python (`balancer/app.py`), operando de forma centralizada como ponto único de entrada (via túnel público do `ngrok`) e também como ponto de saída das respostas aos clientes.
- **SGBD / Banco de Dados:** **PostgreSQL 16** (`postgres:16-alpine`), inicializado automaticamente pelo script `database/init.sql`.
- **Acesso Externo:** **ngrok** (`ngrok/ngrok:latest`), expondo exclusivamente a porta `8000` do Balanceador de Carga para acesso externo pelos clientes.

### Bibliotecas Utilizadas

#### Bibliotecas Nativas do Python
- `xmlrpc.server` e `xmlrpc.client`: Implementação dos servidores RPC, do despacho no balanceador e das chamadas remotas no cliente.
- `socketserver` (`ThreadingMixIn`) e `threading`: Suporte a múltiplos clientes simultâneos e controle de concorrência (*thread-safe*) no índice do Round-Robin e na escrita do arquivo de log.
- `os`, `random`, `time`, `datetime`, `contextlib`: Manipulação de variáveis de ambiente, sorteio de questões/alternativas e controle de tempo.

#### Bibliotecas Adicionais (`requirements.txt`)
1. **`Flask==3.0.3`**: Utilizado exclusivamente na aplicação do **Cliente** (`client/app.py`) para renderizar a interface gráfica Web (as 6 telas obrigatórias) no navegador do jogador.
2. **`psycopg2-binary==2.9.9`**: Driver PostgreSQL utilizado pelos **3 Servidores** (`server/db.py`) para consultar o banco de questões e persistir todas as ações e o histórico das partidas.
3. **`python-dotenv==1.0.1`**: Utilizado para carregar as configurações do arquivo `.env`.

---

## Estrutura do Repositório

```text
euroquiz/
├── .env.example              # Modelo das variáveis de ambiente (Banco, Balanceador, Cliente e ngrok)
├── docker-compose.yml        # Orquestração dos 6 containers: postgres, server1..3, balancer e ngrok
├── requirements.txt          # Dependências externas do Python
├── README.md                 # Documentação e instruções de compilação e execução
├── database/
│   ├── init.sql              # Criação das tabelas (questions e game_history) e carga das 48 perguntas
│   └── diagrama_banco.svg    # Diagrama Entidade-Relacionamento (DER) da modelagem do banco
├── balancer/
│   └── app.py                # Balanceador de carga XML-RPC com Round-Robin clássico e registro de log
├── server/
│   ├── app.py                # Servidor XML-RPC (instanciado em 3 containers: servidor-1, servidor-2, servidor-3)
│   └── db.py                 # Camada de persistência e consultas SQL no PostgreSQL
├── client/
│   ├── app.py                # Interface Web do Cliente (conecta ao Balanceador via XML-RPC pelo ngrok)
│   └── templates/            # Telas HTML:
│       ├── index.html        # 1. Tela inicial
│       ├── ranking.html      # 2. Visualizar maiores pontuações (Top 10 vencedores)
│       ├── novo_jogo.html    # 3. Iniciar novo jogo (solicitação e validação de nickname único)
│       ├── pergunta.html     # 4. Tela de pergunta, alternativas e ajudas disponíveis
│       ├── fim_de_jogo.html  # 5. Tela de fim de jogo (em caso de erro)
│       └── campeao.html      # 6. Tela de vencedor (ao acertar a Pergunta Final)
└── logs/
    └── balancer.log          # Arquivo de log gerado pelo balanceador a cada requisição recebida
```

---

## Como Configurar e Executar o Sistema

A arquitetura foi projetada para execução distribuída em **2 dispositivos computacionais** (podendo também ser executada em um único dispositivo para testes):
- **Dispositivo 1 (Servidor Centralizado):** Executa via Docker Compose o banco PostgreSQL, os 3 Servidores (`servidor-1`, `servidor-2`, `servidor-3`), o Balanceador de Carga e o `ngrok`.
- **Dispositivo 2 (Cliente):** Executa a interface Web do jogador e realiza chamadas RPC apontando exclusivamente para o endereço público do `ngrok` associado ao balanceador.

---

### Passo 1: Executar o Dispositivo Servidor (Docker Compose + ngrok)

1. Na raiz do projeto, crie o arquivo `.env` a partir do `.env.example`:
   ```bash
   cp .env.example .env
   ```

2. Edite o arquivo `.env` preenchendo o seu `NGROK_AUTHTOKEN` e o seu `NGROK_DOMAIN` (obtidos no painel do [ngrok](https://dashboard.ngrok.com)):
   ```env
   # Configurações do Banco de Dados (PostgreSQL)
   POSTGRES_USER=euroquiz
   POSTGRES_PASSWORD=euroquiz123
   POSTGRES_DB=euroquiz
   POSTGRES_PORT=5432

   # Porta do Balanceador de Carga no host
   BALANCER_PORT=8000

   # Configurações do Cliente Web
   CLIENT_PORT=3000
   BALANCER_URL=https://cradling-language-nuclei.ngrok-free.dev

   # Configurações do ngrok (Acesso externo ao Balanceador de Carga)
   NGROK_AUTHTOKEN=seu_token_do_ngrok_aqui
   NGROK_DOMAIN=cradling-language-nuclei.ngrok-free.dev
   ```

3. Inicie todos os containers em segundo plano:
   ```bash
   sudo docker compose up -d
   ```

4. Verifique se todos os 6 containers (`euroquiz-postgres`, `euroquiz-server1`, `euroquiz-server2`, `euroquiz-server3`, `euroquiz-balancer` e `euroquiz-ngrok`) estão ativos:
   ```bash
   sudo docker compose ps
   ```

#### Monitoramento e Logs no Servidor
- **Acompanhar o arquivo de log obrigatório do Balanceador em tempo real:**
  ```bash
  tail -f logs/balancer.log
  ```
  Cada requisição RPC recebida grava uma linha no padrão exigido:
  ```text
  IP/porta cliente; tipo requisicao; horario; servidor atribuido
  ```
- **Visualizar a saída de console dos containers em tempo real:**
  ```bash
  sudo docker compose logs -f balancer server1 server2 server3
  ```
- **Painel do ngrok:** Disponível no navegador do servidor em `http://localhost:4040`.

---

### Passo 2: Executar o Dispositivo Cliente

No computador do **Cliente** (requer Python 3.10+ instalado):

1. Crie e ative um ambiente virtual Python e instale as dependências de `requirements.txt`:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Certifique-se de que o arquivo `.env` na máquina do cliente possui a variável `BALANCER_URL` apontando para o endereço público do **ngrok** do servidor:
   ```env
   CLIENT_PORT=3000
   BALANCER_URL=https://cradling-language-nuclei.ngrok-free.dev
   ```
   *(Para testes locais sem ngrok na mesma máquina do servidor, pode-se usar `BALANCER_URL=http://localhost:8000`).*

3. Inicie a aplicação do cliente:
   ```bash
   python client/app.py
   ```

4. Acesse a interface do jogo no navegador:
   ```text
   http://localhost:3000
   ```

---

## Como Parar Todos os Containers de Uma Vez

Para encerrar toda a aplicação do servidor de uma só vez, utilize um dos comandos abaixo na raiz do projeto:

- **Parar e remover todos os containers (mantendo os dados e o ranking salvos no banco PostgreSQL):**
  ```bash
  sudo docker compose down
  ```

- **Apenas pausar/parar os containers em execução (sem removê-los):**
  ```bash
  sudo docker compose stop
  ```

- **Parar todos os containers e ZERAR o banco de dados (apaga o volume do PostgreSQL para recriar as tabelas do zero na próxima subida):**
  ```bash
  sudo docker compose down -v
  ```

---

## Regras de Pontuação e Ajudas Implementadas

- **Formato da Partida:** 10 perguntas sorteadas sem repetição dentre as 48 questões do banco de dados, divididas em 4 níveis:
  - **Perguntas 1 a 3 (Nível Fácil):** **50 pontos** + bônus de tempo (`fator = 1`)
  - **Perguntas 4 a 6 (Nível Médio):** **100 pontos** + bônus de tempo (`fator = 1.5`)
  - **Perguntas 7 a 9 (Nível Difícil):** **300 pontos** + bônus de tempo (`fator = 2`)
  - **Pergunta 10 (Pergunta Final):** **1000 pontos** + bônus de tempo (`fator = 10`)
- **Fórmula do Bônus de Tempo:**
  ```text
  bônus = max(0, (60 - segundos)) * fator
  ```
- **Estratégia de Pontuação Final em Caso de Erro:**
  - Segue a regra padrão definida na especificação: caso o jogador erre uma pergunta, a partida é encerrada ("Fim de Jogo") e a sua pontuação final é a **pontuação acumulada até a pergunta imediatamente anterior** que foi respondida corretamente.
- **Ajudas Disponíveis (1 uso de cada por partida):**
  - **1/2 Meio a Meio (`meio_meio`):** Sorteia 2 alternativas incorretas da questão atual e as elimina da tela, restando a correta e 1 incorreta.
  - **Pular Questão (`pulo`):** Permite pular a pergunta atual, sorteando uma nova questão do mesmo nível ainda não apresentada na partida. Pode ser acionada mesmo após o uso do "Meio a Meio".
  - **Passe Livre (`passe_livre`):** O jogador acerta automaticamente a pergunta atual e avança para a próxima, recebendo apenas a pontuação base do nível (sem pontuação bônus de tempo). Não pode ser utilizada na Pergunta Final (questão 10).
