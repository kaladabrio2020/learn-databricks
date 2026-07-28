"""
API REST — FastAPI

Expõe os dados gerados pelo simulador para consumo externo (ex: Databricks).

Endpoints:
  Full Load:
    GET /clientes
    GET /produtos
    GET /pedidos
    GET /pagamentos
    GET /entregas
    GET /estoque
    GET /itens

  Incremental (filtro since):
    GET /clientes?since=2026-07-20T10:00:00
    GET /pedidos?since=2026-07-20T10:00:00
    GET /pagamentos?since=2026-07-20T10:00:00

  Por período:
    GET /pedidos?start=2026-07-01&end=2026-07-31

  Estado do simulador:
    GET /status

Iniciar: uvicorn api:app --reload --port 8001
"""
import sys
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

_ROOT = os.path.dirname(__file__)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import database as db
from state import SimulatorState

app = FastAPI(
    title="E-commerce Simulator API",
    description="API REST para consulta dos dados do simulador de e-commerce.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _paginar(rows: list, limit: int, offset: int) -> dict:
    total = len(rows)
    dados = rows[offset : offset + limit]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": dados,
    }


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

@app.get("/status", tags=["Sistema"])
def get_status():
    """Estado interno do simulador."""
    state = SimulatorState.load()
    stats = db.get_stats()
    return {**state.to_dict(), **stats}


# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------

@app.get("/clientes", tags=["Clientes"])
def get_clientes(
    since: Optional[str] = Query(None, description="Filtro incremental: data ISO 8601"),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    if since:
        try:
            datetime.fromisoformat(since)
        except ValueError:
            raise HTTPException(400, "Parâmetro 'since' deve ser ISO 8601")
        rows = db.query(
            "SELECT * FROM clientes WHERE created_at >= ? ORDER BY id_cliente",
            (since,),
        )
    else:
        rows = db.query("SELECT * FROM clientes ORDER BY id_cliente")
    return _paginar(rows, limit, offset)


@app.get("/clientes/{id_cliente}", tags=["Clientes"])
def get_cliente(id_cliente: int):
    row = db.query_one("SELECT * FROM clientes WHERE id_cliente = ?", (id_cliente,))
    if not row:
        raise HTTPException(404, "Cliente não encontrado")
    return row


# ---------------------------------------------------------------------------
# Produtos
# ---------------------------------------------------------------------------

@app.get("/produtos", tags=["Produtos"])
def get_produtos(
    categoria: Optional[str] = Query(None),
    ativo: Optional[int] = Query(None, ge=0, le=1),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    conditions = []
    params = []
    if categoria:
        conditions.append("categoria LIKE ?")
        params.append(f"%{categoria}%")
    if ativo is not None:
        conditions.append("ativo = ?")
        params.append(ativo)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = db.query(f"SELECT * FROM produtos {where} ORDER BY id_produto", params)
    return _paginar(rows, limit, offset)


@app.get("/produtos/{id_produto}", tags=["Produtos"])
def get_produto(id_produto: int):
    row = db.query_one("SELECT * FROM produtos WHERE id_produto = ?", (id_produto,))
    if not row:
        raise HTTPException(404, "Produto não encontrado")
    return row


# ---------------------------------------------------------------------------
# Pedidos
# ---------------------------------------------------------------------------

@app.get("/pedidos", tags=["Pedidos"])
def get_pedidos(
    since: Optional[str] = Query(None),
    start: Optional[str] = Query(None, description="Data inicial do período"),
    end: Optional[str] = Query(None, description="Data final do período"),
    status: Optional[str] = Query(None),
    id_cliente: Optional[int] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    conditions = []
    params = []

    if since:
        conditions.append("created_at >= ?")
        params.append(since)
    if start:
        conditions.append("date(data_pedido) >= ?")
        params.append(start)
    if end:
        conditions.append("date(data_pedido) <= ?")
        params.append(end)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if id_cliente:
        conditions.append("id_cliente = ?")
        params.append(id_cliente)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = db.query(f"SELECT * FROM pedidos {where} ORDER BY id_pedido", params)
    return _paginar(rows, limit, offset)


@app.get("/pedidos/{id_pedido}", tags=["Pedidos"])
def get_pedido(id_pedido: int):
    pedido = db.query_one("SELECT * FROM pedidos WHERE id_pedido = ?", (id_pedido,))
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado")
    itens = db.query("SELECT * FROM itens_pedido WHERE id_pedido = ?", (id_pedido,))
    return {**pedido, "itens": itens}


# ---------------------------------------------------------------------------
# Itens de Pedido
# ---------------------------------------------------------------------------

@app.get("/itens", tags=["Itens"])
def get_itens(
    id_pedido: Optional[int] = Query(None),
    id_produto: Optional[int] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    conditions = []
    params = []
    if id_pedido:
        conditions.append("id_pedido = ?")
        params.append(id_pedido)
    if id_produto:
        conditions.append("id_produto = ?")
        params.append(id_produto)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = db.query(f"SELECT * FROM itens_pedido {where} ORDER BY id_item", params)
    return _paginar(rows, limit, offset)


# ---------------------------------------------------------------------------
# Pagamentos
# ---------------------------------------------------------------------------

@app.get("/pagamentos", tags=["Pagamentos"])
def get_pagamentos(
    since: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    metodo: Optional[str] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    conditions = []
    params = []
    if since:
        conditions.append("created_at >= ?")
        params.append(since)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if metodo:
        conditions.append("metodo LIKE ?")
        params.append(f"%{metodo}%")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = db.query(f"SELECT * FROM pagamentos {where} ORDER BY id_pagamento", params)
    return _paginar(rows, limit, offset)


# ---------------------------------------------------------------------------
# Estoque
# ---------------------------------------------------------------------------

@app.get("/estoque", tags=["Estoque"])
def get_estoque(
    id_produto: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None, description="entrada ou saida"),
    since: Optional[str] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    conditions = []
    params = []
    if id_produto:
        conditions.append("id_produto = ?")
        params.append(id_produto)
    if tipo:
        conditions.append("tipo = ?")
        params.append(tipo)
    if since:
        conditions.append("created_at >= ?")
        params.append(since)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = db.query(
        f"SELECT * FROM estoque_movimentacoes {where} ORDER BY id_movimentacao", params
    )
    return _paginar(rows, limit, offset)


# ---------------------------------------------------------------------------
# Entregas
# ---------------------------------------------------------------------------

@app.get("/entregas", tags=["Entregas"])
def get_entregas(
    since: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    id_pedido: Optional[int] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    conditions = []
    params = []
    if since:
        conditions.append("created_at >= ?")
        params.append(since)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if id_pedido:
        conditions.append("id_pedido = ?")
        params.append(id_pedido)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = db.query(f"SELECT * FROM entregas {where} ORDER BY id_entrega", params)
    return _paginar(rows, limit, offset)


# ---------------------------------------------------------------------------
# Analytics rápido
# ---------------------------------------------------------------------------

@app.get("/analytics/resumo", tags=["Analytics"])
def get_resumo():
    """Resumo executivo dos dados gerados."""
    return {
        "totais": db.get_stats(),
        "pedidos_por_status": db.query(
            "SELECT status, COUNT(*) as total FROM pedidos GROUP BY status"
        ),
        "pagamentos_por_metodo": db.query(
            "SELECT metodo, COUNT(*) as total, SUM(valor) as receita "
            "FROM pagamentos WHERE status='aprovado' GROUP BY metodo"
        ),
        "entregas_por_status": db.query(
            "SELECT status, COUNT(*) as total FROM entregas GROUP BY status"
        ),
        "top_categorias": db.query(
            "SELECT p.categoria, COUNT(ip.id_item) as total_itens, "
            "SUM(ip.subtotal) as receita "
            "FROM itens_pedido ip "
            "JOIN produtos p ON ip.id_produto = p.id_produto "
            "GROUP BY p.categoria ORDER BY receita DESC LIMIT 10"
        ),
    }
