# Dicionario de Dados: E-commerce de Varejo

Trio: Ana Cristina Schmidt | Tarciso Mota Ney | <terceiro nome>  |  Banco: data/dataops.db (SQLite)

## Tabela: clientes
Descricao: uma linha por pessoa cadastrada na loja.

| Coluna | Tipo | Restricoes | Descricao |
| --- | --- | --- | --- |
| id | INTEGER | PRIMARY KEY | Identificador do cliente |
| nome | TEXT | NOT NULL | Nome completo |
| email | TEXT | | E-mail de contato |
| cidade | TEXT | NOT NULL | Cidade de cadastro |
| criado_em | DATETIME | NOT NULL | Data do cadastro (AAAA-MM-DD) |

## Tabela: produtos
Descricao: uma linha por produto do catalogo.

| Coluna | Tipo | Restricoes | Descricao |
| --- | --- | --- | --- |
| id | INTEGER | PRIMARY KEY | Identificador do produto |
| nome | TEXT | NOT NULL | Nome do produto |
| categoria | TEXT | NOT NULL | Categoria (Eletronicos, Livros, Casa, Esporte, Moda) |
| preco | REAL | NOT NULL | Preco unitario em R$ (deve ser > 0) |
| criado_em | DATETIME | NOT NULL | Data do cadastro do produto (AAAA-MM-DD) |

## Tabela: pedidos
Descricao: uma linha por pedido (um produto por pedido).

| Coluna | Tipo | Restricoes | Descricao |
| --- | --- | --- | --- |
| id | INTEGER | PRIMARY KEY | Identificador do pedido |
| cliente_id | INTEGER | NOT NULL, FOREIGN KEY -> clientes.id | Cliente que fez o pedido |
| produto_id | INTEGER | NOT NULL, FOREIGN KEY -> produtos.id | Produto comprado |
| quantidade | INTEGER | NOT NULL | Quantidade de unidades (1 a 5) |
| valor_total | REAL | NOT NULL | preco x quantidade em R$ |
| data_pedido | DATETIME | NOT NULL | Data do pedido (AAAA-MM-DD) |

## Relacionamentos
- clientes 1 --- N pedidos (pedidos.cliente_id -> clientes.id)
- produtos 1 --- N pedidos (pedidos.produto_id -> produtos.id)

## Perguntas de negocio que o assistente precisara responder
1. Quantos clientes nao possuem e-mail cadastrado?
2. Qual categoria de produto gera o maior faturamento?
3. Existem pedidos com valor negativo? Quantos?
4. Quais e-mails aparecem duplicados na base de clientes?
5. Qual o ticket medio por cidade?
