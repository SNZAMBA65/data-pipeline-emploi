"""
Script d'exécution automatique des notebooks d'analyse.
Génère les visualisations PNG et les CSV dans data/processed/

Usage :
    python scripts/run_notebooks.py
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

notebooks = [
    "notebooks/01_exploration.ipynb",
    "notebooks/02_analyse_scrutins.ipynb",
    "notebooks/03_analyse_deputes.ipynb",
]

print("=" * 55)
print("EXÉCUTION DES NOTEBOOKS — ASSEMBLÉE NATIONALE")
print("=" * 55)

for nb in notebooks:
    chemin = BASE_DIR / nb
    print(f"\n  Exécution de {nb}...")
    try:
        subprocess.run([
            "jupyter", "nbconvert",
            "--to", "notebook",
            "--execute",
            "--inplace",
            "--ExecutePreprocessor.timeout=300",
            str(chemin)
        ], check=True)
        print(f"  ✅ {nb} terminé")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Erreur sur {nb} : {e}")
        sys.exit(1)

print("\n" + "=" * 55)
print("NOTEBOOKS TERMINÉS")
print("  Visualisations → data/processed/*.png")
print("  Exports CSV    → data/processed/*.csv")
print("=" * 55)