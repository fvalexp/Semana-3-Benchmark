import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from io import StringIO

st.set_page_config(page_title="LATAM Startups Benchmark", layout="wide")

# -----------------------------
# 1) RUTAS + DATOS DE RESPALDO
# -----------------------------
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_STARTUPS = """name,country,industry,founded_year,stage,funding_total_usd,employees,arr_usd,cac_usd,ltv_usd,gross_margin_pct,ltv_cac,payback_months,nps,revenue_model
PayFlex,Mexico,Fintech,2020,Series A,35000000,120,5200000,130,980,72,7.54,9,48,Subscription + Interchange
SaludYA,Colombia,HealthTech,2019,Seed,8200000,55,1800000,95,620,68,6.53,10,52,Marketplace fee
EduNova,Brazil,EdTech,2021,Pre-A,12000000,70,2400000,110,680,75,6.18,11,36,SaaS per seat
LogiXpress,Chile,RetailTech,2020,Series A,28000000,90,4100000,140,900,67,6.43,12,44,Usage-based + SaaS
AgroLink,Argentina,AgriTech,2022,Seed,6000000,40,950000,85,540,64,6.35,10,50,Transaction fee
"""

SAMPLE_ROUNDS = """name,round_date,round_type,round_amount_usd
PayFlex,2020-09-10,Seed,4500000
PayFlex,2021-11-03,Pre-A,8000000
PayFlex,2023-05-22,Series A,22500000
SaludYA,2020-03-18,Pre-Seed,1200000
SaludYA,2021-06-30,Seed,7000000
EduNova,2021-10-12,Pre-Seed,2000000
EduNova,2023-02-25,Pre-A,10000000
LogiXpress,2020-11-05,Seed,6000000
LogiXpress,2022-07-14,Series A,22000000
AgroLink,2022-04-21,Pre-Seed,1000000
AgroLink,2023-08-19,Seed,5000000
"""

def ensure_csv(fp: Path, sample_text: str):
    if not fp.exists():
        fp.write_text(sample_text, encoding="utf-8")

# -----------------------------
# 2) CARGA FLEXIBLE DE DATOS
# -----------------------------
@st.cache_data
def load_from_disk() -> tuple[pd.DataFrame, pd.DataFrame]:
    startups_fp = DATA_DIR / "startups_clean.csv"
    rounds_fp   = DATA_DIR / "rounds.csv"
    # Si faltan, crea muestra
    ensure_csv(startups_fp, SAMPLE_STARTUPS)
    ensure_csv(rounds_fp, SAMPLE_ROUNDS)
    startups = pd.read_csv(startups_fp)
    rounds = pd.read_csv(rounds_fp, parse_dates=["round_date"])
    return startups, rounds

def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    # Conversión segura de columnas esperadas
    num_cols = {
        "funding_total_usd","employees","arr_usd","cac_usd","ltv_usd",
        "gross_margin_pct","ltv_cac","payback_months","nps"
    }
    for c in df.columns:
        if c in num_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

# -----------------------------
# 3) UI: CARGA DE ARCHIVOS
# -----------------------------
st.title("Benchmark LATAM Startups – Dashboard Interactivo")
st.caption("Incluye subida de CSV / fallback a datos de muestra. Asegura que tus CSV estén en ./data para Streamlit Cloud.")

with st.expander("Opcional: subir tus CSV (reemplaza los del disco en esta sesión)"):
    up1 = st.file_uploader("Sube startups_clean.csv", type=["csv"], key="up_startups")
    up2 = st.file_uploader("Sube rounds.csv", type=["csv"], key="up_rounds")

    if up1 and up2:
        try:
            startups = pd.read_csv(up1)
            rounds = pd.read_csv(up2, parse_dates=["round_date"])
            startups = coerce_types(startups)
            st.success("Usando CSV subidos en esta sesión.")
        except Exception as e:
            st.error(f"Error leyendo CSV subidos: {e}")
            st.stop()
    else:
        startups, rounds = load_from_disk()

# Derivados
startups["funding_total_usd_m"] = startups["funding_total_usd"] / 1e6
startups["arr_usd_m"]           = startups["arr_usd"] / 1e6

# -----------------------------
# 4) FILTROS
# -----------------------------
st.sidebar.header("Filtros")
countries  = st.sidebar.multiselect("País",     sorted(startups["country"].dropna().unique()),  default=sorted(startups["country"].dropna().unique()))
stages     = st.sidebar.multiselect("Stage",    sorted(startups["stage"].dropna().unique()),    default=sorted(startups["stage"].dropna().unique()))
industries = st.sidebar.multiselect("Industria",sorted(startups["industry"].dropna().unique()), default=sorted(startups["industry"].dropna().unique()))

filtered = startups.query("country in @countries and stage in @stages and industry in @industries")

# -----------------------------
# 5) KPI CARDS
# -----------------------------
c1,c2,c3,c4 = st.columns(4)
with c1: st.metric("Startups", len(filtered))
with c2: st.metric("Funding total (USD M)", f"{filtered['funding_total_usd'].sum()/1e6:,.1f}" if len(filtered)>0 else "0.0")
with c3: st.metric("ARR medio (USD M)", f"{filtered['arr_usd'].mean()/1e6:,.2f}" if len(filtered)>0 else "0.00")
with c4: st.metric("LTV/CAC promedio", f"{filtered['ltv_cac'].mean():.2f}x" if len(filtered)>0 else "0.00x")

st.markdown("---")

# -----------------------------
# 6) GRÁFICOS
# -----------------------------
st.subheader("LTV/CAC vs Funding total (burbuja)")
if not filtered.empty:
    fig_bubble = px.scatter(
        filtered,
        x="ltv_cac", y="funding_total_usd_m",
        size="arr_usd_m", color="industry",
        hover_data=["name","country","stage","employees","gross_margin_pct","arr_usd_m"],
        labels={"ltv_cac":"LTV/CAC (x)", "funding_total_usd_m":"Funding total (USD M)", "arr_usd_m":"ARR (USD M)"}
    )
    fig_bubble.update_traces(marker_line_width=1)
    st.plotly_chart(fig_bubble, use_container_width=True)
else:
    st.info("No hay datos para el gráfico de burbuja con los filtros actuales.")

st.subheader("Timeline de rondas de financiación")
rounds_f = rounds[rounds["name"].isin(filtered["name"])].sort_values("round_date")
if not rounds_f.empty:
    fig_tl = px.scatter(
        rounds_f, x="round_date", y="name",
        size="round_amount_usd", color="round_type",
        labels={"round_date":"Fecha","name":"Startup","round_amount_usd":"Monto (USD)"}
    )
    st.plotly_chart(fig_tl, use_container_width=True)
else:
    st.info("No hay rondas para los filtros actuales.")

st.subheader("Modelos de ingresos (Treemap)")
if not filtered.empty and "revenue_model" in filtered.columns:
    fig_tm = px.treemap(filtered, path=["industry","revenue_model","name"], values="arr_usd")
    st.plotly_chart(fig_tm, use_container_width=True)
else:
    st.info("No hay datos para treemap (verifica columna 'revenue_model' y 'arr_usd').")

# -----------------------------
# 7) TABLA
# -----------------------------
st.subheader("Tabla comparativa")
cols = [c for c in ["name","country","industry","stage","funding_total_usd","arr_usd","employees","ltv_cac","payback_months","gross_margin_pct","nps","revenue_model"] if c in filtered.columns]
st.dataframe(filtered[cols].sort_values("funding_total_usd", ascending=False) if not filtered.empty else filtered)
st.caption("Fuente: CSV limpios (Crunchbase/Dealroom/AngelList). Documenta supuestos y conversión a USD en tu informe.")

