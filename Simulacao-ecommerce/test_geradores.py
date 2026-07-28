from importador import get_clientes, get_produtos
from datetime import datetime

now = datetime.now()

cli = get_clientes()
clientes = cli.gerar_lote_clientes(3, now)
print("Clientes gerados:", len(clientes))
for c in clientes:
    print(" ", c["nome"], "|", c["cpf"], "|", c["telefone"])

pro = get_produtos()
produtos = pro.gerar_lote_produtos(3, now)
print("Produtos gerados:", len(produtos))
for p in produtos:
    print(" ", p["nome"], "| R$", p["preco"], "| Cat:", p["categoria"])

print("Todos os geradores OK!")
