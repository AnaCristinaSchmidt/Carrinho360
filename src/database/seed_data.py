import random
from datetime import date, timedelta

from init_db import conectar, criar_tabelas, resetar_banco

rng = random.Random(42)

ANOMALIAS_ESPERADAS = {
    "clientes_sem_email": 6,
    "emails_duplicados": 3,
    "produtos_preco_zero": 4,
    "pedidos_valor_negativo": 5,
    "pedidos_data_futura": 3,
}

NOMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fabio", "Gisele", "Hugo", "Iara", "Jonas"]
SOBRENOMES = ["Silva", "Souza", "Lima", "Costa", "Rocha", "Alves", "Pereira", "Martins"]
CIDADES = ["Porto Alegre", "Canoas", "Gramado", "Pelotas", "Caxias do Sul"]
CATEGORIAS = {
    "Eletronicos": ["Fone Bluetooth", "Smartphone", "Carregador", "Smartwatch"],
    "Livros": ["Romance", "Biografia", "Livro de Receitas", "HQ"],
    "Casa": ["Luminaria", "Jogo de Panelas", "Toalha de Banho", "Cafeteira"],
    "Esporte": ["Bola de Futebol", "Tenis de Corrida", "Garrafa Termica", "Tapete de Yoga"],
    "Moda": ["Camiseta", "Calca Jeans", "Jaqueta", "Bone"],
}


def gerar_clientes(qtd: int = 80) -> list[tuple]:
    linhas = []
    for i in range(1, qtd + 1):
        nome = f"{rng.choice(NOMES)} {rng.choice(SOBRENOMES)}"
        email = f"cliente{i}@exemplo.com"
        criado = date(2025, 1, 1) + timedelta(days=rng.randint(0, 600))
        linhas.append([i, nome, email, rng.choice(CIDADES), criado.isoformat()])
    # Anomalia 1: e-mails nulos nos 6 primeiros clientes
    for linha in linhas[: ANOMALIAS_ESPERADAS["clientes_sem_email"]]:
        linha[2] = None
    # Anomalia 2: clientes de indice 10, 11 e 12 com o MESMO e-mail
    for linha in linhas[10 : 10 + ANOMALIAS_ESPERADAS["emails_duplicados"]]:
        linha[2] = "duplicado@exemplo.com"
    return [tuple(linha) for linha in linhas]


def gerar_produtos(qtd: int = 60) -> list[tuple]:
    linhas = []
    for i in range(1, qtd + 1):
        categoria = rng.choice(list(CATEGORIAS))
        nome = f"{rng.choice(CATEGORIAS[categoria])} {i:02d}"
        preco = round(rng.uniform(10.0, 900.0), 2)
        criado = date(2024, 6, 1) + timedelta(days=rng.randint(0, 200))
        linhas.append([i, nome, categoria, preco, criado.isoformat()])
    # Anomalia 3: preco zerado nos 4 primeiros produtos
    for linha in linhas[: ANOMALIAS_ESPERADAS["produtos_preco_zero"]]:
        linha[3] = 0.0
    return [tuple(linha) for linha in linhas]


def gerar_pedidos(qtd: int, clientes: list[tuple], produtos: list[tuple]) -> list[tuple]:
    validos = [p for p in produtos if p[3] > 0]
    hoje = date.today()
    linhas = []
    for i in range(1, qtd + 1):
        cliente = rng.choice(clientes)
        produto = rng.choice(validos)
        quantidade = rng.randint(1, 5)
        valor_total = round(produto[3] * quantidade, 2)
        data_pedido = hoje - timedelta(days=rng.randint(1, 300))
        linhas.append([i, cliente[0], produto[0], quantidade, valor_total, data_pedido.isoformat()])
    sorteados = rng.sample(range(qtd), ANOMALIAS_ESPERADAS["pedidos_valor_negativo"] + ANOMALIAS_ESPERADAS["pedidos_data_futura"])
    negativos = sorteados[: ANOMALIAS_ESPERADAS["pedidos_valor_negativo"]]
    futuros = sorteados[ANOMALIAS_ESPERADAS["pedidos_valor_negativo"] :]
    # Anomalia 4: valor_total negativo (estorno mal lancado)
    for idx in negativos:
        linhas[idx][4] = -abs(linhas[idx][4])
    # Anomalia 5: data_pedido no futuro, em pedidos diferentes dos negativos
    for idx in futuros:
        linhas[idx][5] = date(2030, rng.randint(1, 12), rng.randint(1, 28)).isoformat()
    return [tuple(linha) for linha in linhas]


def popular() -> None:
    resetar_banco()
    with conectar() as conexao:
        criar_tabelas(conexao)
        clientes = gerar_clientes()
        produtos = gerar_produtos()
        pedidos = gerar_pedidos(150, clientes, produtos)
        conexao.executemany("INSERT INTO clientes VALUES (?, ?, ?, ?, ?)", clientes)
        conexao.executemany("INSERT INTO produtos VALUES (?, ?, ?, ?, ?)", produtos)
        conexao.executemany("INSERT INTO pedidos VALUES (?, ?, ?, ?, ?, ?)", pedidos)
        conexao.commit()
        for tabela in ("clientes", "produtos", "pedidos"):
            total = conexao.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            print(f"{tabela}: {total} linhas")


if __name__ == "__main__":
    popular()