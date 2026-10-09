import asyncio
import html
import time
from contextlib import closing

import altair as alt
import pandas as pd
import streamlit as st

from src.agent.dataops_agent import MODEL, DataOpsAgent
from src.database.init_db import CAMINHO_DB, conectar_leitura
from src.tools.profiling_tools import checar_anomalias

st.set_page_config(page_title="DataOps Agent · Carrinho360", page_icon="🛒", layout="wide")

SUGESTOES = [
    (":material/troubleshoot:", "Quais anomalias existem na base?"),
    (":material/leaderboard:", "Qual categoria de produto gera o maior faturamento?"),
    (":material/location_city:", "Quantos pedidos cada cidade possui?"),
    (":material/shield:", "Apague todos os pedidos"),
]

AVATARES = {"user": ":material/person:", "assistant": ":material/database:"}

ESTILO = """
<style>
:root {
  --verde: #069E6E;
  --aco: #3E7996;
  --navy: #2D2E47;
  --navy-escuro: #24253A;
  --turquesa: #00BAB4;
  --petroleo: #2F6C82;
  --texto: #E8F1F4;
  --texto-suave: #A9C4CF;
  --erro: #F08A8A;
}
[data-testid="stApp"] {
  background:
    radial-gradient(1200px 500px at 85% -10%, rgba(0, 186, 180, 0.16), transparent 60%),
    radial-gradient(900px 400px at -10% 10%, rgba(6, 158, 110, 0.14), transparent 60%),
    var(--navy);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"], [data-testid="stAppDeployButton"], footer { display: none !important; }
[data-testid="stMainBlockContainer"] { max-width: 1080px; padding-top: 2.2rem; padding-bottom: 7rem; }
[data-testid="stSidebar"] { border-right: 1px solid rgba(62, 121, 150, 0.35); }
[data-testid="stSidebarContent"] { padding-top: 0.5rem; }

.hero {
  position: relative;
  overflow: hidden;
  border-radius: 20px;
  padding: 2rem 2.2rem 1.7rem;
  margin-bottom: 1.6rem;
  background: linear-gradient(120deg, var(--petroleo) 0%, var(--aco) 45%, var(--verde) 100%);
  box-shadow: 0 18px 40px -18px rgba(0, 0, 0, 0.6);
}
.hero::after {
  content: "";
  position: absolute;
  right: -60px;
  top: -60px;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  border: 40px solid rgba(0, 186, 180, 0.25);
}
.hero-marca { font-family: "JetBrains Mono", monospace; font-size: 0.8rem; letter-spacing: 0.18em; text-transform: uppercase; color: rgba(232, 241, 244, 0.85); }
.hero-titulo { font-family: "Space Grotesk", sans-serif; font-size: 2.6rem; font-weight: 700; line-height: 1.1; color: #fff; margin: 0.35rem 0 0.6rem; }
.hero-texto { max-width: 620px; color: rgba(255, 255, 255, 0.9); font-size: 1.02rem; margin: 0 0 1.1rem; }
.hero-selos { display: flex; flex-wrap: wrap; gap: 0.5rem; position: relative; z-index: 1; }
.hero-selos span {
  font-size: 0.78rem;
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  background: rgba(45, 46, 71, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #fff;
}

.boas-vindas { color: var(--texto-suave); margin: 0.2rem 0 0.8rem; font-size: 0.95rem; }
.st-key-sugestoes button {
  min-height: 4.2rem;
  justify-content: flex-start;
  text-align: left;
  background: rgba(62, 121, 150, 0.14);
  border: 1px solid rgba(62, 121, 150, 0.45);
  color: var(--texto);
  transition: border-color 0.15s, background 0.15s, transform 0.15s;
}
.st-key-sugestoes button div { justify-content: flex-start; }
.st-key-sugestoes button:hover { border-color: var(--turquesa); background: rgba(0, 186, 180, 0.12); color: #fff; transform: translateY(-2px); }

[data-testid="stChatMessage"] {
  border-radius: 16px;
  padding: 1rem 1.1rem;
  margin-bottom: 0.9rem;
  background: rgba(36, 37, 58, 0.75);
  border: 1px solid rgba(62, 121, 150, 0.35);
}
[data-testid="stChatMessage"]:has(.msg-user) {
  background: linear-gradient(120deg, rgba(47, 108, 130, 0.55), rgba(62, 121, 150, 0.35));
  border-color: rgba(62, 121, 150, 0.6);
  width: auto;
  max-width: 88%;
  margin-left: auto;
}
[data-testid="stChatMessage"]:has(.msg-bot) { border-left: 3px solid var(--turquesa); }
[data-testid="stElementContainer"]:has(.msg-user), [data-testid="stElementContainer"]:has(.msg-bot),
[data-testid="stElementContainer"]:has(> div > div > style), [data-testid="stElementContainer"]:has(style) { display: none; }
[data-testid="stChatMessageAvatarCustom"], [data-testid^="stChatMessageAvatar"] {
  background: var(--navy) !important;
  border: 1px solid var(--turquesa);
  color: var(--turquesa);
}

[data-testid="stChatInput"] { border: 1px solid var(--aco) !important; background: var(--navy-escuro) !important; border-radius: 14px !important; }
[data-testid="stChatInput"] > div { border-radius: 14px !important; background: transparent !important; }
[data-testid="stChatInput"]:focus-within { border-color: var(--turquesa) !important; box-shadow: 0 0 0 3px rgba(0, 186, 180, 0.18); }
[data-testid="stBottomBlockContainer"] { background: linear-gradient(transparent, var(--navy) 35%); }

[data-testid="stExpander"] details { border: 1px solid rgba(62, 121, 150, 0.45); background: rgba(45, 46, 71, 0.6); border-radius: 12px; }
[data-testid="stExpander"] summary:hover { color: var(--turquesa); }
[data-testid="stTabs"] button[aria-selected="true"] { color: var(--turquesa); }
[data-baseweb="tab-highlight"] { background-color: var(--turquesa) !important; }

.rotulo-secao { font-family: "JetBrains Mono", monospace; font-size: 0.72rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--texto-suave); margin: 0.9rem 0 0.4rem; }

.passo { position: relative; padding: 0.15rem 0 0.2rem 2.4rem; margin-top: 0.6rem; }
.passo::before { content: ""; position: absolute; left: 0.85rem; top: 1.9rem; bottom: -0.9rem; width: 2px; background: rgba(62, 121, 150, 0.45); }
.passo-num {
  position: absolute;
  left: 0;
  top: 0.1rem;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-family: "JetBrains Mono", monospace;
  font-size: 0.75rem;
  font-weight: 600;
  background: var(--navy-escuro);
  border: 1px solid var(--turquesa);
  color: var(--turquesa);
}
.passo-cabeca { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; }
.passo-ferramenta { font-family: "JetBrains Mono", monospace; font-weight: 600; color: var(--texto); }
.chip { font-family: "JetBrains Mono", monospace; font-size: 0.72rem; padding: 0.15rem 0.55rem; border-radius: 999px; background: rgba(62, 121, 150, 0.25); color: var(--texto-suave); }
.selo { font-size: 0.75rem; font-weight: 600; padding: 0.18rem 0.65rem; border-radius: 999px; }
.selo-ok { background: rgba(6, 158, 110, 0.2); border: 1px solid var(--verde); color: #fff; }
.selo-bloqueado { background: rgba(240, 138, 138, 0.14); border: 1px solid var(--erro); color: #fff; }
.passo-args { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.45rem; }
.arg { font-family: "JetBrains Mono", monospace; font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 6px; background: var(--navy-escuro); border: 1px solid rgba(62, 121, 150, 0.4); color: var(--texto); }
.arg b { color: var(--turquesa); font-weight: 600; margin-right: 0.3rem; }
.passo-erro { margin-top: 0.5rem; padding: 0.55rem 0.8rem; border-radius: 10px; border-left: 3px solid var(--erro); background: rgba(240, 138, 138, 0.1); color: var(--texto); font-size: 0.85rem; }

.uso { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.8rem; }
.uso span { font-family: "JetBrains Mono", monospace; font-size: 0.72rem; padding: 0.2rem 0.6rem; border-radius: 999px; border: 1px solid rgba(62, 121, 150, 0.5); color: var(--texto-suave); }

.marca-lateral { display: flex; align-items: center; gap: 0.7rem; padding: 0.4rem 0 1.1rem; }
.marca-icone { width: 2.4rem; height: 2.4rem; border-radius: 12px; display: grid; place-items: center; font-size: 1.25rem; background: linear-gradient(135deg, var(--turquesa), var(--verde)); }
.marca-nome { font-family: "Space Grotesk", sans-serif; font-weight: 700; font-size: 1.15rem; color: var(--texto); line-height: 1.1; }
.marca-sub { font-size: 0.75rem; color: var(--texto-suave); }
.kpis { display: grid; grid-template-columns: 1fr 1fr; gap: 0.55rem; margin-bottom: 0.55rem; }
.kpi { border-radius: 14px; padding: 0.75rem 0.85rem; background: var(--navy); border: 1px solid rgba(62, 121, 150, 0.4); }
.kpi-largo { grid-column: span 2; display: flex; align-items: center; justify-content: space-between; }
.kpi-rotulo { font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--texto-suave); }
.kpi-valor { font-family: "Space Grotesk", sans-serif; font-size: 1.6rem; font-weight: 700; color: var(--texto); line-height: 1.2; }
.kpi-alerta .kpi-valor { color: var(--turquesa); }
.status { display: inline-flex; align-items: center; gap: 0.4rem; font-weight: 600; font-size: 0.9rem; }
.status::before { content: ""; width: 0.55rem; height: 0.55rem; border-radius: 50%; background: var(--verde); box-shadow: 0 0 0 4px rgba(6, 158, 110, 0.25); }
.status-off::before { background: var(--erro); box-shadow: 0 0 0 4px rgba(240, 138, 138, 0.2); }
.camadas { margin: 0.4rem 0 0.2rem; padding: 0; list-style: none; }
.camadas li { font-size: 0.8rem; color: var(--texto-suave); padding: 0.35rem 0 0.35rem 1.4rem; position: relative; border-bottom: 1px dashed rgba(62, 121, 150, 0.3); }
.camadas li::before { content: ""; position: absolute; left: 0.2rem; top: 0.72rem; width: 0.5rem; height: 0.5rem; border-radius: 2px; background: var(--turquesa); transform: rotate(45deg); }
.modelo { font-family: "JetBrains Mono", monospace; font-size: 0.75rem; color: var(--texto-suave); margin-top: 0.8rem; }
.modelo b { color: var(--turquesa); font-weight: 600; }
.st-key-limpar button { width: 100%; border: 1px solid var(--aco); background: transparent; }
.st-key-limpar button:hover { border-color: var(--turquesa); color: var(--turquesa); }
</style>
"""


def _html(conteudo: str) -> None:
    st.markdown(conteudo, unsafe_allow_html=True)


def _e(valor) -> str:
    return html.escape(str(valor))


def _milhar(numero: int) -> str:
    return f"{numero:,}".replace(",", ".")


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
        return {"status": "arquivo ausente", "tabelas": 0, "registros": 0, "anomalias": 0}
    with closing(conectar_leitura()) as conexao:
        tabelas = [
            linha[0]
            for linha in conexao.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
        ]
        registros = sum(conexao.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0] for tabela in tabelas)
    anomalias = sum(item["quantidade"] for item in checar_anomalias().values())
    return {"status": "conectado", "tabelas": len(tabelas), "registros": registros, "anomalias": anomalias}


def limpar_conversa() -> None:
    st.session_state.messages = []
    st.session_state.historico_llm = []


def renderizar_sidebar() -> None:
    metricas = metricas_do_banco()
    conectado = metricas["status"] == "conectado"
    with st.sidebar:
        _html(
            '<div class="marca-lateral"><div class="marca-icone">🛒</div>'
            '<div><div class="marca-nome">Carrinho360</div><div class="marca-sub">DataOps Agent</div></div></div>'
            '<div class="rotulo-secao">Saúde da base</div>'
            '<div class="kpis">'
            f'<div class="kpi kpi-largo"><span class="kpi-rotulo">dataops.db</span>'
            f'<span class="status{"" if conectado else " status-off"}">{_e(metricas["status"])}</span></div>'
            f'<div class="kpi"><div class="kpi-rotulo">Tabelas</div><div class="kpi-valor">{metricas["tabelas"]}</div></div>'
            f'<div class="kpi"><div class="kpi-rotulo">Registros</div><div class="kpi-valor">{_milhar(metricas["registros"])}</div></div>'
            f'<div class="kpi kpi-largo kpi-alerta"><span class="kpi-rotulo">Anomalias detectadas</span>'
            f'<span class="kpi-valor">{metricas["anomalias"]}</span></div>'
            "</div>"
            '<div class="rotulo-secao">Camadas de defesa</div>'
            '<ul class="camadas">'
            "<li>Guardrail de SQL em Python</li>"
            "<li>Authorizer do próprio SQLite</li>"
            "<li>Conexão somente leitura</li>"
            "<li>Timeout de 3 s e LIMIT de 50 linhas</li>"
            "</ul>"
            f'<div class="modelo">modelo <b>{_e(MODEL)}</b></div>'
        )
        st.write("")
        st.button("Limpar conversa", key="limpar", icon=":material/refresh:", width="stretch", on_click=limpar_conversa)


def renderizar_cabecalho() -> None:
    _html(
        '<div class="hero">'
        '<div class="hero-marca">Carrinho360 · auditoria de dados</div>'
        '<div class="hero-titulo">DataOps Agent</div>'
        '<p class="hero-texto">Pergunte em português. O agente descobre o schema, escreve o SQL, aplica as regras '
        "de negócio e mostra cada passo, sem nunca alterar um dado.</p>"
        '<div class="hero-selos"><span>Somente leitura</span><span>Guardrail + authorizer</span>'
        "<span>Rastro de cada ferramenta</span><span>Dicionário de dados</span></div>"
        "</div>"
    )


def escolher_sugestao(texto: str) -> None:
    st.session_state.pergunta_pendente = texto


def renderizar_sugestoes() -> None:
    _html('<p class="boas-vindas">Comece por uma destas perguntas ou escreva a sua abaixo.</p>')
    with st.container(key="sugestoes"):
        colunas = st.columns(2)
        for indice, (icone, texto) in enumerate(SUGESTOES):
            colunas[indice % 2].button(
                texto, key=f"sugestao_{indice}", icon=icone, width="stretch", on_click=escolher_sugestao, args=(texto,)
            )


def desenhar_grafico(df: pd.DataFrame) -> None:
    """Grafico de barras quando ha exatamente 1 coluna categorica e 1+ numericas, com poucas linhas."""
    categoricas = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    numericas = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(categoricas) == 1 and numericas and 1 < len(df) <= 30:
        grafico = (
            alt.Chart(df)
            .mark_bar(color="#00BAB4", cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X(f"{categoricas[0]}:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0, labelLimit=140)),
                y=alt.Y(
                    f"{numericas[0]}:Q",
                    title=numericas[0],
                    axis=alt.Axis(labelExpr="replace(format(datum.value, ',.0f'), /,/g, '.')"),
                ),
                tooltip=[categoricas[0], numericas[0]],
            )
            .properties(height=280)
            .configure_view(strokeWidth=0)
            .configure_axis(gridColor="#3E799640", domainColor="#3E7996", labelColor="#A9C4CF", titleColor="#A9C4CF")
        )
        st.altair_chart(grafico, width="stretch")


def _cartao_passo(numero: int, passo: dict) -> str:
    guardrail = passo.get("guardrail")
    selo = ""
    if guardrail is not None:
        if guardrail["aprovada"]:
            selo = '<span class="selo selo-ok">Aprovado pelo guardrail</span>'
        else:
            selo = f'<span class="selo selo-bloqueado">Bloqueado: {_e(guardrail["motivo"])}</span>'
    argumentos = "".join(
        f'<span class="arg"><b>{_e(chave)}</b>{_e(valor)}</span>'
        for chave, valor in passo["argumentos"].items()
        if chave != "query"
    )
    erro = ""
    if not passo["sucesso"]:
        resultado = passo["resultado"]
        mensagem = resultado.get("erro") if isinstance(resultado, dict) else resultado
        erro = f'<div class="passo-erro">A ferramenta retornou erro: {_e(mensagem)}</div>'
    return (
        f'<div class="passo"><span class="passo-num">{numero}</span>'
        f'<div class="passo-cabeca"><span class="passo-ferramenta">{_e(passo["ferramenta"])}</span>'
        f'<span class="chip">turno {passo["turno"]}</span><span class="chip">{passo["tempo_ms"]} ms</span>{selo}</div>'
        f'{f"<div class=passo-args>{argumentos}</div>" if argumentos else ""}{erro}</div>'
    )


def renderizar_trace(trace: list[dict]) -> None:
    tempo_total = round(sum(passo["tempo_ms"] for passo in trace), 1)
    rotulo = f"Rastro de execução · {len(trace)} ferramentas · {tempo_total} ms"
    with st.expander(rotulo, expanded=False, icon=":material/route:"):
        for numero, passo in enumerate(trace, start=1):
            _html(_cartao_passo(numero, passo))
            if passo.get("query_sql"):
                st.code(passo["query_sql"], language="sql", wrap_lines=True)


def _mostrar_resultado(resultado: dict) -> None:
    df = pd.DataFrame(resultado["linhas"], columns=resultado.get("colunas"))
    _html(f'<div class="rotulo-secao">Resultado · {len(df)} {"linha" if len(df) == 1 else "linhas"}</div>')
    st.dataframe(df, width="stretch", hide_index=True)
    desenhar_grafico(df)


def renderizar_dados(trace: list[dict]) -> None:
    """Mostra o resultado de cada consulta analitica bem-sucedida; com mais de uma, cada uma ganha sua aba."""
    consultas = [
        p for p in trace
        if p["ferramenta"] == "executar_query_analitica" and p["sucesso"] and isinstance(p["resultado"], dict)
    ]
    if len(consultas) == 1:
        _mostrar_resultado(consultas[0]["resultado"])
    elif consultas:
        abas = st.tabs([f"Consulta {indice}" for indice in range(1, len(consultas) + 1)])
        for aba, consulta in zip(abas, consultas):
            with aba:
                _mostrar_resultado(consulta["resultado"])


def renderizar_uso(mensagem: dict) -> None:
    uso = mensagem.get("uso")
    if not uso:
        return
    itens = [
        f"{uso['chamadas_modelo']} {'chamada' if uso['chamadas_modelo'] == 1 else 'chamadas'} ao modelo",
        f"{_milhar(uso['tokens_total'])} tokens",
        f"{_milhar(uso['tokens_entrada'])} entrada / {_milhar(uso['tokens_saida'])} saída",
    ]
    if mensagem.get("tempo_s") is not None:
        itens.append(f"{mensagem['tempo_s']} s")
    _html('<div class="uso">' + "".join(f"<span>{_e(item)}</span>" for item in itens) + "</div>")


def renderizar_mensagem(mensagem: dict) -> None:
    with st.chat_message(mensagem["role"], avatar=AVATARES[mensagem["role"]]):
        _html(f'<span class="{"msg-user" if mensagem["role"] == "user" else "msg-bot"}"></span>')
        st.markdown(mensagem["content"])
        if mensagem.get("trace"):
            renderizar_dados(mensagem["trace"])
            renderizar_trace(mensagem["trace"])
        renderizar_uso(mensagem)


def main() -> None:
    _html(ESTILO)
    inicializar_estado()
    renderizar_sidebar()
    renderizar_cabecalho()

    pergunta = st.chat_input("Pergunte algo sobre os dados…") or st.session_state.pop("pergunta_pendente", None)

    if not st.session_state.messages and not pergunta:
        renderizar_sugestoes()

    for mensagem in st.session_state.messages:
        renderizar_mensagem(mensagem)

    if pergunta:
        mensagem_usuario = {"role": "user", "content": pergunta}
        st.session_state.messages.append(mensagem_usuario)
        renderizar_mensagem(mensagem_usuario)
        inicio = time.perf_counter()
        with st.spinner("Consultando o agente…"):
            try:
                saida = perguntar_ao_agente(pergunta)
                resposta = {"role": "assistant", "content": saida["resposta"], "trace": saida["trace"], "uso": saida.get("uso")}
            except Exception as erro:
                resposta = {"role": "assistant", "content": f"Não consegui concluir: {erro}", "trace": []}
        resposta["tempo_s"] = round(time.perf_counter() - inicio, 1)
        st.session_state.messages.append(resposta)
        renderizar_mensagem(resposta)


main()
