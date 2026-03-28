"""
Module de transformation et nettoyage des données.
Normalise les députés, scrutins et groupes avant chargement.
"""

import re
from datetime import datetime
from loguru import logger
from dataclasses import dataclass, field
from typing import Optional


# ─── Modèles enrichis ────────────────────────────────────────────────────────

@dataclass
class DeputeClean:
    """Député nettoyé et enrichi avec son groupe politique."""
    uid: str
    nom: str
    prenom: str
    nom_complet: str
    civilite: Optional[str]              = None
    date_naissance: Optional[str]        = None
    age: Optional[int]                   = None
    lieu_naissance: Optional[str]        = None
    departement_naissance: Optional[str] = None
    profession: Optional[str]            = None
    groupe_sigle: Optional[str]          = None
    groupe_nom: Optional[str]            = None
    url_photo: Optional[str]             = None
    collecte_le: str                     = field(
        default_factory=lambda: datetime.now().isoformat()
    )


@dataclass
class ScrutinClean:
    """Scrutin nettoyé et enrichi."""
    uid: str
    numero: Optional[int]                = None
    titre: Optional[str]                 = None
    titre_court: Optional[str]           = None
    date: Optional[str]                  = None
    annee: Optional[int]                 = None
    mois: Optional[int]                  = None
    legislature: Optional[str]           = None
    type_vote: Optional[str]             = None
    sort: Optional[str]                  = None
    adopte: Optional[bool]               = None
    pour: int                            = 0
    contre: int                          = 0
    abstention: int                      = 0
    non_votant: int                      = 0
    total_votants: int                   = 0
    taux_participation: Optional[float]  = None
    collecte_le: str                     = field(
        default_factory=lambda: datetime.now().isoformat()
    )


# ─── Classe principale ────────────────────────────────────────────────────────

class DataCleaner:
    """
    Nettoie et normalise les données brutes collectées.
    Le groupe politique est déjà résolu dans DeputesCollector.
    """

    TOTAL_DEPUTES = 577  # Assemblée nationale française

    def __init__(self):
        logger.info("Initialisation de DataCleaner")

    # ── Point d'entrée principal ──────────────────────────────────────────────

    def transformer(
        self,
        deputes_bruts: list,
        scrutins_bruts: list,
        groupes_bruts: list,
        organes_bruts: list = None,
    ) -> tuple[list[DeputeClean], list[ScrutinClean]]:
        """
        Transforme toutes les données brutes.

        Args:
            deputes_bruts: Liste de Depute depuis DeputesCollector
            scrutins_bruts: Liste de Scrutin depuis ScrutinsCollector
            groupes_bruts: Liste de GroupePolitique depuis GroupesScraper
            organes_bruts: Non utilisé, conservé pour compatibilité

        Returns:
            Tuple (deputes_clean, scrutins_clean)
        """
        logger.info("Début de la transformation des données")

        # Mapping sigle → nom complet du groupe depuis le scraping HTML
        mapping_nom_groupe = {g.sigle: g.nom for g in groupes_bruts}

        deputes_clean  = self._nettoyer_deputes(deputes_bruts, mapping_nom_groupe)
        scrutins_clean = self._nettoyer_scrutins(scrutins_bruts)

        logger.success(
            f"Transformation terminée — "
            f"{len(deputes_clean)} députés / {len(scrutins_clean)} scrutins"
        )
        return deputes_clean, scrutins_clean

    # ── Nettoyage des députés ─────────────────────────────────────────────────

    def _nettoyer_deputes(
        self,
        deputes: list,
        mapping_nom_groupe: dict,
    ) -> list[DeputeClean]:
        """
        Nettoie et enrichit la liste des députés.
        Le groupe_sigle est déjà résolu dans DeputesCollector.

        Args:
            deputes: Liste brute de Depute
            mapping_nom_groupe: sigle → nom_groupe

        Returns:
            Liste de DeputeClean — uniquement les députés avec un groupe
        """
        results = []
        sans_groupe = 0

        for d in deputes:
            try:
                nom    = self._nettoyer_texte(d.nom)
                prenom = self._nettoyer_texte(d.prenom)

                if not nom or not prenom:
                    continue

                nom_complet  = f"{prenom} {nom}"
                age          = self._calculer_age(d.date_naissance)
                groupe_sigle = d.groupe_sigle
                groupe_nom   = mapping_nom_groupe.get(groupe_sigle) \
                               if groupe_sigle else None

                if not groupe_sigle:
                    sans_groupe += 1
                    continue  # On ne garde que les députés actifs avec groupe

                results.append(DeputeClean(
                    uid=d.uid,
                    nom=nom,
                    prenom=prenom,
                    nom_complet=nom_complet,
                    civilite=d.civilite,
                    date_naissance=d.date_naissance,
                    age=age,
                    lieu_naissance=self._nettoyer_texte(d.lieu_naissance),
                    departement_naissance=self._nettoyer_texte(
                        d.departement_naissance
                    ),
                    profession=self._nettoyer_texte(d.profession),
                    groupe_sigle=groupe_sigle,
                    groupe_nom=groupe_nom,
                    url_photo=d.url_photo,
                ))

            except Exception as e:
                logger.warning(f"Erreur nettoyage député {d.uid} : {e}")
                continue

        logger.info(
            f"Députés nettoyés : {len(results)} actifs "
            f"({sans_groupe} sans groupe ignorés)"
        )
        return results

    # ── Nettoyage des scrutins ────────────────────────────────────────────────

    def _nettoyer_scrutins(self, scrutins: list) -> list[ScrutinClean]:
        """
        Nettoie et enrichit la liste des scrutins.

        Args:
            scrutins: Liste brute de Scrutin

        Returns:
            Liste de ScrutinClean
        """
        results = []

        for s in scrutins:
            try:
                numero = None
                try:
                    numero = int(s.numero) if s.numero else None
                except (ValueError, TypeError):
                    pass

                date_str = s.date
                annee    = None
                mois     = None
                if date_str:
                    try:
                        dt    = datetime.strptime(date_str, "%Y-%m-%d")
                        annee = dt.year
                        mois  = dt.month
                    except ValueError:
                        pass

                adopte = None
                if s.sort:
                    adopte = "adopt" in s.sort.lower()

                total = s.pour + s.contre + s.abstention
                taux  = round((total / self.TOTAL_DEPUTES) * 100, 1) \
                        if total > 0 else None

                titre_court = None
                if s.titre:
                    titre_court = s.titre[:100].strip()
                    if len(s.titre) > 100:
                        titre_court += "..."

                results.append(ScrutinClean(
                    uid=s.uid,
                    numero=numero,
                    titre=self._nettoyer_texte(s.titre),
                    titre_court=titre_court,
                    date=date_str,
                    annee=annee,
                    mois=mois,
                    legislature=s.legislature,
                    type_vote=s.type_vote,
                    sort=s.sort,
                    adopte=adopte,
                    pour=s.pour,
                    contre=s.contre,
                    abstention=s.abstention,
                    non_votant=s.non_votant,
                    total_votants=total,
                    taux_participation=taux,
                ))

            except Exception as e:
                logger.warning(f"Erreur nettoyage scrutin {s.uid} : {e}")
                continue

        logger.info(f"Scrutins nettoyés : {len(results)}")
        return results

    # ── Utilitaires ───────────────────────────────────────────────────────────

    def _nettoyer_texte(self, texte: Optional[str]) -> Optional[str]:
        """Nettoie une chaîne de caractères."""
        if not texte:
            return None
        try:
            texte = str(texte).strip()
            texte = re.sub(r"\s+", " ", texte)
            return texte if texte else None
        except Exception:
            return None

    def _calculer_age(self, date_naissance: Optional[str]) -> Optional[int]:
        """Calcule l'âge depuis une date de naissance au format YYYY-MM-DD."""
        if not date_naissance:
            return None
        try:
            naissance   = datetime.strptime(date_naissance, "%Y-%m-%d")
            aujourd_hui = datetime.now()
            age = aujourd_hui.year - naissance.year
            if (aujourd_hui.month, aujourd_hui.day) < \
               (naissance.month, naissance.day):
                age -= 1
            return age if 18 <= age <= 100 else None
        except (ValueError, TypeError):
            return None