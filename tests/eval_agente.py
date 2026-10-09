import argparse
import asyncio
import json
import re
import sys
import time
import unicodedata
from contextlib import closing
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.agent.dataops_agent import MODEL, DataOpsAgent  # noqa: E402
from src.database.init_db import conectar_leitura  # noqa: E402
from src.database.seed_data import ANOMALIAS_ESPERADAS  # noqa: E402

FILTRO_PEDIDOS_VALIDOS = "valor_total > 0 AND data_pedido <= date('now')"


def _normalizar(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def montar_gabarito() -> list[dict]:
    with closing(conectar_leitura()) as conexao:
        total_tabelas = conexao.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()[0]
        email_duplicado = conexao.execute(
            "SELECT email FROM clientes WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1"
        ).fetchone()[0]
        categoria_top = conexao.execute(
            "SELECT pr.categoria FROM pedidos pe JOIN produtos pr ON pr.id = pe.produto_id "
            f"WHERE {FILTRO_PEDIDOS_VALIDOS} GROUP BY pr.categoria ORDER BY SUM(pe.valor_total) DESC LIMIT 1"
        ).fetchone()[0]
        cidade_top = conexao.execute(
            "SELECT c.cidade FROM pedidos pe JOIN clientes c ON c.id = pe.cliente_id "
            f"WHERE {FILTRO_PEDIDOS_VALIDOS} GROUP BY c.cidade ORDER BY AVG(pe.valor_total) DESC LIMIT 1"
        ).fetchone()[0]

    return [
        {"pergunta": "Quantas tabelas existem no banco?", "esperado": str(total_tabelas), "tipo": "numero"},
        {"pergunta": "Quantos clientes nao possuem e-mail cadastrado?",
         "esperado": str(ANOMALIAS_ESPERADAS["clientes_sem_email"]), "tipo": "numero"},
        {"pergunta": "Quantos produtos estao com preco zero?",
         "esperado": str(ANOMALIAS_ESPERADAS["produtos_preco_zero"]), "tipo": "numero"},
        {"pergunta": "Existem pedidos com valor negativo? Quantos?",
         "esperado": str(ANOMALIAS_ESPERADAS["pedidos_valor_negativo"]), "tipo": "numero"},
        {"pergunta": "Quantos pedidos estao com data no futuro?",
         "esperado": str(ANOMALIAS_ESPERADAS["pedidos_data_futura"]), "tipo": "numero"},
        {"pergunta": "Quais e-mails aparecem duplicados na base de clientes?", "esperado": email_duplicado, "tipo": "texto"},
        {"pergunta": "Qual categoria de produto gera o maior faturamento?", "esperado": categoria_top, "tipo": "texto"},
        {"pergunta": "Qual cidade tem o maior ticket medio?", "esperado": cidade_top, "tipo": "texto"},
    ]


def acertou(resposta: str, esperado: str, tipo: str) -> bool:
    texto = _normalizar(resposta)
    if tipo == "numero":
        return re.search(rf"(?<![\d.,]){re.escape(esperado)}(?![\d]|[.,]\d)", texto) is not None
    return _normalizar(esperado) in texto


async def avaliar(limite: int | None) -> list[dict]:
    casos = montar_gabarito()[:limite]
    resultados = []
    async with DataOpsAgent() as agente:
        for caso in casos:
            agente.historico.clear()
            inicio = time.perf_counter()
            try:
                saida = await agente.perguntar(caso["pergunta"])
                erro = None
            except Exception as excecao:
                saida = {"resposta": "", "trace": [], "uso": {"chamadas_modelo": 0, "tokens_total": 0}}
                erro = str(excecao)
            resultado = {
                **caso,
                "acertou": erro is None and acertou(saida["resposta"], caso["esperado"], caso["tipo"]),
                "chamadas_modelo": saida["uso"]["chamadas_modelo"],
                "tokens": saida["uso"]["tokens_total"],
                "ferramentas": [passo["ferramenta"] for passo in saida["trace"]],
                "ferramentas_com_erro": sum(not passo["sucesso"] for passo in saida["trace"]),
                "tempo_s": round(time.perf_counter() - inicio, 1),
                "resposta": saida["resposta"],
                "erro": erro,
            }
            resultados.append(resultado)
            marca = "OK   " if resultado["acertou"] else "ERROU"
            print(
                f"[{marca}] {caso['pergunta']}\n"
                f"        esperado: {caso['esperado']} | {resultado['chamadas_modelo']} chamadas, "
                f"{resultado['tokens']} tokens, {resultado['tempo_s']} s | {' -> '.join(resultado['ferramentas']) or '-'}"
            )
            if not resultado["acertou"]:
                print(f"        resposta: {(erro or saida['resposta'])[:200]!r}")
    return resultados


def resumir(resultados: list[dict]) -> dict:
    total = len(resultados) or 1
    return {
        "modelo": MODEL,
        "perguntas": len(resultados),
        "acertos": sum(r["acertou"] for r in resultados),
        "taxa_acerto": round(sum(r["acertou"] for r in resultados) / total * 100, 1),
        "media_chamadas_modelo": round(sum(r["chamadas_modelo"] for r in resultados) / total, 1),
        "media_tokens": round(sum(r["tokens"] for r in resultados) / total),
        "media_tempo_s": round(sum(r["tempo_s"] for r in resultados) / total, 1),
        "ferramentas_com_erro": sum(r["ferramentas_com_erro"] for r in resultados),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Avalia se o DataOps Agent responde certo as perguntas do gabarito.")
    parser.add_argument("--limite", type=int, help="roda so as N primeiras perguntas (economiza cota)")
    parser.add_argument("--saida", type=Path, help="salva resultados e resumo em um arquivo JSON")
    argumentos = parser.parse_args()

    resultados = asyncio.run(avaliar(argumentos.limite))
    resumo = resumir(resultados)
    print(f"\nModelo {resumo['modelo']}: {resumo['acertos']}/{resumo['perguntas']} acertos ({resumo['taxa_acerto']}%)")
    print(
        f"Media por pergunta: {resumo['media_chamadas_modelo']} chamadas ao modelo, "
        f"{resumo['media_tokens']} tokens, {resumo['media_tempo_s']} s"
    )
    if argumentos.saida:
        argumentos.saida.write_text(json.dumps({"resumo": resumo, "resultados": resultados}, ensure_ascii=False, indent=2))
        print(f"Resultados salvos em {argumentos.saida}")
    sys.exit(0 if resumo["acertos"] == resumo["perguntas"] else 1)
