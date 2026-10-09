import sqlite3
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from src.agent.guardrails import validar_query_segura  # noqa: E402
from src.database.init_db import conectar_leitura  # noqa: E402

LIMITE_MAXIMO = 50
TIMEOUT_SEGUNDOS = 3.0
INSTRUCOES_ENTRE_CHECAGENS = 10_000

FUNCOES_PERMITIDAS = {
    "count", "sum", "avg", "min", "max", "total", "group_concat", "string_agg",
    "round", "abs", "coalesce", "ifnull", "nullif", "iif", "typeof",
    "lower", "upper", "length", "substr", "substring", "trim", "ltrim", "rtrim", "replace", "instr",
    "like", "glob", "printf", "format",
    "strftime", "date", "time", "datetime", "julianday", "unixepoch",
    "row_number", "rank", "dense_rank", "ntile", "lag", "lead", "first_value", "last_value",
    "percent_rank", "cume_dist",
}


def _criar_autorizador(negacoes: list[str]):
    def autorizador(acao, arg1, arg2, _banco, _origem):
        if acao == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if acao == sqlite3.SQLITE_READ:
            tabela = (arg1 or "").lower()
            if tabela.startswith(("sqlite_", "pragma_")):
                negacoes.append(f"leitura da tabela interna '{arg1}' nao permitida; use as ferramentas de schema")
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        if acao == sqlite3.SQLITE_FUNCTION:
            if (arg2 or "").lower() in FUNCOES_PERMITIDAS:
                return sqlite3.SQLITE_OK
            negacoes.append(f"funcao '{arg2}' nao permitida")
            return sqlite3.SQLITE_DENY
        if acao == getattr(sqlite3, "SQLITE_RECURSIVE", 33):
            negacoes.append("CTE recursiva (WITH RECURSIVE) nao permitida")
            return sqlite3.SQLITE_DENY
        negacoes.append("operacao fora de leitura nao permitida")
        return sqlite3.SQLITE_DENY

    return autorizador


def conectar_somente_leitura(timeout_s: float = TIMEOUT_SEGUNDOS, negacoes: list[str] | None = None) -> sqlite3.Connection:
    """Abre o banco read-only; o proprio SQLite nega o que nao for leitura e interrompe consultas lentas."""
    conexao = conectar_leitura()
    conexao.set_authorizer(_criar_autorizador(negacoes if negacoes is not None else []))
    prazo = time.monotonic() + timeout_s
    conexao.set_progress_handler(lambda: 1 if time.monotonic() > prazo else 0, INSTRUCOES_ENTRE_CHECAGENS)
    return conexao


def garantir_limit(query: str, limite: int) -> str:
    """Envolve a consulta em uma subquery para que o LIMIT externo nunca passe de `limite`."""
    query = query.strip().rstrip(";").strip()
    return f"SELECT * FROM ({query}) LIMIT {limite}"


def executar_query_analitica(query: str, limite_linhas: int = 50) -> dict:
    """Valida e executa uma consulta de leitura.

    Use somente depois de consultar o schema.
    Retorna no máximo 50 linhas e interrompe consultas que passem de 3 segundos.
    """
    valida, mensagem = validar_query_segura(query)
    if not valida:
        return {"sucesso": False, "erro": mensagem, "query_executada": None}

    limite = max(1, min(limite_linhas, LIMITE_MAXIMO))
    query_final = garantir_limit(query, limite)
    negacoes: list[str] = []
    inicio = time.perf_counter()

    conexao = None
    try:
        conexao = conectar_somente_leitura(negacoes=negacoes)
        cursor = conexao.execute(query_final)
        colunas = [descricao[0] for descricao in cursor.description]
        linhas = [dict(linha) for linha in cursor.fetchmany(limite)]
    except FileNotFoundError as erro:
        return {"sucesso": False, "erro": str(erro), "query_executada": query_final}
    except sqlite3.Error as erro:
        if negacoes:
            texto = f"Bloqueado pelo banco: {'; '.join(dict.fromkeys(negacoes))}"
        elif "interrupted" in str(erro):
            texto = f"Consulta interrompida: passou do limite de {TIMEOUT_SEGUNDOS:g} s. Simplifique a consulta."
        else:
            texto = f"{type(erro).__name__}: {erro}"
        return {"sucesso": False, "erro": texto, "query_executada": query_final}
    finally:
        if conexao is not None:
            conexao.close()

    return {
        "sucesso": True,
        "query_executada": query_final,
        "colunas": colunas,
        "linhas": linhas,
        "total_linhas": len(linhas),
        "tempo_ms": round((time.perf_counter() - inicio) * 1000, 2),
    }


if __name__ == "__main__":
    print(executar_query_analitica("SELECT cidade, COUNT(*) AS total FROM clientes GROUP BY cidade"))
    print(executar_query_analitica("SELECT * FROM pedidos LIMIT 500")["total_linhas"])
    print(executar_query_analitica("SELECT * FROM pedidos ORDER BY id LIMIT 10 OFFSET 5")["total_linhas"])
    print(executar_query_analitica("SELECT coluna_inexistente FROM clientes"))
    print(executar_query_analitica("SELECT COUNT(*) FROM pedidos a, pedidos b, pedidos c, pedidos d"))
    print(executar_query_analitica("DELETE FROM clientes"))
