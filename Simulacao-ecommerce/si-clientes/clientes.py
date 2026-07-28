"""
Gerador de clientes com Faker (pt_BR).

Dados levemente sujos (intencionais para exercitar ELT):
  - ~5%  telefone sem parênteses  ex: "11 98765-4321"
  - ~3%  nome em CAPS LOCK
  - ~5%  CPF sem formatação        ex: "12345678901"
  - ~2%  complemento como string vazia ao invés de NULL
"""
import random
from datetime import datetime
from faker import Faker

_fake = Faker("pt_BR")
Faker.seed(0)


# ---------------------------------------------------------------------------
# Helpers para imperfeições intencionais
# ---------------------------------------------------------------------------

def _fmt_telefone(digitos: str) -> str:
    """~5% formato alternativo sem parênteses."""
    if random.random() < 0.05:
        return f"{digitos[:2]} {digitos[2:7]}-{digitos[7:]}"
    return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"


def _fmt_cpf(cpf: str) -> str:
    """~5% CPF sem formatação (só dígitos)."""
    if random.random() < 0.05:
        return cpf.replace(".", "").replace("-", "")
    return cpf


def _fmt_nome(nome: str) -> str:
    """~3% nome em CAPS LOCK."""
    if random.random() < 0.03:
        return nome.upper()
    return nome


def _fmt_complemento(valor: str | None) -> str | None:
    """~2% complemento como string vazia ao invés de None."""
    if valor is None and random.random() < 0.02:
        return ""
    return valor


# ---------------------------------------------------------------------------
# Gerador principal
# ---------------------------------------------------------------------------

def gerar_cliente(data_cadastro: datetime) -> dict:
    """Gera um único cliente com dados levemente sujos."""
    digitos = _fake.msisdn()[2:13]  # 11 dígitos sem prefixo de país

    complemento = _fake.secondary_address() if random.random() < 0.55 else None
    complemento = _fmt_complemento(complemento)

    return {
        "nome":          _fmt_nome(_fake.name()),
        "cpf":           _fmt_cpf(_fake.cpf()),
        "email":         _fake.email(),
        "telefone":      _fmt_telefone(digitos),
        "logradouro":    _fake.street_name(),
        "numero":        _fake.building_number(),
        "complemento":   complemento,
        "bairro":        _fake.bairro(),
        "cidade":        _fake.city(),
        "estado":        _fake.estado_sigla(),
        "cep":           _fake.postcode(),
        "data_cadastro": data_cadastro.isoformat(),
    }


def gerar_lote_clientes(n: int, data_base: datetime) -> list:
    """
    Gera N clientes garantindo CPF e email únicos dentro do lote.
    Duplicatas com o banco serão rejeitadas pelo UNIQUE constraint (INSERT OR IGNORE).
    """
    vistos_cpf = set()
    vistos_email = set()
    clientes = []
    tentativas = 0
    max_tentativas = n * 5

    while len(clientes) < n and tentativas < max_tentativas:
        tentativas += 1
        c = gerar_cliente(data_base)
        cpf_clean = c["cpf"].replace(".", "").replace("-", "")
        if cpf_clean in vistos_cpf or c["email"] in vistos_email:
            continue
        vistos_cpf.add(cpf_clean)
        vistos_email.add(c["email"])
        clientes.append(c)

    return clientes
