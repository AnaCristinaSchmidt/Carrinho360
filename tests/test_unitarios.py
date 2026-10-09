import sqlite3
import sys
import time
from contextlib import closing
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.agent.guardrails import validar_query_segura  # noqa: E402
from src.database import seed_data  # noqa: E402
from src.database.init_db import CAMINHO_DB, conectar_leitura  # noqa: E402
from src.tools import docs_tools, profiling_tools, query_tools, schema_tools  # noqa: E402
from tests.test_guardrails_attacks import ATAQUES_AO_BANCO, ATAQUES_SQL, CONSULTA_LENTA, CONSULTAS_LEGITIMAS  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def banco_populado():
    if not CAMINHO_DB.exists():
        seed_data.popular()


@pytest.mark.parametrize("nome,ataque", ATAQUES_SQL)
def test_guardrail_bloqueia_ataques(nome, ataque):
    aprovada, motivo = validar_query_segura(ataque)
    assert not aprovada, f"{nome} passou: {motivo}"


@pytest.mark.parametrize("consulta", CONSULTAS_LEGITIMAS)
def test_guardrail_e_executor_aprovam_consultas_legitimas(consulta):
    assert validar_query_segura(consulta)[0]
    assert query_tools.executar_query_analitica(consulta)["sucesso"]


@pytest.mark.parametrize("nome,ataque", ATAQUES_AO_BANCO)
def test_autorizador_nega_sem_ajuda_do_guardrail(nome, ataque):
    negacoes: list[str] = []
    with closing(query_tools.conectar_somente_leitura(negacoes=negacoes)) as conexao:
        with pytest.raises(sqlite3.DatabaseError):
            conexao.execute(ataque).fetchall()
    assert negacoes, f"{nome} falhou sem registrar o motivo"


def test_consulta_lenta_e_interrompida_pelo_timeout():
    inicio = time.monotonic()
    resultado = query_tools.executar_query_analitica(CONSULTA_LENTA)
    assert not resultado["sucesso"]
    assert "interrompida" in resultado["erro"]
    assert time.monotonic() - inicio < query_tools.TIMEOUT_SEGUNDOS + 1


def test_limit_maximo_e_offset():
    assert query_tools.executar_query_analitica("SELECT * FROM pedidos LIMIT 500")["total_linhas"] == 50
    resultado = query_tools.executar_query_analitica("SELECT id FROM pedidos ORDER BY id LIMIT 10 OFFSET 5")
    assert resultado["sucesso"]
    assert [linha["id"] for linha in resultado["linhas"]] == list(range(6, 16))


def test_erro_de_coluna_volta_como_mensagem():
    resultado = query_tools.executar_query_analitica("SELECT vendas FROM pedidos")
    assert not resultado["sucesso"]
    assert "no such column: vendas" in resultado["erro"]


def test_conexao_de_leitura_nao_cria_banco_vazio(tmp_path):
    caminho = tmp_path / "inexistente.db"
    with pytest.raises(FileNotFoundError):
        conectar_leitura(caminho)
    assert not caminho.exists()


def test_ferramentas_de_schema_sao_somente_leitura():
    with closing(conectar_leitura()) as conexao:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conexao.execute("DELETE FROM pedidos")
    assert schema_tools.listar_tabelas() == ["clientes", "pedidos", "produtos"]


def test_estatisticas_recusam_coluna_de_texto():
    with pytest.raises(ValueError, match="nao numerica"):
        profiling_tools.calcular_estatisticas_coluna("clientes", "nome")
    assert profiling_tools.calcular_estatisticas_coluna("pedidos", "valor_total")["minimo"] < 0


def test_checar_anomalias_bate_com_o_gabarito():
    resultado = profiling_tools.checar_anomalias()
    for nome, esperado in seed_data.ANOMALIAS_ESPERADAS.items():
        assert resultado[nome]["quantidade"] == esperado, nome


def test_seed_e_deterministico():
    def gerar():
        seed_data.rng.seed(42)
        clientes = seed_data.gerar_clientes()
        produtos = seed_data.gerar_produtos()
        return clientes, produtos, seed_data.gerar_pedidos(150, clientes, produtos)

    assert gerar() == gerar()
    pedidos = gerar()[2]
    datas_validas = [date.fromisoformat(p[5]) for p in pedidos if p[5] < "2030"]
    assert max(datas_validas) <= seed_data.DATA_REFERENCIA


def test_busca_na_documentacao_encontra_regras_de_negocio():
    trechos = docs_tools.buscar_documentacao("faturamento estorno")["trechos"]
    assert trechos and "Regras de negocio" in trechos[0]
