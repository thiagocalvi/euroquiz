import os
import time
import xmlrpc.client
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for

load_dotenv()

app = Flask(__name__)

# Endereço de acesso balanceador
BALANCER_URL = os.getenv("BALANCER_URL", "http://localhost:8000").rstrip("/")
CLIENT_PORT = int(os.getenv("CLIENT_PORT", "3000"))


class NgrokXMLRPCTransport(xmlrpc.client.Transport):
    """Transporte HTTP para XML-RPC adiciona header para evitar bloqueio do ngrok gratuito."""

    def send_headers(self, connection, headers):
        headers.append(("ngrok-skip-browser-warning", "true"))
        super().send_headers(connection, headers)


class NgrokXMLRPCSafeTransport(xmlrpc.client.SafeTransport):
    """Transporte HTTPS para XML-RPC que adiciona header para evitar bloqueio do ngrok gratuito."""

    def send_headers(self, connection, headers):
        headers.append(("ngrok-skip-browser-warning", "true"))
        super().send_headers(connection, headers)


def get_rpc_proxy() -> xmlrpc.client.ServerProxy:
    """Cria o cliente XML-RPC conectado ao endereço do Balanceador de Carga."""
    rpc_endpoint = f"{BALANCER_URL}/RPC2"
    transport = (
        NgrokXMLRPCSafeTransport()
        if rpc_endpoint.startswith("https://")
        else NgrokXMLRPCTransport()
    )
    return xmlrpc.client.ServerProxy(
        rpc_endpoint,
        transport=transport,
        allow_none=True,
        encoding="utf-8",
    )


# ==============================================================================
# FUNÇÕES PARA COMUNICAÇÃO RPC COM O BALANCEADOR DE CARGA
# ==============================================================================


def balanceador_verificar_nickname(nickname: str) -> bool:
    """
    Solicita ao balanceador verificar via RPC se o nickname já existe no banco de dados.
    Retorna True se estiver disponível, False caso contrário.
    """
    return bool(get_rpc_proxy().verificar_nickname(nickname))


def balanceador_obter_ranking() -> list:
    """
    Solicita ao balanceador via RPC as 10 maiores pontuações dos jogadores que venceram.
    """
    return get_rpc_proxy().obter_ranking()


def balanceador_iniciar_partida(nickname: str) -> dict:
    """
    Inicia uma nova partida via RPC para o nickname e retorna o estado inicial/primeira pergunta.
    """
    return get_rpc_proxy().iniciar_partida(nickname)


def balanceador_obter_estado_partida(nickname: str) -> dict:
    """
    Obtém via RPC o estado atual da partida em andamento do jogador.
    """
    return get_rpc_proxy().obter_estado_partida(nickname)


def balanceador_enviar_resposta(nickname: str, alternativa_id: str, tempo_resposta: float) -> dict:
    """
    Envia via RPC a resposta escolhida e o tempo de resposta para o balanceador.
    """
    return get_rpc_proxy().enviar_resposta(nickname, alternativa_id, float(tempo_resposta))


def balanceador_solicitar_ajuda(nickname: str, tipo_ajuda: str) -> dict:
    """
    Solicita via RPC uma das ajudas: 'meio_meio', 'pulo' ou 'passe_livre'.
    """
    return get_rpc_proxy().solicitar_ajuda(nickname, tipo_ajuda)


# ==============================================================================
# ROTAS FLASK (INTERFACE CLIENTE)
# ==============================================================================


@app.route("/")
def index():
    """1. Tela inicial"""
    return render_template("index.html")


@app.route("/ranking")
def ranking():
    """2. Visualizar maiores pontuações"""
    try:
        top_10 = balanceador_obter_ranking()
    except Exception:
        top_10 = []
    return render_template("ranking.html", ranking=top_10)


@app.route("/novo_jogo", methods=["GET", "POST"])
def novo_jogo():
    """3. Iniciar novo jogo / solicitação de nickname"""
    erro = None
    if request.method == "POST":
        nickname = request.form.get("nickname", "").strip()

        if not nickname:
            erro = "Por favor, insira um nickname."
        else:
            try:
                disponivel = balanceador_verificar_nickname(nickname)
                if not disponivel:
                    erro = "Este nickname já está em uso. Por favor, escolha outro."
                else:
                    session["nickname"] = nickname
                    session["pontuacao"] = 0
                    session["tempo_inicio"] = time.time()
                    # Inicializa partida no backend via RPC
                    balanceador_iniciar_partida(nickname)
                    return redirect(url_for("pergunta"))
            except Exception as exc:
                erro = f"Erro de comunicação RPC com o balanceador: {exc}"

    return render_template("novo_jogo.html", erro=erro)


@app.route("/pergunta", methods=["GET", "POST"])
def pergunta():
    """4. Tela de pergunta e manipulação de ajudas/respostas"""
    nickname = session.get("nickname")
    if not nickname:
        return redirect(url_for("novo_jogo"))

    # Caso seja envio de resposta ou solicitação de ajuda
    if request.method == "POST":
        acao = request.form.get("acao")

        if acao == "responder":
            alternativa_escolhida = request.form.get("alternativa")
            tempo_resposta = time.time() - session.get("tempo_inicio", time.time())

            resultado = balanceador_enviar_resposta(
                nickname, alternativa_escolhida, tempo_resposta
            )
            session["pontuacao"] = resultado.get("pontuacao_atual", 0)
            session["tempo_inicio"] = time.time()

            if resultado.get("status") == "WON":
                return redirect(url_for("vitoria"))
            if resultado.get("status") == "LOST":
                return redirect(url_for("game_over"))

            return redirect(url_for("pergunta"))

        elif acao in ["meio_meio", "pulo", "passe_livre"]:
            estado_atualizado = balanceador_solicitar_ajuda(nickname, acao)
            session["pontuacao"] = estado_atualizado.get("pontuacao_atual", 0)
            if acao in ["pulo", "passe_livre"]:
                session["tempo_inicio"] = time.time()
            return redirect(url_for("pergunta"))

    dados_pergunta = balanceador_obter_estado_partida(nickname)
    session["pontuacao"] = dados_pergunta.get("pontuacao_atual", 0)

    if dados_pergunta.get("status") == "WON":
        return redirect(url_for("vitoria"))
    if dados_pergunta.get("status") == "LOST":
        return redirect(url_for("game_over"))

    return render_template("pergunta.html", dados=dados_pergunta)


@app.route("/fim_de_jogo")
def game_over():
    """5. Tela de fim de jogo caso erre"""
    pontuacao_final = session.get("pontuacao", 0)
    nickname = session.get("nickname", "Jogador")
    return render_template(
        "fim_de_jogo.html", nickname=nickname, pontuacao=pontuacao_final
    )


@app.route("/campeao")
def vitoria():
    """6. Tela de vencedor"""
    pontuacao_final = session.get("pontuacao", 0)
    nickname = session.get("nickname", "Jogador")
    return render_template(
        "campeao.html", nickname=nickname, pontuacao=pontuacao_final
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=CLIENT_PORT, debug=True)
