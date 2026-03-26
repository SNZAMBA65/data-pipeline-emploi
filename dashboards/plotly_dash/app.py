"""
Dashboard Plotly Dash — Assemblée nationale française 17e législature.
Analyse interactive des données parlementaires.

Usage :
    python dashboards/plotly_dash/app.py
    Puis ouvrir http://localhost:8050
"""

import sys
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc

# Force le template plotly par défaut pour éviter les conflits avec dbc
pio.templates.default = "plotly"

load_dotenv()

# ─── Connexion base de données ────────────────────────────────────────────────

def get_engine():
    return create_engine(
        "postgresql+psycopg2://jobs_user:jobs_password123@localhost:5432/jobs_db"
    )

def charger_donnees():
    """Charge toutes les données depuis PostgreSQL."""
    engine = get_engine()

    df_deputes = pd.read_sql("SELECT * FROM deputes", engine)
    df_scrutins = pd.read_sql("SELECT * FROM scrutins ORDER BY date", engine)
    df_groupes = pd.read_sql("SELECT * FROM groupes_politiques", engine)

    # Nettoyage
    def nettoyer(val):
        if isinstance(val, dict):
            return None
        if isinstance(val, str) and val.startswith("{'@"):
            return None
        return val

    df_deputes["profession"]     = df_deputes["profession"].apply(nettoyer)
    df_deputes["date_naissance"] = pd.to_datetime(
        df_deputes["date_naissance"], errors="coerce"
    )
    df_deputes["genre"] = df_deputes["civilite"].map(
        {"M.": "Homme", "Mme": "Femme"}
    )
    df_scrutins["date"] = pd.to_datetime(df_scrutins["date"])

    return df_deputes, df_scrutins, df_groupes


# ─── Chargement initial ───────────────────────────────────────────────────────

df_deputes, df_scrutins, df_groupes = charger_donnees()

# ─── Initialisation de l'app ─────────────────────────────────────────────────

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="Assemblée Nationale — Dashboard"
)

# ─── Couleurs ─────────────────────────────────────────────────────────────────

COLORS = {
    "primary":   "#2c3e50",
    "secondary": "#3498db",
    "success":   "#2ecc71",
    "danger":    "#e74c3c",
    "warning":   "#f39c12",
    "light":     "#ecf0f1",
    "adopte":    "#2ecc71",
    "rejete":    "#e74c3c",
    "homme":     "#4878CF",
    "femme":     "#D65F5F",
}

# ─── Composants réutilisables ─────────────────────────────────────────────────

def carte_stat(titre, valeur, couleur="#3498db", icone="📊"):
    return dbc.Card(
        dbc.CardBody([
            html.P(icone + " " + titre,
                   className="text-muted mb-1",
                   style={"fontSize": "13px"}),
            html.H3(str(valeur),
                    style={"color": couleur, "fontWeight": "bold"}),
        ]),
        className="shadow-sm mb-3",
    )


# ─── Layout ───────────────────────────────────────────────────────────────────

app.layout = dbc.Container([

    # En-tête
    dbc.Row([
        dbc.Col([
            html.H1(
                "🏛️ Assemblée Nationale — 17e Législature",
                className="text-center mt-4 mb-1",
                style={"color": COLORS["primary"], "fontWeight": "bold"}
            ),
            html.P(
                "Analyse interactive des données parlementaires françaises",
                className="text-center text-muted mb-4"
            ),
            html.Hr()
        ])
    ]),

    # Onglets
    dbc.Tabs([

        # ── Onglet 1 : Vue d'ensemble ─────────────────────────────────────
        dbc.Tab(label="📊 Vue d'ensemble", tab_id="overview", children=[

            dbc.Row([
                dbc.Col(carte_stat(
                    "Députés", f"{len(df_deputes):,}", COLORS["secondary"], "👤"
                ), width=3),
                dbc.Col(carte_stat(
                    "Scrutins", f"{len(df_scrutins):,}", COLORS["primary"], "🗳️"
                ), width=3),
                dbc.Col(carte_stat(
                    "Adoptés",
                    f"{df_scrutins['adopte'].mean()*100:.1f}%",
                    COLORS["success"], "✅"
                ), width=3),
                dbc.Col(carte_stat(
                    "Participation moy.",
                    f"{df_scrutins['taux_participation'].mean():.1f}%",
                    COLORS["warning"], "📈"
                ), width=3),
            ], className="mt-4"),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="graph-genre")
                ], width=4),
                dbc.Col([
                    dcc.Graph(id="graph-age-dist")
                ], width=8),
            ], className="mt-2"),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="graph-scrutins-resultats")
                ], width=6),
                dbc.Col([
                    dcc.Graph(id="graph-participation-dist")
                ], width=6),
            ], className="mt-2"),

        ]),

        # ── Onglet 2 : Scrutins ───────────────────────────────────────────
        dbc.Tab(label="🗳️ Scrutins", tab_id="scrutins", children=[

            dbc.Row([
                dbc.Col([
                    html.Label("Filtrer par résultat :"),
                    dcc.Dropdown(
                        id="filtre-sort",
                        options=[
                            {"label": "Tous", "value": "tous"},
                            {"label": "✅ Adoptés", "value": "adopté"},
                            {"label": "❌ Rejetés", "value": "rejeté"},
                        ],
                        value="tous",
                        clearable=False,
                    )
                ], width=3),
                dbc.Col([
                    html.Label("Filtrer par année :"),
                    dcc.Dropdown(
                        id="filtre-annee",
                        options=[{"label": str(a), "value": a}
                                 for a in sorted(df_scrutins["annee"].dropna().unique())],
                        value=None,
                        placeholder="Toutes les années",
                    )
                ], width=3),
            ], className="mt-4 mb-2"),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="graph-scrutins-timeline")
                ], width=12),
            ]),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="graph-votes-scatter")
                ], width=6),
                dbc.Col([
                    dcc.Graph(id="graph-types-vote")
                ], width=6),
            ], className="mt-2"),

        ]),

        # ── Onglet 3 : Députés ────────────────────────────────────────────
        dbc.Tab(label="👤 Députés", tab_id="deputes", children=[

            dbc.Row([
                dbc.Col([
                    html.Label("Filtrer par genre :"),
                    dcc.Dropdown(
                        id="filtre-genre",
                        options=[
                            {"label": "Tous", "value": "tous"},
                            {"label": "👨 Hommes", "value": "Homme"},
                            {"label": "👩 Femmes", "value": "Femme"},
                        ],
                        value="tous",
                        clearable=False,
                    )
                ], width=3),
            ], className="mt-4 mb-2"),

            dbc.Row([
                dbc.Col([dcc.Graph(id="graph-professions")], width=7),
                dbc.Col([dcc.Graph(id="graph-age-genre")],   width=5),
            ]),

            dbc.Row([
                dbc.Col([dcc.Graph(id="graph-lieux-naissance")], width=12),
            ], className="mt-2"),

        ]),

    ], id="tabs", active_tab="overview"),

], fluid=True)


# ─── Callbacks — Vue d'ensemble ───────────────────────────────────────────────

@app.callback(
    Output("graph-genre", "figure"),
    Input("tabs", "active_tab")
)
def graph_genre(_):
    civilite = df_deputes["civilite"].value_counts().reset_index()
    civilite.columns = ["civilite", "count"]
    civilite["label"] = civilite["civilite"].map({"M.": "Hommes", "Mme": "Femmes"})

    fig = px.pie(
        civilite, values="count", names="label",
        color="label",
        color_discrete_map={"Hommes": COLORS["homme"], "Femmes": COLORS["femme"]},
        title="Répartition Hommes / Femmes",
        hole=0.4,
    )
    fig.update_layout(margin=dict(t=50, b=10))
    return fig


@app.callback(
    Output("graph-age-dist", "figure"),
    Input("tabs", "active_tab")
)
def graph_age_dist(_):
    df = df_deputes[df_deputes["age"].notna() & df_deputes["genre"].notna()]

    fig = px.histogram(
        df, x="age", color="genre",
        color_discrete_map={"Homme": COLORS["homme"], "Femme": COLORS["femme"]},
        barmode="overlay", opacity=0.7,
        title="Distribution des âges par genre",
        labels={"age": "Âge", "count": "Nombre"},
        nbins=25,
    )
    fig.update_layout(legend_title="Genre")
    return fig


@app.callback(
    Output("graph-scrutins-resultats", "figure"),
    Input("tabs", "active_tab")
)
def graph_scrutins_resultats(_):
    counts = df_scrutins["sort"].value_counts().reset_index()
    counts.columns = ["sort", "nb"]
    counts["couleur"] = counts["sort"].map(
        {"adopté": COLORS["adopte"], "rejeté": COLORS["rejete"]}
    )

    fig = px.bar(
        counts, x="sort", y="nb",
        color="sort",
        color_discrete_map={"adopté": COLORS["adopte"], "rejeté": COLORS["rejete"]},
        title="Résultats des scrutins",
        labels={"sort": "Résultat", "nb": "Nombre de scrutins"},
    )
    fig.update_layout(showlegend=False)
    return fig


@app.callback(
    Output("graph-participation-dist", "figure"),
    Input("tabs", "active_tab")
)
def graph_participation_dist(_):
    fig = px.histogram(
        df_scrutins, x="taux_participation",
        nbins=30, color_discrete_sequence=[COLORS["secondary"]],
        title="Distribution du taux de participation aux scrutins",
        labels={"taux_participation": "Taux de participation (%)"},
    )
    fig.add_vline(
        x=df_scrutins["taux_participation"].mean(),
        line_dash="dash", line_color="red",
        annotation_text=f"Moyenne: {df_scrutins['taux_participation'].mean():.1f}%"
    )
    return fig


# ─── Callbacks — Scrutins ─────────────────────────────────────────────────────

@app.callback(
    Output("graph-scrutins-timeline", "figure"),
    Input("filtre-sort",  "value"),
    Input("filtre-annee", "value"),
)
def graph_scrutins_timeline(filtre_sort, filtre_annee):
    df = df_scrutins.copy()

    if filtre_sort != "tous":
        df = df[df["sort"] == filtre_sort]
    if filtre_annee:
        df = df[df["annee"] == filtre_annee]

    df_mois = (
        df.groupby(df["date"].dt.to_period("M"))
        .agg(nb=("uid", "count"), adoption=("adopte", "mean"))
        .reset_index()
    )
    df_mois["date"] = df_mois["date"].dt.to_timestamp()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=df_mois["date"], y=df_mois["nb"],
               name="Nb scrutins", marker_color=COLORS["secondary"], opacity=0.8),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(x=df_mois["date"], y=df_mois["adoption"] * 100,
                   name="Taux adoption (%)", mode="lines+markers",
                   line=dict(color=COLORS["success"], width=2)),
        secondary_y=True
    )
    fig.update_layout(
        title="Évolution mensuelle des scrutins",
        xaxis_title="Mois",
        legend=dict(orientation="h", y=1.1),
    )
    fig.update_yaxes(title_text="Nombre de scrutins", secondary_y=False)
    fig.update_yaxes(title_text="Taux d'adoption (%)", secondary_y=True)
    return fig


@app.callback(
    Output("graph-votes-scatter", "figure"),
    Input("filtre-sort",  "value"),
    Input("filtre-annee", "value"),
)
def graph_votes_scatter(filtre_sort, filtre_annee):
    df = df_scrutins.copy()
    if filtre_sort != "tous":
        df = df[df["sort"] == filtre_sort]
    if filtre_annee:
        df = df[df["annee"] == filtre_annee]

    fig = px.scatter(
        df, x="pour", y="contre",
        color="sort",
        color_discrete_map={"adopté": COLORS["adopte"], "rejeté": COLORS["rejete"]},
        hover_data=["titre_court", "date", "taux_participation"],
        title="Votes Pour vs Contre",
        labels={"pour": "Votes Pour", "contre": "Votes Contre"},
        opacity=0.6,
    )
    return fig


@app.callback(
    Output("graph-types-vote", "figure"),
    Input("filtre-sort",  "value"),
    Input("filtre-annee", "value"),
)
def graph_types_vote(filtre_sort, filtre_annee):
    df = df_scrutins.copy()
    if filtre_sort != "tous":
        df = df[df["sort"] == filtre_sort]
    if filtre_annee:
        df = df[df["annee"] == filtre_annee]

    type_counts = df["type_vote"].value_counts().head(8).reset_index()
    type_counts.columns = ["type_vote", "nb"]

    fig = px.bar(
        type_counts, x="nb", y="type_vote",
        orientation="h",
        color_discrete_sequence=[COLORS["primary"]],
        title="Types de scrutins",
        labels={"nb": "Nombre", "type_vote": ""},
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


# ─── Callbacks — Députés ──────────────────────────────────────────────────────

@app.callback(
    Output("graph-professions", "figure"),
    Input("filtre-genre", "value"),
)
def graph_professions(filtre_genre):
    df = df_deputes[df_deputes["profession"].notna()].copy()

    if filtre_genre != "tous":
        df = df[df["genre"] == filtre_genre]

    top = df["profession"].value_counts().head(15).reset_index()
    top.columns = ["profession", "nb"]

    couleur = (COLORS["homme"] if filtre_genre == "Homme"
               else COLORS["femme"] if filtre_genre == "Femme"
               else COLORS["secondary"])

    fig = px.bar(
        top, x="nb", y="profession",
        orientation="h",
        color_discrete_sequence=[couleur],
        title=f"Top 15 professions — {filtre_genre if filtre_genre != 'tous' else 'Tous'}",
        labels={"nb": "Nombre de députés", "profession": ""},
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


@app.callback(
    Output("graph-age-genre", "figure"),
    Input("filtre-genre", "value"),
)
def graph_age_genre(filtre_genre):
    df = df_deputes[df_deputes["age"].notna() & df_deputes["genre"].notna()].copy()

    if filtre_genre != "tous":
        df = df[df["genre"] == filtre_genre]

    fig = px.box(
        df, x="genre", y="age",
        color="genre",
        color_discrete_map={"Homme": COLORS["homme"], "Femme": COLORS["femme"]},
        title="Distribution des âges par genre",
        labels={"age": "Âge", "genre": ""},
        points="outliers",
    )
    fig.update_layout(showlegend=False)
    return fig


@app.callback(
    Output("graph-lieux-naissance", "figure"),
    Input("filtre-genre", "value"),
)
def graph_lieux_naissance(filtre_genre):
    df = df_deputes[df_deputes["lieu_naissance"].notna()].copy()

    if filtre_genre != "tous":
        df = df[df["genre"] == filtre_genre]

    top = df["lieu_naissance"].value_counts().head(20).reset_index()
    top.columns = ["ville", "nb"]

    fig = px.bar(
        top, x="ville", y="nb",
        color_discrete_sequence=[COLORS["primary"]],
        title="Top 20 villes de naissance des députés",
        labels={"ville": "Ville", "nb": "Nombre de députés"},
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig


# ─── Lancement ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)