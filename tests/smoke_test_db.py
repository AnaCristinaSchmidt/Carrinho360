import sqlite3
import sys
from contextlib import closing
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.database.init_db import CAMINHO_DB, conectar  # noqa: E402
from src.database.seed_data import ANOMALIAS_ESPERADAS  # noqa: E402

resultados = []


def checar(nome: str, condicao: bool, detalhe: str = "") -> None:
    resultados.append(condicao)
    print(f"[{'OK' if condicao else 'FALHA'}] {nome} {detalhe}")


def escalar(conexao: sqlite3.Connection, sql: str):
    return conexao.execute(sql).fetchone()[0]


def main() -> int:
    checar("arquivo dataops.db existe", CAMINHO_DB.exists())
    if not CAMINHO_DB.exists():
        print("Rode primeiro: python src/database/init_db.py && python src/database/seed_data.py")
        return 1

    with closing(conectar()) as conexao:
        checar("integridade do arquivo", escalar(conexao, "PRAGMA integrity_check") == "ok")

        for tabela in ("clientes", "produtos", "pedidos"):
            total = escalar(conexao, f"SELECT COUNT(*) FROM {tabela}")
            checar(f"{tabela} tem 50+ linhas", total >= 50, f"({total})")

        linhas_join = escalar(
            conexao,
            "SELECT COUNT(*) FROM pedidos p JOIN clientes c ON c.id = p.cliente_id",
        )
        checar("JOIN pedidos-clientes funciona", linhas_join > 0, f"({linhas_join})")

        consultas = {
            "clientes_sem_email": "SELECT COUNT(*) FROM clientes WHERE email IS NULL",
            "produtos_preco_zero": "SELECT COUNT(*) FROM produtos WHERE preco = 0",
            "pedidos_valor_negativo": "SELECT COUNT(*) FROM pedidos WHERE valor_total < 0",
            "pedidos_data_futura": "SELECT COUNT(*) FROM pedidos WHERE data_pedido > date('now')",
            "clientes_email_duplicado": (
                "SELECT COUNT(*) FROM clientes WHERE email IN ("
                "SELECT email FROM clientes WHERE email IS NOT NULL "
                "GROUP BY email HAVING COUNT(*) > 1)"
            ),
        }
        for nome, sql in consultas.items():
            obtido = escalar(conexao, sql)
            esperado = ANOMALIAS_ESPERADAS[nome]
            checar(f"anomalia {nome}", obtido == esperado, f"(esperado {esperado}, obtido {obtido})")

        try:
            conexao.execute(
                "INSERT INTO pedidos (cliente_id, produto_id, quantidade, valor_total, data_pedido) "
                "VALUES (?, ?, ?, ?, ?)",
                (9999, 10, 1, 10.0, "2025-01-01"),
            )
            checar("FK recusa cliente inexistente", False)
        except sqlite3.IntegrityError:
            checar("FK recusa cliente inexistente", True)
        conexao.rollback()

    total_ok = sum(resultados)
    print(f"\n{total_ok}/{len(resultados)} verificacoes aprovadas")
    return 0 if all(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())