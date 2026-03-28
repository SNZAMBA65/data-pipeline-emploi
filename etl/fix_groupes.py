"""
Script de correction du mapping groupe_sigle pour les députés.
Lit les fichiers acteurs et organes du ZIP officiel pour établir
le lien uid_depute → groupe_sigle, puis met à jour PostgreSQL.

Usage :
    python etl/fix_groupes.py
"""

import json
import zipfile
import urllib.request
import tempfile
import os
from sqlalchemy import create_engine, text
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────────

ZIP_URL = (
    "https://data.assemblee-nationale.fr/static/openData/repository/17/"
    "amo/deputes_actifs_mandats_actifs_organes/"
    "AMO10_deputes_actifs_mandats_actifs_organes.json.zip"
)

DB_URL = "postgresql+psycopg2://jobs_user:jobs_password123@localhost:5432/jobs_db"

# Mapping libelleAbrege → sigle en base (normalisation)
SIGLE_MAP = {
    "RN":       "RN",
    "EPR":      "EPR",
    "LFI-NFP":  "LFI-NFP",
    "SOC":      "SOC",
    "DR":       "DR",
    "ECO":      "ECO",
    "EcoS":     "ECO",
    "DEM":      "DEM",
    "Dem":      "DEM",
    "HOR":      "HOR",
    "LIOT":     "LIOT",
    "GDR":      "GDR",
    "UDR":      "UDR",
    "NI":       "NI",
}


def telecharger_zip() -> str:
    """Télécharge le ZIP et retourne le chemin local."""
    logger.info("Téléchargement du ZIP officiel...")
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
        urllib.request.urlretrieve(ZIP_URL, f.name)
        logger.info(f"ZIP téléchargé : {f.name}")
        return f.name


def construire_mapping_organe_sigle(z: zipfile.ZipFile) -> dict:
    """
    Construit le mapping organeRef (PO...) → sigle
    depuis les fichiers organe de type GP.
    """
    mapping = {}
    organes = [n for n in z.namelist() if "organe" in n.lower()]
    logger.info(f"Lecture de {len(organes)} fichiers organes...")

    for name in organes:
        try:
            with z.open(name) as f:
                data = json.load(f)
                o = data.get("organe", {})
                if o.get("codeType") != "GP":
                    continue
                uid_organe = o.get("uid", "")
                sigle_brut = o.get("libelleAbrege", "")
                sigle = SIGLE_MAP.get(sigle_brut, sigle_brut)
                if uid_organe and sigle:
                    mapping[uid_organe] = sigle
        except Exception as e:
            logger.warning(f"Erreur organe {name} : {e}")
            continue

    logger.info(f"Mapping organe → sigle : {len(mapping)} entrées")
    for k, v in mapping.items():
        logger.debug(f"  {k} → {v}")
    return mapping


def construire_mapping_depute_groupe(
    z: zipfile.ZipFile,
    mapping_organe: dict
) -> dict:
    """
    Construit le mapping uid_acteur (PA...) → sigle_groupe
    depuis les mandats de type GP dans les fichiers acteurs.
    """
    mapping = {}
    acteurs = [n for n in z.namelist() if "acteur" in n.lower()]
    logger.info(f"Lecture de {len(acteurs)} fichiers acteurs...")

    for name in acteurs:
        try:
            with z.open(name) as f:
                data = json.load(f)
                acteur = data.get("acteur", {})

                uid_acteur = acteur.get("uid", {})
                if isinstance(uid_acteur, dict):
                    uid_acteur = uid_acteur.get("#text", "")

                if not uid_acteur:
                    continue

                mandats = acteur.get("mandats", {}).get("mandat", [])
                if isinstance(mandats, dict):
                    mandats = [mandats]

                for mandat in mandats:
                    if mandat.get("typeOrgane") != "GP":
                        continue
                    if mandat.get("dateFin") is not None:
                        continue  # Mandat terminé

                    organe_ref = (
                        mandat.get("organes", {}).get("organeRef", "")
                    )
                    sigle = mapping_organe.get(organe_ref)
                    if sigle:
                        mapping[uid_acteur] = sigle
                        break

        except Exception as e:
            logger.warning(f"Erreur acteur {name} : {e}")
            continue

    logger.info(f"Mapping depute → groupe : {len(mapping)} entrées")
    return mapping


def mettre_a_jour_postgres(mapping_depute: dict) -> None:
    """
    Met à jour la colonne groupe_sigle dans la table deputes
    et corrige le nb_membres dans groupes_politiques.
    """
    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        # Met à jour groupe_sigle pour chaque député
        logger.info("Mise à jour de groupe_sigle dans PostgreSQL...")
        updated = 0
        for uid, sigle in mapping_depute.items():
            result = conn.execute(
                text(
                    "UPDATE deputes SET groupe_sigle = :sigle "
                    "WHERE uid = :uid"
                ),
                {"sigle": sigle, "uid": uid}
            )
            updated += result.rowcount

        logger.success(f"{updated} députés mis à jour avec leur groupe")

        # Recalcule nb_membres pour chaque groupe
        logger.info("Recalcul du nb_membres par groupe...")
        conn.execute(text("""
            UPDATE groupes_politiques gp
            SET nb_membres = (
                SELECT COUNT(*)
                FROM deputes d
                WHERE d.groupe_sigle = gp.sigle
            )
        """))
        logger.success("nb_membres recalculé pour tous les groupes")

        # Affiche le résultat
        result = conn.execute(text("""
            SELECT sigle, nb_membres
            FROM groupes_politiques
            ORDER BY nb_membres DESC
        """))
        logger.info("Groupes politiques après mise à jour :")
        for row in result:
            logger.info(f"  {row[0]:10s} : {row[1]} membres")

        # Vérifie les députés sans groupe
        result = conn.execute(text(
            "SELECT COUNT(*) FROM deputes WHERE groupe_sigle IS NULL"
        ))
        sans_groupe = result.scalar()
        logger.info(f"Députés sans groupe : {sans_groupe}")


def main():
    logger.info("=" * 50)
    logger.info("FIX GROUPES — Assemblée nationale")
    logger.info("=" * 50)

    zip_path = telecharger_zip()

    with zipfile.ZipFile(zip_path) as z:
        mapping_organe = construire_mapping_organe_sigle(z)
        mapping_depute = construire_mapping_depute_groupe(z, mapping_organe)

    mettre_a_jour_postgres(mapping_depute)

    os.unlink(zip_path)
    logger.success("Script terminé avec succès")


if __name__ == "__main__":
    main()