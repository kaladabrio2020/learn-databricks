"""
main.py — Interface de controle operacional do Simulador E-commerce.

Execute com:
    streamlit run main.py

Abas:
    🏠 Dashboard   — KPIs em tempo real
    ⚙️  Bootstrap   — Configuração e execução da Fase 1
    ▶️  Operacional — Start/Pause/Stop da geração contínua
    📊 Dados       — Visualizador das tabelas
    🔌 API         — Documentação dos endpoints
"""
import sys
import os
import time
import queue
import threading
from datetime import datetime, date, timedelta

import streamlit as st
import pandas as pd

# Garante imports do projeto
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import database as db
from state import SimulatorState
from operacional import get_modo_operacional

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="E-commerce Simulator",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS personalizado — tema dark premium
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ── Fontes ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Fundo geral ── */
.stApp {
    background: linear-gradient(135deg, #0d1117 0%, #0f1923 50%, #0a1628 100%);
    color: #e6edf3;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #8b949e;
    font-size: 0.78rem;
}

/* ── KPI Cards ── */
.kpi-card {
    background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(88, 166, 255, 0.15);
    border-color: #58a6ff;
}
.kpi-label {
    font-size: 0.72rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #8b949e;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #58a6ff;
    line-height: 1;
    margin-bottom: 4px;
}
.kpi-icon {
    font-size: 1.4rem;
    margin-bottom: 8px;
}
.kpi-sub {
    font-size: 0.7rem;
    color: #57ab5a;
}

/* ── Seção header ── */
.section-header {
    background: linear-gradient(90deg, #1f2937 0%, #161b22 100%);
    border-left: 4px solid #58a6ff;
    border-radius: 0 8px 8px 0;
    padding: 12px 20px;
    margin-bottom: 24px;
}
.section-header h2 {
    color: #e6edf3;
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
}
.section-header p {
    color: #8b949e;
    font-size: 0.8rem;
    margin: 4px 0 0 0;
}

/* ── Status badges ── */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}
.badge-running  { background: #1a3e2f; color: #57ab5a; border: 1px solid #57ab5a; }
.badge-paused   { background: #3d2e0a; color: #e3b341; border: 1px solid #e3b341; }
.badge-stopped  { background: #2e1a1a; color: #f85149; border: 1px solid #f85149; }
.badge-done     { background: #1a3e2f; color: #57ab5a; border: 1px solid #57ab5a; }

/* ── Botões customizados ── */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s;
    border: 1px solid #30363d;
}
.stButton > button:hover {
    border-color: #58a6ff;
    color: #58a6ff;
    box-shadow: 0 0 12px rgba(88, 166, 255, 0.2);
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #161b22;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #8b949e;
    font-weight: 500;
    font-size: 0.85rem;
}
.stTabs [aria-selected="true"] {
    background: #1f6feb !important;
    color: #ffffff !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #30363d;
    border-radius: 8px;
    overflow: hidden;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px;
}

/* ── Code block ── */
.stCode {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #e6edf3;
}

/* ── Progress bar ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #1f6feb, #58a6ff);
}

/* ── Logo / título sidebar ── */
.logo-area {
    padding: 20px 0 10px 0;
    text-align: center;
    border-bottom: 1px solid #30363d;
    margin-bottom: 20px;
}
.logo-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: #58a6ff;
}
.logo-sub {
    font-size: 0.7rem;
    color: #8b949e;
    margin-top: 2px;
}

/* ── Alert personalizado ── */
.custom-alert {
    background: #1a2535;
    border: 1px solid #1f6feb;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 12px 0;
    font-size: 0.85rem;
    color: #79c0ff;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Estado de sessão
# ---------------------------------------------------------------------------
if "bootstrap_queue" not in st.session_state:
    st.session_state.bootstrap_queue = queue.Queue()
if "bootstrap_running" not in st.session_state:
    st.session_state.bootstrap_running = False
if "bootstrap_thread" not in st.session_state:
    st.session_state.bootstrap_thread = None
if "bootstrap_progress" not in st.session_state:
    st.session_state.bootstrap_progress = None

# Inicializa banco se necessário
db.init_db()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="logo-area">
        <div class="logo-title">🛒 Ecommerce Sim</div>
        <div class="logo-sub">Simulador de Dados · v1.0</div>
    </div>
    """, unsafe_allow_html=True)

    state = SimulatorState.load()
    stats = db.get_stats()

    # Status do sistema
    status = state.simulation_status
    badge_class = {
        "Running": "badge-running",
        "Paused":  "badge-paused",
        "Stopped": "badge-stopped",
    }.get(status, "badge-stopped")

    op = get_modo_operacional()
    status_real = op.status()
    badge_class = {
        "Running": "badge-running",
        "Paused":  "badge-paused",
        "Stopped": "badge-stopped",
    }.get(status_real, "badge-stopped")

    st.markdown(f"""
    <div style="margin-bottom:16px;">
        <div style="font-size:0.7rem;color:#8b949e;margin-bottom:6px;">STATUS OPERACIONAL</div>
        <span class="badge {badge_class}">{status_real}</span>
    </div>
    """, unsafe_allow_html=True)

    # Bootstrap status
    bootstrap_ok = state.bootstrap_completed
    st.markdown(f"""
    <div style="margin-bottom:16px;">
        <div style="font-size:0.7rem;color:#8b949e;margin-bottom:6px;">BOOTSTRAP</div>
        <span class="badge {'badge-done' if bootstrap_ok else 'badge-stopped'}">
            {'✅ Concluído' if bootstrap_ok else '⏳ Pendente'}
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Mini KPIs
    st.markdown("<div style='font-size:0.7rem;color:#8b949e;margin-bottom:8px;'>TOTAIS</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.metric("Clientes", f"{stats['total_clientes']:,}")
    col2.metric("Produtos", f"{stats['total_produtos']:,}")
    col1.metric("Pedidos", f"{stats['total_pedidos']:,}")
    col2.metric("Pagamentos", f"{stats['total_pagamentos']:,}")

    st.divider()
    st.markdown(f"""
    <div style="font-size:0.68rem;color:#484f58;">
        Banco: <code>ecommerce.db</code><br>
        Última geração:<br>
        {state.last_generation or '—'}
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Atualizar", use_container_width=True):
        st.rerun()

# ---------------------------------------------------------------------------
# Tabs principais
# ---------------------------------------------------------------------------
tab_dash, tab_boot, tab_op, tab_dados, tab_api = st.tabs([
    "🏠 Dashboard",
    "⚙️ Bootstrap",
    "▶️ Operacional",
    "📊 Dados",
    "🔌 API",
])


# ============================================================= #
#  TAB 1 — DASHBOARD
# ============================================================= #
with tab_dash:
    st.markdown("""
    <div class="section-header">
        <h2>Dashboard Operacional</h2>
        <p>Visão em tempo real dos dados gerados pelo simulador</p>
    </div>
    """, unsafe_allow_html=True)

    stats = db.get_stats()
    receita = stats.get("receita_total", 0.0)

    # KPI row
    cols = st.columns(5)
    kpis = [
        ("👥", "Clientes", f"{stats['total_clientes']:,}", "registrados"),
        ("📦", "Produtos", f"{stats['total_produtos']:,}", "no catálogo"),
        ("🛍️", "Pedidos", f"{stats['total_pedidos']:,}", "gerados"),
        ("💳", "Pagamentos", f"{stats['total_pagamentos']:,}", "processados"),
        ("🚚", "Entregas", f"{stats['total_entregas']:,}", "criadas"),
    ]
    for col, (icon, label, value, sub) in zip(cols, kpis):
        col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Receita
    st.markdown(f"""
    <div class="kpi-card" style="background: linear-gradient(135deg, #1a3e2f 0%, #0d2318 100%);
         border-color:#57ab5a; text-align:left; padding:20px 30px;">
        <div class="kpi-label" style="color:#57ab5a;">💰 RECEITA TOTAL (pagamentos aprovados)</div>
        <div class="kpi-value" style="color:#57ab5a;font-size:2.5rem;">
            R$ {receita:,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos e tabelas
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### 📊 Pedidos por Status")
        rows_status = db.query(
            "SELECT status, COUNT(*) as total FROM pedidos GROUP BY status ORDER BY total DESC"
        )
        if rows_status:
            df_status = pd.DataFrame(rows_status)
            st.bar_chart(df_status.set_index("status")["total"], color="#58a6ff")
        else:
            st.info("Nenhum dado disponível. Execute o Bootstrap primeiro.")

    with col_r:
        st.markdown("#### 💳 Receita por Método de Pagamento")
        rows_metodo = db.query(
            "SELECT metodo, ROUND(SUM(valor), 2) as receita "
            "FROM pagamentos WHERE status='aprovado' GROUP BY metodo ORDER BY receita DESC"
        )
        if rows_metodo:
            df_metodo = pd.DataFrame(rows_metodo)
            st.bar_chart(df_metodo.set_index("metodo")["receita"], color="#57ab5a")
        else:
            st.info("Nenhum pagamento aprovado ainda.")

    st.markdown("#### 🏆 Top Categorias por Receita")
    rows_cat = db.query(
        "SELECT p.categoria, COUNT(ip.id_item) as itens_vendidos, "
        "ROUND(SUM(ip.subtotal), 2) as receita "
        "FROM itens_pedido ip JOIN produtos p ON ip.id_produto = p.id_produto "
        "GROUP BY p.categoria ORDER BY receita DESC LIMIT 10"
    )
    if rows_cat:
        df_cat = pd.DataFrame(rows_cat)
        df_cat.columns = ["Categoria", "Itens Vendidos", "Receita (R$)"]
        df_cat["Receita (R$)"] = df_cat["Receita (R$)"].map("R$ {:,.2f}".format)
        st.dataframe(df_cat, use_container_width=True, hide_index=True)
    else:
        st.info("Execute o Bootstrap para ver análises de categorias.")


# ============================================================= #
#  TAB 2 — BOOTSTRAP
# ============================================================= #
with tab_boot:
    st.markdown("""
    <div class="section-header">
        <h2>⚙️ Fase 1 — Bootstrap Histórico</h2>
        <p>Gera toda a base histórica da empresa entre duas datas</p>
    </div>
    """, unsafe_allow_html=True)

    state = SimulatorState.load()

    if state.bootstrap_completed:
        stats = db.get_stats()
        st.success(f"""
        ✅ **Bootstrap já concluído!**
        Período: `{state.bootstrap_start_date}` → `{state.bootstrap_until}`
        — {stats['total_clientes']:,} clientes · {stats['total_produtos']:,} produtos ·
        {stats['total_pedidos']:,} pedidos
        """)
        if st.button("🔁 Re-executar Bootstrap (apaga dados existentes)", type="secondary"):
            state.bootstrap_completed = False
            state.save()
            st.rerun()
    else:
        st.markdown("""
        <div class="custom-alert">
            💡 Configure os parâmetros abaixo e clique em <strong>Iniciar Bootstrap</strong>.
            O progresso será exibido em tempo real.
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_bootstrap"):
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "📅 Data inicial",
                    value=date.today() - timedelta(days=180),
                    help="Primeira data do histórico",
                )
                customer_growth = st.number_input(
                    "👥 Clientes por dia",
                    min_value=1, max_value=100, value=5,
                )
                order_growth = st.number_input(
                    "🛍️ Pedidos por dia",
                    min_value=1, max_value=200, value=10,
                )
                random_seed = st.number_input(
                    "🎲 Random seed",
                    min_value=0, max_value=99999, value=42,
                    help="Para reproduzir os mesmos dados",
                )

            with col2:
                bootstrap_until = st.date_input(
                    "📅 Data final (bootstrap_until)",
                    value=date.today() - timedelta(days=1),
                    help="Última data do histórico",
                )
                product_growth = st.number_input(
                    "📦 Produtos por mês",
                    min_value=1, max_value=50, value=8,
                )
                business_calendar = st.checkbox(
                    "📆 Respeitar calendário comercial",
                    value=False,
                    help="Reduz geração em fins de semana",
                )
                reset_database = st.checkbox(
                    "🗑️ Resetar banco antes de iniciar",
                    value=True,
                )

            submitted = st.form_submit_button(
                "🚀 Iniciar Bootstrap", use_container_width=True, type="primary"
            )

        if submitted:
            if bootstrap_until <= start_date:
                st.error("⚠️ A data final deve ser posterior à data inicial.")
            else:
                from bootstrap import executar_bootstrap

                config = {
                    "start_date":           datetime.combine(start_date, datetime.min.time()),
                    "bootstrap_until":      datetime.combine(bootstrap_until, datetime.max.time().replace(microsecond=0)),
                    "random_seed":          random_seed,
                    "reset_database":       reset_database,
                    "customer_growth_rate": customer_growth,
                    "order_growth_rate":    order_growth,
                    "product_growth_rate":  product_growth,
                    "business_calendar":    business_calendar,
                }

                st.markdown("---")
                progress_bar = st.progress(0.0, text="Iniciando...")
                status_box = st.empty()
                stats_box = st.empty()

                for prog in executar_bootstrap(config):
                    pct = prog["percentual"]
                    msg = prog["mensagem"]
                    s = prog["stats"]

                    progress_bar.progress(pct, text=msg)
                    status_box.markdown(
                        f"`{prog['dia_atual']}` — Dia {prog['dia_numero']}/{prog['total_dias']}"
                    )
                    stats_box.markdown(
                        f"👥 {s['total_clientes']:,} clientes · "
                        f"📦 {s['total_produtos']:,} produtos · "
                        f"🛍️ {s['total_pedidos']:,} pedidos · "
                        f"💳 {s['total_pagamentos']:,} pagamentos · "
                        f"🚚 {s['total_entregas']:,} entregas"
                    )

                progress_bar.progress(1.0, text="✅ Concluído!")
                st.success("🎉 Bootstrap finalizado com sucesso! Vá para a aba Dashboard para ver os dados.")
                st.rerun()


# ============================================================= #
#  TAB 3 — OPERACIONAL
# ============================================================= #
with tab_op:
    st.markdown("""
    <div class="section-header">
        <h2>▶️ Fase 2 — Modo Operacional</h2>
        <p>Geração contínua de novos eventos em intervalos configuráveis</p>
    </div>
    """, unsafe_allow_html=True)

    state = SimulatorState.load()
    op = get_modo_operacional()
    op_status = op.status()

    if not state.bootstrap_completed:
        st.warning("⚠️ Execute o **Bootstrap** antes de iniciar o modo operacional.")
    else:
        # Status display
        badge_map = {
            "Running": ("badge-running", "▶️ Rodando"),
            "Paused":  ("badge-paused",  "⏸️ Pausado"),
            "Stopped": ("badge-stopped", "⏹️ Parado"),
        }
        badge_cls, badge_txt = badge_map.get(op_status, ("badge-stopped", "⏹️ Parado"))

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:24px;">
            <span style="font-size:0.9rem;color:#8b949e;">Status:</span>
            <span class="badge {badge_cls}" style="font-size:0.85rem;padding:6px 18px;">{badge_txt}</span>
        </div>
        """, unsafe_allow_html=True)

        # Controles
        col_start, col_pause, col_stop = st.columns(3)

        with col_start:
            if st.button("▶️ Iniciar", use_container_width=True, type="primary",
                         disabled=op.is_running()):
                op.start()
                st.rerun()

        with col_pause:
            if op.is_running():
                if st.button("⏸️ Pausar", use_container_width=True):
                    op.pause()
                    st.rerun()
            elif op.is_paused():
                if st.button("▶️ Retomar", use_container_width=True, type="primary"):
                    op.resume()
                    st.rerun()
            else:
                st.button("⏸️ Pausar", use_container_width=True, disabled=True)

        with col_stop:
            if st.button("⏹️ Parar", use_container_width=True,
                         disabled=op_status == "Stopped"):
                op.stop()
                st.rerun()

        st.divider()

        # Configuração do ciclo
        st.markdown("#### ⚙️ Configuração do Ciclo")
        with st.expander("Configurar parâmetros operacionais", expanded=op_status == "Stopped"):
            col_a, col_b = st.columns(2)
            with col_a:
                intervalo = st.selectbox(
                    "⏱️ Intervalo de geração",
                    options=[30, 60, 120, 300, 600, 1800, 3600],
                    format_func=lambda x: (
                        f"{x}s" if x < 60 else
                        f"{x//60} min" if x < 3600 else
                        f"{x//3600}h"
                    ),
                    index=3,
                )
                max_pedidos = st.slider("🛍️ Máx. pedidos por ciclo", 1, 50, 10)
            with col_b:
                business_hours = st.checkbox("🕐 Respeitar horário comercial", value=False)
                max_clientes = st.slider("👥 Máx. clientes por ciclo", 0, 20, 5)

            if st.button("💾 Salvar e Reiniciar", type="secondary"):
                config_op = {
                    "realtime_enabled":      True,
                    "generation_interval":   intervalo,
                    "max_orders_per_cycle":  max_pedidos,
                    "max_clients_per_cycle": max_clientes,
                    "business_hours":        business_hours,
                }
                op.stop()
                time.sleep(0.5)
                op.start(config_op)

                state.generation_interval_seconds = intervalo
                state.max_orders_per_cycle = max_pedidos
                state.max_clients_per_cycle = max_clientes
                state.save()
                st.success("✅ Configuração salva! Modo operacional reiniciado.")
                st.rerun()

        # Estatísticas operacionais
        st.divider()
        st.markdown("#### 📈 Geração em Tempo Real")
        state = SimulatorState.load()
        col1, col2 = st.columns(2)
        col1.info(f"**Última geração:** {state.last_generation or '—'}")
        col2.info(f"**Próxima geração:** {state.next_generation or '—'}")

        # Últimos pedidos
        st.markdown("##### 🕐 Últimos 10 Pedidos")
        ult_pedidos = db.query(
            "SELECT p.id_pedido, c.nome as cliente, p.status, p.valor_total, p.data_pedido "
            "FROM pedidos p JOIN clientes c ON p.id_cliente = c.id_cliente "
            "ORDER BY p.id_pedido DESC LIMIT 10"
        )
        if ult_pedidos:
            df_ult = pd.DataFrame(ult_pedidos)
            df_ult["valor_total"] = df_ult["valor_total"].map("R$ {:,.2f}".format)
            st.dataframe(df_ult, use_container_width=True, hide_index=True)

        if st.button("🔄 Atualizar dados", use_container_width=True):
            st.rerun()


# ============================================================= #
#  TAB 4 — DADOS
# ============================================================= #
with tab_dados:
    st.markdown("""
    <div class="section-header">
        <h2>📊 Visualizador de Dados</h2>
        <p>Explore as tabelas geradas pelo simulador</p>
    </div>
    """, unsafe_allow_html=True)

    tabela = st.selectbox(
        "Selecione a tabela",
        ["clientes", "produtos", "pedidos", "itens_pedido",
         "pagamentos", "estoque_movimentacoes", "entregas"],
        key="tabela_select",
    )

    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        filtro_texto = st.text_input("🔍 Filtro (SQL WHERE clause opcional)", placeholder="ex: status = 'aprovado'")
    with col_f2:
        limite = st.number_input("Limite de linhas", min_value=10, max_value=5000, value=100, step=50)
    with col_f3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔎 Buscar", type="primary", use_container_width=True):
            pass  # trigger via state

    try:
        where_clause = f"WHERE {filtro_texto}" if filtro_texto.strip() else ""
        sql = f"SELECT * FROM {tabela} {where_clause} ORDER BY rowid DESC LIMIT {limite}"
        rows = db.query(sql)

        if rows:
            df = pd.DataFrame(rows)
            st.markdown(f"**{len(rows):,} registros** encontrados em `{tabela}`")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Download
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                f"⬇️ Download {tabela}.csv",
                data=csv,
                file_name=f"{tabela}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        else:
            st.info(f"Nenhum registro encontrado em `{tabela}`.")
    except Exception as e:
        st.error(f"❌ Erro na consulta: {e}")

    # Qualidade dos dados
    st.divider()
    st.markdown("#### 🔬 Análise de Qualidade dos Dados")
    if st.button("Analisar imperfeições nos dados"):
        with st.spinner("Analisando qualidade..."):
            # Clientes com CPF sem formatação
            cpf_sem_fmt = db.query(
                "SELECT COUNT(*) as n FROM clientes WHERE cpf NOT LIKE '%-%'"
            )[0]["n"]

            # Clientes com nome em CAPS
            nome_caps = db.query(
                "SELECT COUNT(*) as n FROM clientes WHERE nome = UPPER(nome) AND LENGTH(nome) > 3"
            )[0]["n"]

            # Complemento vazio (string vazia)
            complemento_vazio = db.query(
                "SELECT COUNT(*) as n FROM clientes WHERE complemento = ''"
            )[0]["n"]

            # Produtos com descrição em minúsculas
            desc_minusc = db.query(
                "SELECT COUNT(*) as n FROM produtos WHERE descricao = LOWER(descricao)"
            )[0]["n"]

            # Pagamentos pendentes
            pag_pendente = db.query(
                "SELECT COUNT(*) as n FROM pagamentos WHERE status = 'pendente'"
            )[0]["n"]

            # Pedidos sem entrega (pagamento aprovado mas sem entrega)
            ped_sem_entrega = db.query(
                "SELECT COUNT(*) as n FROM pedidos p "
                "JOIN pagamentos pg ON p.id_pedido = pg.id_pedido "
                "LEFT JOIN entregas e ON p.id_pedido = e.id_pedido "
                "WHERE pg.status = 'aprovado' AND e.id_entrega IS NULL"
            )[0]["n"]

        issues = [
            ("🔴 CPF sem formatação",      cpf_sem_fmt,        "Clientes"),
            ("🟡 Nomes em CAPS LOCK",       nome_caps,          "Clientes"),
            ("🟡 Complemento vazio ('')",   complemento_vazio,  "Clientes"),
            ("🟡 Descrição não padronizada", desc_minusc,       "Produtos"),
            ("🔴 Pagamentos pendentes",      pag_pendente,       "Pagamentos"),
            ("🔴 Pedidos aprovados s/ entrega", ped_sem_entrega, "Integridade"),
        ]

        df_quality = pd.DataFrame(issues, columns=["Problema", "Ocorrências", "Tabela"])
        st.dataframe(df_quality, use_container_width=True, hide_index=True)
        st.caption("💡 Esses problemas são intencionais para exercitar transformações ELT no Databricks.")


# ============================================================= #
#  TAB 5 — API
# ============================================================= #
with tab_api:
    st.markdown("""
    <div class="section-header">
        <h2>🔌 API REST</h2>
        <p>Endpoints para consumo externo dos dados (Databricks, etc.)</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="custom-alert">
        🚀 Para iniciar a API: <code>uvicorn api:app --reload --port 8001</code><br>
        Documentação interativa: <a href="http://localhost:8001/docs" style="color:#79c0ff;">http://localhost:8001/docs</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Endpoints Disponíveis")

    endpoints = [
        ("GET", "/status",                    "Estado interno do simulador"),
        ("GET", "/clientes",                  "Full load de clientes"),
        ("GET", "/clientes?since=DATETIME",   "Incremental de clientes"),
        ("GET", "/produtos",                  "Full load de produtos"),
        ("GET", "/pedidos",                   "Full load de pedidos"),
        ("GET", "/pedidos?since=DATETIME",    "Incremental de pedidos"),
        ("GET", "/pedidos?start=DATE&end=DATE","Pedidos por período"),
        ("GET", "/itens",                     "Itens de pedidos"),
        ("GET", "/pagamentos",                "Full load de pagamentos"),
        ("GET", "/pagamentos?since=DATETIME", "Incremental de pagamentos"),
        ("GET", "/estoque",                   "Movimentações de estoque"),
        ("GET", "/entregas",                  "Full load de entregas"),
        ("GET", "/analytics/resumo",          "Resumo executivo"),
    ]

    df_endpoints = pd.DataFrame(endpoints, columns=["Método", "Endpoint", "Descrição"])
    st.dataframe(df_endpoints, use_container_width=True, hide_index=True)

    st.markdown("### Exemplos de Uso")

    col_ex1, col_ex2 = st.columns(2)

    with col_ex1:
        st.markdown("**Full Load:**")
        st.code("GET http://localhost:8001/clientes", language="http")
        st.code("GET http://localhost:8001/pedidos", language="http")

        st.markdown("**Incremental:**")
        st.code("GET http://localhost:8001/pagamentos?since=2026-07-01T00:00:00", language="http")

    with col_ex2:
        st.markdown("**Por período:**")
        st.code("GET http://localhost:8001/pedidos?start=2026-07-01&end=2026-07-31", language="http")

        st.markdown("**Paginação:**")
        st.code("GET http://localhost:8001/clientes?limit=500&offset=1000", language="http")

    st.markdown("### Exemplo de Resposta")
    st.code("""{
  "total": 1250,
  "limit": 1000,
  "offset": 0,
  "data": [
    {
      "id_cliente": 1,
      "nome": "Maria Silva",
      "cpf": "123.456.789-00",
      "email": "maria.silva@gmail.com",
      "telefone": "(11) 98765-4321",
      "cidade": "São Paulo",
      "estado": "SP",
      "data_cadastro": "2025-01-15T10:30:00"
    }
  ]
}""", language="json")

    st.markdown("### Integração com Databricks")
    st.code("""# Exemplo: ingestão incremental no Databricks
from datetime import datetime, timedelta
import requests

BASE_URL = "http://<host>:8001"
since = (datetime.now() - timedelta(hours=1)).isoformat()

# Clientes novos na última hora
clientes = requests.get(f"{BASE_URL}/clientes?since={since}").json()
pedidos   = requests.get(f"{BASE_URL}/pedidos?since={since}").json()
pagamentos = requests.get(f"{BASE_URL}/pagamentos?since={since}").json()

print(f"Novos dados: {clientes['total']} clientes, "
      f"{pedidos['total']} pedidos, "
      f"{pagamentos['total']} pagamentos")
""", language="python")
