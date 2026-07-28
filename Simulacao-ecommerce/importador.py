"""
Carregador de módulos dos subdiretórios com hífen no nome.

Python não aceita 'from si-clientes.clientes import ...' pois hífen
é inválido em identificadores. Este módulo usa importlib.util para
carregar os arquivos pelo caminho absoluto.
"""
import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).parent


def _load(relpath: str, alias: str):
    """Carrega um módulo Python a partir de caminho relativo e registra no sys.modules."""
    if alias in sys.modules:
        return sys.modules[alias]
    path = _ROOT / relpath
    spec = importlib.util.spec_from_file_location(alias, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


# Expõe os módulos dos geradores
def get_clientes():
    return _load("si-clientes/clientes.py", "si_clientes_clientes")

def get_produtos():
    return _load("si-produtos/produtos.py", "si_produtos_produtos")

def get_vendas():
    return _load("si-pedidos/vendas.py", "si_pedidos_vendas")

def get_pagamentos():
    return _load("si-pagamentos/pagamentos.py", "si_pagamentos_pagamentos")

def get_estoque():
    return _load("si-estoque/estoque.py", "si_estoque_estoque")

def get_entregas():
    return _load("si-entregas/entregas.py", "si_entregas_entregas")
