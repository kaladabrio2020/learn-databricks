# Especificação das Fases do Simulador


# FASE 1 - HISTÓRICA (BOOTSTRAP)


# Ferramentas
+ Python 3.12
+ FastAPI
+ Pydantic
+ Faker
+ NumPy
+ Pandas
+ Uvicorn

## Objetivo

Construir toda a base histórica da empresa antes do início da operação.

Essa fase executará apenas uma vez e será responsável por gerar todos os registros compreendidos entre uma data inicial e uma data final definida pelo usuário.

---

## Configuração

| Atributo | Tipo | Obrigatório | Descrição |
|----------|------|-------------|-----------|
| start_date | datetime | Sim | Data inicial da simulação |
| bootstrap_until | datetime | Sim | Última data do histórico |
| random_seed | integer | Não | Seed para reproduzir os mesmos dados |
| reset_database | boolean | Não | Remove todos os dados existentes antes do bootstrap |
| customer_growth_rate | integer | Não | Clientes gerados por dia |
| order_growth_rate | integer | Não | Pedidos gerados por dia |
| product_growth_rate | integer | Não | Produtos criados por mês |
| business_calendar | boolean | Não | Considera finais de semana e feriados |
| timezone | string | Não | Timezone da simulação |

---

## Entradas

```
start_date

↓

bootstrap_until
```

---

## Processamento

Durante essa fase o sistema deverá:

- Criar clientes
- Criar produtos
- Criar pedidos
- Criar itens dos pedidos
- Criar pagamentos
- Criar movimentações de estoque
- Criar entregas

Respeitando sempre a ordem cronológica dos eventos.

---

## Regras

### Clientes

- IDs sequenciais
- Cadastro distribuído ao longo do período
- CPF único
- Email único

---

### Produtos

- Cadastro distribuído durante o histórico
- Preços variáveis
- Estoque inicial

---

### Pedidos

- Cliente deve existir
- Produto deve existir
- Valor calculado pelos itens
- Data dentro do período

---

### Pagamentos

- Pedido deve existir
- Data posterior ao pedido

---

### Entregas

- Pagamento aprovado
- Data posterior ao pagamento

---

## Saída

Ao finalizar o bootstrap teremos:

```
Clientes

Produtos

Pedidos

Itens

Pagamentos

Estoque

Entregas
```

Todos armazenados permanentemente.

---

# FASE 2 - OPERACIONAL

## Objetivo

Simular uma empresa em funcionamento.

Após finalizar o bootstrap, o sistema passa a gerar apenas novos eventos.

Nunca modifica o histórico.

---

## Configuração

| Atributo | Tipo | Obrigatório | Descrição |
|----------|------|-------------|-----------|
| realtime_enabled | boolean | Sim | Ativa a geração contínua |
| generation_interval | string | Sim | Intervalo de geração (1 min, 5 min, 1 hora, etc.) |
| records_per_cycle | integer | Não | Quantidade fixa de registros por ciclo |
| simulation_speed | decimal | Não | Velocidade do relógio simulado |
| business_hours | boolean | Não | Respeita horário comercial |
| pause_generation | boolean | Não | Suspende a geração |
| auto_resume | boolean | Não | Retoma automaticamente |
| max_orders_per_cycle | integer | Não | Limite de pedidos por execução |
| max_clients_per_cycle | integer | Não | Limite de clientes por execução |
| random_seed | integer | Não | Mantém previsibilidade da geração |

---

## Funcionamento

O simulador ficará executando continuamente.

Exemplo:

```
09:00

↓

gera novos registros

↓

09:05

↓

gera novos registros

↓

09:10

↓

gera novos registros
```

---

## Fluxo

A cada execução deverão ser criados novos:

- Clientes
- Pedidos
- Itens
- Pagamentos
- Movimentações
- Entregas

Sempre preservando os dados anteriores.

---

## Regras

### Clientes

Novos clientes poderão ser cadastrados.

Jamais alterar clientes existentes.

---

### Produtos

Por padrão permanecem iguais.

Opcionalmente novos produtos podem surgir.

---

### Pedidos

Sempre associados a clientes existentes.

---

### Pagamentos

Somente para pedidos criados.

---

### Estoque

Atualizado conforme novos pedidos.

---

### Entregas

Criadas somente após pagamento aprovado.

---

# API

A API passa apenas a consultar a base.

## Full Load

```
GET /clientes

GET /produtos

GET /pedidos
```

---

## Incremental

```
GET /clientes?since=2026-07-20T10:00:00

GET /pedidos?since=2026-07-20T10:00:00

GET /pagamentos?since=2026-07-20T10:00:00
```

---

## Consulta por período

```
GET /pedidos?start=2026-07-01&end=2026-07-31
```

---

# Estado do Sistema

O simulador deverá manter um estado interno.

| Atributo | Descrição |
|----------|-----------|
| current_simulation_time | Horário atual da simulação |
| bootstrap_completed | Histórico concluído |
| total_customers | Total de clientes |
| total_products | Total de produtos |
| total_orders | Total de pedidos |
| total_payments | Total de pagamentos |
| total_deliveries | Total de entregas |
| last_generation | Última geração realizada |
| next_generation | Próxima geração prevista |
| simulation_status | Running, Paused ou Stopped |

---

# Fluxo Completo

```
Início

      │

      ▼

Bootstrap

      │

Gera histórico

      │

Atualiza estado

      │

Bootstrap Finalizado

      │

      ▼

Modo Operacional

      │

Relógio Simulado

      │

Geração Contínua

      │

Persistência

      │

API REST

      │

Databricks
```