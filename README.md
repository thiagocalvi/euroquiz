# EuroQuiz

Trabalho Prático da disciplina **6920 - Sistemas Distribuídos** (Bacharelado em Ciência da Computação - Universidade Estadual de Maringá - UEM)
---

## Especificações

- **Tema do Quiz:** Eurovision
- **Linguagem de Programação:** Python 3
- **Estratégia de Comunicação:** RPC
- **Balanceamento de Carga:** Algoritmo **Round-Robin (RR) clássico** implementado em (`balancer/app.py`).
- **SGBD / Banco de Dados:** PostgreSQL 16 (`postgres:16-alpine`)

### Bibliotecas Adicionais Utilizadas (`requirements.txt`)
Além das bibliotecas nativas do Python (`os`, `random`, `threading`, `datetime`, `contextlib`, `socketserver`, `xmlrpc.client`, `xmlrpc.server`), utilizamos as seguintes bibliotecas externas:
1. **`Flask==3.0.3`**: Microframework web utilizado na interface do cliente (`client/app.py`) para renderizar as telas no navegador.
2. **`psycopg2-binary`**: Driver adaptador de banco de dados PostgreSQL para Python, utilizado pelos 3 servidores para consultar as questões e persistir o histórico de cada jogo.
3. **`python-dotenv==1.0.1`**: Carregamento de variáveis de ambiente a partir do arquivo `.env`.

## Como Compilar e Executar o Sistema - Localmente por enquanto

A execução do sistema pode ser feita em **2 dispositivos** (ou localmente em um único dispositivo):
1. **Dispositivo 1 (Servidor Centralizado):** Executa o SGBD PostgreSQL, os 3 Servidores (`servidor-1`, `servidor-2`, `servidor-3`), o Balanceador de Carga e o túnel `ngrok`.
2. **Dispositivo 2 (Cliente):** Executa a interface Web do jogador e se comunica exclusivamente com o endereço público do `ngrok` associado ao balanceador.
---

### Passo 1: Executar o Servidor (Balanceador + 3 Servidores + SGBD)

1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```

2. Construa as imagens e inicie os serviços via **Docker Compose**:
   ```bash
   docker compose up -d
   ```
  
3. Verifique se os containers estão em execução:
   ```bash
   docker compose ps
   ```
   O arquivo de log do balanceador será gravado em `./logs/balancer.log` no formato:
   ```text
   IP/porta cliente; tipo requisicao; horario; servidor atribuido
   ```

---

### Passo 2: Executar o Cliente

É necessário ter o **Python 3+** instalado.

1. Instale as dependências listadas em `requirements.txt`:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Inicie o cliente:
   ```bash
   python client/app.py
   ```
   
3. Abra o navegador no endereço:
   ```text
   http://localhost:3000
   ```
