import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

CAMINHO_DICIONARIO = RAIZ / "docs" / "dicionario_dados.md"
MAXIMO_SECOES = 3


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower()


def ler_dicionario() -> str:
    """Retorna o dicionario de dados completo em Markdown."""
    return CAMINHO_DICIONARIO.read_text(encoding="utf-8")


def _secoes() -> list[dict]:
    partes = re.split(r"^## ", ler_dicionario(), flags=re.MULTILINE)[1:]
    return [{"titulo": parte.splitlines()[0].strip(), "conteudo": "## " + parte.strip()} for parte in partes]


def buscar_documentacao(termo: str = "") -> dict:
    """Busca no dicionario de dados o significado de tabelas, colunas, anomalias e regras de negocio."""
    secoes = _secoes()
    palavras = [p for p in re.findall(r"\w+", _normalizar(termo)) if len(p) >= 3]
    if not palavras:
        return {"termo": termo, "secoes_disponiveis": [s["titulo"] for s in secoes], "trechos": [s["conteudo"] for s in secoes]}

    pontuadas = []
    for secao in secoes:
        texto = _normalizar(secao["conteudo"])
        pontos = sum(texto.count(palavra) for palavra in palavras)
        if pontos:
            pontuadas.append((pontos, secao))
    pontuadas.sort(key=lambda item: item[0], reverse=True)

    return {
        "termo": termo,
        "secoes_disponiveis": [s["titulo"] for s in secoes],
        "trechos": [secao["conteudo"] for _, secao in pontuadas[:MAXIMO_SECOES]],
    }


if __name__ == "__main__":
    print(buscar_documentacao("faturamento estorno"))
    print(buscar_documentacao("email")["trechos"][0][:200])
