import re


def validar_query_segura(query: str) -> tuple[bool, str]:
    """Verifica regras de segurança sem executar a consulta SQL."""
    if not isinstance(query, str) or not query.strip():
        return False, "A consulta deve ser uma string não vazia."

    texto = re.sub(r"'(?:[^']|'')*'", " CONTEUDO_ENTRE_ASPAS ", query)

    if "'" in texto or texto.count('"') % 2:
        return False, "A consulta contém aspas não fechadas."

    texto = texto.replace('"', " ").replace("`", " ").replace("[", " ").replace("]", " ")

    if "--" in texto or "/*" in texto or "*/" in texto:
        return False, "Comentários SQL não são permitidos."

    texto = re.sub(r"\s+", " ", texto).strip().upper()

    if texto.endswith(";"):
        texto = texto[:-1].rstrip()

    if ";" in texto:
        return False, "Apenas uma consulta SQL é permitida."

    tokens = re.findall(r"[A-Z_][A-Z0-9_$]*|[^\s]", texto)

    if not tokens or tokens[0] not in {"SELECT", "WITH"}:
        return False, "A consulta deve começar com SELECT ou WITH."

    proibidos = {
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
        "TRUNCATE", "ATTACH", "DETACH", "CREATE",
        "EXEC", "VACUUM", "PRAGMA", "LOAD_EXTENSION", "RECURSIVE",
    }

    internas = {"SQLITE_MASTER", "SQLITE_SCHEMA", "SQLITE_TEMP_MASTER", "SQLITE_TEMP_SCHEMA"}

    for token in tokens:
        if token in proibidos:
            return False, f"Operação não permitida: {token}."
        if token in internas or token.startswith("PRAGMA_"):
            return False, f"Acesso a tabela interna não permitido: {token}."

    for atual, seguinte in zip(tokens, tokens[1:]):
        if atual == "REPLACE" and seguinte == "INTO":
            return False, "Operação não permitida: REPLACE INTO."

    return True, "Query aprovada."


if __name__ == "__main__":
    exemplos = [
        "SELECT * FROM clientes",
        "select cidade, count(*) from clientes group by cidade;",
        "SELECT * FROM clientes WHERE nome = 'DELETE; DROP'",
        "WITH t AS (SELECT * FROM pedidos) SELECT COUNT(*) FROM t",
        "DROP TABLE clientes",
        "SELECT 1; DELETE FROM pedidos",
        "WITH x AS (SELECT 1) DELETE FROM clientes",
        "SELECT 1 -- ; DROP TABLE clientes",
    ]
    for exemplo in exemplos:
        aprovada, motivo = validar_query_segura(exemplo)
        print(f"{'APROVADA ' if aprovada else 'BLOQUEADA'} | {motivo:<45} | {exemplo}")