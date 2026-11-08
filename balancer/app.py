import os
import threading
import xmlrpc.client
from datetime import datetime
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer

# Lista de servidores disponíveis para o balanceamento Round-Robin
SERVERS_ENV = os.getenv(
    "SERVERS",
    "http://server1:5000,http://server2:5000,http://server3:5000",
)
SERVERS = [s.strip() for s in SERVERS_ENV.split(",") if s.strip()]
LOG_FILE = os.getenv("LOG_FILE", "/app/logs/balancer.log")
BALANCER_PORT = int(os.getenv("BALANCER_PORT", "8000"))

# Controle thread-safe para o algoritmo Round-Robin (RR) clássico
rr_lock = threading.Lock()
rr_index = 0


def get_next_server() -> tuple[str, str]:
    """Seleciona o próximo servidor seguindo a estratégia Round-Robin (RR) clássica."""
    global rr_index
    with rr_lock:
        server_url = SERVERS[rr_index]
        server_label = f"servidor-{rr_index + 1}"
        rr_index = (rr_index + 1) % len(SERVERS)
    return server_url, server_label


def log_request(client_addr: str, req_type: str, assigned_server: str) -> None:
    """
    Salva no arquivo de log uma linha por requisição no formato especificado:
    IP/porta cliente; tipo requisicao; horario; servidor atribuido
    """
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    horario = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{client_addr}; {req_type}; {horario}; {assigned_server}\n"
    with rr_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
    print(f"[BALANCER] {log_line.strip()}", flush=True)


class BalancerRPCRequestHandler(SimpleXMLRPCRequestHandler):
    """
    Manipulador XML-RPC nativo do Balanceador.
    Recebe a chamada RPC do cliente, aplica o Round-Robin, grava o log
    e repassa a execução ao servidor selecionado via xmlrpc.client.ServerProxy.
    """

    rpc_paths = ("/", "/RPC2", "/rpc")

    def extract_client_addr(self) -> str:
        """Obtém o IP e a porta do cliente (considerando headers do ngrok se presentes)."""
        forwarded_for = self.headers.get("X-Forwarded-For")
        client_ip = (
            forwarded_for.split(",")[0].strip()
            if forwarded_for
            else self.client_address[0]
        )
        client_port = self.headers.get(
            "X-Forwarded-Port",
            str(self.client_address[1]),
        )
        return f"{client_ip}:{client_port}"

    def _dispatch(self, method: str, params: tuple):
        """
        Intercepta qualquer chamada RPC feita pelo cliente, seleciona o servidor
        da vez no Round-Robin, registra no balancer.log e retorna a resposta.
        """
        target_base_url, server_label = get_next_server()
        client_addr = self.extract_client_addr()

        # Grava no arquivo de log obrigatório:
        # IP/porta cliente; tipo requisicao; horario; servidor atribuido
        log_request(
            client_addr,
            f"RPC:{method}",
            f"{server_label} ({target_base_url})",
        )

        # Repassa a chamada XML-RPC ao servidor selecionado e devolve a resposta ao cliente
        server_proxy = xmlrpc.client.ServerProxy(
            f"{target_base_url}/RPC2",
            allow_none=True,
            encoding="utf-8",
        )
        remote_function = getattr(server_proxy, method)
        return remote_function(*params)


class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    """Servidor XML-RPC multi-thread para atender múltiplos clientes simultaneamente."""

    daemon_threads = True


if __name__ == "__main__":
    print(
        f"[BALANCER] Iniciando Balanceador XML-RPC (Round-Robin) na porta {BALANCER_PORT}...",
        flush=True,
    )
    with ThreadedXMLRPCServer(
        ("0.0.0.0", BALANCER_PORT),
        requestHandler=BalancerRPCRequestHandler,
        allow_none=True,
        encoding="utf-8",
        logRequests=False,
    ) as server:
        server.serve_forever()
