# 🛒 Carrinho360 — DataOps Agent

**Sprint 2 · Grupo de estudos IA Data Lakers + Navi**
**Integrantes:** Ana Cristina Schmidt · Tarciso Ney

## 🎯 Problema
Analistas e engenheiros de dados perdem horas escrevendo queries repetitivas para auditar esquemas, checar nulos e anomalias e procurar documentação espalhada.

## 💡 Solução
Um assistente de IA **local e autônomo** que audita e consulta a base de um e-commerce fictício (Carrinho360) a partir de perguntas em português:

- 🗄️ Conecta-se a um banco **SQLite** local (sem servidor, sem custo)
- 🧰 Expõe ferramentas analíticas via servidor **MCP** (Model Context Protocol)
- 🧠 Inspeciona o schema, gera e executa **queries SQL somente de leitura**
- 🛡️ **Guardrails** bloqueiam comandos de escrita (`DROP`, `DELETE`, `UPDATE`...)
- 💬 Interface **Streamlit** mostra os dados, o raciocínio e as ferramentas usadas em cada turno

## 🗃️ Base de dados
```
clientes ──< pedidos >── produtos
```
Banco SQLite local em `data/dataops.db`, gerado de forma determinística (`random.Random(42)`) com anomalias propositais para auditoria. Detalhes em [docs/dicionario_dados.md](docs/dicionario_dados.md).

## 🧰 Ferramentas MCP
`listar_tabelas` · `descrever_tabela` · `executar_consulta` · `checar_nulos` · `checar_anomalias` · `buscar_documentacao`

## 💬 Exemplos
- "Quais colunas da tabela clientes têm valores nulos?"
- "Qual foi o faturamento por mês?"
- "Apague a tabela pedidos" → 🚫 bloqueado

## 🧪 Tecnologias
Python · SQLite · MCP · Gemini API · Streamlit

## 📂 Estrutura
```
Carrinho360/
├── src/
│   ├── database/     # init_db.py (DDL) e seed_data.py (carga + anomalias)
│   ├── tools/        # Ferramentas analíticas e de schema
│   ├── agent/        # Loop ReAct e guardrails de segurança
│   └── mcp_server/   # Servidor FastMCP local
├── data/             # dataops.db (gerado, fora do Git) e .gitkeep
├── tests/            # smoke_test_db.py
├── docs/             # Dicionário de dados e arquitetura
├── requirements.txt
└── README.md
```

## 🤝 Como trabalhamos
- Piloto (teclado): escreve o codigo. Copilotos: pesquisam, revisam e testam ao vivo.
- O piloto muda todo dia. Escala: Dia 16 = <Ana Cristina Schmidt>, Dia 17 = <Tarciso Mota Ney>, Dia 18 = <nome>, Dia 19 = <nome>, Dia 20 = <nome> (pitch: todos).
- Commits pequenos, mensagem no padrao "feat: ...", "fix: ...", "docs: ...".
- Ninguem faz push direto quebrando a execucao de outro: rode "python tests/smoke_test_db.py" antes de cada push.
- Ao comecar o dia: git pull. Ao terminar: git push e tag do dia (v0.1-setup no Dia 16).
- Conflito no Git: resolver juntos, na mesma tela.

## ▶️ Como rodar
Todos os comandos são executados a partir da raiz do repositório.

### 1. Primeira vez (setup)
```bash
python3 -m venv .venv               # cria o ambiente virtual do projeto
source .venv/bin/activate           # ativa o venv (o terminal passa a mostrar "(.venv)")
pip install -r requirements.txt     # instala as dependencias DENTRO do venv
echo "GEMINI_API_KEY=sua_chave_aqui" > .env   # chave em https://aistudio.google.com/apikey
```

No VSCode, selecione o interpretador do venv: `Cmd+Shift+P` → **Python: Select Interpreter** → `.venv`.

### 2. Todo dia (antes de rodar qualquer script)
```bash
git pull
source .venv/bin/activate
```

### 3. Banco de dados
```bash
python src/database/init_db.py      # cria as tabelas (apaga o banco anterior)
python src/database/seed_data.py    # popula com dados + anomalias
python tests/smoke_test_db.py       # deve mostrar 12/12 verificacoes aprovadas
```

### 4. Ferramentas
```bash
python src/tools/schema_tools.py      # tabelas, colunas e chaves estrangeiras
python src/tools/profiling_tools.py   # nulos, distintos, estatisticas e amostras
python src/tools/query_tools.py       # executor SQL somente leitura com LIMIT
python src/agent/test_tools_llm.py    # Gemini usando as ferramentas (precisa do .env)
```

### 5. Guardrails, servidor MCP e agente
```bash
python src/agent/guardrails.py                    # 4 consultas aprovadas e 4 bloqueadas
python tests/test_guardrails_attacks.py           # ataques SQL (sem API): deve dar APROVADO
python tests/test_guardrails_attacks.py --com-modelo   # + pedidos maliciosos ao agente (usa a API)
python -m src.mcp_server.dataops_mcp              # servidor MCP (fica esperando: Ctrl+C para sair)
python -m src.agent.dataops_agent                 # agente ReAct com a pergunta padrao
python -m src.agent.dataops_agent "Qual o total de vendas por categoria?"
```
Inspecionar o servidor MCP no navegador: `npx @modelcontextprotocol/inspector python -m src.mcp_server.dataops_mcp`.

> ⚠️ **Cota gratuita do Gemini:** o `gemini-3.8-flash` permite 5 requisições por minuto e 20 por dia, e cada pergunta ao agente usa de 3 a 5.
> O agente espera e tenta de novo nos erros 429 por minuto e 503 (modelo sobrecarregado). Quando a cota **diária** acabar, troque de modelo no `.env`:
> `GEMINI_MODEL=gemini-3.5-flash-lite`
