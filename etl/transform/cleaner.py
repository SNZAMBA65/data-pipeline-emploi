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
    Enrichit les députés avec leur groupe politique.
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
            organes_bruts: Données organes du ZIP (optionnel)

        Returns:
            Tuple (deputes_clean, scrutins_clean)
        """
        logger.info("Début de la transformation des données")

        # Construit le mapping uid_depute → groupe
        mapping_groupe = self._construire_mapping_groupes(
            groupes_bruts, organes_bruts
        )
        logger.info(f"Mapping groupe : {len(mapping_groupe)} entrées")

        # Construit le mapping sigle → nom complet du groupe
        mapping_nom_groupe = {g.sigle: g.nom for g in groupes_bruts}

        deputes_clean = self._nettoyer_deputes(
            deputes_bruts, mapping_groupe, mapping_nom_groupe
        )
        scrutins_clean = self._nettoyer_scrutins(scrutins_bruts)

        logger.success(
            f"Transformation terminée — "
            f"{len(deputes_clean)} députés / {len(scrutins_clean)} scrutins"
        )
        return deputes_clean, scrutins_clean

    # ── Mapping groupe ────────────────────────────────────────────────────────

    def _construire_mapping_groupes(
        self,
        groupes: list,
        organes_bruts: list = None
    ) -> dict[str, str]:
        """
        Construit un mapping uid_depute → sigle_groupe
        depuis les données des organes du ZIP officiel.

        Args:
            groupes: Liste de GroupePolitique
            organes_bruts: Données organes du ZIP (optionnel)

        Returns:
            Dict {uid_depute: sigle_groupe}
        """
        mapping = {}

        try:
            if organes_bruts:
                # Utilise les données organes du ZIP
                for organe in organes_bruts:
                    try:
                        o = organe.get("organe", organe)
                        code_type = o.get("codeType", "")

                        # GP = Groupe Politique
                        if code_type != "GP":
                            continue

                        libelle = o.get("libelle", "")
                        sigle = self._trouver_sigle_depuis_libelle(
                            libelle, groupes
                        )

                        if not sigle:
                            continue

                        # Membres de l'organe
                        membres = (
                            o.get("membres", {})
                             .get("membre", [])
                        )
                        if isinstance(membres, dict):
                            membres = [membres]

                        for membre in membres:
                            uid = membre.get("acteurRef", "")
                            if uid:
                                mapping[uid] = sigle

                    except Exception as e:
                        logger.warning(f"Erreur organe : {e}")
                        continue

            logger.info(f"Mapping depuis organes : {len(mapping)} entrées")

        except Exception as e:
            logger.error(f"Erreur construction mapping : {e}")

        return mapping

    def _trouver_sigle_depuis_libelle(
        self, libelle: str, groupes: list
    ) -> Optional[str]:
        """
        Cherche le sigle correspondant à un libellé d'organe.

        Args:
            libelle: Nom de l'organe
            groupes: Liste des groupes scrapés

        Returns:
            Sigle du groupe ou None
        """
        libelle_lower = libelle.lower()

        for groupe in groupes:
            if (
                groupe.nom.lower() in libelle_lower
                or libelle_lower in groupe.nom.lower()
                or groupe.slug.replace("-", " ") in libelle_lower
            ):
                return groupe.sigle

        return None

    # ── Nettoyage des députés ─────────────────────────────────────────────────

    def _nettoyer_deputes(
        self,
        deputes: list,
        mapping_groupe: dict,
        mapping_nom_groupe: dict,
    ) -> list[DeputeClean]:
        """
        Nettoie et enrichit la liste des députés.

        Args:
            deputes: Liste brute de Depute
            mapping_groupe: uid → sigle_groupe
            mapping_nom_groupe: sigle → nom_groupe

        Returns:
            Liste de DeputeClean
        """
        results = []
        sans_groupe = 0

        for d in deputes:
            try:
                # Nettoyage des chaînes
                nom    = self._nettoyer_texte(d.nom)
                prenom = self._nettoyer_texte(d.prenom)

                if not nom or not prenom:
                    continue

                nom_complet = f"{prenom} {nom}"

                # Calcul de l'âge
                age = self._calculer_age(d.date_naissance)

                # Groupe politique
                groupe_sigle = mapping_groupe.get(d.uid)
                groupe_nom   = mapping_nom_groupe.get(groupe_sigle) \
                               if groupe_sigle else None

                if not groupe_sigle:
                    sans_groupe += 1

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
            f"Députés nettoyés : {len(results)} "
            f"({sans_groupe} sans groupe)"
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
                # Numéro en entier
                numero = None
                try:
                    numero = int(s.numero) if s.numero else None
                except (ValueError, TypeError):
                    pass

                # Date
                date_str = s.date
                annee    = None
                mois     = None
                if date_str:
                    try:
                        dt   = datetime.strptime(date_str, "%Y-%m-%d")
                        annee = dt.year
                        mois  = dt.month
                    except ValueError:
                        pass

                # Sort → booléen
                adopte = None
                if s.sort:
                    adopte = "adopt" in s.sort.lower()

                # Total votants et taux de participation
                total = s.pour + s.contre + s.abstention
                taux  = round((total / self.TOTAL_DEPUTES) * 100, 1) \
                        if total > 0 else None

                # Titre court (100 premiers caractères)
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
        """
        Nettoie une chaîne de caractères.
        Supprime les espaces multiples et les caractères parasites.
        """
        if not texte:
            return None
        try:
            texte = str(texte).strip()
            texte = re.sub(r"\s+", " ", texte)
            return texte if texte else None
        except Exception:
            return None

    def _calculer_age(self, date_naissance: Optional[str]) -> Optional[int]:
        """
        Calcule l'âge depuis une date de naissance au format YYYY-MM-DD.
        """
        if not date_naissance:
            return None
        try:
            naissance = datetime.strptime(date_naissance, "%Y-%m-%d")
            aujourd_hui = datetime.now()
            age = aujourd_hui.year - naissance.year
            if (aujourd_hui.month, aujourd_hui.day) < \
               (naissance.month, naissance.day):
                age -= 1
            return age if 18 <= age <= 100 else None
        except (ValueError, TypeError):
            return None