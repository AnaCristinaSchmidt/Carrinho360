import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from src.agent.guardrails import validar_query_segura  # noqa: E402
from src.tools import docs_tools, profiling_tools, query_tools, schema_tools  # noqa: E402

mcp = FastMCP("dataops-agent")


@mcp.tool()
def listar_tabelas() -> list[str]:
    """Lista as tabelas de dados do banco. Use SEMPRE como primeiro passo."""
    return schema_tools.listar_tabelas()


@mcp.tool()
def descrever_schema(nome_tabela: str) -> dict:
    """Descreve colunas, tipos e chave primaria de uma tabela."""
    return schema_tools.descrever_schema_tabela(nome_tabela)


@mcp.tool()
def obter_relacionamentos(nome_tabela: str) -> list[dict]:
    """Lista as chaves estrangeiras de uma tabela; use antes de escrever JOINs."""
    return schema_tools.obter_chaves_estrangeiras(nome_tabela)


@mcp.tool()
def executar_query_analitica(query: str, limite: int = 50) -> dict:
    """Executa uma consulta SQL SELECT (somente leitura) e retorna colunas, linhas e tempo gasto."""
    aprovada, motivo = validar_query_segura(query)
    if not aprovada:
        return {
            "sucesso": False,
            "erro": f"Bloqueado pelo guardrail: {motivo}",
            "query_executada": None,
            "guardrail": {"aprovada": False, "motivo": motivo},
        }
    resultado = query_tools.executar_query_analitica(query, limite)
    resultado["guardrail"] = {"aprovada": True, "motivo": motivo}
    return resultado


@mcp.tool()
def calcular_estatisticas_coluna(nome_tabela: str, nome_coluna: str) -> dict:
    """Calcula minimo, maximo, media e soma de uma coluna numerica (recusa colunas de texto)."""
    return profiling_tools.calcular_estatisticas_coluna(nome_tabela, nome_coluna)


@mcp.tool()
def contar_nulos_e_distintos(nome_tabela: str, nome_coluna: str) -> dict:
    """Mede a qualidade de uma coluna: total de linhas, nulos, percentual preenchido e valores distintos."""
    return profiling_tools.contar_nulos_e_distintos(nome_tabela, nome_coluna)


@mcp.tool()
def amostrar_linhas(nome_tabela: str, qtd: int = 5) -> list[dict]:
    """Retorna ate 20 linhas de exemplo de uma tabela para entender o formato dos dados."""
    return profiling_tools.amostrar_linhas(nome_tabela, qtd)


@mcp.tool()
def checar_anomalias() -> dict:
    """Roda de uma vez todas as checagens de qualidade (e-mails nulos e duplicados, preco zero, valores negativos, datas futuras)."""
    return profiling_tools.checar_anomalias()


@mcp.tool()
def buscar_documentacao(termo: str = "") -> dict:
    """Busca no dicionario de dados o significado de colunas, anomalias e regras de negocio (ex: faturamento, estorno)."""
    return docs_tools.buscar_documentacao(termo)


@mcp.resource("docs://dicionario-dados", mime_type="text/markdown")
def dicionario_dados() -> str:
    """Dicionario de dados completo do Carrinho360."""
    return docs_tools.ler_dicionario()


if __name__ == "__main__":
    print("dataops-agent MCP iniciado (stdio)", file=sys.stderr)
    mcp.run(transport="stdio")
