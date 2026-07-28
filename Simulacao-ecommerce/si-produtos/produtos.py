"""
Gerador de produtos com catálogo curado (pt_BR).

Dados levemente sujos (intencionais para exercitar ELT):
  - ~5%  descrição toda em minúsculas sem padronização
  - ~3%  preço com 4 casas decimais ao invés de 2
  - ~2%  categoria com espaço extra no final
"""
import random
from datetime import datetime

# ---------------------------------------------------------------------------
# Catálogo de produtos por categoria
# ---------------------------------------------------------------------------

CATALOGO: dict[str, list[tuple[str, str]]] = {
    "Eletrônicos": [
        ("Smartphone Samsung Galaxy A54", "Smartphone Android 6,4 polegadas 128GB câmera 50MP"),
        ("Notebook Dell Inspiron 15", "Notebook Intel Core i5 8GB RAM 256GB SSD Windows 11"),
        ("Fone Bluetooth JBL Tune 510BT", "Fone de ouvido sem fio até 40h de bateria Pure Bass"),
        ("Smart TV Samsung 50\" 4K Crystal", "Smart TV UHD 4K Wi-Fi Gaming Hub"),
        ("Tablet Lenovo Tab M10 Plus", "Tablet 10 polegadas 4GB RAM 64GB Android 12"),
        ("Caixa de Som JBL Charge 5", "Caixa portátil à prova d'água 20W RMS 20h de bateria"),
        ("Mouse Logitech MX Master 3S", "Mouse sem fio ergonômico 8000 DPI USB-C"),
        ("Teclado Redragon Kumara K552", "Teclado mecânico RGB Switch Red TKL"),
        ("Webcam Logitech C920 HD Pro", "Webcam Full HD 1080p 30fps microfone duplo"),
        ("Carregador GaN 65W USB-C", "Carregador rápido tripla porta PD 65W compacto"),
    ],
    "Casa e Decoração": [
        ("Sofá 3 Lugares Veludo Cinza", "Sofá em tecido veludo suede pés em madeira"),
        ("Mesa de Centro Madeira Rústica", "Mesa de centro em madeira de demolição 120x60cm"),
        ("Luminária de Piso Tripé", "Luminária loft estilo industrial bivolt"),
        ("Quadro Abstrato Canvas 60x80cm", "Quadro decorativo impressão em canvas com moldura"),
        ("Tapete Sala Persa 2x3m", "Tapete estampado antiderrapante lavável"),
        ("Kit 3 Prateleiras Flutuantes MDF", "Prateleiras 60cm com suporte invisível"),
        ("Vaso Cerâmica Artesanal 30cm", "Vaso decorativo em cerâmica artesanal cores neutras"),
        ("Jogo de Cama Queen Percal 300 Fios", "100% algodão egípcio 4 peças"),
        ("Espelho Redondo 60cm com Moldura", "Espelho decorativo sala ou quarto"),
    ],
    "Esportes e Lazer": [
        ("Bicicleta Caloi Explorer Sport 21v", "Mountain bike aro 29 freios a disco"),
        ("Esteira Ergométrica Movement LX 160i", "Esteira elétrica 12 km/h inclinação 12%"),
        ("Par Halteres Emborrachados 10kg", "Halteres hexagonais antiderrapantes"),
        ("Tênis Nike Air Max 270 React", "Tênis masculino amortecimento Air cushioning"),
        ("Raquete Tênis Wilson Blade 98", "Raquete adulto carbono 98in² 305g"),
        ("Bola Futebol Nike Strike Taco", "Bola society/taco tamanho 5 termofusionada"),
        ("Luvas de Boxe Everlast Pro Style", "Luvas 14oz couro sintético treino e sparring"),
        ("Yoga Mat Premium TPE 6mm", "Tapete yoga ecológico antiderrapante 183x61cm"),
        ("Corda de Pular Speed Crossfit", "Corda ajustável alumínio rolamento triplo"),
    ],
    "Beleza e Saúde": [
        ("Perfume Natura Homem Intenso 100ml", "Eau de parfum amadeirado especiado"),
        ("Kit Skincare Neutrogena 3 Produtos", "Hidratante FPS30 + sérum + limpeza facial"),
        ("Secador Philips Walita 2200W", "Secador íons com difusor e bicos concentradores"),
        ("Protetor Solar Nivea Sun FPS 70 Rosto", "Protetor facial toque seco 50g"),
        ("Creme Corporal Dove Hidratação Intensa", "Hidratante corporal manteiga de cacau 400ml"),
        ("Aparelho de Barbear Philips Series 7", "Barbeador elétrico 3 cabeças rotativas"),
        ("Escova Dental Elétrica Oral-B Pro 3", "3 modos de limpeza 2 cabeças extras"),
    ],
    "Livros e Papelaria": [
        ("O Poder do Hábito - Charles Duhigg", "Best-seller sobre neurociência dos hábitos"),
        ("Pai Rico Pai Pobre - Robert Kiyosaki", "Clássico sobre educação financeira pessoal"),
        ("Sapiens - Yuval Noah Harari", "Uma breve história da humanidade"),
        ("Caderno Universitário Tilibra 10 Matérias", "200 folhas capa dura espiral"),
        ("Kit 5 Canetas Pilot G2 Azul", "Caneta gel retrátil 0.7mm escrita suave"),
        ("Agenda Planner 2026 Capa Dura", "Agenda executiva 352 páginas papel reciclado"),
        ("Marca-texto Stabilo Boss 8 cores", "Marca-texto fluorescente resistente à luz"),
    ],
    "Alimentos e Bebidas": [
        ("Café Especial Illy Espresso 250g", "Café torrado e moído blend arábica premium"),
        ("Whey Protein Growth Chocolate 900g", "Proteína soro do leite concentrado 80% proteína"),
        ("Azeite Extra Virgem Carbonell 500ml", "Acidez 0.3% prensado a frio"),
        ("Pasta de Amendoim Integral Sem Açúcar 1kg", "100% amendoim torrado sem conservantes"),
        ("Chá Verde Matcha Orgânico 100g", "Matcha premium cerimônia japonês"),
    ],
    "Brinquedos e Games": [
        ("LEGO Technic Bugatti Chiron 3599 Peças", "Modelo escala 1:8 recomendado 16+ anos"),
        ("Boneca Barbie Fashionista Cadeira de Rodas", "Inclusiva com 25 pontos de articulação"),
        ("Controle Xbox Series X Sem Fio Preto", "Compatível Xbox Series X/S e PC"),
        ("Headset Gamer HyperX Cloud II 7.1", "Som surround USB cancelamento de ruído"),
        ("Banco Imobiliário Brasil Estrela", "Jogo tabuleiro 2-6 jogadores 8+ anos"),
        ("Jogo UNO Classic Mattel", "108 cartas 2-10 jogadores"),
    ],
    "Automotivo": [
        ("Suporte Celular Magnético Veicular", "Base magnética 360° painel ou ventilação"),
        ("Câmera Ré Full HD 170° Visão Noturna", "Câmera traseira colorida 1080p"),
        ("Carregador Veicular GaN 30W Duplo", "USB-C PD + USB-A QC 3.0"),
        ("Cera Automotiva Turtle Wax Liquid 500g", "Proteção 6 meses brilho espelhado"),
        ("Jogo Tapetes Borracha Universal 4 Peças", "PVC premium antiderrapante lavável"),
    ],
    "Ferramentas": [
        ("Furadeira de Impacto Bosch GSB 650W", "Bivolt com maleta e 25 acessórios"),
        ("Jogo 6 Chaves Philips e Fenda Stanley", "Aço cromo-vanádio cabo emborrachado"),
        ("Serra Circular Makita 5007MGK 1.200W", "Disco 184mm corte 66mm bivolt"),
        ("Nível a Laser Bosch Quigo 4 Linhas", "Alcance 10m nivelamento automático"),
        ("Fita Métrica Stanley PowerLock 5m", "Lâmina revestida aço trava automática"),
    ],
    "Roupas e Acessórios": [
        ("Camiseta Básica Hering 100% Algodão", "Disponível P ao GGG cores variadas"),
        ("Calça Jeans Levi's 501 Original", "Corte straight fit denim 12oz"),
        ("Vestido Midi Floral Viscose", "Estampa floral manga curta decote V"),
        ("Mochila Escolar Sestini Reforçada 30L", "Porta USB lateral reforçada"),
        ("Relógio Casio G-Shock DW-5600", "Resistente choque e água 200m"),
        ("Tênis Converse All Star Chuck Taylor", "Cano médio lona unissex"),
        ("Jaqueta Corta-Vento Nike Windrunner", "Impermeável capuz ajustável dry-fit"),
    ],
}

CATEGORIAS = list(CATALOGO.keys())


# ---------------------------------------------------------------------------
# Imperfeições intencionais
# ---------------------------------------------------------------------------

def _fmt_descricao(desc: str) -> str:
    """~5% descrição em minúsculas sem padronização."""
    if random.random() < 0.05:
        return desc.lower()
    return desc


def _fmt_preco(preco: float) -> float:
    """~3% preço com 4 casas decimais ao invés de 2."""
    if random.random() < 0.03:
        return round(preco, 4)
    return round(preco, 2)


def _fmt_categoria(cat: str) -> str:
    """~2% categoria com espaço extra no final."""
    if random.random() < 0.02:
        return cat + " "
    return cat


# ---------------------------------------------------------------------------
# Gerador principal
# ---------------------------------------------------------------------------

def gerar_produto(data_cadastro: datetime) -> dict:
    """Gera um único produto com dados levemente sujos."""
    categoria = random.choice(CATEGORIAS)
    nome, descricao_base = random.choice(CATALOGO[categoria])

    # Variação de preço por categoria
    faixa = {
        "Eletrônicos":        (150.0,  8000.0),
        "Casa e Decoração":   (50.0,   3000.0),
        "Esportes e Lazer":   (40.0,   5000.0),
        "Beleza e Saúde":     (20.0,    500.0),
        "Livros e Papelaria": (10.0,    200.0),
        "Alimentos e Bebidas":(15.0,    300.0),
        "Brinquedos e Games": (30.0,   1500.0),
        "Automotivo":         (25.0,    800.0),
        "Ferramentas":        (30.0,   2000.0),
        "Roupas e Acessórios":(30.0,   1500.0),
    }
    min_p, max_p = faixa.get(categoria, (10.0, 500.0))
    preco_base = random.uniform(min_p, max_p)

    estoque_inicial = random.randint(20, 500)

    return {
        "nome":           nome,
        "categoria":      _fmt_categoria(categoria),
        "descricao":      _fmt_descricao(descricao_base),
        "preco":          _fmt_preco(preco_base),
        "estoque_inicial": estoque_inicial,
        "estoque_atual":  estoque_inicial,
        "ativo":          1,
        "data_cadastro":  data_cadastro.isoformat(),
    }


def gerar_lote_produtos(n: int, data_base: datetime) -> list:
    """Gera N produtos."""
    return [gerar_produto(data_base) for _ in range(n)]