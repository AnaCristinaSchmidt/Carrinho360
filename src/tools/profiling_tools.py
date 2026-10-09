import sys
from contextlib import closing
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from src.database.init_db import conectar_leitura  # noqa: E402
from src.tools.schema_tools import validar_tabela  # noqa: E402

TIPOS_NUMERICOS = ("INT", "REAL", "FLOA", "DOUB", "NUM", "DEC")

CHECAGENS_ANOMALIAS = {
    "clientes_sem_email": (
        "Clientes sem e-mail cadastrado",
        "SELECT id FROM clientes WHERE email IS NULL",
    ),
    "clientes_email_duplicado": (
        "Clientes que compartilham o mesmo e-mail com outro cliente",
        "SELECT id FROM clientes WHERE email IN "
        "(SELECT email FROM clientes WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1)",
    ),
    "produtos_preco_zero": (
        "Produtos com preco zero ou negativo",
        "SELECT id FROM produtos WHERE preco <= 0",
    ),
    "pedidos_valor_negativo": (
        "Pedidos com valor_total negativo (estorno mal lancado)",
        "SELECT id FROM pedidos WHERE valor_total < 0",
    ),
    "pedidos_data_futura": (
        "Pedidos com data_pedido no futuro",
        "SELECT id FROM pedidos WHERE data_pedido > date('now')",
    ),
}


def _colunas(conexao, nome_tabela: str) -> dict[str, str]:
    return {linha["name"]: (linha["type"] or "").upper() for linha in conexao.execute(f"PRAGMA table_info({nome_tabela})")}


def _validar_coluna(conexao, nome_tabela: str, nome_coluna: str) -> str:
    colunas = _colunas(conexao, nome_tabela)
    if nome_coluna not in colunas:
        raise ValueError(f"Coluna '{nome_coluna}' nao existe em '{nome_tabela}'. Colunas validas: {', '.join(colunas)}")
    return nome_coluna


def contar_nulos_e_distintos(nome_tabela: str, nome_coluna: str) -> dict:
    """Mede a qualidade de uma coluna: total de linhas, nulos, percentual preenchido e valores distintos."""
    with closing(conectar_leitura()) as conexao:
        validar_tabela(conexao, nome_tabela)
        _validar_coluna(conexao, nome_tabela, nome_coluna)
        linha = conexao.execute(
            f"SELECT COUNT(*) AS total, "
            f"SUM(CASE WHEN {nome_coluna} IS NULL THEN 1 ELSE 0 END) AS nulos, "
            f"COUNT(DISTINCT {nome_coluna}) AS distintos FROM {nome_tabela}"
        ).fetchone()
        total = linha["total"]
        nulos = linha["nulos"] or 0
        percentual_preenchido = round((total - nulos) / total * 100, 2) if total > 0 else 0.0
        return {
            "tabela": nome_tabela,
            "coluna": nome_coluna,
            "total_linhas": total,
            "nulos": nulos,
            "distintos": linha["distintos"],
            "percentual_preenchido": percentual_preenchido,
        }


def calcular_estatisticas_coluna(nome_tabela: str, nome_coluna: str) -> dict:
    """Calcula minimo, maximo, media e soma de uma coluna NUMERICA (ex: preco, valor_total)."""
    with closing(conectar_leitura()) as conexao:
        validar_tabela(conexao, nome_tabela)
        _validar_coluna(conexao, nome_tabela, nome_coluna)
        tipo = _colunas(conexao, nome_tabela)[nome_coluna]
        if not any(parte in tipo for parte in TIPOS_NUMERICOS):
            raise ValueError(
                f"Coluna '{nome_coluna}' e do tipo {tipo or 'sem tipo'}, nao numerica. "
                "Use contar_nulos_e_distintos para colunas de texto."
            )
        linha = conexao.execute(
            f"SELECT MIN({nome_coluna}) AS minimo, MAX({nome_coluna}) AS maximo, "
            f"AVG({nome_coluna}) AS media, SUM({nome_coluna}) AS soma FROM {nome_tabela}"
        ).fetchone()
        return {
            "tabela": nome_tabela,
            "coluna": nome_coluna,
            "minimo": linha["minimo"],
            "maximo": linha["maximo"],
            "media": round(linha["media"], 2) if linha["media"] is not None else None,
            "soma": round(linha["soma"], 2) if linha["soma"] is not None else None,
        }


def amostrar_linhas(nome_tabela: str, qtd: int = 5) -> list[dict]:
    """Retorna ate 20 linhas de exemplo de uma tabela, para o modelo entender o formato dos dados."""
    qtd = max(1, min(qtd, 20))
    with closing(conectar_leitura()) as conexao:
        validar_tabela(conexao, nome_tabela)
        linhas = conexao.execute(f"SELECT * FROM {nome_tabela} LIMIT ?", (qtd,)).fetchall()
        return [dict(linha) for linha in linhas]


def checar_anomalias() -> dict:
    """Roda todas as checagens de qualidade conhecidas e devolve quantidade e ids de exemplo de cada anomalia."""
    with closing(conectar_leitura()) as conexao:
        resultado = {}
        for nome, (descricao, sql) in CHECAGENS_ANOMALIAS.items():
            ids = [linha["id"] for linha in conexao.execute(sql)]
            resultado[nome] = {"descricao": descricao, "quantidade": len(ids), "ids_exemplo": ids[:10]}
        return resultado


if __name__ == "__main__":
    print(contar_nulos_e_distintos("clientes", "email"))
    print(calcular_estatisticas_coluna("pedidos", "valor_total"))
    print(amostrar_linhas("produtos", 3))
    print(checar_anomalias())
