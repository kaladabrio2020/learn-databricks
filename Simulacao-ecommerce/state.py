"""
Estado interno do simulador.

Persiste em simulator_state.json para sobreviver restarts.
"""
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

STATE_PATH = Path(__file__).parent / "simulator_state.json"


@dataclass
class SimulatorState:
    # Relógio da simulação
    current_simulation_time: Optional[str] = None

    # Bootstrap
    bootstrap_completed: bool = False
    bootstrap_start_date: Optional[str] = None
    bootstrap_until: Optional[str] = None

    # Totais
    total_customers: int = 0
    total_products: int = 0
    total_orders: int = 0
    total_payments: int = 0
    total_deliveries: int = 0

    # Operacional
    last_generation: Optional[str] = None
    next_generation: Optional[str] = None
    simulation_status: str = "Stopped"  # Running | Paused | Stopped

    # Configuração operacional salva
    generation_interval_seconds: int = 300
    max_orders_per_cycle: int = 10
    max_clients_per_cycle: int = 5

    def save(self):
        STATE_PATH.write_text(
            json.dumps(asdict(self), indent=2, default=str),
            encoding="utf-8",
        )

    @classmethod
    def load(cls) -> "SimulatorState":
        if STATE_PATH.exists():
            try:
                data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
                # Filtrar apenas campos que existem na dataclass
                valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
                data = {k: v for k, v in data.items() if k in valid_fields}
                return cls(**data)
            except Exception:
                pass
        return cls()

    def to_dict(self) -> dict:
        return asdict(self)

    def update_from_db(self, stats: dict):
        """Sincroniza totais com o banco de dados."""
        self.total_customers = stats.get("total_clientes", self.total_customers)
        self.total_products = stats.get("total_produtos", self.total_products)
        self.total_orders = stats.get("total_pedidos", self.total_orders)
        self.total_payments = stats.get("total_pagamentos", self.total_payments)
        self.total_deliveries = stats.get("total_entregas", self.total_deliveries)
