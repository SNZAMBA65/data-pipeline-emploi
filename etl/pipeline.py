"""
Pipeline ETL principal — Assemblée nationale française.
Orchestre : Extract → Transform → Load (MinIO + PostgreSQL)

Usage :
    python etl/pipeline.py
    python etl/pipeline.py --scrutins-limite 500 --deputes-limite 200
    python etl/pipeline.py --skip-minio
    python etl/pipeline.py --skip-postgres
"""

import sys
import os
import argparse
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# ─── Résolution des chemins d'import ─────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "scrapers"))
sys.path.insert(0, os.path.join(BASE_DIR, "transform"))
sys.path.insert(0, os.path.join(BASE_DIR, "load"))

from nosdeputes_scraper import DeputesCollector, ScrutinsCollector
from groupes_scraper import GroupesScraper
from cleaner import DataCleaner
from minio_loader import MinioLoader
from postgres_loader import PostgresLoader


# ─── Arguments CLI ───────────────────────────────────────────────────────────

def parse_args():
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Pipeline ETL — Assemblée nationale française"
    )
    parser.add_argument(
        "--scrutins-limite",
        type=int,
        default=None,
        help="Nombre maximum de scrutins à collecter (défaut: tous)"
    )
    parser.add_argument(
        "--deputes-limite",
        type=int,
        default=None,
        help="Nombre maximum de députés à collecter (défaut: tous)"
    )
    parser.add_argument(
        "--skip-minio",
        action="store_true",
        help="Ne pas charger les données brutes dans MinIO"
    )
    parser.add_argument(
        "--skip-postgres",
        action="store_true",
        help="Ne pas charger les données propres dans PostgreSQL"
    )
    return parser.parse_args()


# ─── Pipeline principal ───────────────────────────────────────────────────────

def run_pipeline(args) -> bool:
    """
    Exécute le pipeline ETL complet.

    Étapes :
        1. Extract  — scraping HTML groupes + API ZIP députés/scrutins
        2. Load Raw — données brutes vers MinIO (Data Lake)
        3. Transform — nettoyage et enrichissement
        4. Load Clean — données propres vers PostgreSQL (Data Warehouse)

    Args:
        args: Arguments CLI parsés

    Returns:
        True si pipeline réussi, False sinon
    """
    logger.info("=" * 60)
    logger.info("PIPELINE ETL — ASSEMBLÉE NATIONALE")
    logger.info("=" * 60)

    # ── ÉTAPE 1 : EXTRACT ────────────────────────────────────────
    logger.info("── ÉTAPE 1 : EXTRACTION ──")

    # 1a. Groupes politiques via scraping HTML
    logger.info("Scraping HTML des groupes politiques...")
    try:
        groupes_scraper = GroupesScraper()
        groupes = groupes_scraper.collecter()
    except Exception as e:
        logger.error(f"Erreur critique scraping groupes : {e}")
        return False

    if not groupes:
        logger.error("Aucun groupe collecté — arrêt du pipeline")
        return False

    # 1b. Députés via API ZIP officielle (AMO30 — tous acteurs)
    logger.info("Collecte des députés via API officielle...")
    try:
        deputes_collector = DeputesCollector()
        deputes_bruts = deputes_collector.collecter(
            limite=args.deputes_limite
        )
    except Exception as e:
        logger.error(f"Erreur critique collecte députés : {e}")
        return False

    if not deputes_bruts:
        logger.error("Aucun député collecté — arrêt du pipeline")
        return False

    # 1c. Scrutins via API ZIP officielle
    logger.info("Collecte des scrutins via API officielle...")
    try:
        scrutins_collector = ScrutinsCollector()
        scrutins_bruts = scrutins_collector.collecter(
            limite=args.scrutins_limite
        )
    except Exception as e:
        logger.error(f"Erreur critique collecte scrutins : {e}")
        scrutins_bruts = []

    logger.success(
        f"Extraction terminée — "
        f"{len(groupes)} groupes | "
        f"{len(deputes_bruts)} députés | "
        f"{len(scrutins_bruts)} scrutins"
    )

    # ── ÉTAPE 2 : LOAD RAW → MINIO ───────────────────────────────
    if not args.skip_minio:
        logger.info("── ÉTAPE 2 : CHARGEMENT RAW → MINIO (Data Lake) ──")
        try:
            minio = MinioLoader()
            if minio.connecter():
                minio.charger_groupes(groupes)
                minio.charger_deputes(deputes_bruts)
                minio.charger_scrutins(scrutins_bruts)
            else:
                logger.warning(
                    "MinIO non disponible — données brutes non sauvegardées"
                )
        except Exception as e:
            logger.warning(f"Erreur MinIO (non bloquant) : {e}")
    else:
        logger.info("MinIO ignoré (--skip-minio)")

    # ── ÉTAPE 3 : TRANSFORM ──────────────────────────────────────
    logger.info("── ÉTAPE 3 : TRANSFORMATION ──")
    try:
        cleaner = DataCleaner()
        deputes_clean, scrutins_clean = cleaner.transformer(
            deputes_bruts=deputes_bruts,
            scrutins_bruts=scrutins_bruts,
            groupes_bruts=groupes,
        )
    except Exception as e:
        logger.error(f"Erreur critique transformation : {e}")
        return False

    # ── ÉTAPE 4 : LOAD CLEAN → POSTGRESQL ────────────────────────
    if not args.skip_postgres:
        logger.info(
            "── ÉTAPE 4 : CHARGEMENT CLEAN → POSTGRESQL "
            "(Data Warehouse) ──"
        )
        try:
            pg = PostgresLoader()
            if pg.connecter():
                pg.creer_tables()
                pg.inserer_groupes(groupes)
                pg.inserer_deputes(deputes_clean)
                pg.inserer_scrutins(scrutins_clean)
                pg.inserer_stats({
                    "acteurs_bruts":   deputes_collector.nb_acteurs_bruts,
                    "acteurs_ignores": deputes_collector.nb_ignores,
                    "acteurs_retenus": len(deputes_bruts),
                    "scrutins_bruts":  len(scrutins_bruts),
                    "scrutins_nets":   len(scrutins_clean),
                    "groupes":         len(groupes),
                })
            else:
                logger.warning(
                    "PostgreSQL non disponible — "
                    "données propres non sauvegardées"
                )
        except Exception as e:
            logger.warning(f"Erreur PostgreSQL (non bloquant) : {e}")
    else:
        logger.info("PostgreSQL ignoré (--skip-postgres)")

    # ── RÉSUMÉ FINAL ─────────────────────────────────────────────
    logger.info("=" * 60)
    logger.success("PIPELINE TERMINÉ AVEC SUCCÈS")
    logger.info(f"  Groupes politiques : {len(groupes)}")
    logger.info(f"  ── NETTOYAGE DÉPUTÉS ──────────────────────")
    logger.info(
        f"  Acteurs bruts (AMO30)         : "
        f"{deputes_collector.nb_acteurs_bruts:,}"
    )
    logger.info(
        f"  Ignorés (autres législatures) : "
        f"{deputes_collector.nb_ignores:,}"
    )
    logger.info(f"  Retenus (17e lég. actifs)     : {len(deputes_bruts):,}")
    logger.info(f"  Députés nettoyés              : {len(deputes_clean):,}")
    logger.info(f"  ── SCRUTINS ───────────────────────────────")
    logger.info(f"  Scrutins collectés : {len(scrutins_bruts):,}")
    logger.info(f"  Scrutins nettoyés  : {len(scrutins_clean):,}")
    logger.info("=" * 60)
    return True


# ─── Point d'entrée ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = parse_args()
    succes = run_pipeline(args)
    sys.exit(0 if succes else 1)