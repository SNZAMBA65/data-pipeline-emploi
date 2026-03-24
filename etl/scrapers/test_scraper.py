"""Test des collecteurs Assemblée nationale."""
from loguru import logger
from nosdeputes_scraper import DeputesCollector, ScrutinsCollector

if __name__ == "__main__":

    # ── Test 1 : Députés ──────────────────────────────────────────
    logger.info("=== Test DeputesCollector ===")
    collector = DeputesCollector()
    deputes = collector.collecter()

    if deputes:
        logger.success(f"{len(deputes)} députés collectés")
        for d in deputes[:3]:
            print(f"  → {d.prenom} {d.nom} | {d.uid}")
    else:
        logger.error("Aucun député collecté")

    # ── Test 2 : Scrutins ─────────────────────────────────────────
    logger.info("=== Test ScrutinsCollector ===")
    scrutins = ScrutinsCollector().collecter(limite=5)

    if scrutins:
        logger.success(f"{len(scrutins)} scrutins collectés")
        for s in scrutins[:3]:
            print(f"  → [{s.date}] {s.titre[:60] if s.titre else '?'}... | {s.sort}")
    else:
        logger.error("Aucun scrutin collecté")