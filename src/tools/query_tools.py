import re
import sqlite3
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from src.agent.guardrails import validar_query_segura  # noqa: E402
from src.database.init_db import CAMINHO_DB  # noqa: E402

LIMITE_MAXIMO = 50


def conectar_somente_leitura() -> sqlite3.Connection:
    """Abre o banco em modo somente leitura."""
    conexao = sqlite3.connect(f"file:{CAMINHO_DB}?mode=ro", uri=True)
    conexao.row_factory = sqlite3.Row
    return conexao


def garantir_limit(query: str, limite: int) -> str:
    """Remove o ';' final e limita consultas com LIMIT inteiro simples."""
    query = query.strip().rstrip(";").strip()

    correspondencia = re.search(
        r"\blimit\s+(\d+)\s*$",
        query,
        flags=re.IGNORECASE,
    )

    if correspondencia is None:
        return f"{query} LIMIT {limite}"

    if int(correspondencia.group(1)) > limite:
        return (
            query[:correspondencia.start(1)]
            + str(limite)
            + query[correspondencia.end(1):]
        )

    return query


def executar_query_analitica(query: str, limite_linhas: int = 50) -> dict:
    """Valida e executa uma consulta de leitura.

    Use somente depois de consultar o schema.
    Retorna no máximo 50 linhas.
    """
    valida, mensagem = validar_query_segura(query)
    if not valida:
        return {
            "sucesso": False,
            "erro": mensagem,
            "query_executada": None,
        }

    limite = max(1, min(limite_linhas, LIMITE_MAXIMO))
    query_final = garantir_limit(query, limite)
    inicio = time.perf_counter()

    conexao = None
    try:
        conexao = conectar_somente_leitura()
        cursor = conexao.execute(query_final)

        colunas = [descricao[0] for descricao in cursor.description]
        linhas = [dict(linha) for linha in cursor.fetchmany(limite)]

    except sqlite3.Error as erro:
        return {
            "sucesso": False,
            "erro": f"{type(erro).__name__}: {erro}",
            "query_executada": query_final,
        }

    finally:
        if conexao is not None:
            conexao.close()

    tempo_ms = round((time.perf_counter() - inicio) * 1000, 2)

    return {
        "sucesso": True,
        "query_executada": query_final,
        "colunas": colunas,
        "linhas": linhas,
        "total_linhas": len(linhas),
        "tempo_ms": tempo_ms,
    }


if __name__ == "__main__":
    print(
        executar_query_analitica(
            "SELECT cidade, COUNT(*) AS total FROM clientes GROUP BY cidade"
        )
    )
    print(executar_query_analitica("SELECT * FROM pedidos LIMIT 500"))
    print(executar_query_analitica("SELECT coluna_inexistente FROM clientes"))
    print(executar_query_analitica("DELETE FROM clientes"))