"""
DAG Airflow — Pipeline ETL Assemblée nationale française.

Orchestre les étapes du pipeline de collecte et traitement
des données parlementaires françaises.

Planning : quotidien à 6h00
"""

import sys
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# ─── Résolution des chemins ───────────────────────────────────────────────────
AIRFLOW_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(AIRFLOW_HOME, "etl", "scrapers"))
sys.path.insert(0, os.path.join(AIRFLOW_HOME, "etl", "transform"))
sys.path.insert(0, os.path.join(AIRFLOW_HOME, "etl", "load"))

from dotenv import load_dotenv
load_dotenv(os.path.join(AIRFLOW_HOME, ".env"))


# ─── Configuration par défaut du DAG ─────────────────────────────────────────

default_args = {
    "owner":            "data-pipeline",
    "depends_on_past":  False,
    "start_date":       datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry":   False,
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
}


# ─── Fonctions des tâches ─────────────────────────────────────────────────────

def task_scraper_groupes(**context):
    """
    Tâche 1 : Scraping HTML des groupes politiques.
    Résultat poussé dans XCom pour les tâches suivantes.
    """
    from groupes_scraper import GroupesScraper

    scraper = GroupesScraper()
    groupes = scraper.collecter()

    if not groupes:
        raise ValueError("Aucun groupe collecté — arrêt du DAG")

    # Sérialise pour XCom (dicts simples)
    groupes_data = [
        {
            "slug":        g.slug,
            "nom":         g.nom,
            "sigle":       g.sigle,
            "president":   g.president,
            "nb_membres":  g.nb_membres,
            "declaration": g.declaration,
            "url":         g.url,
        }
        for g in groupes
    ]

    context["ti"].xcom_push(key="groupes", value=groupes_data)
    return f"{len(groupes)} groupes collectés"


def task_collecter_deputes(**context):
    """
    Tâche 2 : Collecte des députés via API ZIP officielle.
    """
    from nosdeputes_scraper import DeputesCollector

    collector = DeputesCollector()
    deputes = collector.collecter()

    if not deputes:
        raise ValueError("Aucun député collecté")

    deputes_data = [
        {
            "uid":                   d.uid,
            "nom":                   d.nom,
            "prenom":                d.prenom,
            "civilite":              d.civilite,
            "date_naissance":        d.date_naissance,
            "lieu_naissance":        d.lieu_naissance,
            "departement_naissance": d.departement_naissance,
            "profession":            d.profession,
            "url_photo":             d.url_photo,
        }
        for d in deputes
    ]

    context["ti"].xcom_push(key="deputes", value=deputes_data)
    return f"{len(deputes)} députés collectés"


def task_collecter_scrutins(**context):
    """
    Tâche 3 : Collecte des scrutins via API ZIP officielle.
    """
    from nosdeputes_scraper import ScrutinsCollector

    collector = ScrutinsCollector()
    scrutins = collector.collecter()

    scrutins_data = [
        {
            "uid":        s.uid,
            "numero":     s.numero,
            "titre":      s.titre,
            "date":       s.date,
            "legislature": s.legislature,
            "type_vote":  s.type_vote,
            "sort":       s.sort,
            "pour":       s.pour,
            "contre":     s.contre,
            "abstention": s.abstention,
            "non_votant": s.non_votant,
        }
        for s in scrutins
    ]

    context["ti"].xcom_push(key="scrutins", value=scrutins_data)
    return f"{len(scrutins)} scrutins collectés"


def task_load_minio(**context):
    """
    Tâche 4 : Chargement des données brutes dans MinIO (Data Lake).
    """
    from minio_loader import MinioLoader

    ti = context["ti"]
    groupes  = ti.xcom_pull(task_ids="scraper_groupes",    key="groupes")
    deputes  = ti.xcom_pull(task_ids="collecter_deputes",  key="deputes")
    scrutins = ti.xcom_pull(task_ids="collecter_scrutins", key="scrutins")

    loader = MinioLoader()
    if not loader.connecter():
        raise ConnectionError("Impossible de se connecter à MinIO")

    date = datetime.now().strftime("%Y-%m-%d")
    loader.charger_json(groupes,  f"groupes/raw_{date}.json")
    loader.charger_json(deputes,  f"deputes/raw_{date}.json")
    loader.charger_json(scrutins, f"scrutins/raw_{date}.json")

    return "Données brutes chargées dans MinIO"


def task_transform(**context):
    """
    Tâche 5 : Transformation et nettoyage des données.
    """
    from nosdeputes_scraper import Depute, Scrutin
    from groupes_scraper import GroupePolitique
    from cleaner import DataCleaner

    ti = context["ti"]
    groupes_data  = ti.xcom_pull(task_ids="scraper_groupes",    key="groupes")
    deputes_data  = ti.xcom_pull(task_ids="collecter_deputes",  key="deputes")
    scrutins_data = ti.xcom_pull(task_ids="collecter_scrutins", key="scrutins")

    # Reconstruit les objets depuis les dicts XCom
    from dataclasses import fields

    groupes = [
        type("GroupePolitique", (), {
            "slug":        g["slug"],
            "nom":         g["nom"],
            "sigle":       g["sigle"],
            "president":   g.get("president"),
            "nb_membres":  g.get("nb_membres"),
            "declaration": g.get("declaration"),
            "url":         g.get("url"),
        })()
        for g in groupes_data
    ]

    deputes = [
        Depute(
            uid=d["uid"],
            nom=d["nom"],
            prenom=d["prenom"],
            civilite=d.get("civilite"),
            date_naissance=d.get("date_naissance"),
            lieu_naissance=d.get("lieu_naissance"),
            departement_naissance=d.get("departement_naissance"),
            profession=d.get("profession"),
            url_photo=d.get("url_photo"),
        )
        for d in deputes_data
    ]

    scrutins = [
        Scrutin(
            uid=s["uid"],
            numero=s.get("numero"),
            titre=s.get("titre"),
            date=s.get("date"),
            legislature=s.get("legislature"),
            type_vote=s.get("type_vote"),
            sort=s.get("sort"),
            pour=s.get("pour", 0),
            contre=s.get("contre", 0),
            abstention=s.get("abstention", 0),
            non_votant=s.get("non_votant", 0),
        )
        for s in scrutins_data
    ]

    cleaner = DataCleaner()
    deputes_clean, scrutins_clean = cleaner.transformer(
        deputes_bruts=deputes,
        scrutins_bruts=scrutins,
        groupes_bruts=groupes,
    )

    # Sérialise les résultats pour XCom
    context["ti"].xcom_push(key="deputes_clean", value=[
        {
            "uid":                   d.uid,
            "nom":                   d.nom,
            "prenom":                d.prenom,
            "nom_complet":           d.nom_complet,
            "civilite":              d.civilite,
            "date_naissance":        d.date_naissance,
            "age":                   d.age,
            "lieu_naissance":        d.lieu_naissance,
            "departement_naissance": d.departement_naissance,
            "profession":            d.profession,
            "groupe_sigle":          d.groupe_sigle,
            "groupe_nom":            d.groupe_nom,
            "url_photo":             d.url_photo,
        }
        for d in deputes_clean
    ])

    context["ti"].xcom_push(key="scrutins_clean", value=[
        {
            "uid":               s.uid,
            "numero":            s.numero,
            "titre":             s.titre,
            "titre_court":       s.titre_court,
            "date":              s.date,
            "annee":             s.annee,
            "mois":              s.mois,
            "legislature":       s.legislature,
            "type_vote":         s.type_vote,
            "sort":              s.sort,
            "adopte":            s.adopte,
            "pour":              s.pour,
            "contre":            s.contre,
            "abstention":        s.abstention,
            "non_votant":        s.non_votant,
            "total_votants":     s.total_votants,
            "taux_participation": s.taux_participation,
        }
        for s in scrutins_clean
    ])

    return (
        f"Transformation terminée — "
        f"{len(deputes_clean)} députés / {len(scrutins_clean)} scrutins"
    )


def task_load_postgres(**context):
    """
    Tâche 6 : Chargement des données propres dans PostgreSQL.
    """
    from postgres_loader import PostgresLoader
    from groupes_scraper import GroupePolitique
    from cleaner import DeputeClean, ScrutinClean

    ti = context["ti"]
    groupes_data      = ti.xcom_pull(task_ids="scraper_groupes", key="groupes")
    deputes_clean_data = ti.xcom_pull(task_ids="transform",      key="deputes_clean")
    scrutins_clean_data = ti.xcom_pull(task_ids="transform",     key="scrutins_clean")

    # Reconstruit les objets GroupePolitique
    groupes = [
        type("G", (), {
            "slug":        g["slug"],
            "nom":         g["nom"],
            "sigle":       g["sigle"],
            "president":   g.get("president"),
            "nb_membres":  g.get("nb_membres"),
            "declaration": g.get("declaration"),
            "url":         g.get("url"),
        })()
        for g in groupes_data
    ]

    # Reconstruit les DeputeClean
    deputes_clean = [
        DeputeClean(
            uid=d["uid"],
            nom=d["nom"],
            prenom=d["prenom"],
            nom_complet=d["nom_complet"],
            civilite=d.get("civilite"),
            date_naissance=d.get("date_naissance"),
            age=d.get("age"),
            lieu_naissance=d.get("lieu_naissance"),
            departement_naissance=d.get("departement_naissance"),
            profession=d.get("profession"),
            groupe_sigle=d.get("groupe_sigle"),
            groupe_nom=d.get("groupe_nom"),
            url_photo=d.get("url_photo"),
        )
        for d in deputes_clean_data
    ]

    # Reconstruit les ScrutinClean
    scrutins_clean = [
        ScrutinClean(
            uid=s["uid"],
            numero=s.get("numero"),
            titre=s.get("titre"),
            titre_court=s.get("titre_court"),
            date=s.get("date"),
            annee=s.get("annee"),
            mois=s.get("mois"),
            legislature=s.get("legislature"),
            type_vote=s.get("type_vote"),
            sort=s.get("sort"),
            adopte=s.get("adopte"),
            pour=s.get("pour", 0),
            contre=s.get("contre", 0),
            abstention=s.get("abstention", 0),
            non_votant=s.get("non_votant", 0),
            total_votants=s.get("total_votants", 0),
            taux_participation=s.get("taux_participation"),
        )
        for s in scrutins_clean_data
    ]

    pg = PostgresLoader()
    if not pg.connecter():
        raise ConnectionError("Impossible de se connecter à PostgreSQL")

    pg.creer_tables()
    pg.inserer_groupes(groupes)
    pg.inserer_deputes(deputes_clean)
    pg.inserer_scrutins(scrutins_clean)

    return (
        f"PostgreSQL alimenté — "
        f"{len(deputes_clean)} députés / {len(scrutins_clean)} scrutins"
    )


# ─── Définition du DAG ────────────────────────────────────────────────────────

with DAG(
    dag_id="pipeline_assemblee_nationale",
    description="Pipeline ETL — données parlementaires Assemblée nationale FR",
    default_args=default_args,
    schedule_interval="0 6 * * *",   # tous les jours à 6h00
    catchup=False,
    tags=["assemblee-nationale", "etl", "politique", "france"],
) as dag:

    # ── Tâche 1 : Scraping groupes ────────────────────────────────
    t1_groupes = PythonOperator(
        task_id="scraper_groupes",
        python_callable=task_scraper_groupes,
    )

    # ── Tâche 2 : Collecte députés ────────────────────────────────
    t2_deputes = PythonOperator(
        task_id="collecter_deputes",
        python_callable=task_collecter_deputes,
    )

    # ── Tâche 3 : Collecte scrutins ───────────────────────────────
    t3_scrutins = PythonOperator(
        task_id="collecter_scrutins",
        python_callable=task_collecter_scrutins,
    )

    # ── Tâche 4 : Load MinIO ──────────────────────────────────────
    t4_minio = PythonOperator(
        task_id="load_minio",
        python_callable=task_load_minio,
    )

    # ── Tâche 5 : Transform ───────────────────────────────────────
    t5_transform = PythonOperator(
        task_id="transform",
        python_callable=task_transform,
    )

    # ── Tâche 6 : Load PostgreSQL ─────────────────────────────────
    t6_postgres = PythonOperator(
        task_id="load_postgres",
        python_callable=task_load_postgres,
    )

    # ── Dépendances ───────────────────────────────────────────────
    # t1 doit finir avant t2 et t3 (en parallèle)
    # t4 attend t2 et t3
    # t5 attend t4
    # t6 attend t5
    t1_groupes >> [t2_deputes, t3_scrutins] >> t4_minio >> t5_transform >> t6_postgres