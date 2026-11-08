import os
import random
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_config() -> dict:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "user": os.getenv("POSTGRES_USER", "euroquiz"),
        "password": os.getenv("POSTGRES_PASSWORD", "euroquiz123"),
        "dbname": os.getenv("POSTGRES_DB", "euroquiz"),
    }


@contextmanager
def get_db_cursor(commit: bool = False):
    conn = psycopg2.connect(**get_db_config(), cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def nickname_exists(nickname: str) -> bool:
    """Verifica se o nickname já foi utilizado anteriormente no banco de dados."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM game_history WHERE LOWER(nickname) = LOWER(%s) LIMIT 1;",
            (nickname,),
        )
        return cur.fetchone() is not None


def get_random_question(level: str, exclude_ids: list[int]) -> dict | None:
    """Sorteia uma pergunta do nível solicitado que ainda não foi usada na partida."""
    with get_db_cursor() as cur:
        if exclude_ids:
            cur.execute(
                """
                SELECT id, level, statement, option_a, option_b, option_c, option_d, correct_option
                FROM questions
                WHERE level = %s AND id != ALL(%s)
                ORDER BY RANDOM()
                LIMIT 1;
                """,
                (level, exclude_ids),
            )
        else:
            cur.execute(
                """
                SELECT id, level, statement, option_a, option_b, option_c, option_d, correct_option
                FROM questions
                WHERE level = %s
                ORDER BY RANDOM()
                LIMIT 1;
                """,
                (level,),
            )
        return cur.fetchone()


def get_question_by_id(question_id: int) -> dict | None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT id, level, statement, option_a, option_b, option_c, option_d, correct_option
            FROM questions
            WHERE id = %s;
            """,
            (question_id,),
        )
        return cur.fetchone()


def get_latest_game_state(nickname: str) -> dict | None:
    """Retorna o estado mais recente do jogo de um determinado jogador."""
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                gh.*,
                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - gh.question_started_at)) AS server_elapsed_seconds
            FROM game_history gh
            WHERE LOWER(gh.nickname) = LOWER(%s)
            ORDER BY gh.id DESC
            LIMIT 1;
            """,
            (nickname,),
        )
        return cur.fetchone()


def insert_game_history(
    nickname: str,
    action_type: str,
    question_order: int,
    question_level: str,
    current_question_id: int,
    asked_question_ids: str,
    eliminated_options: str,
    used_half: bool,
    used_skip: bool,
    used_free_pass: bool,
    score: float,
    status: str,
    server_name: str,
    keep_question_started_at=None,
) -> dict:
    """Insere um novo registro de ação na tabela unificada de histórico do jogo."""
    with get_db_cursor(commit=True) as cur:
        if keep_question_started_at is not None:
            cur.execute(
                """
                INSERT INTO game_history (
                    nickname, action_type, question_order, question_level,
                    current_question_id, asked_question_ids, eliminated_options,
                    used_half, used_skip, used_free_pass, score, status,
                    question_started_at, server_name
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *;
                """,
                (
                    nickname,
                    action_type,
                    question_order,
                    question_level,
                    current_question_id,
                    asked_question_ids,
                    eliminated_options,
                    used_half,
                    used_skip,
                    used_free_pass,
                    score,
                    status,
                    keep_question_started_at,
                    server_name,
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO game_history (
                    nickname, action_type, question_order, question_level,
                    current_question_id, asked_question_ids, eliminated_options,
                    used_half, used_skip, used_free_pass, score, status,
                    server_name
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *;
                """,
                (
                    nickname,
                    action_type,
                    question_order,
                    question_level,
                    current_question_id,
                    asked_question_ids,
                    eliminated_options,
                    used_half,
                    used_skip,
                    used_free_pass,
                    score,
                    status,
                    server_name,
                ),
            )
        return cur.fetchone()


def get_top_10_winners() -> list[dict]:
    """
    Retorna as 10 maiores pontuações obtidas no jogo apenas pelos jogadores
    que conseguiram vencer o jogo (responderam a pergunta final).
    """
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT nickname, score, server_name, created_at
            FROM game_history
            WHERE status = 'WON' AND action_type = 'GAME_WON'
            ORDER BY score DESC, created_at ASC
            LIMIT 10;
            """
        )
        return cur.fetchall()


def get_player_history(nickname: str) -> list[dict]:
    """Retorna todas as ações realizadas pelo jogador na partida."""
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT id, nickname, action_type, question_order, question_level,
                   current_question_id, eliminated_options, used_half, used_skip,
                   used_free_pass, score, status, server_name, created_at
            FROM game_history
            WHERE LOWER(nickname) = LOWER(%s)
            ORDER BY id ASC;
            """,
            (nickname,),
        )
        return cur.fetchall()
