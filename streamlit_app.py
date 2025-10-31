import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Benchmark LATAM Startups", layout="wide")

# --- RUTA PERSONALIZADA (ADÁPTALA SI ES NECESARIO) ---
DATA_PATH = Path("/Users/freddyvillar/Documents/Documents - MacBook Air de Freddy/Maestria/Innovación/Programación/data")

# --- CARGA DE DATOS ---
@st.cache_data
def load_data():
    startups = pd.read_csv(DATA_PATH / "startups_clean.csv")
    rounds = pd.read_csv(DATA_PATH / "rounds.csv", parse_dates=["round_date"])
    startups["funding_total_usd_m"] = startups["funding_total_usd"] / 1e6
    startups["arr_usd_m"] = startups["arr_usd"] / 1e6
    return startups, rounds

startups, rounds = load_data()

# --- DASHBOARD ---
st.title("Benchmark LATAM Startups – Dashboard Interactivo")
st.caption("Análisis comparativo de startups LATAM (2019–2024).")

# --- FILTROS ---
st.sidebar.header("Filtros")
countries = st.sidebar.multiselect("País", sorted(startups["country"].unique()), default=sorted(startups["country"].unique()))
stages = st.sidebar.multiselect("Stage", sorted(startups["stage"].unique()), default=sorted(startups["stage"].unique()))
industries = st.sidebar.multiselect("Industria", sorted(startups["industry"].unique()), default=sorted(startups["industry"].unique()))

filtered = startups.query("country in @countries and stage in @stages and industry in @industries")

# --- KPIs ---
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Startups", len(filtered))
with c2: st.metric("Funding total (USD M)", f"{filtered['funding_total_usd'].sum()/1e6:,.1f}")
with c3: st.metric("ARR medio (USD M)", f"{filtered['arr_usd'].mean()/1e6:,.2f}")
with c4: st.metric("LTV/CAC promedio", f"{filtered['ltv_cac'].mean():.2f}x")

st.markdown("---")

# --- GRÁFICO 1 ---
st.subheader("LTV/CAC vs Funding total (Burbuja)")
if not filtered.empty:
    fig_bubble = px.scatter(
        filtered,
        x="ltv_cac",
        y="funding_total_usd_m",
        size="arr_usd_m",
        color="industry",
        hover_data=["name", "country", "stage", "employees", "gross_margin_pct", "arr_usd_m"],
        labels={"ltv_cac": "LTV/CAC (x)", "funding_total_usd_m": "Funding total (USD M)", "arr_usd_m": "ARR (USD M)"},
    )
    st.plotly_chart(fig_bubble, use_container_width=True)
else:
    st.info("No hay datos para los filtros seleccionados.")

# --- GRÁFICO 2 ---
st.subheader("Timeline de rondas de financiación")
rounds_f = rounds[rounds["name"].isin(filtered["name"])]
if not rounds_f.empty:
    fig_tl = px.scatter(
        rounds_f.sort_values("round_date"),
        x="round_date",
        y="name",
        size="round_amount_usd",
        color="round_type",
        labels={"round_date": "Fecha", "name": "Startup", "round_amount_usd": "Monto (USD)"},
    )
    st.plotly_chart(fig_tl, use_container_width=True)
else:
    st.info("No hay rondas para los filtros seleccionados.")

# --- GRÁFICO 3 ---
st.subheader("Modelos de ingresos (Treemap)")
if not filtered.empty:
    fig_tm = px.treemap(filtered, path=["industry", "revenue_model", "name"], values="arr_usd")
    st.plotly_chart(fig_tm, use_container_width=True)
else:
    st.info("No hay datos disponibles para este gráfico.")

# --- TABLA COMPARATIVA ---
st.subheader("Tabla comparativa de startups")
st.dataframe(
    filtered[
        ["name", "country", "industry", "stage", "funding_total_usd", "arr_usd", "employees", "ltv_cac", "payback_months", "gross_margin_pct", "nps", "revenue_model"]
    ]
)
st.caption("Fuente: Crunchbase / Dealroom / AngelList – datos simulados de muestra.")

