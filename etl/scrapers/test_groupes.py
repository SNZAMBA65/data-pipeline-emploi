"""Test du scraper des groupes politiques."""
from loguru import logger
from groupes_scraper import GroupesScraper

if __name__ == "__main__":
    logger.info("=== Test GroupesScraper ===")

    scraper = GroupesScraper()
    groupes = scraper.collecter()

    if groupes:
        logger.success(f"{len(groupes)} groupes collectés")
        print()
        for g in groupes:
            print(f"  [{g.sigle:10}] {g.nom[:45]:45} — {g.nb_membres} membres")

        mapping = scraper.construire_mapping_slug_sigle()
        logger.info(f"Mapping slug→sigle : {len(mapping)} entrées")
        for slug, sigle in mapping.items():
            print(f"  {slug:50} → {sigle}")
    else:
        logger.error("Aucun groupe collecté")