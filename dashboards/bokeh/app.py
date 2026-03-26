"""
Dashboard Assemblée nationale française 17e législature.

Usage :
    bokeh serve dashboards/bokeh/app.py --port 5006 --show
"""

import numpy as np
import pandas as pd
from math import pi
from sqlalchemy import create_engine
from dotenv import load_dotenv

from bokeh.plotting import figure, curdoc
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource, Div, HoverTool,
    DatetimeTickFormatter, Tabs, TabPanel,
)
from bokeh.transform import cumsum, linear_cmap
from bokeh.palettes import RdYlGn11

load_dotenv()

# ─── Connexion ───────────────────────────────────────────────────────────────

engine = create_engine(
    "postgresql+psycopg2://jobs_user:jobs_password123@localhost:5432/jobs_db"
)

# ─── Chargement ──────────────────────────────────────────────────────────────

def charger_donnees():
    df_deputes  = pd.read_sql("SELECT * FROM deputes",                engine)
    df_scrutins = pd.read_sql("SELECT * FROM scrutins ORDER BY date", engine)

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
    return df_deputes, df_scrutins


df_deputes, df_scrutins = charger_donnees()

BLEU  = "#3498db"
VERT  = "#2ecc71"
ROUGE = "#e74c3c"


# ─── Vue d'ensemble ───────────────────────────────────────────────────────────

def fig_overview():
    nb_deputes    = len(df_deputes)
    nb_scrutins   = len(df_scrutins)
    pct_femmes    = round((df_deputes["civilite"] == "Mme").sum() / nb_deputes * 100, 1)
    pct_adoption  = round(df_scrutins["adopte"].mean() * 100, 1)
    age_moyen     = round(df_deputes["age"].dropna().mean(), 1)
    participation = round(df_scrutins["taux_participation"].mean(), 1)

    kpis = Div(text=f"""
    <div style="font-family:sans-serif; padding:10px;">
        <div style="display:flex; flex-wrap:wrap; gap:16px; justify-content:center;">
            <div style="background:#3498db;color:white;padding:20px 30px;
                        border-radius:10px;text-align:center;min-width:160px;">
                <div style="font-size:32px;font-weight:bold;">{nb_deputes:,}</div>
                <div style="font-size:14px;opacity:0.9;">👤 Députés</div>
            </div>
            <div style="background:#2c3e50;color:white;padding:20px 30px;
                        border-radius:10px;text-align:center;min-width:160px;">
                <div style="font-size:32px;font-weight:bold;">{nb_scrutins:,}</div>
                <div style="font-size:14px;opacity:0.9;">🗳️ Scrutins</div>
            </div>
            <div style="background:#2ecc71;color:white;padding:20px 30px;
                        border-radius:10px;text-align:center;min-width:160px;">
                <div style="font-size:32px;font-weight:bold;">{pct_adoption}%</div>
                <div style="font-size:14px;opacity:0.9;">✅ Taux adoption</div>
            </div>
            <div style="background:#e74c3c;color:white;padding:20px 30px;
                        border-radius:10px;text-align:center;min-width:160px;">
                <div style="font-size:32px;font-weight:bold;">{pct_femmes}%</div>
                <div style="font-size:14px;opacity:0.9;">👩 Femmes</div>
            </div>
            <div style="background:#f39c12;color:white;padding:20px 30px;
                        border-radius:10px;text-align:center;min-width:160px;">
                <div style="font-size:32px;font-weight:bold;">{age_moyen}</div>
                <div style="font-size:14px;opacity:0.9;">📅 Âge moyen</div>
            </div>
            <div style="background:#9b59b6;color:white;padding:20px 30px;
                        border-radius:10px;text-align:center;min-width:160px;">
                <div style="font-size:32px;font-weight:bold;">{participation}%</div>
                <div style="font-size:14px;opacity:0.9;">📈 Participation moy.</div>
            </div>
        </div>
    </div>
    """)

    # Résultats scrutins — couleurs dans le ColumnDataSource
    sort_counts = df_scrutins["sort"].value_counts().reset_index()
    sort_counts.columns = ["sort", "nb"]
    sort_counts["color"] = sort_counts["sort"].map(
        {"adopté": VERT, "rejeté": ROUGE}
    ).fillna("#95a5a6")

    source_sort = ColumnDataSource(sort_counts)

    p_sort = figure(
        x_range=sort_counts["sort"].tolist(),
        height=300, width=420,
        title="Résultats des scrutins",
        toolbar_location=None,
    )
    p_sort.vbar(
        x="sort", top="nb", width=0.5,
        source=source_sort,
        fill_color="color",
        line_color="white",
    )
    p_sort.add_tools(HoverTool(tooltips=[
        ("Résultat", "@sort"),
        ("Nombre",   "@nb"),
    ]))
    p_sort.title.text_font_size  = "13px"
    p_sort.title.text_font_style = "bold"
    p_sort.xaxis.axis_label      = "Résultat"
    p_sort.yaxis.axis_label      = "Nombre de scrutins"
    p_sort.outline_line_color    = None
    p_sort.xgrid.grid_line_color = None

    # Distribution participation
    hist, edges = np.histogram(
        df_scrutins["taux_participation"].dropna(), bins=25
    )
    source_part = ColumnDataSource({
        "top":   hist,
        "left":  edges[:-1],
        "right": edges[1:],
        "pmin":  edges[:-1].round(1),
        "pmax":  edges[1:].round(1),
    })

    p_part = figure(
        height=300, width=480,
        title="Distribution du taux de participation",
        toolbar_location=None,
    )
    p_part.quad(
        top="top", bottom=0,
        left="left", right="right",
        source=source_part,
        fill_color="#9b59b6", line_color="white", alpha=0.8,
    )
    p_part.add_tools(HoverTool(tooltips=[
        ("Tranche",      "@pmin% - @pmax%"),
        ("Nb scrutins",  "@top"),
    ]))
    p_part.xaxis.axis_label      = "Taux de participation (%)"
    p_part.yaxis.axis_label      = "Nombre de scrutins"
    p_part.title.text_font_size  = "13px"
    p_part.title.text_font_style = "bold"
    p_part.outline_line_color    = None

    return column(kpis, row(p_sort, p_part), sizing_mode="stretch_width")


# ─── Députés ──────────────────────────────────────────────────────────────────

def fig_professions():
    top = (
        df_deputes["profession"].dropna()
        .value_counts().head(15).reset_index()
    )
    top.columns = ["profession", "nb"]
    top = top.sort_values("nb")
    source = ColumnDataSource(top)

    p = figure(
        y_range=top["profession"].tolist(),
        height=450, width=650,
        title="Top 15 des professions des députés",
        toolbar_location=None,
    )
    p.hbar(
        y="profession", right="nb", height=0.6,
        source=source, fill_color=BLEU,
        line_color="white", alpha=0.85
    )
    p.add_tools(HoverTool(tooltips=[
        ("Profession", "@profession"),
        ("Nb députés", "@nb"),
    ]))
    p.xaxis.axis_label      = "Nombre de députés"
    p.title.text_font_size  = "13px"
    p.title.text_font_style = "bold"
    p.ygrid.grid_line_color = None
    p.outline_line_color    = None
    return p


def fig_ages():
    ages = df_deputes["age"].dropna().values
    hist, edges = np.histogram(ages, bins=25)
    source = ColumnDataSource({
        "top":     hist,
        "left":    edges[:-1],
        "right":   edges[1:],
        "age_min": edges[:-1].astype(int),
        "age_max": edges[1:].astype(int),
    })

    p = figure(
        height=350, width=480,
        title="Distribution des âges des députés",
        toolbar_location=None,
    )
    p.quad(
        top="top", bottom=0, left="left", right="right",
        source=source, fill_color=BLEU,
        line_color="white", alpha=0.8
    )
    p.add_tools(HoverTool(tooltips=[
        ("Tranche", "@age_min - @age_max ans"),
        ("Nb",      "@top"),
    ]))
    p.xaxis.axis_label      = "Âge"
    p.yaxis.axis_label      = "Nombre de députés"
    p.title.text_font_size  = "13px"
    p.title.text_font_style = "bold"
    p.outline_line_color    = None
    return p


def fig_genre():
    civilite = df_deputes["civilite"].value_counts().reset_index()
    civilite.columns = ["civilite", "nb"]
    civilite["label"] = civilite["civilite"].map(
        {"M.": "Hommes", "Mme": "Femmes"}
    )
    civilite["angle"] = civilite["nb"] / civilite["nb"].sum() * 2 * pi
    civilite["color"] = ["#4878CF", "#D65F5F"]
    civilite["pct"]   = (
        civilite["nb"] / civilite["nb"].sum() * 100
    ).round(1).astype(str) + "%"

    source = ColumnDataSource(civilite)

    p = figure(
        height=350, width=380,
        title="Répartition Hommes / Femmes",
        toolbar_location=None,
        x_range=(-0.6, 1.0),
    )
    p.wedge(
        x=0, y=1, radius=0.35,
        start_angle=cumsum("angle", include_zero=True),
        end_angle=cumsum("angle"),
        line_color="white", fill_color="color",
        legend_field="label", source=source,
    )
    p.add_tools(HoverTool(tooltips=[
        ("Genre",       "@label"),
        ("Nb",          "@nb"),
        ("Pourcentage", "@pct"),
    ]))
    p.axis.visible          = False
    p.grid.grid_line_color  = None
    p.title.text_font_size  = "13px"
    p.title.text_font_style = "bold"
    p.outline_line_color    = None
    p.legend.location       = "bottom_right"
    return p


# ─── Scrutins ────────────────────────────────────────────────────────────────

def fig_scrutins_timeline():
    df_mois = (
        df_scrutins
        .groupby(df_scrutins["date"].dt.to_period("M"))
        .agg(nb=("uid", "count"), adoption=("adopte", "mean"))
        .reset_index()
    )
    df_mois["date_ts"]      = df_mois["date"].dt.to_timestamp()
    df_mois["adoption_pct"] = (df_mois["adoption"] * 100).round(1)
    source = ColumnDataSource(df_mois)

    p = figure(
        x_axis_type="datetime",
        height=350, width=900,
        title="Évolution mensuelle des scrutins",
        toolbar_location="above",
    )
    p.vbar(
        x="date_ts", top="nb",
        width=20 * 24 * 3600 * 1000,
        source=source,
        fill_color=BLEU, line_color="white", alpha=0.8,
    )
    p.add_tools(HoverTool(tooltips=[
        ("Mois",          "@date_ts{%b %Y}"),
        ("Scrutins",      "@nb"),
        ("Taux adoption", "@adoption_pct{0.0}%"),
    ], formatters={"@date_ts": "datetime"}))
    p.xaxis.formatter       = DatetimeTickFormatter(months="%b %Y")
    p.xaxis.axis_label      = "Mois"
    p.yaxis.axis_label      = "Nombre de scrutins"
    p.title.text_font_size  = "13px"
    p.title.text_font_style = "bold"
    p.outline_line_color    = None
    return p


def fig_scatter_votes():
    adoptes = df_scrutins[df_scrutins["sort"] == "adopté"]
    rejetes = df_scrutins[df_scrutins["sort"] == "rejeté"]

    p = figure(
        height=380, width=520,
        title="Votes Pour vs Contre par scrutin",
        toolbar_location="above",
    )
    p.circle(
        x=rejetes["pour"].tolist(), y=rejetes["contre"].tolist(),
        color=ROUGE, alpha=0.4, size=5, legend_label="Rejeté"
    )
    p.circle(
        x=adoptes["pour"].tolist(), y=adoptes["contre"].tolist(),
        color=VERT, alpha=0.4, size=5, legend_label="Adopté"
    )
    p.add_tools(HoverTool(tooltips=[
        ("Pour",   "$x{0}"),
        ("Contre", "$y{0}"),
    ]))
    p.xaxis.axis_label      = "Votes Pour"
    p.yaxis.axis_label      = "Votes Contre"
    p.title.text_font_size  = "13px"
    p.title.text_font_style = "bold"
    p.legend.location       = "top_right"
    p.outline_line_color    = None
    return p


def fig_heatmap_adoption():
    df = df_scrutins.copy()
    df["annee"] = df["date"].dt.year.astype(str)
    df["mois"]  = df["date"].dt.month.astype(str)

    pivot = (
        df.groupby(["annee", "mois"])["adopte"]
        .mean().reset_index()
    )
    pivot["adoption_pct"] = (pivot["adopte"] * 100).round(1)

    annees = sorted(pivot["annee"].unique().tolist())
    mois   = [str(m) for m in range(1, 13)]
    source = ColumnDataSource(pivot)

    mapper = linear_cmap(
        field_name="adoption_pct",
        palette=RdYlGn11, low=0, high=100
    )

    p = figure(
        x_range=mois, y_range=annees,
        height=280, width=680,
        title="Taux d'adoption par mois et année (%)",
        toolbar_location=None,
    )
    p.rect(
        x="mois", y="annee",
        width=0.95, height=0.95,
        source=source, fill_color=mapper,
        line_color=None,
    )
    p.add_tools(HoverTool(tooltips=[
        ("Année",         "@annee"),
        ("Mois",          "@mois"),
        ("Taux adoption", "@adoption_pct{0.0}%"),
    ]))
    p.xaxis.axis_label      = "Mois"
    p.yaxis.axis_label      = "Année"
    p.title.text_font_size  = "13px"
    p.title.text_font_style = "bold"
    p.outline_line_color    = None
    return p


# ─── Assemblage ───────────────────────────────────────────────────────────────

titre = Div(text="""
<div style="text-align:center; padding:20px 0 10px 0;">
    <h1 style="color:#2c3e50; font-family:sans-serif; margin:0;">
        🏛️ Assemblée Nationale — Dashboard Bokeh
    </h1>
    <p style="color:#7f8c8d; font-family:sans-serif;">
        17e Législature — Visualisations interactives
    </p>
    <hr style="border-color:#ecf0f1;">
</div>
""")

tab_overview = TabPanel(
    child=fig_overview(),
    title="📊 Vue d'ensemble"
)
tab_deputes = TabPanel(
    child=column(row(fig_genre(), fig_ages()), fig_professions()),
    title="👤 Députés"
)
tab_scrutins = TabPanel(
    child=column(
        fig_scrutins_timeline(),
        row(fig_scatter_votes(), fig_heatmap_adoption()),
    ),
    title="🗳️ Scrutins"
)

tabs   = Tabs(tabs=[tab_overview, tab_deputes, tab_scrutins])
layout = column(titre, tabs, sizing_mode="stretch_width")

curdoc().add_root(layout)
curdoc().title = "Assemblée Nationale"