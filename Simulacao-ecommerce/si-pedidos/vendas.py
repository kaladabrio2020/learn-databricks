"""
Gerador de pedidos e itens.

Regras:
  - Cliente deve existir antes do pedido
  - Produto deve existir antes do pedido
  - Valor total = soma dos itens
  - Status inicial: 'pendente' (muda conforme pagamento)
"""
import random
from datetime import datetime


STATUS_PEDIDO = ["pendente", "confirmado", "cancelado"]

OBSERVACOES = [
    "Entrega no período da manhã.",
    "Deixar com o porteiro.",
    "Não bater campainha.",
    "Presente — não incluir nota fiscal na caixa.",
    "Urgente.",
    None, None, None, None, None,  # maioria sem observação
]


def gerar_itens_pedido(id_pedido: int, produtos: list, max_itens: int = 5) -> tuple:
    """
    Gera lista de itens para um pedido.
    Retorna (itens, valor_total).
    """
    if not produtos:
        return [], 0.0

    n_itens = random.randint(1, min(max_itens, len(produtos)))
    selecionados = random.sample(produtos, n_itens)

    itens = []
    valor_total = 0.0

    for produto in selecionados:
        quantidade = random.randint(1, 4)
        preco_unitario = round(produto["preco"], 2)
        subtotal = round(preco_unitario * quantidade, 2)
        valor_total += subtotal

        itens.append({
            "id_pedido":      id_pedido,
            "id_produto":     produto["id_produto"],
            "quantidade":     quantidade,
            "preco_unitario": preco_unitario,
            "subtotal":       subtotal,
        })

    return itens, round(valor_total, 2)


def gerar_pedido(id_cliente: int, data_pedido: datetime) -> dict:
    """Gera a estrutura base de um pedido (sem itens ainda)."""
    return {
        "id_cliente":   id_cliente,
        "status":       "pendente",
        "valor_total":  0.0,
        "observacoes":  random.choice(OBSERVACOES),
        "data_pedido":  data_pedido.isoformat(),
    }
