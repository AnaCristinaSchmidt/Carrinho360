import asyncio
import sqlite3

import pandas as pd
import streamlit as st

from src.agent.dataops_agent import DataOpsAgent
from src.database.init_db import CAMINHO_DB

st.set_page_config(page_title="DataOps Agent", page_icon="🛒", layout="wide")


def inicializar_estado() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "historico_llm" not in st.session_state:
        st.session_state.historico_llm = []


async def _consultar(pergunta: str, historico_llm: list) -> dict:
    async with DataOpsAgent(historico=historico_llm) as agente:
        return await agente.perguntar(pergunta)


def perguntar_ao_agente(pergunta: str) -> dict:
    """O Streamlit e sincrono: abrimos o agente (e o servidor MCP) a cada pergunta e fechamos ao final."""
    historico = st.session_state.historico_llm
    tamanho_anterior = len(historico)
    try:
        return asyncio.run(_consultar(pergunta, historico))
    except BaseException:
        del historico[tamanho_anterior:]
        raise


def metricas_do_banco() -> dict:
    """Le metadados do banco sem alterar nada (modo read-only)."""
    if not CAMINHO_DB.exists():
        return {"status": "arquivo ausente", "tabelas": 0, "registros": 0}
    with sqlite3.connect(f"file:{CAMINHO_DB}?mode=ro", uri=True) as conexao:
        tabelas = [
            linha[0]
            for linha in conexao.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
        ]
        registros = sum(conexao.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0] for tabela in tabelas)
    return {"status": "conectado", "tabelas": len(tabelas), "registros": registros}


def renderizar_sidebar() -> None:
    metricas = metricas_do_banco()
    st.sidebar.header("Saude da base")
    st.sidebar.metric("Status", metricas["status"])
    st.sidebar.metric("Tabelas", metricas["tabelas"])
    st.sidebar.metric("Registros auditados", metricas["registros"])
    st.sidebar.divider()
    if st.sidebar.button("Limpar conversa"):
        st.session_state.messages = []
        st.session_state.historico_llm = []
        st.rerun()


def desenhar_grafico(df: pd.DataFrame) -> None:
    """Grafico de barras quando ha exatamente 1 coluna categorica e 1+ numericas, com poucas linhas."""
    categoricas = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    numericas = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(categoricas) == 1 and numericas and 1 < len(df) <= 30:
        st.bar_chart(df, x=categoricas[0], y=numericas[0])


def renderizar_trace(trace: list[dict]) -> None:
    with st.expander(f"🛠️ Rastro de Execução das Ferramentas MCP ({len(trace)} chamadas)", expanded=False):
        for passo in trace:
            st.markdown(f"**Turno {passo['turno']}: `{passo['ferramenta']}`** ({passo['tempo_ms']} ms)")
            st.json(passo["argumentos"])

            guardrail = passo.get("guardrail")
            if guardrail is not None:
                if guardrail["aprovada"]:
                    st.success("✅ Aprovado pelo guardrail")
                else:
                    st.error(f"❌ Bloqueado pelo guardrail: {guardrail['motivo']}")

            if passo.get("query_sql"):
                st.code(passo["query_sql"], language="sql")

            if not passo["sucesso"]:
                erro = passo["resultado"].get("erro") if isinstance(passo["resultado"], dict) else passo["resultado"]
                st.warning(f"A ferramenta retornou erro: {erro}")
            st.divider()


def renderizar_dados(trace: list[dict]) -> None:
    """Mostra a tabela da ULTIMA consulta analitica bem-sucedida do turno."""
    consultas = [
        p for p in trace
        if p["ferramenta"] == "executar_query_analitica" and p["sucesso"] and isinstance(p["resultado"], dict)
    ]
    if not consultas:
        return
    resultado = consultas[-1]["resultado"]
    df = pd.DataFrame(resultado["linhas"], columns=resultado.get("colunas"))
    st.dataframe(df, width="stretch")
    desenhar_grafico(df)


def renderizar_mensagem(mensagem: dict) -> None:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])
        if mensagem.get("trace"):
            renderizar_dados(mensagem["trace"])
            renderizar_trace(mensagem["trace"])


def main() -> None:
    renderizar_sidebar()
    st.title("DataOps Agent")
    st.caption("Assistente de auditoria de dados: somente leitura, com rastreabilidade de cada ferramenta.")
    inicializar_estado()

    for mensagem in st.session_state.messages:
        renderizar_mensagem(mensagem)

    pergunta = st.chat_input("Pergunte algo sobre os dados...")
    if pergunta:
        mensagem_usuario = {"role": "user", "content": pergunta}
        st.session_state.messages.append(mensagem_usuario)
        renderizar_mensagem(mensagem_usuario)
        with st.spinner("Consultando o agente..."):
            try:
                saida = perguntar_ao_agente(pergunta)
                resposta = {"role": "assistant", "content": saida["resposta"], "trace": saida["trace"]}
            except Exception as erro:
                resposta = {"role": "assistant", "content": f"Nao consegui concluir: {erro}", "trace": []}
        st.session_state.messages.append(resposta)
        renderizar_mensagem(resposta)


main()
