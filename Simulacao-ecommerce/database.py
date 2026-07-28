"""
Camada de acesso ao banco de dados SQLite.

Thread-safe: usa um lock global para todas as escritas.
WAL journal mode para melhor concorrência de leitura.
"""
import sqlite3
import threading
from pathlib import Path

DB_PATH = Path(__file__).parent / "ecommerce.db"
_lock = threading.Lock()

DDL = """
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente    INTEGER  PRIMARY KEY AUTOINCREMENT,
    nome          TEXT     NOT NULL,
    cpf           TEXT     NOT NULL UNIQUE,
    email         TEXT     NOT NULL UNIQUE,
    telefone      TEXT,
    logradouro    TEXT,
    numero        TEXT,
    complemento   TEXT,
    bairro        TEXT,
    cidade        TEXT,
    estado        TEXT,
    cep           TEXT,
    data_cadastro DATETIME NOT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS produtos (
    id_produto     INTEGER  PRIMARY KEY AUTOINCREMENT,
    nome           TEXT     NOT NULL,
    categoria      TEXT     NOT NULL,
    descricao      TEXT,
    preco          REAL     NOT NULL,
    estoque_inicial INTEGER  NOT NULL DEFAULT 0,
    estoque_atual  INTEGER  NOT NULL DEFAULT 0,
    ativo          INTEGER  NOT NULL DEFAULT 1,
    data_cadastro  DATETIME NOT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pedidos (
    id_pedido   INTEGER  PRIMARY KEY AUTOINCREMENT,
    id_cliente  INTEGER  NOT NULL REFERENCES clientes(id_cliente),
    status      TEXT     NOT NULL DEFAULT 'pendente',
    valor_total REAL     NOT NULL DEFAULT 0.0,
    observacoes TEXT,
    data_pedido DATETIME NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS itens_pedido (
    id_item        INTEGER  PRIMARY KEY AUTOINCREMENT,
    id_pedido      INTEGER  NOT NULL REFERENCES pedidos(id_pedido),
    id_produto     INTEGER  NOT NULL REFERENCES produtos(id_produto),
    quantidade     INTEGER  NOT NULL,
    preco_unitario REAL     NOT NULL,
    subtotal       REAL     NOT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pagamentos (
    id_pagamento   INTEGER  PRIMARY KEY AUTOINCREMENT,
    id_pedido      INTEGER  NOT NULL REFERENCES pedidos(id_pedido),
    metodo         TEXT     NOT NULL,
    modalidade     TEXT     NOT NULL,
    parcelas       INTEGER  NOT NULL DEFAULT 1,
    valor          REAL     NOT NULL,
    status         TEXT     NOT NULL DEFAULT 'pendente',
    data_pagamento DATETIME NOT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS estoque_movimentacoes (
    id_movimentacao   INTEGER  PRIMARY KEY AUTOINCREMENT,
    id_produto        INTEGER  NOT NULL REFERENCES produtos(id_produto),
    id_pedido         INTEGER  REFERENCES pedidos(id_pedido),
    tipo              TEXT     NOT NULL,
    quantidade        INTEGER  NOT NULL,
    estoque_antes     INTEGER  NOT NULL,
    estoque_depois    INTEGER  NOT NULL,
    motivo            TEXT,
    data_movimentacao DATETIME NOT NULL,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS entregas (
    id_entrega      INTEGER  PRIMARY KEY AUTOINCREMENT,
    id_pedido       INTEGER  NOT NULL REFERENCES pedidos(id_pedido),
    id_pagamento    INTEGER  NOT NULL REFERENCES pagamentos(id_pagamento),
    status          TEXT     NOT NULL DEFAULT 'em_preparacao',
    transportadora  TEXT,
    codigo_rastreio TEXT,
    data_previsao   DATETIME,
    data_envio      DATETIME,
    data_entrega    DATETIME,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


# ---------------------------------------------------------------------------
# Conexão
# ---------------------------------------------------------------------------

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

def init_db():
    """Cria todas as tabelas se não existirem."""
    with _lock:
        conn = get_conn()
        try:
            conn.executescript(DDL)
            conn.commit()
        finally:
            conn.close()


def reset_db():
    """Remove todos os dados de todas as tabelas (mantém estrutura)."""
    tables = [
        "entregas",
        "estoque_movimentacoes",
        "pagamentos",
        "itens_pedido",
        "pedidos",
        "produtos",
        "clientes",
    ]
    with _lock:
        conn = get_conn()
        try:
            conn.execute("PRAGMA foreign_keys = OFF")
            for table in tables:
                conn.execute(f"DELETE FROM {table}")
                conn.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
            conn.execute("PRAGMA foreign_keys = ON")
            conn.commit()
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# DML — escrita
# ---------------------------------------------------------------------------

def insert(table: str, data: dict, ignore_conflicts: bool = True) -> int:
    """Insere um registro e retorna o id gerado."""
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    or_ignore = "OR IGNORE" if ignore_conflicts else ""
    sql = f"INSERT {or_ignore} INTO {table} ({cols}) VALUES ({placeholders})"
    with _lock:
        conn = get_conn()
        try:
            cur = conn.execute(sql, list(data.values()))
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()


def insert_many(table: str, rows: list, ignore_conflicts: bool = True):
    """Insere múltiplos registros em um único transaction."""
    if not rows:
        return
    cols = ", ".join(rows[0].keys())
    placeholders = ", ".join(["?"] * len(rows[0]))
    or_ignore = "OR IGNORE" if ignore_conflicts else ""
    sql = f"INSERT {or_ignore} INTO {table} ({cols}) VALUES ({placeholders})"
    with _lock:
        conn = get_conn()
        try:
            conn.executemany(sql, [list(r.values()) for r in rows])
            conn.commit()
        finally:
            conn.close()


def update(table: str, data: dict, where: dict):
    """Atualiza registros na tabela."""
    set_clause = ", ".join(f"{k} = ?" for k in data.keys())
    where_clause = " AND ".join(f"{k} = ?" for k in where.keys())
    sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
    params = list(data.values()) + list(where.values())
    with _lock:
        conn = get_conn()
        try:
            conn.execute(sql, params)
            conn.commit()
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# DML — leitura
# ---------------------------------------------------------------------------

def query(sql: str, params=()) -> list:
    """Executa SELECT e retorna lista de dicts."""
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def query_one(sql: str, params=()) -> dict | None:
    """Executa SELECT e retorna o primeiro registro como dict."""
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def count(table: str, where: dict = None) -> int:
    """Conta registros em uma tabela."""
    if where:
        conditions = " AND ".join(f"{k} = ?" for k in where.keys())
        sql = f"SELECT COUNT(*) AS n FROM {table} WHERE {conditions}"
        result = query_one(sql, list(where.values()))
    else:
        result = query_one(f"SELECT COUNT(*) AS n FROM {table}")
    return result["n"] if result else 0


def get_stats() -> dict:
    """Retorna contagens de todas as entidades principais."""
    return {
        "total_clientes":  count("clientes"),
        "total_produtos":  count("produtos"),
        "total_pedidos":   count("pedidos"),
        "total_pagamentos": count("pagamentos"),
        "total_entregas":  count("entregas"),
        "receita_total":   (
            query_one("SELECT COALESCE(SUM(valor), 0) AS v FROM pagamentos WHERE status = 'aprovado'") or {}
        ).get("v", 0.0),
    }
