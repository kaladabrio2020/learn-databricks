"""
Gerador de entregas.

Status progressão:
  em_preparacao → enviado → em_transito → entregue
  (ou devolvido em caso de problemas)

Transportadoras fictícias brasileiras.
"""
import random
import string
from datetime import datetime, timedelta


TRANSPORTADORAS = [
    "Correios PAC",
    "Correios SEDEX",
    "Jadlog",
    "Total Express",
    "Azul Cargo",
    "Sequoia Logística",
    "DHL Express",
    "Mercado Envios",
]

STATUS_ENTREGA_SEQUENCIA = [
    "em_preparacao",
    "enviado",
    "em_transito",
    "entregue",
]


def _gerar_codigo_rastreio(transportadora: str) -> str:
    """Gera código de rastreio no formato BR (Correios) ou alfanumérico."""
    if "Correios" in transportadora:
        letras = "".join(random.choices(string.ascii_uppercase, k=2))
        digitos = "".join(random.choices(string.digits, k=9))
        return f"{letras}{digitos}BR"
    else:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=14))


def gerar_entrega(
    id_pedido: int,
    id_pagamento: int,
    data_pagamento: datetime,
    data_limite: datetime | None = None,
) -> dict:
    """
    Gera uma entrega para um pagamento aprovado.
    data_limite: se fornecida, limita quando a entrega pode ser marcada como 'entregue'.
    """
    transportadora = random.choice(TRANSPORTADORAS)
    codigo_rastreio = _gerar_codigo_rastreio(transportadora)

    dias_envio = random.randint(1, 3)
    dias_transito = random.randint(2, 10)

    data_envio = data_pagamento + timedelta(days=dias_envio)
    data_previsao = data_envio + timedelta(days=dias_transito)

    # Determina status baseado nas datas e se tem data_limite
    if data_limite and data_previsao > data_limite:
        # Entrega ainda em andamento no período do bootstrap
        status = random.choice(["em_preparacao", "enviado", "em_transito"])
        data_entrega = None
    else:
        # ~5% devolvidas
        if random.random() < 0.05:
            status = "devolvido"
            data_entrega = (data_previsao + timedelta(days=random.randint(1, 5))).isoformat()
        else:
            status = "entregue"
            atraso = timedelta(days=random.randint(-1, 3))
            data_entrega = (data_previsao + atraso).isoformat()

    return {
        "id_pedido":       id_pedido,
        "id_pagamento":    id_pagamento,
        "status":          status,
        "transportadora":  transportadora,
        "codigo_rastreio": codigo_rastreio,
        "data_previsao":   data_previsao.isoformat(),
        "data_envio":      data_envio.isoformat(),
        "data_entrega":    data_entrega,
    }
