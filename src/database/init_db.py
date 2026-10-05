import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CAMINHO_DB = RAIZ / "data" / "dataops.db"


def conectar(caminho: Path = CAMINHO_DB) -> sqlite3.Connection:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    # As chaves estrangeiras do SQLite vem DESLIGADAS por padrao: ligue em TODA conexao
    conexao.execute("PRAGMA foreign_keys = ON;")
    return conexao


DDL = """
CREATE TABLE IF NOT EXISTS clientes (
    id         INTEGER PRIMARY KEY,
    nome       TEXT NOT NULL,
    email      TEXT,
    cidade     TEXT NOT NULL,
    criado_em  DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS produtos (
    id         INTEGER PRIMARY KEY,
    nome       TEXT NOT NULL,
    categoria  TEXT NOT NULL,
    preco      REAL NOT NULL,
    criado_em  DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS pedidos (
    id           INTEGER PRIMARY KEY,
    cliente_id   INTEGER NOT NULL,
    produto_id   INTEGER NOT NULL,
    quantidade   INTEGER NOT NULL,
    valor_total  REAL NOT NULL,
    data_pedido  DATETIME NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON pedidos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_produto ON pedidos(produto_id);
"""


def criar_tabelas(conexao: sqlite3.Connection) -> None:
    conexao.executescript(DDL)
    conexao.commit()


def resetar_banco() -> None:
    """Apaga o arquivo do banco (se existir) para recomecar do zero."""
    if CAMINHO_DB.exists():
        CAMINHO_DB.unlink()


if __name__ == "__main__":
    resetar_banco()
    with conectar() as conexao:
        criar_tabelas(conexao)
        tabelas = conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        print("Tabelas criadas:", [linha["name"] for linha in tabelas])
        print("Chaves estrangeiras ativas:", conexao.execute("PRAGMA foreign_keys").fetchone()[0])