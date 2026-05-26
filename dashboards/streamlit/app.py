"""
Dashboard Streamlit - Assemblée nationale française, 17e législature.
Projet #2 - Infrastructure Data Cloud · DPIA 1
Auteur : Samir NZAMBA · Fonderie de l'Image

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
import os
from dotenv import load_dotenv
load_dotenv()

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
[data-testid="stSidebar"] .stMultiSelect svg { fill: #ffffff !important; }
[data-testid="stSidebar"] ul[role="listbox"],
[data-testid="stSidebar"] div[role="listbox"] {
    background-color: #0d2b8e !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}
[data-testid="stSidebar"] ul[role="listbox"] li,
[data-testid="stSidebar"] div[role="listbox"] div { color: #ffffff !important; }

[data-testid="metric-container"] {
    border-radius: 12px;
    padding: 1.1rem 1.3rem 1rem 1.3rem;
    border: 1px solid rgba(128,128,128,0.15);
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
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
    border-radius: 12px;
    border: 1px solid rgba(128,128,128,0.15);
    padding: 1.25rem 1.5rem 0.75rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
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
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=12),
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
        linecolor="rgba(128,128,128,0.2)",
        tickcolor="rgba(0,0,0,0)",
        tickfont=dict(size=11),
        title_font=dict(size=11),
    )
    d.update(kw)
    return d

def ay(**kw):
    d = dict(
        gridcolor="rgba(128,128,128,0.12)",
        gridwidth=1,
        linecolor="rgba(0,0,0,0)",
        tickcolor="rgba(0,0,0,0)",
        tickfont=dict(size=11),
        title_font=dict(size=11),
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
        return "-"
    if isinstance(val, float) and math.isnan(val):
        return "-"
    if isinstance(val, dict):
        if "@xsi:nil" in val or "@xmlns:xsi" in val:
            return "-"
        for k in ("#text", "value", "text"):
            if k in val:
                return str(val[k])
        return "-"
    if isinstance(val, str):
        v = val.strip()
        if v == "" or v.lower() == "none":
            return "-"
        if "@xsi:nil" in v or "@xmlns:xsi" in v:
            return "-"
    return val

def nettoyer_serie(serie: pd.Series) -> pd.Series:
    return serie.apply(nettoyer_affichage).replace("-", None)


# ─── Données ──────────────────────────────────────────────────────────────────

@st.cache_resource
def get_engine():
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@localhost:5432/"
        f"{os.getenv('POSTGRES_DB')}"
    )

@st.cache_data
def charger():
    eng = get_engine()

    # Données brutes - tous les enregistrements sans filtre
    d_brut = pd.read_sql("SELECT * FROM deputes", eng)

    # Données propres - uniquement les 577 actifs avec groupe
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

    return d, d_brut, s, g


@st.cache_data
def charger_pipeline_stats():
    """Charge les statistiques de la dernière exécution du pipeline."""
    eng = get_engine()
    try:
        df = pd.read_sql(
            "SELECT * FROM pipeline_stats ORDER BY run_date DESC LIMIT 1",
            eng
        )
        if df.empty:
            return None
        return df.iloc[0]
    except Exception:
        return None


df_d, df_d_brut, df_s, df_g = charger()
pipeline_stats = charger_pipeline_stats()

AGE_MIN     = int(df_d["age"].dropna().min())
AGE_MAX     = int(df_d["age"].dropna().max())
NB_DEPUTES  = len(df_d)
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
    ["Vue d'ensemble", "Députés", "Scrutins", "Pipeline"],
    label_visibility="collapsed"
    )

    st.markdown("---")

    if page == "Députés":
        genre_opt = st.selectbox("Genre", ["Tous", "Homme", "Femme"])
        age_range = st.slider(
            "Âge",
            min_value=AGE_MIN,
            max_value=AGE_MAX,
            value=(AGE_MIN, AGE_MAX)
        )
        groupes_dispo = ["Tous"] + df_g["sigle"].tolist()
        groupe_opt = st.selectbox("Groupe politique", groupes_dispo)
        st.markdown("---")
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
        "Fonderie de l'Image<br>"
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

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Députés actifs", f"{NB_DEPUTES}", "17e législature")
    k2.metric("Scrutins publics", f"{NB_SCRUTINS:,}", "juil. 2024 - mars 2026")
    k3.metric("Taux d'adoption", f"{adopte_pct:.1f} %",
              f"{df_s['adopte'].sum():,} adoptés")
    k4.metric("Femmes à l'AN", f"{femmes_pct:.1f} %",
              f"{(df_d['civilite']=='Mme').sum()} élues")
    k5.metric("Âge médian", f"{int(df_d['age'].median())} ans",
              f"moy. {df_d['age'].mean():.1f} ans")
    k6.metric("Participation", f"{df_s['taux_participation'].mean():.1f} %",
              "par scrutin")

    st.markdown("<br>", unsafe_allow_html=True)

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
                     gridcolor="rgba(128,128,128,0.12)", secondary_y=False)
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
                textfont=dict(size=15, family=FONT),
                hovertemplate=(
                    f"<b>{row['sort'].capitalize()}</b>"
                    f"<br>{row['nb']:,} scrutins"
                    f"<br>{row['pct']} % du total<extra></extra>"
                ),
            ))
        fig.update_layout(**plo(height=300, showlegend=False, bargap=0.5))
        fig.update_xaxes(**ax(tickfont=dict(size=12)))
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
                    "<br><span style='font-size:11px;'>femmes</span>"
                ),
                x=0.5, y=0.5, font_size=18, showarrow=False,
                font=dict(family=FONT)
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
                      annotation_font=dict(size=11, color=ROUGE, family=FONT),
                      annotation_position="top right")
        fig.add_vline(x=med, line_dash="dash",
                      line_color=GRIS, line_width=1.5,
                      annotation_text=f"Méd. {med:.1f} %",
                      annotation_font=dict(size=10, color=GRIS, family=FONT),
                      annotation_position="top left")
        fig.update_layout(**plo(height=300))
        fig.update_xaxes(**ax(title_text="Taux de participation (%)"))
        fig.update_yaxes(**ay(title_text="Nombre de scrutins"))
        chart(fig)
        st.markdown('</div>', unsafe_allow_html=True)

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
        textfont=dict(size=10.5, family=FONT),
        customdata=groupes_count[["nom", "pct"]].values,
        hovertemplate=(
            "<b>%{x}</b> - %{customdata[0]}<br>"
            "%{y} sièges · %{customdata[1]} %<extra></extra>"
        ),
    ))
    fig.update_layout(**plo(height=360, showlegend=False))
    fig.update_xaxes(**ax(tickfont=dict(size=11)))
    fig.update_yaxes(**ay(title_text="Nombre de sièges"))
    chart(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
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
        if df["age"].notna().any() else "-",
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
            textfont=dict(size=11, family=FONT),
            hovertemplate=(
                "<b>%{y}</b><br>%{x} député·e·s<extra></extra>"
            ),
        ))
        fig.update_layout(**plo(height=500))
        fig.update_xaxes(**ax(range=[0, max_nb * 1.18]))
        fig.update_yaxes(
            categoryorder="total ascending",
            gridcolor="rgba(0,0,0,0)",
            tickfont=dict(size=10.5)
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
            textfont=dict(size=11, family=FONT),
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
            textfont=dict(size=10.5, family=FONT),
            hovertemplate=(
                "<b>%{x}</b><br>%{y} député·e·s<extra></extra>"
            ),
        ))
        fig.update_layout(**plo(height=310))
        fig.update_xaxes(**ax(tickangle=-38, tickfont=dict(size=10)))
        fig.update_yaxes(**ay())
        chart(fig)
    st.markdown('</div>', unsafe_allow_html=True)

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
            f"font-size:0.78rem;'>"
            f"Affichage de <b>{affiches:,}</b>"
            f" sur <b>{total:,}</b> "
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
        lambda x: f"{int(float(x))} ans" if x != "-" else "-"
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
                · {NB_SCRUTINS:,} scrutins · juil. 2024 - mars 2026
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Filtres ──────────────────────────────────────────────────
    df = df_s.copy()
    if sort_opt != "Tous":
        df = df[df["sort"] == sort_opt]
    if annees_sel:
        df = df[df["annee"].isin(annees_sel)]

    # Filtre type de scrutin
    types_dispo = ["Tous"] + sorted(
        df_s["type_vote"].dropna().unique().tolist()
    )
    col_f1, col_f2 = st.columns([2, 3])
    with col_f1:
        type_opt = st.selectbox(
            "Type de scrutin",
            types_dispo,
            key="type_scrutin"
        )
    with col_f2:
        recherche = st.text_input(
            "Rechercher dans les titres",
            placeholder="ex. budget, retraite, motion...",
            key="recherche_scrutin"
        )

    if type_opt != "Tous":
        df = df[df["type_vote"] == type_opt]
    if recherche.strip():
        df = df[
            df["titre"].fillna("").str.lower().str.contains(
                recherche.strip().lower(), regex=False
            ) |
            df["titre_court"].fillna("").str.lower().str.contains(
                recherche.strip().lower(), regex=False
            )
        ]

    st.caption(
        f"{len(df):,} scrutin{'s' if len(df) > 1 else ''} "
        f"dans la sélection."
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── KPIs ─────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Scrutins", f"{len(df):,}", "sélectionnés")
    k2.metric("Adoptés", f"{df['adopte'].sum():,}",
              f"{df['adopte'].mean()*100:.1f} %" if len(df) > 0 else "0 %")
    k3.metric("Rejetés", f"{(~df['adopte']).sum():,}",
              f"{(~df['adopte']).mean()*100:.1f} %" if len(df) > 0 else "0 %")
    k4.metric("Votes pour (moy.)",
              f"{df['pour'].mean():.0f}" if len(df) > 0 else "-",
              "par scrutin")
    k5.metric("Participation moy.",
              f"{df['taux_participation'].mean():.1f} %" if len(df) > 0 else "-",
              f"max. {df['taux_participation'].max():.1f} %" if len(df) > 0 else "")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Export CSV ───────────────────────────────────────────────
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    col_titre_export, col_btn_export = st.columns([3, 1])
    with col_titre_export:
        st.markdown("### Données filtrées")
        st.caption(
            "Exportez les scrutins de la sélection courante "
            "pour vos analyses dans R, Python ou Excel."
        )
    with col_btn_export:
        st.markdown("<br>", unsafe_allow_html=True)
        df_export = df[[
            "date", "titre", "titre_court", "type_vote",
            "sort", "pour", "contre", "abstention",
            "non_votant", "total_votants", "taux_participation"
        ]].copy()
        df_export["date"] = df_export["date"].dt.strftime("%Y-%m-%d")
        csv = df_export.to_csv(index=False, encoding="utf-8")
        st.download_button(
            label="Télécharger CSV",
            data=csv,
            file_name="scrutins_selection.csv",
            mime="text/csv",
            use_container_width=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Évolution mensuelle ──────────────────────────────────────
    if len(df) > 0:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("### Évolution mensuelle des scrutins")
        st.caption(
            "Nombre de scrutins (barres) et participation "
            "moyenne (courbe) par mois"
        )

        df_mois = (
            df.groupby(df["date"].dt.to_period("M"))
            .agg(nb=("uid", "count"),
                 participation=("taux_participation", "mean"))
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
                         gridcolor="rgba(128,128,128,0.12)",
                         secondary_y=False)
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
                if not sub.empty:
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
            st.markdown("### Participation par type de scrutin")
            st.caption(
                "Taux de participation moyen selon la nature du vote "
                "- utile pour identifier les textes qui mobilisent"
            )

            part_type = (
                df.groupby("type_vote")["taux_participation"]
                .agg(["mean", "count"])
                .reset_index()
                .rename(columns={"mean": "participation_moy", "count": "nb"})
                .sort_values("participation_moy", ascending=True)
                .head(10)
            )

            fig = go.Figure(go.Bar(
                x=part_type["participation_moy"].round(1),
                y=part_type["type_vote"],
                orientation="h",
                marker=dict(
                    color=part_type["participation_moy"],
                    colorscale=COLORSCALE_BLEU,
                    showscale=False,
                    line=dict(color="rgba(0,0,0,0)"),
                ),
                text=[
                    f"{v:.1f} % ({n} scrutins)"
                    for v, n in zip(
                        part_type["participation_moy"],
                        part_type["nb"]
                    )
                ],
                textposition="outside",
                textfont=dict(size=10, family=FONT),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Participation moy. : %{x:.1f} %<extra></extra>"
                ),
            ))
            fig.update_layout(**plo(height=380))
            fig.update_xaxes(**ax(title_text="Participation moyenne (%)"))
            fig.update_yaxes(
                categoryorder="total ascending",
                tickfont=dict(size=10),
                gridcolor="rgba(0,0,0,0)"
            )
            chart(fig)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Tableau des scrutins ──────────────────────────────────
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("### Liste des scrutins")
        st.caption(
            "Triez par colonne · cliquez sur un scrutin pour le détail"
        )

        df["ecart"] = abs(df["pour"] - df["contre"])
        df_table = (
            df[[
                "date", "titre_court", "type_vote",
                "pour", "contre", "ecart", "sort",
                "taux_participation"
            ]]
            .copy()
            .sort_values("date", ascending=False)
        )
        df_table["date"] = df_table["date"].dt.strftime("%d/%m/%Y")
        df_table["sort"] = df_table["sort"].apply(
            lambda x: "Adopté" if x == "adopté" else "Rejeté"
        )
        df_table["titre_court"] = df_table["titre_court"].apply(
            nettoyer_affichage
        )

        hauteur_table = min(max(len(df_table) * 35 + 60, 300), 550)

        st.dataframe(
            df_table.rename(columns={
                "date":               "Date",
                "titre_court":        "Objet",
                "type_vote":          "Type",
                "pour":               "Pour",
                "contre":             "Contre",
                "ecart":              "Écart",
                "sort":               "Résultat",
                "taux_participation": "Participation %",
            }).reset_index(drop=True),
            use_container_width=True,
            height=hauteur_table,
            column_config={
                "Date":          st.column_config.TextColumn(width="small"),
                "Objet":         st.column_config.TextColumn(width="large"),
                "Type":          st.column_config.TextColumn(width="medium"),
                "Pour":          st.column_config.NumberColumn(width="small"),
                "Contre":        st.column_config.NumberColumn(width="small"),
                "Écart":         st.column_config.NumberColumn(width="small"),
                "Résultat":      st.column_config.TextColumn(width="small"),
                "Participation %": st.column_config.NumberColumn(
                    width="small", format="%.1f %%"
                ),
            }
        )
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("Aucun scrutin ne correspond aux filtres sélectionnés.")

# ═══════════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════════

elif page == "Pipeline":

    st.markdown("""
    <div class="page-banner">
        <div>
            <div class="banner-title">Pipeline ETL - Data Lake → Data Warehouse</div>
            <div class="banner-desc">
                Collecte · Transformation · Chargement ·
                Visualisation de la chaîne complète de traitement
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Statistiques dynamiques - dernière exécution du pipeline ─
    if pipeline_stats is None:
        st.error(
            "⚠️ Aucune statistique de pipeline disponible. "
            "Lancez le pipeline ETL pour alimenter les données : "
            "`python etl/pipeline.py`"
        )
        st.stop()

    nb_brut    = int(pipeline_stats["acteurs_bruts"])
    nb_actifs  = int(pipeline_stats["acteurs_retenus"])
    nb_ignores = int(pipeline_stats["acteurs_ignores"])

    # ── KPIs du pipeline ─────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Enregistrements bruts",
              f"{nb_brut:,}",
              "avant filtre - toutes législatures")
    k2.metric("Députés actifs retenus",
              f"{nb_actifs:,}",
              f"−{nb_ignores:,} ignorés")
    k3.metric("Scrutins traités",
              f"{len(df_s):,}",
              "chargés en DWH")
    k4.metric("Groupes politiques",
              f"{len(df_g)}",
              "mappés")
    k5.metric("Taux de complétion",
              f"{df_d.notna().mean().mean()*100:.1f} %",
              "données propres")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Architecture du pipeline ─────────────────────────────────
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("### Architecture du pipeline ETL")
    st.caption(
        "Flux de données de la collecte à la visualisation"
    )

    st.markdown("""
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:separate;
                  border-spacing:0;font-size:0.85rem;">
      <thead>
        <tr>
          <th style="background:#002395;color:white;padding:0.75rem 1rem;
                     border-radius:8px 0 0 0;text-align:center;">
            Extract
          </th>
          <th style="background:#1a1a2e;color:white;padding:0.75rem 1rem;
                     text-align:center;">→</th>
          <th style="background:#4f7ed4;color:white;padding:0.75rem 1rem;
                     text-align:center;">
            Data Lake (MinIO)
          </th>
          <th style="background:#1a1a2e;color:white;padding:0.75rem 1rem;
                     text-align:center;">→</th>
          <th style="background:#2E7D32;color:white;padding:0.75rem 1rem;
                     text-align:center;">
            Transform
          </th>
          <th style="background:#1a1a2e;color:white;padding:0.75rem 1rem;
                     text-align:center;">→</th>
          <th style="background:#DAA520;color:white;padding:0.75rem 1rem;
                     text-align:center;">
            Data Warehouse (PostgreSQL)
          </th>
          <th style="background:#1a1a2e;color:white;padding:0.75rem 1rem;
                     text-align:center;">→</th>
          <th style="background:#C1002A;color:white;padding:0.75rem 1rem;
                     border-radius:0 8px 0 0;text-align:center;">
            Visualisation
          </th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td style="padding:0.75rem 1rem;border:1px solid rgba(128,128,128,0.15);
                     vertical-align:top;">
            API officielle AN<br>
            <span style="opacity:0.6;font-size:0.78rem;">
              ZIP AMO30 - tous acteurs<br>depuis la XIe législature<br>
              ZIP JSON scrutins
            </span><br><br>
            Scraping HTML<br>
            <span style="opacity:0.6;font-size:0.78rem;">
              Groupes politiques
            </span>
          </td>
          <td style="padding:0.75rem;text-align:center;
                     border:1px solid rgba(128,128,128,0.15);"></td>
          <td style="padding:0.75rem 1rem;border:1px solid rgba(128,128,128,0.15);
                     vertical-align:top;">
            Données brutes JSON<br>
            <span style="opacity:0.6;font-size:0.78rem;">
              deputes/raw_YYYY-MM-DD.json<br>
              scrutins/raw_YYYY-MM-DD.json<br>
              groupes/raw_YYYY-MM-DD.json
            </span><br><br>
            <span style="color:#C1002A;font-size:0.78rem;">
              ⚠ {nb_brut:,} acteurs bruts<br>
              ⚠ Valeurs XML brutes<br>
              ⚠ Sans calcul d'âge<br>
              ⚠ Sans mapping groupes<br>
              ⚠ Toutes législatures mélangées
            </span>
          </td>
          <td style="padding:0.75rem;text-align:center;
                     border:1px solid rgba(128,128,128,0.15);"></td>
          <td style="padding:0.75rem 1rem;border:1px solid rgba(128,128,128,0.15);
                     vertical-align:top;">
            DataCleaner<br>
            <span style="opacity:0.6;font-size:0.78rem;">
              etl/transform/cleaner.py
            </span><br><br>
            <span style="color:#2E7D32;font-size:0.78rem;">
              ✓ Filtre 17e législature<br>
              &nbsp;&nbsp;{nb_ignores:,} ignorés<br>
              ✓ Nettoyage @xsi:nil<br>
              ✓ Calcul de l'âge<br>
              ✓ Déduction du genre<br>
              ✓ Mapping groupe→sigle
            </span>
          </td>
          <td style="padding:0.75rem;text-align:center;
                     border:1px solid rgba(128,128,128,0.15);"></td>
          <td style="padding:0.75rem 1rem;border:1px solid rgba(128,128,128,0.15);
                     vertical-align:top;">
            Tables normalisées<br>
            <span style="opacity:0.6;font-size:0.78rem;">
              deputes · scrutins<br>groupes_politiques<br>pipeline_stats
            </span><br><br>
            <span style="color:#2E7D32;font-size:0.78rem;">
              ✓ {nb_actifs:,} députés actifs<br>
              ✓ {nb_s:,} scrutins<br>
              ✓ 12 groupes mappés<br>
              ✓ Données normalisées
            </span>
          </td>
          <td style="padding:0.75rem;text-align:center;
                     border:1px solid rgba(128,128,128,0.15);"></td>
          <td style="padding:0.75rem 1rem;border:1px solid rgba(128,128,128,0.15);
                     vertical-align:top;">
            Streamlit Dashboard<br>
            <span style="opacity:0.6;font-size:0.78rem;">
              Ce dashboard
            </span><br><br>
            Notebooks Jupyter<br>
            <span style="opacity:0.6;font-size:0.78rem;">
              Analyse en 4 actes
            </span><br><br>
            Grafana<br>
            <span style="opacity:0.6;font-size:0.78rem;">
              Monitoring infra
            </span>
          </td>
        </tr>
      </tbody>
    </table>
    </div>
    """.format(
        nb_brut=nb_brut,
        nb_ignores=nb_ignores,
        nb_actifs=nb_actifs,
        nb_s=len(df_s)
    ), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Avant / Après nettoyage ──────────────────────────────────
    # ── Du brut au propre ────────────────────────────────────────
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("### Du brut au propre - pipeline de nettoyage")
    st.caption(
        f"De {nb_brut:,} acteurs bruts (AMO30) à {nb_actifs:,} députés "
        f"actifs enrichis · {nb_ignores:,} ignorés"
    )

    col_funnel, col_delta = st.columns([1, 1])

    with col_funnel:
        fig = go.Figure(go.Funnel(
            y=[
                f"ZIP AMO30 téléchargé<br>{nb_brut:,} acteurs bruts",
                f"Filtre 17e législature<br>{nb_actifs:,} mandats GP actifs",
                f"Nettoyage XML + dates<br>{nb_actifs:,} enregistrements propres",
                f"Enrichissement<br>{nb_actifs:,} députés avec âge, genre, groupe",
            ],
            x=[nb_brut, nb_actifs, nb_actifs, nb_actifs],
            textinfo="value+percent initial",
            textfont=dict(size=11, family=FONT),
            marker=dict(
                color=["#C1002A", "#DAA520", "#4f7ed4", "#2E7D32"],
                line=dict(width=2, color="white")
            ),
            connector=dict(
                line=dict(color="rgba(128,128,128,0.3)", width=1)
            ),
        ))
        fig.update_layout(**plo(
            height=380,
            margin=dict(t=20, b=20, l=10, r=10)
        ))
        chart(fig)

    with col_delta:
        champs = [
            ("Groupe politique",   0,   100, "Absent dans le ZIP · construit par mapping organes"),
            ("Genre",              0,   100, "Absent dans l'API · déduit de la civilité"),
            ("Âge",                0,   100, "Absent dans l'API · calculé depuis date naissance"),
            ("Profession",        62,    78, "Valeurs @xsi:nil nettoyées"),
            ("Lieu de naissance", 95,    95, "Déjà renseigné dans l'API"),
            ("Date naissance",   100,   100, "Déjà renseigné dans l'API"),
            ("Nom / Prénom",     100,   100, "Déjà renseigné dans l'API"),
        ]

        st.markdown("<br>", unsafe_allow_html=True)
        for champ, avant_pct, apres_pct, note in champs:
            delta        = apres_pct - avant_pct
            couleur_delta = "#2E7D32" if delta > 0 else "#757575"
            fleche       = "↑" if delta > 0 else "→"
            st.markdown(f"""
            <div style="margin-bottom:0.85rem;padding:0.75rem 1rem;
                        border-radius:8px;
                        border:1px solid rgba(128,128,128,0.12);">
                <div style="display:flex;justify-content:space-between;
                            align-items:center;margin-bottom:0.3rem;">
                    <span style="font-weight:600;font-size:0.88rem;">
                        {champ}
                    </span>
                    <span style="font-size:0.85rem;font-weight:700;
                                 color:{couleur_delta};">
                        {fleche} {avant_pct}% → {apres_pct}%
                    </span>
                </div>
                <div style="background:rgba(128,128,128,0.1);
                            border-radius:4px;height:6px;
                            margin-bottom:0.3rem;">
                    <div style="background:#C1002A;border-radius:4px;
                                height:6px;width:{avant_pct}%;
                                display:inline-block;"></div>
                </div>
                <div style="background:rgba(128,128,128,0.1);
                            border-radius:4px;height:6px;
                            margin-bottom:0.4rem;">
                    <div style="background:#2E7D32;border-radius:4px;
                                height:6px;width:{apres_pct}%;
                                display:inline-block;"></div>
                </div>
                <div style="font-size:0.75rem;opacity:0.6;">{note}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Fonction est_propre (utilisée plus bas) ──────────────────
    def est_propre(val):
        if val is None:
            return False
        if isinstance(val, float) and pd.isna(val):
            return False
        if isinstance(val, dict):
            return False
        if isinstance(val, str) and (
            "@xsi:nil" in val or "@xmlns:xsi" in val
            or val.strip() == ""
        ):
            return False
        return True

    # ── Étapes de nettoyage ──────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("### Étapes de transformation")
        st.caption("Ce que le pipeline fait concrètement sur les données")

        etapes = [
            ("1", "Filtre 17e législature",
             f"Sur {nb_brut:,} acteurs bruts (AMO30 - toutes législatures "
             f"depuis 1997), seuls les {nb_actifs:,} acteurs avec un mandat "
             f"de groupe politique actif en 17e législature sont retenus "
             f"- {nb_ignores:,} ignorés.",
             "#002395"),
            ("2", "Nettoyage valeurs XML",
             "Les valeurs @xsi:nil retournées par l'API sont "
             "converties en NULL exploitable.",
             "#4f7ed4"),
            ("3", "Conversion des dates",
             "Les dates de naissance sont converties au format "
             "datetime, les formats invalides passent en NaT.",
             "#2E7D32"),
            ("4", "Calcul de l'âge",
             "L'âge est calculé dynamiquement depuis la date "
             "de naissance et validé contre la colonne âge de l'API.",
             "#DAA520"),
            ("5", "Déduction du genre",
             "Le genre est déduit de la civilité (M. → Homme, "
             "Mme → Femme) - non fourni directement par l'API.",
             "#FF8F00"),
            ("6", "Mapping groupe politique",
             "Le sigle du groupe est résolu depuis les organes "
             "actifs du mandat de chaque député.",
             "#C1002A"),
        ]

        for num, titre, desc, color in etapes:
            st.markdown(f"""
            <div style="display:flex;gap:1rem;margin-bottom:1rem;
                        align-items:flex-start;">
                <div style="min-width:2rem;height:2rem;
                            background:{color};border-radius:50%;
                            display:flex;align-items:center;
                            justify-content:center;color:white;
                            font-weight:700;font-size:0.85rem;">
                    {num}
                </div>
                <div>
                    <div style="font-weight:600;font-size:0.9rem;
                                margin-bottom:0.2rem;">{titre}</div>
                    <div style="font-size:0.8rem;opacity:0.7;
                                line-height:1.5;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("### Complétude des champs après nettoyage")
        st.caption("Proportion de valeurs renseignées par colonne")

        completude_data = []
        for col in df_d.columns:
            if col in ["id", "collecte_le"]:
                continue
            propre = df_d[col].apply(est_propre).sum()
            pct    = round(propre / len(df_d) * 100, 1)
            completude_data.append({
                "colonne": col,
                "pct":     pct,
                "couleur": "#2E7D32" if pct >= 95
                           else "#DAA520" if pct >= 70
                           else "#C1002A"
            })

        df_comp = pd.DataFrame(completude_data).sort_values(
            "pct", ascending=True
        )

        fig = go.Figure(go.Bar(
            x=df_comp["pct"],
            y=df_comp["colonne"],
            orientation="h",
            marker_color=df_comp["couleur"].tolist(),
            marker_opacity=0.85,
            marker_line=dict(color="rgba(0,0,0,0)"),
            text=[f"{v} %" for v in df_comp["pct"]],
            textposition="outside",
            textfont=dict(size=10, family=FONT),
            hovertemplate=(
                "<b>%{y}</b><br>%{x} % de complétion<extra></extra>"
            ),
        ))
        fig.update_layout(**plo(height=420))
        fig.update_xaxes(**ax(range=[0, 115],
                              title_text="% de complétion"))
        fig.update_yaxes(tickfont=dict(size=10),
                         gridcolor="rgba(0,0,0,0)")
        chart(fig)

        st.markdown("""
        <div style="font-size:0.78rem;margin-top:0.5rem;
                    display:flex;gap:1rem;">
            <span style="color:#2E7D32;">■ ≥ 95 % - complet</span>
            <span style="color:#DAA520;">■ 70-94 % - partiel</span>
            <span style="color:#C1002A;">■ < 70 % - incomplet</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Du brut au propre ────────────────────────────────────────
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("### Du brut au propre - ce que le pipeline transforme")
    st.caption(
        f"3,114 acteurs bruts téléchargés · "
        f"577 députés actifs enrichis · "
        f"2,537 ignorés (autres législatures)"
    )

    col_funnel, col_delta = st.columns([1, 1])

    with col_funnel:
        st.markdown("""
        <div style="margin-top:1rem;">
        """, unsafe_allow_html=True)

        etapes_funnel = [
            (nb_brut,    "#C1002A", "ZIP AMO30",
             f"{nb_brut:,} acteurs bruts téléchargés"),
            (nb_ignores, "#e8a0a0", "Ignorés",
             f"{nb_ignores:,} acteurs d'autres législatures"),
            (nb_actifs,  "#DAA520", "Filtre 17e",
             f"{nb_actifs:,} avec mandat GP actif"),
            (nb_actifs,  "#4f7ed4", "Nettoyage",
             f"{nb_actifs:,} après nettoyage XML"),
            (nb_actifs,  "#2E7D32", "Enrichissement",
             f"{nb_actifs:,} avec âge, genre, groupe"),
        ]

        for valeur, couleur, etape, desc in etapes_funnel:
            largeur = max(int(valeur / nb_brut * 100), 8)
            st.markdown(f"""
            <div style="margin-bottom:0.6rem;">
                <div style="font-size:0.78rem;font-weight:600;
                            margin-bottom:0.2rem;color:{couleur};">
                    {etape}
                </div>
                <div style="background:rgba(128,128,128,0.08);
                            border-radius:6px;height:32px;
                            position:relative;overflow:hidden;">
                    <div style="background:{couleur};opacity:0.85;
                                border-radius:6px;height:32px;
                                width:{largeur}%;
                                display:flex;align-items:center;
                                padding-left:0.75rem;">
                        <span style="color:white;font-weight:700;
                                     font-size:0.82rem;white-space:nowrap;">
                            {valeur:,}
                        </span>
                    </div>
                </div>
                <div style="font-size:0.72rem;opacity:0.6;
                            margin-top:0.15rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col_delta:
        champs = [
            ("Groupe politique",
             0, 100,
             "#002395",
             "Absent dans le ZIP. Construit par croisement des organes actifs."),
            ("Genre",
             0, 100,
             "#4f7ed4",
             "Non fourni par l'API. Déduit de la civilité (M. / Mme)."),
            ("Age",
             0, 100,
             "#DAA520",
             "Non fourni par l'API. Calculé depuis la date de naissance."),
            ("Profession",
             62, 78,
             "#FF8F00",
             "62% avant nettoyage. Valeurs XML (@xsi:nil) converties en NULL."),
            ("Lieu de naissance",
             95, 95,
             "#2E7D32",
             "Deja bien renseigné dans l'API. Aucune perte."),
            ("Nom et prénom",
             100, 100,
             "#2E7D32",
             "Complet dans la source. Aucun traitement nécessaire."),
        ]

        st.markdown("<br>", unsafe_allow_html=True)
        for champ, avant_pct, apres_pct, couleur, note in champs:
            delta = apres_pct - avant_pct
            if delta > 0:
                label_delta = f"+{delta} points - enrichissement"
                couleur_delta = "#2E7D32"
            elif delta == 0 and avant_pct == 100:
                label_delta = "Complet"
                couleur_delta = "#2E7D32"
            elif delta == 0:
                label_delta = f"{avant_pct}% - stable"
                couleur_delta = "#757575"
            else:
                label_delta = f"{delta} points"
                couleur_delta = "#C1002A"

            st.markdown(f"""
            <div style="margin-bottom:1rem;padding:0.85rem 1rem;
                        border-radius:8px;
                        border-left:3px solid {couleur};
                        border-top:1px solid rgba(128,128,128,0.1);
                        border-right:1px solid rgba(128,128,128,0.1);
                        border-bottom:1px solid rgba(128,128,128,0.1);">
                <div style="display:flex;justify-content:space-between;
                            align-items:center;margin-bottom:0.5rem;">
                    <span style="font-weight:600;font-size:0.88rem;">
                        {champ}
                    </span>
                    <span style="font-size:0.78rem;font-weight:600;
                                 color:{couleur_delta};background:rgba(0,0,0,0.04);
                                 padding:0.1rem 0.5rem;border-radius:4px;">
                        {label_delta}
                    </span>
                </div>
                <div style="display:flex;gap:0.5rem;align-items:center;
                            margin-bottom:0.35rem;">
                    <span style="font-size:0.7rem;opacity:0.5;
                                 width:3rem;">Avant</span>
                    <div style="flex:1;background:rgba(128,128,128,0.1);
                                border-radius:3px;height:5px;">
                        <div style="background:#C1002A;border-radius:3px;
                                    height:5px;width:{avant_pct}%;
                                    opacity:0.7;"></div>
                    </div>
                    <span style="font-size:0.7rem;opacity:0.5;
                                 width:2.5rem;text-align:right;">
                        {avant_pct}%
                    </span>
                </div>
                <div style="display:flex;gap:0.5rem;align-items:center;
                            margin-bottom:0.4rem;">
                    <span style="font-size:0.7rem;opacity:0.5;
                                 width:3rem;">Après</span>
                    <div style="flex:1;background:rgba(128,128,128,0.1);
                                border-radius:3px;height:5px;">
                        <div style="background:{couleur};border-radius:3px;
                                    height:5px;width:{apres_pct}%;"></div>
                    </div>
                    <span style="font-size:0.7rem;opacity:0.5;
                                 width:2.5rem;text-align:right;">
                        {apres_pct}%
                    </span>
                </div>
                <div style="font-size:0.73rem;opacity:0.55;
                            line-height:1.4;">{note}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    def est_propre(val):
        if val is None:
            return False
        if isinstance(val, float) and pd.isna(val):
            return False
        if isinstance(val, dict):
            return False
        if isinstance(val, str) and (
            "@xsi:nil" in val or "@xmlns:xsi" in val
            or val.strip() == ""
        ):
            return False
        return True