"""
Dashboard Streamlit — Assemblée nationale française, 17e législature.
Projet #2 — Infrastructure Data Cloud · DPIA 1
Auteur : Samir NZAMBA · L'École Multimédia · Paris

Usage :
    streamlit run dashboards/streamlit/app.py
"""

import math
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings("ignore")

# ─── Configuration ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Assemblée nationale · Analyse",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, sans-serif;
    font-size: 14px;
    -webkit-font-smoothing: antialiased;
}

.stApp { background-color: #f0f2f8; }

.block-container {
    padding: 2rem 2.75rem !important;
    max-width: 1380px !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #002395 0%, #001f80 100%) !important;
}
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.12) !important;
    margin: 1.1rem 0 !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.875rem !important;
    padding: 0.45rem 0.75rem !important;
    border-radius: 7px !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stMultiSelect label {
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
    opacity: 0.55 !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stMultiSelect > div > div {
    background-color: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div > div,
[data-testid="stSidebar"] .stMultiSelect > div > div > div {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stSelectbox svg,
[data-testid="stSidebar"] .stMultiSelect svg {
    fill: #ffffff !important;
}
[data-testid="stSidebar"] ul[role="listbox"],
[data-testid="stSidebar"] div[role="listbox"] {
    background-color: #0d2b8e !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}
[data-testid="stSidebar"] ul[role="listbox"] li,
[data-testid="stSidebar"] div[role="listbox"] div {
    color: #ffffff !important;
}

[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e4e8f0;
    border-radius: 12px;
    padding: 1.1rem 1.3rem 1rem 1.3rem;
    box-shadow: 0 1px 3px rgba(0,35,149,0.06),
                0 4px 12px rgba(0,35,149,0.04);
}
[data-testid="metric-container"] label {
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
    color: #8896b0 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.85rem !important;
    font-weight: 700 !important;
    color: #0a1628 !important;
    letter-spacing: -0.025em !important;
    line-height: 1.1 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.75rem !important;
    color: #64748b !important;
}

h1 {
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    color: #0a1628 !important;
    letter-spacing: -0.025em !important;
    margin: 0 0 0.2rem 0 !important;
    line-height: 1.2 !important;
}
h3 {
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #1e293b !important;
    letter-spacing: -0.01em !important;
    margin: 0 0 0.15rem 0 !important;
}

[data-testid="stCaptionContainer"] p {
    color: #94a3b8 !important;
    font-size: 0.76rem !important;
    margin-bottom: 0.75rem !important;
}

[data-testid="stAlert"] {
    border-radius: 10px !important;
    border: 1px solid #dbeafe !important;
    background: #f0f7ff !important;
    padding: 0.9rem 1.1rem !important;
}
[data-testid="stAlert"] p {
    font-size: 0.83rem !important;
    line-height: 1.65 !important;
    color: #334155 !important;
}

[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    border: 1px solid #e4e8f0 !important;
    overflow: hidden !important;
    box-shadow: 0 1px 3px rgba(0,35,149,0.04) !important;
}

.page-banner {
    background: linear-gradient(135deg, #002395 0%, #0035c9 100%);
    border-radius: 14px;
    padding: 1.75rem 2.25rem;
    margin-bottom: 1.75rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.banner-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.02em;
    margin: 0 0 0.2rem 0;
    line-height: 1.2;
}
.banner-desc {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.65);
    margin: 0;
}
.banner-badge {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    color: #ffffff;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.4rem 0.9rem;
    border-radius: 999px;
    letter-spacing: 0.04em;
    white-space: nowrap;
}

.chart-card {
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid #e4e8f0;
    padding: 1.25rem 1.5rem 0.75rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0,35,149,0.05);
    margin-bottom: 1.25rem;
}

.author-card {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
    padding: 0.875rem 1rem;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Palette ──────────────────────────────────────────────────────────────────

BLEU   = "#002395"
ROUGE  = "#C1002A"
BLEU_C = "#4f7ed4"
GRIS   = "#64748b"
BLANC  = "#ffffff"
FONT   = "Inter, system-ui, sans-serif"

COLORSCALE_BLEU = [
    [0,   "#c7d8f5"],
    [0.5, "#4f7ed4"],
    [1,   "#002395"],
]

COULEURS_GROUPES = {
    "RN":      "#1E3A8A",
    "EPR":     "#DAA520",
    "LFI-NFP": "#CC0000",
    "SOC":     "#E91E63",
    "DR":      "#1565C0",
    "ECO":     "#2E7D32",
    "DEM":     "#FF8F00",
    "HOR":     "#00838F",
    "LIOT":    "#6A1B9A",
    "GDR":     "#B71C1C",
    "UDR":     "#0D47A1",
    "NI":      "#757575",
}

def plo(**kw):
    base = dict(
        paper_bgcolor=BLANC,
        plot_bgcolor=BLANC,
        font=dict(family=FONT, size=12, color="#374151"),
        margin=dict(t=20, b=20, l=8, r=16),
        hoverlabel=dict(
            bgcolor="#0a1628",
            font_size=12,
            font_color="white",
            bordercolor="#1e293b",
        ),
    )
    base.update(kw)
    return base

def ax(**kw):
    d = dict(
        showgrid=False,
        linecolor="#eaecf2",
        tickcolor="rgba(0,0,0,0)",
        tickfont=dict(size=11, color="#64748b"),
        title_font=dict(size=11, color="#64748b"),
    )
    d.update(kw)
    return d

def ay(**kw):
    d = dict(
        gridcolor="#f4f6fb",
        gridwidth=1,
        linecolor="rgba(0,0,0,0)",
        tickcolor="rgba(0,0,0,0)",
        tickfont=dict(size=11, color="#64748b"),
        title_font=dict(size=11, color="#64748b"),
    )
    d.update(kw)
    return d

def chart(fig):
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": [
                "select2d", "lasso2d", "autoScale2d"
            ],
        }
    )


# ─── Nettoyage ────────────────────────────────────────────────────────────────

def nettoyer_affichage(val):
    if val is None:
        return "—"
    if isinstance(val, float) and math.isnan(val):
        return "—"
    if isinstance(val, dict):
        if "@xsi:nil" in val or "@xmlns:xsi" in val:
            return "—"
        for k in ("#text", "value", "text"):
            if k in val:
                return str(val[k])
        return "—"
    if isinstance(val, str):
        v = val.strip()
        if v == "" or v.lower() == "none":
            return "—"
        if "@xsi:nil" in v or "@xmlns:xsi" in v:
            return "—"
    return val

def nettoyer_serie(serie: pd.Series) -> pd.Series:
    return serie.apply(nettoyer_affichage).replace("—", None)


# ─── Données ──────────────────────────────────────────────────────────────────

@st.cache_resource
def get_engine():
    return create_engine(
        "postgresql+psycopg2://jobs_user:jobs_password123@localhost:5432/jobs_db"
    )

@st.cache_data
def charger():
    eng = get_engine()
    # Uniquement les députés actifs de la 17e législature
    d = pd.read_sql(
        "SELECT * FROM deputes WHERE groupe_sigle IS NOT NULL",
        eng
    )
    s = pd.read_sql("SELECT * FROM scrutins ORDER BY date", eng)
    g = pd.read_sql(
        "SELECT * FROM groupes_politiques ORDER BY nb_membres DESC",
        eng
    )

    def clean(v):
        if isinstance(v, dict):
            if "@xsi:nil" in v or "@xmlns:xsi" in v:
                return None
            for k in ("#text", "value", "text"):
                if k in v:
                    return str(v[k])
            return None
        if isinstance(v, str) and (
            "@xsi:nil" in v or "@xmlns:xsi" in v
        ):
            return None
        return v

    d["profession"]     = d["profession"].apply(clean)
    d["lieu_naissance"] = d["lieu_naissance"].apply(clean)
    d["date_naissance"] = pd.to_datetime(d["date_naissance"], errors="coerce")
    d["genre"]          = d["civilite"].map({"M.": "Homme", "Mme": "Femme"})
    s["date"]           = pd.to_datetime(s["date"])
    return d, s, g

df_d, df_s, df_g = charger()

# Constantes dynamiques
AGE_MIN    = int(df_d["age"].dropna().min())
AGE_MAX    = int(df_d["age"].dropna().max())
NB_DEPUTES = len(df_d)
NB_SCRUTINS = len(df_s)


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        "<div style='font-size:1rem;font-weight:700;"
        "letter-spacing:-0.01em;margin-bottom:0.1rem;'>"
        "Assemblée nationale</div>"
        "<div style='font-size:0.73rem;opacity:0.5;"
        "margin-bottom:1.25rem;'>17e législature · France</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    page = st.radio(
        "Section",
        ["Vue d'ensemble", "Députés", "Scrutins"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    if page == "Députés":
        genre_opt = st.selectbox("Genre", ["Tous", "Homme", "Femme"])

        # Bornes d'âge dynamiques
        age_range = st.slider(
            "Âge",
            min_value=AGE_MIN,
            max_value=AGE_MAX,
            value=(AGE_MIN, AGE_MAX)
        )

        # Filtre par groupe politique
        groupes_dispo = ["Tous"] + df_g["sigle"].tolist()
        groupe_opt = st.selectbox("Groupe politique", groupes_dispo)

        st.markdown("---")

        # Slider adapté — pas de valeur redondante avec le total
        nb_deputes = st.select_slider(
            "Députés affichés",
            options=[25, 50, 100, 200, 300, "Tous"],
            value=100,
        )

    elif page == "Scrutins":
        sort_opt   = st.selectbox("Résultat", ["Tous", "adopté", "rejeté"])
        annees_all = sorted(df_s["annee"].dropna().unique().astype(int))
        annees_sel = st.multiselect("Années", annees_all, default=annees_all)

    st.markdown("---")

    st.markdown(
        "<div class='author-card'>"
        "<div style='font-size:0.78rem;font-weight:600;"
        "margin-bottom:0.3rem;'>Samir NZAMBA</div>"
        "<div style='font-size:0.7rem;opacity:0.65;line-height:1.6;'>"
        "Mastère DPIA 1<br>"
        "Directeur de Projet IA<br>"
        "L'École Multimédia · Paris<br>"
        "Projet #2 · Infrastructure Data Cloud"
        "</div></div>",
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.68rem;opacity:0.45;line-height:1.9;'>"
        "Source · data.assemblee-nationale.fr<br>"
        "API officielle + scraping HTML<br>"
        "Licence Ouverte / Open Licence<br>"
        "Pipeline ETL · mise à jour quotidienne"
        "</div>",
        unsafe_allow_html=True
    )


# ═══════════════════════════════════════════════════════════════════
# VUE D'ENSEMBLE
# ═══════════════════════════════════════════════════════════════════

if page == "Vue d'ensemble":

    adopte_pct = df_s["adopte"].mean() * 100
    femmes_pct = (df_d["civilite"] == "Mme").mean() * 100
    rejete_pct = 100 - adopte_pct
    date_max   = df_s["date"].max().strftime("%d/%m/%Y")

    st.markdown(f"""
    <div class="page-banner">
        <div>
            <div class="banner-title">Assemblée nationale française</div>
            <div class="banner-desc">
                Analyse des données parlementaires · 17e législature
                · {NB_DEPUTES} députés actifs · {NB_SCRUTINS:,} scrutins publics
            </div>
        </div>
        <div class="banner-badge">● Données au {date_max}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs ──────────────────────────────────────────────────────
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Députés actifs", f"{NB_DEPUTES}",
              "17e législature")
    k2.metric("Scrutins publics", f"{NB_SCRUTINS:,}",
              "juil. 2024 — mars 2026")
    k3.metric("Taux d'adoption", f"{adopte_pct:.1f} %",
              f"{df_s['adopte'].sum():,} adoptés")
    k4.metric("Femmes à l'AN", f"{femmes_pct:.1f} %",
              f"{(df_d['civilite']=='Mme').sum()} élues")
    k5.metric("Âge médian", f"{int(df_d['age'].median())} ans",
              f"moy. {df_d['age'].mean():.1f} ans")
    k6.metric("Participation", f"{df_s['taux_participation'].mean():.1f} %",
              "par scrutin")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Activité mensuelle ────────────────────────────────────────
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("### Activité législative mensuelle")
    st.caption(
        "Nombre de scrutins publics (barres) et taux de participation "
        "moyen (courbe) · par mois depuis juillet 2024"
    )

    df_mois = (
        df_s.groupby(df_s["date"].dt.to_period("M"))
        .agg(nb=("uid","count"),
             participation=("taux_participation","mean"))
        .reset_index()
    )
    df_mois["date"]         = df_mois["date"].dt.to_timestamp()
    df_mois["particip_pct"] = df_mois["participation"].round(1)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=df_mois["date"], y=df_mois["nb"],
        name="Scrutins",
        marker_color=BLEU, marker_opacity=0.82,
        marker_line=dict(color="rgba(0,0,0,0)"),
        hovertemplate="<b>%{x|%b %Y}</b><br>%{y} scrutins<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df_mois["date"], y=df_mois["particip_pct"],
        name="Participation (%)", mode="lines+markers",
        line=dict(color=ROUGE, width=2.5, shape="spline"),
        marker=dict(size=7, color=ROUGE,
                    line=dict(color="white", width=2)),
        hovertemplate="<b>%{x|%b %Y}</b><br>%{y:.1f} %<extra></extra>",
    ), secondary_y=True)
    fig.update_layout(**plo(
        height=340,
        legend=dict(orientation="h", y=1.08,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=12))
    ))
    fig.update_xaxes(**ax())
    fig.update_yaxes(title_text="Nombre de scrutins",
                     gridcolor="#f4f6fb", secondary_y=False)
    fig.update_yaxes(title_text="Participation (%)",
                     showgrid=False, secondary_y=True)
    chart(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("### Résultats des scrutins")
        st.caption("Adoptés vs rejetés · 17e législature")

        sc = df_s["sort"].value_counts().reset_index()
        sc.columns = ["sort", "nb"]
        sc["pct"] = (sc["nb"] / sc["nb"].sum() * 100).round(1)

        fig = go.Figure()
        for _, row in sc.iterrows():
            c = BLEU if row["sort"] == "adopté" else ROUGE
            fig.add_trace(go.Bar(
                x=[row["sort"]], y=[row["nb"]],
                name=row["sort"],
                marker_color=c, marker_opacity=0.88,
                marker_line=dict(color="rgba(0,0,0,0)"),
                text=f"<b>{row['pct']} %</b>",
                textposition="outside",
                textfont=dict(size=15, color="#0a1628", family=FONT),
                hovertemplate=(
                    f"<b>{row['sort'].capitalize()}</b>"
                    f"<br>{row['nb']:,} scrutins"
                    f"<br>{row['pct']} % du total<extra></extra>"
                ),
            ))
        fig.update_layout(**plo(height=300, showlegend=False, bargap=0.5))
        fig.update_xaxes(**ax(tickfont=dict(size=12, color="#374151")))
        fig.update_yaxes(**ay())
        chart(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("### Composition de l'hémicycle")
        st.caption(f"Répartition hommes / femmes · {NB_DEPUTES} députés actifs")

        civ = df_d["civilite"].value_counts().reset_index()
        civ.columns = ["civilite", "nb"]
        civ["label"] = civ["civilite"].map(
            {"M.": "Hommes", "Mme": "Femmes"}
        )

        fig = go.Figure(go.Pie(
            labels=civ["label"], values=civ["nb"],
            hole=0.65,
            marker=dict(
                colors=[BLEU, ROUGE],
                line=dict(color="white", width=4)
            ),
            textinfo="percent+label",
            textfont=dict(size=12, color="white", family=FONT),
            insidetextorientation="radial",
            hovertemplate=(
                "<b>%{label}</b><br>"
                "%{value:,} députés<br>"
                "%{percent:.1%}<extra></extra>"
            ),
            rotation=90,
            pull=[0.03, 0.03],
        ))
        fig.update_layout(**plo(
            height=300, showlegend=False,
            annotations=[dict(
                text=(
                    f"<b>{femmes_pct:.0f} %</b>"
                    "<br><span style='font-size:11px;"
                    "color:#64748b'>femmes</span>"
                ),
                x=0.5, y=0.5, font_size=18, showarrow=False,
                font=dict(color="#0a1628", family=FONT)
            )]
        ))
        chart(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_c:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("### Taux de participation")
        st.caption("Distribution sur l'ensemble des scrutins")

        moy = df_s["taux_participation"].mean()
        med = df_s["taux_participation"].median()

        fig = go.Figure(go.Histogram(
            x=df_s["taux_participation"].dropna(),
            nbinsx=28,
            name="Scrutins",
            marker_color=BLEU_C, marker_opacity=0.85,
            marker_line=dict(color="white", width=0.8),
            hovertemplate=(
                "Taux : %{x:.1f} %<br>"
                "Scrutins : %{y}<extra></extra>"
            ),
        ))
        fig.add_vline(x=moy, line_dash="dot",
                      line_color=ROUGE, line_width=2,
                      annotation_text=f"Moy. {moy:.1f} %",
                      annotation_font=dict(size=11, color=ROUGE,
                                           family=FONT),
                      annotation_position="top right")
        fig.add_vline(x=med, line_dash="dash",
                      line_color=GRIS, line_width=1.5,
                      annotation_text=f"Méd. {med:.1f} %",
                      annotation_font=dict(size=10, color=GRIS,
                                           family=FONT),
                      annotation_position="top left")
        fig.update_layout(**plo(height=300))
        fig.update_xaxes(**ax(title_text="Taux de participation (%)"))
        fig.update_yaxes(**ay(title_text="Nombre de scrutins"))
        chart(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Répartition par groupe ────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("### Composition par groupe politique")
    st.caption(
        f"Nombre de sièges par groupe · {NB_DEPUTES} députés actifs "
        f"· 17e législature"
    )

    groupes_count = (
        df_d.groupby("groupe_sigle")
        .size()
        .reset_index(name="nb")
        .sort_values("nb", ascending=False)
    )
    groupes_count = groupes_count.merge(
        df_g[["sigle", "nom"]], left_on="groupe_sigle",
        right_on="sigle", how="left"
    )
    groupes_count["couleur"] = groupes_count["groupe_sigle"].map(
        COULEURS_GROUPES
    ).fillna(BLEU_C)
    groupes_count["pct"] = (
        groupes_count["nb"] / groupes_count["nb"].sum() * 100
    ).round(1)

    fig = go.Figure(go.Bar(
        x=groupes_count["groupe_sigle"],
        y=groupes_count["nb"],
        marker_color=groupes_count["couleur"].tolist(),
        marker_opacity=0.88,
        marker_line=dict(color="rgba(0,0,0,0)"),
        text=[f"{n}<br>{p} %" for n, p in
              zip(groupes_count["nb"], groupes_count["pct"])],
        textposition="outside",
        textfont=dict(size=10.5, color="#374151", family=FONT),
        customdata=groupes_count[["nom", "pct"]].values,
        hovertemplate=(
            "<b>%{x}</b> — %{customdata[0]}<br>"
            "%{y} sièges · %{customdata[1]} %<extra></extra>"
        ),
    ))
    fig.update_layout(**plo(height=360, showlegend=False))
    fig.update_xaxes(**ax(tickfont=dict(size=11)))
    fig.update_yaxes(**ay(title_text="Nombre de sièges"))
    chart(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Insights ──────────────────────────────────────────────────
    st.markdown("### Points d'analyse")
    st.caption(
        "Lecture synthétique des principales tendances "
        "de la 17e législature"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    ci1, ci2, ci3 = st.columns(3)
    with ci1:
        st.info(
            f"**{rejete_pct:.1f} % des scrutins rejetés** : "
            f"un niveau inédit sous la Ve République, témoignant "
            f"d'une majorité particulièrement fragile depuis "
            f"juillet 2024."
        )
    with ci2:
        st.info(
            f"**{femmes_pct:.1f} % de femmes** parmi les "
            f"{NB_DEPUTES} députés actifs. Leur âge médian est "
            f"inférieur de plusieurs années à celui de leurs "
            f"collègues masculins."
        )
    with ci3:
        st.info(
            f"**{df_s['taux_participation'].mean():.1f} % de "
            f"participation** en moyenne, avec un maximum de "
            f"{df_s['taux_participation'].max():.1f} %. "
            f"L'absentéisme reste un marqueur structurel "
            f"de cette législature."
        )


# ═══════════════════════════════════════════════════════════════════
# DÉPUTÉS
# ═══════════════════════════════════════════════════════════════════

elif page == "Députés":

    st.markdown(f"""
    <div class="page-banner">
        <div>
            <div class="banner-title">Profil des députés</div>
            <div class="banner-desc">
                Démographie, parcours professionnels et origines
                géographiques · {NB_DEPUTES} députés actifs
                · 17e législature
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df = df_d.copy()
    if genre_opt != "Tous":
        df = df[df["genre"] == genre_opt]
    df = df[(df["age"] >= age_range[0]) & (df["age"] <= age_range[1])]
    if groupe_opt != "Tous":
        df = df[df["groupe_sigle"] == groupe_opt]

    st.caption(
        f"{len(df):,} député{'s' if len(df) > 1 else ''} "
        f"dans la sélection."
    )
    st.markdown("<br>", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Sélection", f"{len(df):,}", "députés")
    k2.metric(
        "Âge médian",
        f"{int(df['age'].median())} ans"
        if df["age"].notna().any() else "—",
        f"moy. {df['age'].mean():.1f} ans"
        if df["age"].notna().any() else ""
    )
    k3.metric(
        "Professions",
        f"{nettoyer_serie(df['profession']).dropna().nunique()}",
        "métiers déclarés"
    )
    k4.metric(
        "Villes de naissance",
        f"{nettoyer_serie(df['lieu_naissance']).dropna().nunique()}",
        "communes représentées"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("### Professions déclarées avant le mandat")
        st.caption(
            "Top 15 · catégories socioprofessionnelles avant "
            "l'entrée au Parlement"
        )

        top_p = (
            nettoyer_serie(df["profession"])
            .dropna()
            .value_counts()
            .head(15)
            .reset_index()
        )
        top_p.columns = ["profession", "nb"]
        max_nb = top_p["nb"].max() if not top_p.empty else 1

        fig = go.Figure(go.Bar(
            x=top_p["nb"],
            y=top_p["profession"],
            orientation="h",
            marker=dict(
                color=top_p["nb"],
                colorscale=COLORSCALE_BLEU,
                showscale=False,
                line=dict(color="rgba(0,0,0,0)"),
            ),
            text=top_p["nb"],
            textposition="outside",
            textfont=dict(size=11, color=GRIS, family=FONT),
            hovertemplate=(
                "<b>%{y}</b><br>%{x} député·e·s<extra></extra>"
            ),
        ))
        fig.update_layout(**plo(height=500))
        fig.update_xaxes(**ax(range=[0, max_nb * 1.18]))
        fig.update_yaxes(
            categoryorder="total ascending",
            gridcolor="rgba(0,0,0,0)",
            tickfont=dict(size=10.5, color="#374151")
        )
        chart(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("### Distribution des âges par genre")
        st.caption("Violin plot · médiane, moyenne et dispersion")

        df_box = df[df["genre"].notna()]
        fig = go.Figure()
        for genre, color in [("Homme", BLEU), ("Femme", ROUGE)]:
            data = df_box[df_box["genre"] == genre]["age"].dropna()
            if not data.empty:
                fig.add_trace(go.Violin(
                    y=data, name=genre,
                    box_visible=True,
                    meanline_visible=True,
                    fillcolor=color,
                    opacity=0.6,
                    line_color=color,
                    line_width=1.5,
                    points="outliers",
                    marker=dict(color=color, size=3, opacity=0.4,
                                line=dict(color="white", width=0.5)),
                    hovertemplate=(
                        f"<b>{genre}</b><br>"
                        "Âge : %{y}<extra></extra>"
                    ),
                ))
        fig.update_layout(**plo(
            height=500,
            legend=dict(orientation="h", y=1.04,
                        bgcolor="rgba(0,0,0,0)",
                        font=dict(size=11))
        ))
        fig.update_xaxes(**ax())
        fig.update_yaxes(**ay(title_text="Âge"))
        chart(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Répartition par groupe ────────────────────────────────────
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("### Répartition par groupe politique")
    st.caption("Nombre de député·e·s par groupe · sélection active")

    if not df.empty:
        gp_sel = (
            df.groupby("groupe_sigle")
            .size()
            .reset_index(name="nb")
            .sort_values("nb", ascending=False)
        )
        gp_sel["couleur"] = gp_sel["groupe_sigle"].map(
            COULEURS_GROUPES
        ).fillna(BLEU_C)

        fig = go.Figure(go.Bar(
            x=gp_sel["groupe_sigle"],
            y=gp_sel["nb"],
            marker_color=gp_sel["couleur"].tolist(),
            marker_opacity=0.88,
            marker_line=dict(color="rgba(0,0,0,0)"),
            text=gp_sel["nb"],
            textposition="outside",
            textfont=dict(size=11, color="#374151", family=FONT),
            hovertemplate=(
                "<b>%{x}</b><br>%{y} député·e·s<extra></extra>"
            ),
        ))
        fig.update_layout(**plo(height=300, showlegend=False))
        fig.update_xaxes(**ax())
        fig.update_yaxes(**ay(title_text="Nombre de député·e·s"))
        chart(fig)
    else:
        st.caption("Aucun député dans la sélection.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Villes de naissance ───────────────────────────────────────
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("### Villes de naissance les plus représentées")
    st.caption("Top 20 communes · nombre de député·e·s nés sur place")

    top_v = (
        nettoyer_serie(df["lieu_naissance"])
        .dropna()
        .value_counts()
        .head(20)
        .reset_index()
    )
    top_v.columns = ["ville", "nb"]

    if not top_v.empty:
        fig = go.Figure(go.Bar(
            x=top_v["ville"], y=top_v["nb"],
            marker=dict(
                color=top_v["nb"],
                colorscale=COLORSCALE_BLEU,
                showscale=False,
                line=dict(color="rgba(0,0,0,0)"),
            ),
            text=top_v["nb"],
            textposition="outside",
            textfont=dict(size=10.5, color=GRIS, family=FONT),
            hovertemplate=(
                "<b>%{x}</b><br>%{y} député·e·s<extra></extra>"
            ),
        ))
        fig.update_layout(**plo(height=310))
        fig.update_xaxes(**ax(tickangle=-38, tickfont=dict(size=10)))
        fig.update_yaxes(**ay())
        chart(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Répertoire ────────────────────────────────────────────────
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)

    col_titre, col_info = st.columns([3, 2])
    with col_titre:
        st.markdown("### Répertoire des députés")
        st.caption(
            "Triez par colonne · nombre affiché réglable dans la sidebar"
        )
    with col_info:
        limite   = None if nb_deputes == "Tous" else int(nb_deputes)
        total    = len(df)
        affiches = min(limite, total) if limite else total
        st.markdown(
            f"<div style='text-align:right;padding-top:0.6rem;"
            f"font-size:0.78rem;color:#94a3b8;'>"
            f"Affichage de <b style='color:#0a1628'>{affiches:,}</b>"
            f" sur <b style='color:#0a1628'>{total:,}</b> "
            f"député{'s' if total > 1 else ''}"
            f"</div>",
            unsafe_allow_html=True
        )

    df_affichage = df[[
        "nom_complet", "civilite", "age",
        "groupe_sigle", "lieu_naissance", "profession"
    ]].copy().sort_values("nom_complet")

    if limite:
        df_affichage = df_affichage.head(limite)

    for col in df_affichage.columns:
        df_affichage[col] = df_affichage[col].apply(nettoyer_affichage)

    df_affichage["age"] = df_affichage["age"].apply(
        lambda x: f"{int(float(x))} ans" if x != "—" else "—"
    )

    hauteur = min(max(affiches * 35 + 60, 250), 600)

    st.dataframe(
        df_affichage.rename(columns={
            "nom_complet":    "Nom",
            "civilite":       "Civ.",
            "age":            "Âge",
            "groupe_sigle":   "Groupe",
            "lieu_naissance": "Lieu de naissance",
            "profession":     "Profession avant mandat",
        }).reset_index(drop=True),
        use_container_width=True,
        height=hauteur,
        column_config={
            "Nom":                     st.column_config.TextColumn(width="medium"),
            "Civ.":                    st.column_config.TextColumn(width="small"),
            "Âge":                     st.column_config.TextColumn(width="small"),
            "Groupe":                  st.column_config.TextColumn(width="small"),
            "Lieu de naissance":       st.column_config.TextColumn(width="medium"),
            "Profession avant mandat": st.column_config.TextColumn(width="large"),
        }
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# SCRUTINS
# ═══════════════════════════════════════════════════════════════════

elif page == "Scrutins":

    st.markdown(f"""
    <div class="page-banner">
        <div>
            <div class="banner-title">Scrutins publics</div>
            <div class="banner-desc">
                Votes en séance publique · 17e législature
                · {NB_SCRUTINS:,} scrutins · juil. 2024 — mars 2026
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df = df_s.copy()
    if sort_opt != "Tous":
        df = df[df["sort"] == sort_opt]
    if annees_sel:
        df = df[df["annee"].isin(annees_sel)]

    st.caption(
        f"{len(df):,} scrutin{'s' if len(df) > 1 else ''} "
        f"dans la sélection."
    )
    st.markdown("<br>", unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Scrutins", f"{len(df):,}", "sélectionnés")
    k2.metric("Adoptés", f"{df['adopte'].sum():,}",
              f"{df['adopte'].mean()*100:.1f} %")
    k3.metric("Rejetés", f"{(~df['adopte']).sum():,}",
              f"{(~df['adopte']).mean()*100:.1f} %")
    k4.metric("Votes pour (moy.)", f"{df['pour'].mean():.0f}",
              "par scrutin")
    k5.metric("Participation moy.",
              f"{df['taux_participation'].mean():.1f} %",
              f"max. {df['taux_participation'].max():.1f} %")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("### Évolution mensuelle des scrutins")
    st.caption(
        "Nombre de scrutins publics (barres) et participation "
        "moyenne (courbe) · par mois"
    )

    df_mois = (
        df.groupby(df["date"].dt.to_period("M"))
        .agg(nb=("uid","count"),
             participation=("taux_participation","mean"))
        .reset_index()
    )
    df_mois["date"]         = df_mois["date"].dt.to_timestamp()
    df_mois["particip_pct"] = df_mois["participation"].round(1)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=df_mois["date"], y=df_mois["nb"],
        name="Scrutins",
        marker_color=BLEU, marker_opacity=0.82,
        marker_line=dict(color="rgba(0,0,0,0)"),
        hovertemplate="<b>%{x|%b %Y}</b><br>%{y} scrutins<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df_mois["date"], y=df_mois["particip_pct"],
        name="Participation (%)", mode="lines+markers",
        line=dict(color=ROUGE, width=2.5, shape="spline"),
        marker=dict(size=7, color=ROUGE,
                    line=dict(color="white", width=2)),
        hovertemplate="<b>%{x|%b %Y}</b><br>%{y:.1f} %<extra></extra>",
    ), secondary_y=True)
    fig.update_layout(**plo(
        height=320,
        legend=dict(orientation="h", y=1.08,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=12))
    ))
    fig.update_xaxes(**ax())
    fig.update_yaxes(title_text="Nombre de scrutins",
                     gridcolor="#f4f6fb", secondary_y=False)
    fig.update_yaxes(title_text="Participation (%)",
                     showgrid=False, secondary_y=True)
    chart(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("### Pour vs Contre")
        st.caption(
            "Un point par scrutin · couleur selon le résultat · "
            "survolez pour le détail"
        )

        fig = go.Figure()
        for sv, color, name in [
            ("rejeté", ROUGE, "Rejeté"),
            ("adopté", BLEU,  "Adopté"),
        ]:
            sub = df[df["sort"] == sv]
            fig.add_trace(go.Scatter(
                x=sub["pour"], y=sub["contre"],
                mode="markers", name=name,
                marker=dict(color=color, size=5, opacity=0.45,
                            line=dict(color="white", width=0.5)),
                customdata=sub[[
                    "titre_court", "date", "taux_participation"
                ]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Date : %{customdata[1]|%d/%m/%Y}<br>"
                    "Pour : %{x} · Contre : %{y}<br>"
                    "Participation : %{customdata[2]:.1f} %"
                    "<extra></extra>"
                ),
            ))
        fig.update_layout(**plo(
            height=380,
            legend=dict(orientation="h", y=1.05,
                        bgcolor="rgba(0,0,0,0)", font=dict(size=11))
        ))
        fig.update_xaxes(**ax(title_text="Votes pour"))
        fig.update_yaxes(**ay(title_text="Votes contre"))
        chart(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("### Types de scrutins")
        st.caption("Répartition par catégorie · top 8 par volume")

        tc = df["type_vote"].value_counts().head(8).reset_index()
        tc.columns = ["type_vote", "nb"]

        fig = go.Figure(go.Bar(
            x=tc["nb"], y=tc["type_vote"],
            orientation="h",
            marker=dict(
                color=tc["nb"],
                colorscale=COLORSCALE_BLEU,
                showscale=False,
                line=dict(color="rgba(0,0,0,0)"),
            ),
            text=tc["nb"],
            textposition="outside",
            textfont=dict(size=11, color=GRIS, family=FONT),
            hovertemplate=(
                "<b>%{y}</b><br>%{x} scrutins<extra></extra>"
            ),
        ))
        fig.update_layout(**plo(height=380))
        fig.update_xaxes(**ax())
        fig.update_yaxes(
            categoryorder="total ascending",
            tickfont=dict(size=10.5),
            gridcolor="rgba(0,0,0,0)"
        )
        chart(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("### Scrutins les plus serrés")
    st.caption(
        "Classés par écart minimal entre votes pour et contre · "
        "révélateurs des tensions politiques au sein de l'hémicycle"
    )

    df["ecart"] = abs(df["pour"] - df["contre"])
    top10 = (
        df.nsmallest(10, "ecart")
        [["date","titre_court","pour","contre","ecart","sort"]]
        .copy()
    )
    top10["date"]        = top10["date"].dt.strftime("%d/%m/%Y")
    top10["titre_court"] = top10["titre_court"].apply(nettoyer_affichage)
    top10["sort"]        = top10["sort"].apply(
        lambda x: "Adopté" if x == "adopté" else "Rejeté"
    )

    st.dataframe(
        top10.rename(columns={
            "date":        "Date",
            "titre_court": "Objet du scrutin",
            "pour":        "Pour",
            "contre":      "Contre",
            "ecart":       "Écart",
            "sort":        "Résultat",
        }).reset_index(drop=True),
        use_container_width=True,
        height=390,
        column_config={
            "Date":             st.column_config.TextColumn(width="small"),
            "Objet du scrutin": st.column_config.TextColumn(width="large"),
            "Pour":             st.column_config.NumberColumn(width="small"),
            "Contre":           st.column_config.NumberColumn(width="small"),
            "Écart":            st.column_config.NumberColumn(width="small"),
            "Résultat":         st.column_config.TextColumn(width="small"),
        }
    )
    st.markdown('</div>', unsafe_allow_html=True)