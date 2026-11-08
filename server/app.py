import os
import random
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer
from db import (
    get_latest_game_state,
    get_question_by_id,
    get_random_question,
    get_top_10_winners,
    insert_game_history,
    nickname_exists,
)

SERVER_NAME = os.getenv("SERVER_NAME", "servidor-1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))

LEVEL_CONFIG = {
    "facil": {"label": "Fácil", "base_points": 50, "bonus_factor": 1.0},
    "medio": {"label": "Médio", "base_points": 100, "bonus_factor": 1.5},
    "dificil": {"label": "Difícil", "base_points": 300, "bonus_factor": 2.0},
    "final": {"label": "Final", "base_points": 1000, "bonus_factor": 10.0},
}


def get_level_for_order(order: int) -> str:
    """
    Define o nível da pergunta conforme a ordem (1 a 10):
    - 1 a 3: fácil (3 perguntas)
    - 4 a 6: médio (3 perguntas)
    - 7 a 9: difícil (3 perguntas)
    - 10: pergunta final (1 pergunta)
    """
    if order <= 3:
        return "facil"
    if order <= 6:
        return "medio"
    if order <= 9:
        return "dificil"
    return "final"


def parse_asked_ids(asked_str: str) -> list[int]:
    if not asked_str:
        return []
    return [int(x) for x in asked_str.split(",") if x.strip().isdigit()]


def format_game_state(state: dict, extra: dict | None = None) -> dict:
    """
    Formata o estado atual da partida exatamente no dicionário esperado
    pelas telas de cliente (pergunta.html, fim_de_jogo.html, campeao.html).
    """
    question = get_question_by_id(state["current_question_id"])
    eliminated = {
        opt.strip()
        for opt in (state.get("eliminated_options") or "").split(",")
        if opt.strip()
    }
    level_key = state["question_level"]
    level_info = LEVEL_CONFIG.get(level_key, LEVEL_CONFIG["facil"])

    alternativas = [
        {
            "id": "A",
            "texto": question["option_a"],
            "eliminada": "A" in eliminated,
        },
        {
            "id": "B",
            "texto": question["option_b"],
            "eliminada": "B" in eliminated,
        },
        {
            "id": "C",
            "texto": question["option_c"],
            "eliminada": "C" in eliminated,
        },
        {
            "id": "D",
            "texto": question["option_d"],
            "eliminada": "D" in eliminated,
        },
    ]

    score_val = float(state["score"])
    pontuacao_fmt = int(score_val) if score_val.is_integer() else round(score_val, 2)

    payload = {
        "nickname": state["nickname"],
        "status": state["status"],
        "acao_registrada": state["action_type"],
        "ordem_pergunta": int(state["question_order"]),
        "total_perguntas": 10,
        "nivel": level_info["label"],
        "pontuacao_atual": pontuacao_fmt,
        "enunciado": question["statement"],
        "alternativas": alternativas,
        "ajuda_meio_meio": not bool(state["used_half"]) and state["status"] == "IN_PROGRESS",
        "ajuda_pulo": not bool(state["used_skip"]) and state["status"] == "IN_PROGRESS",
        "ajuda_passe_livre": (
            not bool(state["used_free_pass"])
            and int(state["question_order"]) < 10
            and state["status"] == "IN_PROGRESS"
        ),
        "servidor": SERVER_NAME,
    }
    if extra:
        payload.update(extra)
    return payload


# Procedimentos remotos (RPC) expostos
def rpc_verificar_nickname(nickname: str) -> bool:
    """
    Verifica se o nickname já existe no banco de dados.
    Retorna True se estiver disponível, False caso contrário.
    """
    nickname = (nickname or "").strip()
    if not nickname:
        return False
    return not nickname_exists(nickname)


def rpc_obter_ranking() -> list[dict]:
    """
    Retorna as 10 maiores pontuações dos jogadores que venceram o jogo
    (responderam corretamente a pergunta final).
    """
    winners = get_top_10_winners()
    ranking = []
    for row in winners:
        score_val = float(row["score"])
        pontuacao_fmt = int(score_val) if score_val.is_integer() else round(score_val, 2)
        ranking.append(
            {
                "nickname": row["nickname"],
                "pontuacao": pontuacao_fmt,
                "servidor": SERVER_NAME,
            }
        )
    return ranking


def rpc_iniciar_partida(nickname: str) -> dict:
    """
    Inicia uma nova partida para o nickname (ou retorna o estado atual caso
    a partida desse nickname já esteja em andamento) e retorna a pergunta atual.
    """
    nickname = (nickname or "").strip()
    existing = get_latest_game_state(nickname)
    if existing:
        return format_game_state(existing)

    first_level = get_level_for_order(1)
    first_question = get_random_question(first_level, [])
    if not first_question:
        raise RuntimeError("Banco de questões vazio ou sem perguntas disponíveis.")

    state = insert_game_history(
        nickname=nickname,
        action_type="START_GAME",
        question_order=1,
        question_level=first_level,
        current_question_id=first_question["id"],
        asked_question_ids=str(first_question["id"]),
        eliminated_options="",
        used_half=False,
        used_skip=False,
        used_free_pass=False,
        score=0.0,
        status="IN_PROGRESS",
        server_name=SERVER_NAME,
    )
    return format_game_state(state)


def rpc_obter_estado_partida(nickname: str) -> dict:
    """Retorna o estado atual da partida em andamento do jogador."""
    nickname = (nickname or "").strip()
    state = get_latest_game_state(nickname)
    if not state:
        return rpc_iniciar_partida(nickname)
    return format_game_state(state)


def rpc_enviar_resposta(nickname: str, alternativa_id: str, tempo_resposta: float) -> dict:
    """
    Valida a resposta escolhida pelo jogador e calcula a pontuação:
    - Fácil: 50 + max(0, (60 - segundos)) * 1
    - Médio: 100 + max(0, (60 - segundos)) * 1.5
    - Difícil: 300 + max(0, (60 - segundos)) * 2
    - Final: 1000 + max(0, (60 - segundos)) * 10
    """
    nickname = (nickname or "").strip()
    chosen_option = (alternativa_id or "").strip().upper()

    state = get_latest_game_state(nickname)
    if not state:
        raise RuntimeError(f"Partida não encontrada para o jogador '{nickname}'.")

    if state["status"] != "IN_PROGRESS":
        return format_game_state(state)

    current_question = get_question_by_id(state["current_question_id"])
    correct_option = current_question["correct_option"]

    try:
        seconds = max(0, int(float(tempo_resposta)))
    except (ValueError, TypeError):
        seconds = max(0, int(float(state.get("server_elapsed_seconds") or 0)))

    # Caso erre a questão: Fim de jogo mantendo a pontuação obtida até a pergunta anterior
    if chosen_option != correct_option:
        final_score = float(state["score"])
        lost_state = insert_game_history(
            nickname=state["nickname"],
            action_type="ANSWER_WRONG",
            question_order=state["question_order"],
            question_level=state["question_level"],
            current_question_id=state["current_question_id"],
            asked_question_ids=state["asked_question_ids"],
            eliminated_options=state["eliminated_options"],
            used_half=state["used_half"],
            used_skip=state["used_skip"],
            used_free_pass=state["used_free_pass"],
            score=final_score,
            status="LOST",
            server_name=SERVER_NAME,
        )
        return format_game_state(
            lost_state,
            extra={
                "acertou": False,
                "alternativa_correta": correct_option,
            },
        )

    # Caso acerte a questão: soma pontos base + bônus de tempo
    # Fórmula: bônus = max(0, (60 - segundos)) * fator
    level_info = LEVEL_CONFIG[state["question_level"]]
    base_points = level_info["base_points"]
    factor = level_info["bonus_factor"]
    bonus_points = max(0, (60 - seconds)) * factor
    new_score = float(state["score"]) + base_points + bonus_points

    # Se respondeu corretamente a 10 pergunta (Pergunta Final) -> Venceu o jogo
    if int(state["question_order"]) >= 10:
        won_state = insert_game_history(
            nickname=state["nickname"],
            action_type="GAME_WON",
            question_order=10,
            question_level="final",
            current_question_id=state["current_question_id"],
            asked_question_ids=state["asked_question_ids"],
            eliminated_options="",
            used_half=state["used_half"],
            used_skip=state["used_skip"],
            used_free_pass=state["used_free_pass"],
            score=new_score,
            status="WON",
            server_name=SERVER_NAME,
        )
        return format_game_state(
            won_state,
            extra={
                "acertou": True,
            },
        )

    # Avança para a próxima pergunta (2..10)
    asked_ids = parse_asked_ids(state["asked_question_ids"])
    next_order = int(state["question_order"]) + 1
    next_level = get_level_for_order(next_order)
    next_question = get_random_question(next_level, asked_ids)
    asked_ids.append(next_question["id"])
    asked_str = ",".join(str(x) for x in asked_ids)

    next_state = insert_game_history(
        nickname=state["nickname"],
        action_type="ANSWER_CORRECT",
        question_order=next_order,
        question_level=next_level,
        current_question_id=next_question["id"],
        asked_question_ids=asked_str,
        eliminated_options="",
        used_half=state["used_half"],
        used_skip=state["used_skip"],
        used_free_pass=state["used_free_pass"],
        score=new_score,
        status="IN_PROGRESS",
        server_name=SERVER_NAME,
    )
    return format_game_state(
        next_state,
        extra={
            "acertou": True,
        },
    )


def rpc_solicitar_ajuda(nickname: str, tipo_ajuda: str) -> dict:
    """
    Executa uma das ajudas solicitadas pelo jogador:
    - 'meio_meio': sorteia 2 alternativas incorretas e as elimina
    - 'pulo': pula para outra questão do mesmo nível (pode ser usada após 'meio_meio')
    - 'passe_livre': acerta automaticamente sem bônus de tempo (proibida na pergunta final)
    """
    nickname = (nickname or "").strip()
    tipo_ajuda = (tipo_ajuda or "").strip().lower()

    state = get_latest_game_state(nickname)
    if not state or state["status"] != "IN_PROGRESS":
        raise RuntimeError("Partida não encontrada ou já encerrada.")

    asked_ids = parse_asked_ids(state["asked_question_ids"])
    current_question = get_question_by_id(state["current_question_id"])

    # Meio a Meio
    if tipo_ajuda in ("meio_meio", "50_50"):
        if state["used_half"]:
            return format_game_state(state)

        correct_opt = current_question["correct_option"]
        wrong_options = [opt for opt in ["A", "B", "C", "D"] if opt != correct_opt]
        eliminated = sorted(random.sample(wrong_options, 2))
        eliminated_str = ",".join(eliminated)

        new_state = insert_game_history(
            nickname=state["nickname"],
            action_type="HALF_HELP",
            question_order=state["question_order"],
            question_level=state["question_level"],
            current_question_id=state["current_question_id"],
            asked_question_ids=state["asked_question_ids"],
            eliminated_options=eliminated_str,
            used_half=True,
            used_skip=state["used_skip"],
            used_free_pass=state["used_free_pass"],
            score=float(state["score"]),
            status="IN_PROGRESS",
            server_name=SERVER_NAME,
            keep_question_started_at=state["question_started_at"],
        )
        return format_game_state(new_state)

    # Pulo (pode ser utilizado mesmo após Meio a Meio)
    if tipo_ajuda in ("pulo", "skip"):
        if state["used_skip"]:
            return format_game_state(state)

        next_question = get_random_question(state["question_level"], asked_ids)
        if not next_question:
            return format_game_state(state)

        asked_ids.append(next_question["id"])
        asked_str = ",".join(str(x) for x in asked_ids)

        new_state = insert_game_history(
            nickname=state["nickname"],
            action_type="SKIP_HELP",
            question_order=state["question_order"],
            question_level=state["question_level"],
            current_question_id=next_question["id"],
            asked_question_ids=asked_str,
            eliminated_options="",
            used_half=state["used_half"],
            used_skip=True,
            used_free_pass=state["used_free_pass"],
            score=float(state["score"]),
            status="IN_PROGRESS",
            server_name=SERVER_NAME,
        )
        return format_game_state(new_state)

    # Passe Livre (não pode na pergunta final e não recebe pontuação bônus)
    if tipo_ajuda in ("passe_livre", "free_pass"):
        if state["used_free_pass"] or int(state["question_order"]) >= 10 or state["question_level"] == "final":
            return format_game_state(state)

        level_info = LEVEL_CONFIG[state["question_level"]]
        base_points = level_info["base_points"]
        new_score = float(state["score"]) + base_points

        next_order = int(state["question_order"]) + 1
        next_level = get_level_for_order(next_order)
        next_question = get_random_question(next_level, asked_ids)
        asked_ids.append(next_question["id"])
        asked_str = ",".join(str(x) for x in asked_ids)

        new_state = insert_game_history(
            nickname=state["nickname"],
            action_type="FREE_PASS_HELP",
            question_order=next_order,
            question_level=next_level,
            current_question_id=next_question["id"],
            asked_question_ids=asked_str,
            eliminated_options="",
            used_half=state["used_half"],
            used_skip=state["used_skip"],
            used_free_pass=True,
            score=new_score,
            status="IN_PROGRESS",
            server_name=SERVER_NAME,
        )
        return format_game_state(new_state)

    return format_game_state(state)


class ServerRPCRequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/", "/RPC2", "/rpc")


class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    daemon_threads = True


if __name__ == "__main__":
    print(f"[{SERVER_NAME}] Iniciando Servidor XML-RPC na porta {SERVER_PORT}...", flush=True)
    with ThreadedXMLRPCServer(
        ("0.0.0.0", SERVER_PORT),
        requestHandler=ServerRPCRequestHandler,
        allow_none=True,
        encoding="utf-8",
        logRequests=False,
    ) as server:
        server.register_function(rpc_verificar_nickname, "verificar_nickname")
        server.register_function(rpc_obter_ranking, "obter_ranking")
        server.register_function(rpc_iniciar_partida, "iniciar_partida")
        server.register_function(rpc_obter_estado_partida, "obter_estado_partida")
        server.register_function(rpc_enviar_resposta, "enviar_resposta")
        server.register_function(rpc_solicitar_ajuda, "solicitar_ajuda")
        server.serve_forever()
