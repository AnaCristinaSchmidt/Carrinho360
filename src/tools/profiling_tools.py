import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from src.database.init_db import conectar  # noqa: E402
from src.tools.schema_tools import validar_tabela  # noqa: E402



def _validar_coluna(conexao, nome_tabela: str, nome_coluna: str) -> str:
    colunas = [linha["name"] for linha in conexao.execute(f"PRAGMA table_info({nome_tabela})")]
    if nome_coluna not in colunas:
        raise ValueError(f"Coluna '{nome_coluna}' nao existe em '{nome_tabela}'. Colunas validas: {', '.join(colunas)}")
    return nome_coluna


def contar_nulos_e_distintos(nome_tabela: str, nome_coluna: str) -> dict:
    """Mede a qualidade de uma coluna: total de linhas, nulos, percentual preenchido e valores distintos."""
    with conectar() as conexao:
        validar_tabela(conexao, nome_tabela)
        _validar_coluna(conexao, nome_tabela, nome_coluna)
        # Identificadores ja validados acima: e seguro interpola-los no SQL
        linha = conexao.execute(
            f"SELECT COUNT(*) AS total, "
            f"SUM(CASE WHEN {nome_coluna} IS NULL THEN 1 ELSE 0 END) AS nulos, "
            f"COUNT(DISTINCT {nome_coluna}) AS distintos FROM {nome_tabela}"
        ).fetchone()
        total = linha["total"]
        nulos = linha["nulos"] or 0
        # TODO: calcule percentual_preenchido = (total - nulos) / total * 100 (0.0 se total == 0), arredondado a 2 casas
        percentual_preenchido = (total - nulos) / total * 100 if total > 0 else 0.0
        percentual_preenchido = round(percentual_preenchido, 2)
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
    with conectar() as conexao:
        validar_tabela(conexao, nome_tabela)
        _validar_coluna(conexao, nome_tabela, nome_coluna)
        # TODO: execute SELECT MIN, MAX, AVG e SUM da coluna e retorne um dicionario com as 4 estatisticas
        #       (arredonde a media e a soma a 2 casas; se a coluna for toda nula, os valores serao None)
        ...
        linha = conexao.execute(
            f"SELECT MIN({nome_coluna}) AS minimo, "
            f"MAX({nome_coluna}) AS maximo, "
            f"AVG({nome_coluna}) AS media, "
            f"SUM({nome_coluna}) AS soma "
            f"FROM {nome_tabela}"
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
    with conectar() as conexao:
        validar_tabela(conexao, nome_tabela)
        # TODO: SELECT * com LIMIT ? (placeholder!) e converta cada sqlite3.Row em dict com dict(linha)
        ...
        linhas = conexao.execute(
            f"SELECT * FROM {nome_tabela} LIMIT ?",
            (qtd,)
        ).fetchall()
        return [dict(linha) for linha in linhas]


if __name__ == "__main__":
    print(contar_nulos_e_distintos("clientes", "email"))
    print(calcular_estatisticas_coluna("pedidos", "valor_total"))
    print(amostrar_linhas("produtos", 3))
