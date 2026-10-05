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
clientes ──< pedidos ──< itens_pedido >── produtos >── categorias
                 └──< pagamentos
```
Dados gerados com Faker (pt_BR), com anomalias propositais para auditoria.

## 🧰 Ferramentas MCP
`listar_tabelas` · `descrever_tabela` · `executar_consulta` · `checar_nulos` · `checar_anomalias` · `buscar_documentacao`

## 💬 Exemplos
- "Quais colunas da tabela clientes têm valores nulos?"
- "Qual foi o faturamento por mês?"
- "Apague a tabela pedidos" → 🚫 bloqueado

## 🧪 Tecnologias
Python · SQLite · MCP · Gemini API · Streamlit · Pandas · Faker

## ▶️ Como executar
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # adicione sua GEMINI_API_KEY
python src/gerar_dados.py
streamlit run app.py
```
