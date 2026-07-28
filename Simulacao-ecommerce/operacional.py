"""
Modo Operacional — Fase 2 do simulador.

Roda em background thread. Gera novos eventos em intervalos configuráveis.
Nunca altera dados históricos.

Controles:
  start()  — inicia a thread
  pause()  — suspende geração (thread continua rodando)
  resume() — retoma geração
  stop()   — encerra a thread
"""
import random
import sys
import os
import threading
import time
from datetime import datetime, timedelta

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import database as db
from state import SimulatorState
from importador import get_clientes, get_produtos, get_vendas, get_pagamentos, get_estoque, get_entregas

_mod_cli = get_clientes()
_mod_pro = get_produtos()
_mod_ven = get_vendas()
_mod_pag = get_pagamentos()
_mod_est = get_estoque()
_mod_ent = get_entregas()

gerar_lote_clientes      = _mod_cli.gerar_lote_clientes
gerar_pedido             = _mod_ven.gerar_pedido
gerar_itens_pedido       = _mod_ven.gerar_itens_pedido
gerar_pagamento          = _mod_pag.gerar_pagamento
gerar_movimentacao_saida = _mod_est.gerar_movimentacao_saida
gerar_entrega            = _mod_ent.gerar_entrega


# ---------------------------------------------------------------------------
# Configuração padrão
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "realtime_enabled":      True,
    "generation_interval":   300,    # segundos
    "records_per_cycle":     None,
    "business_hours":        False,
    "max_orders_per_cycle":  10,
    "max_clients_per_cycle": 5,
    "random_seed":           None,
}


# ---------------------------------------------------------------------------
# Lógica de um ciclo de geração
# ---------------------------------------------------------------------------

def _executar_ciclo(cfg: dict):
    """Executa um único ciclo de geração operacional."""
    agora = datetime.now()
    agora_str = agora.strftime("%Y-%m-%d")

    # Respeita horário comercial (8h–20h, segunda a sexta)
    if cfg.get("business_hours"):
        hora = agora.hour
        dia_semana = agora.weekday()
        if dia_semana >= 5 or not (8 <= hora < 20):
            return  # Fora do horário — pula ciclo

    # Clientes novos
    n_clientes = cfg["max_clients_per_cycle"]
    n_clientes = random.randint(0, n_clientes)
    if n_clientes > 0:
        novos_clientes = gerar_lote_clientes(n_clientes, agora)
        db.insert_many("clientes", novos_clientes)

    # Clientes e produtos disponíveis
    clientes = db.query("SELECT id_cliente FROM clientes")
    produtos = db.query(
        "SELECT id_produto, preco, estoque_atual FROM produtos WHERE ativo = 1"
    )

    if not clientes or not produtos:
        return

    # Pedidos
    n_pedidos = random.randint(1, cfg["max_orders_per_cycle"])
    for _ in range(n_pedidos):
        cliente = random.choice(clientes)
        id_cliente = cliente["id_cliente"]

        pedido_data = gerar_pedido(id_cliente, agora)
        id_pedido = db.insert("pedidos", pedido_data)
        if not id_pedido:
            continue

        itens, valor_total = gerar_itens_pedido(id_pedido, produtos)
        if not itens:
            continue
        db.insert_many("itens_pedido", itens)
        db.update("pedidos", {"valor_total": valor_total}, {"id_pedido": id_pedido})

        pagamento_data = gerar_pagamento(id_pedido, valor_total, agora)
        id_pagamento = db.insert("pagamentos", pagamento_data)

        status_pedido = (
            "confirmado" if pagamento_data["status"] == "aprovado"
            else "cancelado" if pagamento_data["status"] == "recusado"
            else "pendente"
        )
        db.update("pedidos", {"status": status_pedido}, {"id_pedido": id_pedido})

        if pagamento_data["status"] == "aprovado":
            for item in itens:
                prod_info = next(
                    (p for p in produtos if p["id_produto"] == item["id_produto"]),
                    None,
                )
                if prod_info is None:
                    continue

                mov = gerar_movimentacao_saida(
                    id_produto=item["id_produto"],
                    estoque_atual=prod_info["estoque_atual"],
                    quantidade=item["quantidade"],
                    id_pedido=id_pedido,
                    data=agora,
                )
                db.insert("estoque_movimentacoes", mov)
                prod_info["estoque_atual"] = mov["estoque_depois"]
                db.update(
                    "produtos",
                    {"estoque_atual": mov["estoque_depois"]},
                    {"id_produto": item["id_produto"]},
                )

            data_pgto = datetime.fromisoformat(pagamento_data["data_pagamento"])
            entrega_data = gerar_entrega(id_pedido, id_pagamento, data_pgto)
            db.insert("entregas", entrega_data)


# ---------------------------------------------------------------------------
# Thread do modo operacional
# ---------------------------------------------------------------------------

class ModoOperacional:
    """
    Gerencia a thread de geração contínua.
    Thread-safe: usa threading.Event para pause e stop.
    """

    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()  # set = pausado
        self._config = DEFAULT_CONFIG.copy()

    def configurar(self, config: dict):
        self._config = {**DEFAULT_CONFIG, **config}

    def _loop(self):
        state = SimulatorState.load()
        interval = self._config.get("generation_interval", 300)

        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(1)
                continue

            try:
                _executar_ciclo(self._config)
                stats = db.get_stats()
                now_str = datetime.now().isoformat()

                state.update_from_db(stats)
                state.last_generation = now_str
                state.next_generation = (
                    datetime.now() + timedelta(seconds=interval)
                ).isoformat()
                state.simulation_status = "Running"
                state.save()

            except Exception as e:
                # Log mas não interrompe o loop
                print(f"[Operacional] Erro no ciclo: {e}", flush=True)

            # Aguarda intervalo (mas pode ser interrompido por stop_event)
            self._stop_event.wait(interval)

        state = SimulatorState.load()
        state.simulation_status = "Stopped"
        state.next_generation = None
        state.save()

    def start(self, config: dict = None):
        if config:
            self.configurar(config)
        if self._thread and self._thread.is_alive():
            return  # já rodando

        self._stop_event.clear()
        self._pause_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="OperacionalThread")
        self._thread.start()

        state = SimulatorState.load()
        state.simulation_status = "Running"
        state.save()

    def pause(self):
        self._pause_event.set()
        state = SimulatorState.load()
        state.simulation_status = "Paused"
        state.save()

    def resume(self):
        self._pause_event.clear()
        state = SimulatorState.load()
        state.simulation_status = "Running"
        state.save()

    def stop(self):
        self._stop_event.set()
        self._pause_event.clear()
        if self._thread:
            self._thread.join(timeout=5)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._pause_event.is_set()

    def is_paused(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and self._pause_event.is_set()

    def status(self) -> str:
        if self.is_running():
            return "Running"
        if self.is_paused():
            return "Paused"
        return "Stopped"


# Singleton global — compartilhado entre Streamlit reruns
_modo_operacional = ModoOperacional()


def get_modo_operacional() -> ModoOperacional:
    return _modo_operacional
