"""
Bootstrap — Fase 1 do simulador.

Orquestra a geração histórica dia a dia, do start_date até bootstrap_until.
Funciona como gerador (yield) para permitir barra de progresso no Streamlit.

Fluxo diário:
  1. Novos clientes
  2. Novos produtos (apenas no primeiro dia de cada mês)
  3. Novos pedidos + itens (usando clientes e produtos já existentes)
  4. Pagamentos para cada pedido
  5. Movimentações de estoque (para pagamentos aprovados)
  6. Entregas (para pagamentos aprovados)
"""
import random
import sys
import os
from datetime import datetime, timedelta
from typing import Generator

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import database as db
from state import SimulatorState
from importador import get_clientes, get_produtos, get_vendas, get_pagamentos, get_estoque, get_entregas

# Carrega módulos via importlib (nomes com hífen não são importáveis diretamente)
_mod_cli = get_clientes()
_mod_pro = get_produtos()
_mod_ven = get_vendas()
_mod_pag = get_pagamentos()
_mod_est = get_estoque()
_mod_ent = get_entregas()

gerar_lote_clientes    = _mod_cli.gerar_lote_clientes
gerar_lote_produtos    = _mod_pro.gerar_lote_produtos
gerar_pedido           = _mod_ven.gerar_pedido
gerar_itens_pedido     = _mod_ven.gerar_itens_pedido
gerar_pagamento        = _mod_pag.gerar_pagamento
gerar_movimentacao_saida = _mod_est.gerar_movimentacao_saida
gerar_entrega          = _mod_ent.gerar_entrega


# ---------------------------------------------------------------------------
# Configuração padrão
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "start_date":          None,       # datetime — obrigatório
    "bootstrap_until":     None,       # datetime — obrigatório
    "random_seed":         42,
    "reset_database":      False,
    "customer_growth_rate": 5,         # clientes/dia
    "order_growth_rate":   10,         # pedidos/dia
    "product_growth_rate": 8,          # produtos/mês (criados no 1º dia do mês)
    "business_calendar":   False,
    "timezone":            "America/Sao_Paulo",
}


# ---------------------------------------------------------------------------
# Bootstrap principal
# ---------------------------------------------------------------------------

def executar_bootstrap(config: dict) -> Generator[dict, None, None]:
    """
    Executa o bootstrap histórico dia a dia.

    Yields dicts de progresso:
        {
            'dia_atual': str,
            'dia_numero': int,
            'total_dias': int,
            'percentual': float,   # 0.0 a 1.0
            'mensagem': str,
            'stats': dict,
        }
    """
    cfg = {**DEFAULT_CONFIG, **config}

    start: datetime = cfg["start_date"]
    until: datetime = cfg["bootstrap_until"]

    if not start or not until or until <= start:
        raise ValueError("start_date e bootstrap_until são obrigatórios e until > start.")

    seed = cfg.get("random_seed", 42)
    if seed is not None:
        random.seed(seed)

    # Inicializa banco
    db.init_db()
    if cfg.get("reset_database"):
        db.reset_db()

    state = SimulatorState.load()
    state.bootstrap_start_date = start.isoformat()
    state.bootstrap_until = until.isoformat()
    state.simulation_status = "Running"
    state.save()

    total_dias = (until.date() - start.date()).days + 1
    dias_gerados = 0
    dia_atual = start

    yield {
        "dia_atual": dia_atual.strftime("%Y-%m-%d"),
        "dia_numero": 0,
        "total_dias": total_dias,
        "percentual": 0.0,
        "mensagem": "🚀 Iniciando bootstrap...",
        "stats": db.get_stats(),
    }

    while dia_atual.date() <= until.date():
        dia_str = dia_atual.strftime("%Y-%m-%d")
        dia_date = dia_atual.date()

        # ------------------------------------------------------------------ #
        # 1. Clientes novos
        # ------------------------------------------------------------------ #
        n_clientes = cfg["customer_growth_rate"]
        if cfg.get("business_calendar") and dia_date.weekday() >= 5:
            n_clientes = max(1, n_clientes // 3)  # fim de semana: menos cadastros

        novos_clientes = gerar_lote_clientes(n_clientes, dia_atual)
        db.insert_many("clientes", novos_clientes)

        # ------------------------------------------------------------------ #
        # 2. Produtos novos (apenas no primeiro dia do mês ou start_date)
        # ------------------------------------------------------------------ #
        e_primeiro_dia_mes = (dia_date.day == 1 or dia_atual == start)
        if e_primeiro_dia_mes:
            n_produtos = cfg["product_growth_rate"]
            novos_produtos = gerar_lote_produtos(n_produtos, dia_atual)
            db.insert_many("produtos", novos_produtos)

        # ------------------------------------------------------------------ #
        # 3. Carregar clientes e produtos disponíveis até este dia
        # ------------------------------------------------------------------ #
        clientes_disponiveis = db.query(
            "SELECT id_cliente FROM clientes WHERE date(data_cadastro) <= ?",
            (dia_str,),
        )
        produtos_disponiveis = db.query(
            "SELECT id_produto, preco, estoque_atual FROM produtos "
            "WHERE date(data_cadastro) <= ? AND ativo = 1",
            (dia_str,),
        )

        if not clientes_disponiveis or not produtos_disponiveis:
            dia_atual += timedelta(days=1)
            dias_gerados += 1
            continue

        # ------------------------------------------------------------------ #
        # 4 + 5 + 6. Pedidos → Pagamentos → Estoque → Entregas
        # ------------------------------------------------------------------ #
        n_pedidos = cfg["order_growth_rate"]
        if cfg.get("business_calendar") and dia_date.weekday() >= 5:
            n_pedidos = max(2, n_pedidos // 2)

        for _ in range(n_pedidos):
            cliente = random.choice(clientes_disponiveis)
            id_cliente = cliente["id_cliente"]

            # --- Pedido base ---
            pedido_data = gerar_pedido(id_cliente, dia_atual)
            id_pedido = db.insert("pedidos", pedido_data)
            if not id_pedido:
                continue

            # --- Itens ---
            itens, valor_total = gerar_itens_pedido(
                id_pedido, produtos_disponiveis
            )
            if not itens:
                continue
            db.insert_many("itens_pedido", itens)

            # Atualiza valor total do pedido
            db.update("pedidos", {"valor_total": valor_total}, {"id_pedido": id_pedido})

            # --- Pagamento ---
            pagamento_data = gerar_pagamento(id_pedido, valor_total, dia_atual)
            id_pagamento = db.insert("pagamentos", pagamento_data)

            # Atualiza status do pedido
            status_pedido = (
                "confirmado" if pagamento_data["status"] == "aprovado"
                else "cancelado" if pagamento_data["status"] == "recusado"
                else "pendente"
            )
            db.update("pedidos", {"status": status_pedido}, {"id_pedido": id_pedido})

            # --- Estoque + Entrega (apenas pagamento aprovado) ---
            if pagamento_data["status"] == "aprovado":
                for item in itens:
                    prod_info = next(
                        (p for p in produtos_disponiveis if p["id_produto"] == item["id_produto"]),
                        None,
                    )
                    if prod_info is None:
                        continue

                    mov = gerar_movimentacao_saida(
                        id_produto=item["id_produto"],
                        estoque_atual=prod_info["estoque_atual"],
                        quantidade=item["quantidade"],
                        id_pedido=id_pedido,
                        data=dia_atual,
                    )
                    db.insert("estoque_movimentacoes", mov)

                    # Atualiza estoque em memória e no banco
                    novo_estoque = mov["estoque_depois"]
                    prod_info["estoque_atual"] = novo_estoque
                    db.update(
                        "produtos",
                        {"estoque_atual": novo_estoque},
                        {"id_produto": item["id_produto"]},
                    )

                # Entrega
                data_pgto = datetime.fromisoformat(pagamento_data["data_pagamento"])
                entrega_data = gerar_entrega(
                    id_pedido=id_pedido,
                    id_pagamento=id_pagamento,
                    data_pagamento=data_pgto,
                    data_limite=until,
                )
                db.insert("entregas", entrega_data)

        # ------------------------------------------------------------------ #
        # Progresso
        # ------------------------------------------------------------------ #
        dias_gerados += 1
        percentual = dias_gerados / total_dias
        stats = db.get_stats()

        state.current_simulation_time = dia_str
        state.update_from_db(stats)
        state.save()

        yield {
            "dia_atual":  dia_str,
            "dia_numero": dias_gerados,
            "total_dias": total_dias,
            "percentual": percentual,
            "mensagem":   f"📅 Processando {dia_str} ({dias_gerados}/{total_dias})",
            "stats":      stats,
        }

        dia_atual += timedelta(days=1)

    # Finalização
    state.bootstrap_completed = True
    state.simulation_status = "Stopped"
    state.save()

    yield {
        "dia_atual":  until.strftime("%Y-%m-%d"),
        "dia_numero": total_dias,
        "total_dias": total_dias,
        "percentual": 1.0,
        "mensagem":   "✅ Bootstrap concluído!",
        "stats":      db.get_stats(),
    }
