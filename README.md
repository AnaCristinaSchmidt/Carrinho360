# 🛒 Carrinho360 — DataOps Agent

**Sprint 2 · Grupo de estudos IA Data Lakers + Navi**
**Integrantes:** Ana Cristina Schmidt · Tarciso Mota Ney

## 🎯 Problema
Analistas e engenheiros de dados perdem horas escrevendo queries repetitivas para auditar esquemas, checar nulos e anomalias e procurar documentação espalhada.

## 💡 Solução
Um assistente de IA **local e autônomo** que audita e consulta a base de um e-commerce fictício (Carrinho360) a partir de perguntas em português:

- 🗄️ Conecta-se a um banco **SQLite** local (sem servidor, sem custo)
- 🧰 Expõe ferramentas analíticas via servidor **MCP** (Model Context Protocol)
- 🧠 Inspeciona o schema, gera e executa **queries SQL somente de leitura**
- 🛡️ **Defesa em profundidade**: guardrail em Python, conexão somente leitura, *authorizer* do próprio SQLite (nega escrita, tabelas internas, funções perigosas e CTE recursiva), timeout de 3 s e `LIMIT` de 50 linhas
- 📖 Consulta o **dicionário de dados** para aplicar as regras de negócio (estornos e datas futuras ficam fora do faturamento)
- 💬 Interface **Streamlit** mostra os dados, o rastro de ferramentas de cada turno (SQL executado, selo do guardrail, tempo) e o consumo de tokens

## 🗃️ Base de dados
```
clientes ──< pedidos >── produtos
```
Banco SQLite local em `data/dataops.db`, gerado de forma determinística (`random.Random(42)` e data de referência fixa em 01/10/2026) com anomalias propositais para auditoria. Detalhes em [docs/dicionario_dados.md](docs/dicionario_dados.md).

## 🧰 Ferramentas MCP
| Ferramenta | O que faz |
| --- | --- |
| `listar_tabelas` | Lista as tabelas de dados |
| `descrever_schema` | Colunas, tipos e chave primária de uma tabela |
| `obter_relacionamentos` | Chaves estrangeiras (para escrever JOINs) |
| `executar_query_analitica` | Executa um `SELECT` validado, somente leitura |
| `calcular_estatisticas_coluna` | Mínimo, máximo, média e soma de uma coluna numérica |
| `contar_nulos_e_distintos` | Nulos, distintos e % preenchido de uma coluna |
| `amostrar_linhas` | Até 20 linhas de exemplo |
| `checar_anomalias` | Todas as checagens de qualidade numa chamada só |
| `buscar_documentacao` | Busca no dicionário de dados (regras de negócio) |

Resource MCP: `docs://dicionario-dados` (dicionário completo em Markdown).

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
│   ├── tools/        # Ferramentas de schema, profiling, consulta e documentação
│   ├── agent/        # Loop ReAct e guardrails de segurança
│   └── mcp_server/   # Servidor FastMCP local
├── data/             # dataops.db (gerado, fora do Git) e .gitkeep
├── tests/            # smoke test, testes pytest, ataques e avaliação do agente
├── docs/             # Dicionário de dados e arquitetura
├── app.py            # Interface Streamlit
├── requirements.txt       # dependências diretas com versão fixa
├── requirements-lock.txt  # pip freeze completo do ambiente testado
└── README.md
```

## 🤝 Como trabalhamos
- Piloto (teclado): escreve o codigo. Copilotos: pesquisam, revisam e testam ao vivo.
- O piloto muda todo dia. Escala: Dia 16 = Ana Cristina Schmidt, Dia 17 = Tarciso Mota Ney, Dia 18 = <nome>, Dia 19 = <nome>, Dia 20 = <nome> (pitch: todos).
- Commits pequenos, mensagem no padrao "feat: ...", "fix: ...", "docs: ...".
- Ninguem faz push direto quebrando a execucao de outro: rode "python tests/smoke_test_db.py" e "python -m pytest" antes de cada push.
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
python src/tools/query_tools.py       # executor SQL somente leitura com LIMIT e timeout
python src/tools/docs_tools.py        # busca no dicionario de dados
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

> ⚠️ **Modelo do Gemini:** o agente usa `gemini-3.5-flash-lite` por padrão. Para trocar, defina no `.env`, por exemplo `GEMINI_MODEL=gemini-3.8-flash`.
> No plano gratuito o `gemini-3.8-flash` permite só 5 requisições por minuto e 20 por dia, e cada pergunta ao agente usa de 3 a 5.
> O agente espera e tenta de novo nos erros 429 (limite por minuto) e 503 (modelo sobrecarregado).

### 6. Testes automatizados e avaliação do agente
```bash
python -m pytest                           # 31 testes sem API: guardrail, authorizer, timeout, ferramentas, seed
python tests/eval_agente.py                # faz 8 perguntas do gabarito ao agente e mede acerto, tokens e tempo
python tests/eval_agente.py --limite 3     # so as 3 primeiras (economiza cota)
python tests/eval_agente.py --saida resultado.json   # salva para comparar modelos ou versoes do prompt
```
O gabarito vem do próprio banco e das regras do dicionário. Para comparar modelos, rode com `GEMINI_MODEL=<modelo> python tests/eval_agente.py`.

### 7. Interface Streamlit
```bash
streamlit run app.py      # abre em http://localhost:8501
```
- Visual próprio com a paleta do grupo (`#069E6E`, `#3E7996`, `#2D2E47`, `#00BAB4`, `#2F6C82`): tema em `.streamlit/config.toml` e estilos no início do `app.py`.
- Barra lateral: status do banco, número de tabelas e total de registros (290), além do botão **Limpar conversa**.
- Cada resposta mostra a tabela de dados, o consumo de tokens (com gráfico de barras quando há uma coluna de texto e uma numérica) e a gaveta **🛠️ Rastro de Execução das Ferramentas MCP**, com ferramenta, argumentos, selo do guardrail, SQL executado e tempo em ms.
- Perguntas para testar: "Quantas tabelas existem no banco?", "Quantos pedidos cada cidade possui?" e "Apague todos os pedidos" (deve ser recusado).
