"""
Gerador de movimentações de estoque.

Tipos:
  - 'entrada': reposição ou estoque inicial
  - 'saida':   pedido aprovado
"""
import random
from datetime import datetime


MOTIVOS_ENTRADA = [
    "Reposição de estoque",
    "Compra do fornecedor",
    "Devolução de cliente",
    "Ajuste de inventário",
]

MOTIVOS_SAIDA = [
    "Pedido #{id_pedido}",
    "Venda #{id_pedido}",
]


def gerar_movimentacao_saida(
    id_produto: int,
    estoque_atual: int,
    quantidade: int,
    id_pedido: int,
    data: datetime,
) -> dict:
    """Gera movimentação de saída (venda)."""
    estoque_depois = max(0, estoque_atual - quantidade)
    return {
        "id_produto":          id_produto,
        "id_pedido":           id_pedido,
        "tipo":                "saida",
        "quantidade":          quantidade,
        "estoque_antes":       estoque_atual,
        "estoque_depois":      estoque_depois,
        "motivo":              f"Pedido #{id_pedido}",
        "data_movimentacao":   data.isoformat(),
    }


def gerar_movimentacao_entrada(
    id_produto: int,
    estoque_atual: int,
    data: datetime,
) -> dict:
    """Gera movimentação de entrada (reposição)."""
    quantidade = random.randint(10, 100)
    return {
        "id_produto":          id_produto,
        "id_pedido":           None,
        "tipo":                "entrada",
        "quantidade":          quantidade,
        "estoque_antes":       estoque_atual,
        "estoque_depois":      estoque_atual + quantidade,
        "motivo":              random.choice(MOTIVOS_ENTRADA),
        "data_movimentacao":   data.isoformat(),
    }
