"""
Gerador de pagamentos.

METODO_PAGAMENTO e PARCELAMENTO já existiam no arquivo original.
Dados levemente sujos:
  - ~3% status 'pendente' nunca resolvido (anomalia de dados)
  - ~1% método com capitalização inconsistente (ex: 'pix' ao invés de 'Pix')
"""
import random
from datetime import datetime, timedelta

METODO_PAGAMENTO = {
    "Pix":              ["a vista"],
    "Boleto":           ["a vista"],
    "Cartão de Crédito": ["a vista", "parcelado"],
    "Cartão de Débito": ["a vista"],
}

PARCELAMENTO = [i for i in range(1, 13)]

STATUS_PAGAMENTO = ["aprovado", "aprovado", "aprovado", "aprovado",
                    "aprovado", "aprovado", "aprovado",
                    "recusado", "pendente"]  # peso: ~78% aprovado, ~11% recusado, ~11% pendente


def _fmt_metodo(metodo: str) -> str:
    """~1% método em minúsculas (capitalização inconsistente)."""
    if random.random() < 0.01:
        return metodo.lower()
    return metodo


def gerar_pagamento(id_pedido: int, valor: float, data_pedido: datetime) -> dict:
    """
    Gera um pagamento para um pedido.
    Data do pagamento = data_pedido + 0 a 2 dias úteis.
    """
    metodo = random.choice(list(METODO_PAGAMENTO.keys()))
    modalidade = random.choice(METODO_PAGAMENTO[metodo])

    # Parcelamento só em cartão de crédito parcelado
    if metodo == "Cartão de Crédito" and modalidade == "parcelado":
        parcelas = random.choice([2, 3, 4, 6, 8, 10, 12])
    else:
        parcelas = 1

    # ~3% ficam presos em pendente (anomalia intencional)
    status = random.choice(STATUS_PAGAMENTO)
    if random.random() < 0.03:
        status = "pendente"

    atraso = timedelta(hours=random.randint(0, 48))
    data_pagamento = data_pedido + atraso

    return {
        "id_pedido":      id_pedido,
        "metodo":         _fmt_metodo(metodo),
        "modalidade":     modalidade,
        "parcelas":       parcelas,
        "valor":          round(valor, 2),
        "status":         status,
        "data_pagamento": data_pagamento.isoformat(),
    }