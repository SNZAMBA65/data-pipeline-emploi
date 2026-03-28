"""
Collecteurs de données pour l'Assemblée nationale française.
Source : data.assemblee-nationale.fr (Licence Ouverte / Open Licence)

Architecture :
    BaseCollector          → gestion HTTP, téléchargement ZIP
    ├── DeputesCollector   → collecte les députés actifs (17e législature)
    └── ScrutinsCollector  → collecte les scrutins/votes
"""

import io
import json
import zipfile
import requests
from loguru import logger
from fake_useragent import UserAgent
from dataclasses import dataclass, field
from typing import Optional


# ─── Modèles de données ───────────────────────────────────────────────────────

@dataclass
class Depute:
    """Représente un député actif de la 17e législature."""
    uid: str
    nom: str
    prenom: str
    civilite: Optional[str]              = None
    date_naissance: Optional[str]        = None
    lieu_naissance: Optional[str]        = None
    departement_naissance: Optional[str] = None
    profession: Optional[str]            = None
    url_photo: Optional[str]             = None
    groupe_sigle: Optional[str]          = None


@dataclass
class Scrutin:
    """Représente un scrutin (vote) à l'Assemblée nationale."""
    uid: str
    numero: Optional[str]       = None
    titre: Optional[str]        = None
    date: Optional[str]         = None
    legislature: Optional[str]  = None
    type_vote: Optional[str]    = None
    sort: Optional[str]         = None
    pour: int                   = 0
    contre: int                 = 0
    abstention: int             = 0
    non_votant: int             = 0


# ─── Mapping sigle officiel → sigle en base ───────────────────────────────────

SIGLE_MAP = {
    "RN":      "RN",
    "EPR":     "EPR",
    "LFI-NFP": "LFI-NFP",
    "SOC":     "SOC",
    "DR":      "DR",
    "ECO":     "ECO",
    "EcoS":    "ECO",
    "DEM":     "DEM",
    "Dem":     "DEM",
    "HOR":     "HOR",
    "LIOT":    "LIOT",
    "GDR":     "GDR",
    "UDR":     "UDR",
    "NI":      "NI",
}


# ─── Classe de base ───────────────────────────────────────────────────────────

class BaseCollector:
    """
    Classe de base pour tous les collecteurs.
    Gère la session HTTP et le téléchargement de fichiers ZIP.
    """

    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self._configure_session()
        logger.info(f"Initialisation de {self.__class__.__name__}")

    def _configure_session(self):
        """Configure les headers HTTP de la session."""
        self.session.headers.update({
            "User-Agent": self.ua.random,
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Accept": "application/zip,application/json,*/*",
        })

    def _telecharger_zip(self, url: str) -> Optional[zipfile.ZipFile]:
        """
        Télécharge un fichier ZIP et retourne un objet ZipFile en mémoire.
        """
        try:
            nom_fichier = url.split("/")[-1]
            logger.info(f"Téléchargement de {nom_fichier}...")

            response = self.session.get(url, timeout=60)
            response.raise_for_status()

            zip_bytes = io.BytesIO(response.content)
            zip_file  = zipfile.ZipFile(zip_bytes)

            logger.success(
                f"ZIP téléchargé — {len(zip_file.namelist())} fichier(s)"
            )
            return zip_file

        except requests.exceptions.Timeout:
            logger.error(f"Timeout lors du téléchargement de {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erreur HTTP {e.response.status_code} sur {url}")
            return None
        except zipfile.BadZipFile:
            logger.error(f"Fichier ZIP corrompu : {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau inattendue : {e}")
            return None

    def _lire_json(
        self, zip_file: zipfile.ZipFile, chemin: str
    ) -> Optional[dict]:
        """Lit et parse un fichier JSON depuis un ZIP ouvert."""
        try:
            with zip_file.open(chemin) as f:
                return json.loads(f.read().decode("utf-8"))
        except KeyError:
            logger.error(f"Fichier '{chemin}' introuvable dans le ZIP")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Erreur JSON dans '{chemin}' : {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur lecture '{chemin}' : {e}")
            return None


# ─── Collecteur Députés ───────────────────────────────────────────────────────

class DeputesCollector(BaseCollector):
    """
    Collecte les députés actifs de la 17e législature.
    Source : ZIP AMO10 contenant acteurs + mandats + organes.

    Le mapping groupe politique est construit depuis les organes
    et appliqué directement à chaque député.
    """

    URL_ZIP = (
        "https://data.assemblee-nationale.fr/static/openData/repository/17/"
        "amo/deputes_actifs_mandats_actifs_organes/"
        "AMO10_deputes_actifs_mandats_actifs_organes.json.zip"
    )

    def __init__(self):
        super().__init__()
        self.deputes: list[Depute] = []

    def _construire_mapping_organe_sigle(
        self, zip_file: zipfile.ZipFile
    ) -> dict:
        """
        Construit le mapping organeRef (PO...) → sigle
        depuis les fichiers organe de type GP.
        """
        mapping = {}
        organes = [
            f for f in zip_file.namelist()
            if "organe" in f.lower() and f.endswith(".json")
        ]

        for nom in organes:
            try:
                data = self._lire_json(zip_file, nom)
                if data is None:
                    continue
                o = data.get("organe", {})
                if o.get("codeType") != "GP":
                    continue
                uid_organe = o.get("uid", "")
                sigle_brut = o.get("libelleAbrege", "")
                sigle = SIGLE_MAP.get(sigle_brut, sigle_brut)
                if uid_organe and sigle:
                    mapping[uid_organe] = sigle
            except Exception:
                continue

        logger.info(f"Mapping organe → sigle : {len(mapping)} groupes")
        return mapping

    def _construire_mapping_depute_groupe(
        self,
        zip_file: zipfile.ZipFile,
        mapping_organe: dict
    ) -> dict:
        """
        Construit le mapping uid_acteur (PA...) → sigle_groupe
        depuis les mandats de type GP dans les fichiers acteurs.
        """
        mapping = {}
        acteurs = [
            f for f in zip_file.namelist()
            if "acteur" in f.lower() and f.endswith(".json")
        ]

        for nom in acteurs:
            try:
                data = self._lire_json(zip_file, nom)
                if data is None:
                    continue
                acteur = data.get("acteur", {})

                uid_raw = acteur.get("uid", {})
                uid = uid_raw.get("#text", "") \
                      if isinstance(uid_raw, dict) else uid_raw
                if not uid:
                    continue

                mandats = acteur.get("mandats", {}).get("mandat", [])
                if isinstance(mandats, dict):
                    mandats = [mandats]

                for mandat in mandats:
                    if mandat.get("typeOrgane") != "GP":
                        continue
                    if mandat.get("dateFin") is not None:
                        continue
                    organe_ref = mandat.get("organes", {}).get("organeRef", "")
                    sigle = mapping_organe.get(organe_ref)
                    if sigle:
                        mapping[uid] = sigle
                        break

            except Exception:
                continue

        logger.info(f"Mapping député → groupe : {len(mapping)} entrées")
        return mapping

    def collecter(self, limite: Optional[int] = None) -> list[Depute]:
        """
        Télécharge le ZIP AMO10, construit le mapping des groupes
        et parse les 575 députés actifs avec leur groupe politique.
        """
        logger.info(
            "Début collecte des députés actifs — 17e législature"
        )

        try:
            zip_file = self._telecharger_zip(self.URL_ZIP)
            if zip_file is None:
                return []

            # Mapping groupe depuis les organes
            mapping_organe = self._construire_mapping_organe_sigle(zip_file)
            mapping_depute = self._construire_mapping_depute_groupe(
                zip_file, mapping_organe
            )

            fichiers_acteurs = [
                f for f in zip_file.namelist()
                if f.startswith("json/acteur/") and f.endswith(".json")
            ]

            if limite:
                fichiers_acteurs = fichiers_acteurs[:limite]

            logger.info(f"{len(fichiers_acteurs)} fichiers acteurs à parser")

            for chemin in fichiers_acteurs:
                try:
                    data = self._lire_json(zip_file, chemin)
                    if data is None:
                        continue
                    depute = self._parser_depute(data, mapping_depute)
                    if depute:
                        self.deputes.append(depute)
                except Exception as e:
                    logger.warning(f"Erreur sur {chemin} : {e}")
                    continue

            logger.success(
                f"Collecte terminée : {len(self.deputes)} députés actifs"
            )
            return self.deputes

        except Exception as e:
            logger.error(f"Erreur critique : {e}")
            return []

    def _extraire_valeur(self, valeur) -> Optional[str]:
        """Extrait une valeur string depuis un champ XML potentiellement nul."""
        if valeur is None:
            return None
        if isinstance(valeur, dict):
            if valeur.get("@xsi:nil") == "true":
                return None
            return valeur.get("#text")
        return str(valeur) if valeur else None

    def _parser_depute(
        self, data: dict, mapping_groupe: dict = {}
    ) -> Optional[Depute]:
        """
        Parse les données brutes d'un acteur en objet Depute
        avec son groupe politique.
        """
        try:
            acteur = data.get("acteur", {})

            uid_raw = acteur.get("uid", {})
            uid = uid_raw.get("#text", "") \
                  if isinstance(uid_raw, dict) else uid_raw

            etat_civil = acteur.get("etatCivil", {})
            ident      = etat_civil.get("ident", {})
            naissance  = etat_civil.get("infoNaissance", {})

            nom    = ident.get("nom", "")
            prenom = ident.get("prenom", "")

            if not uid or not nom:
                return None

            profession_data = acteur.get("profession", {})
            profession = None
            if isinstance(profession_data, dict):
                profession = self._extraire_valeur(
                    profession_data.get("libelleCourant")
                )

            # Groupe politique depuis le mapping
            groupe_sigle = mapping_groupe.get(uid)

            return Depute(
                uid=uid,
                nom=nom,
                prenom=prenom,
                civilite=self._extraire_valeur(ident.get("civ")),
                date_naissance=self._extraire_valeur(
                    naissance.get("dateNais")
                ),
                lieu_naissance=self._extraire_valeur(
                    naissance.get("villeNais")
                ),
                departement_naissance=self._extraire_valeur(
                    naissance.get("depNais")
                ),
                profession=profession,
                url_photo=(
                    f"https://www.assemblee-nationale.fr"
                    f"/dyn/deputes/photos/{uid}.jpg"
                ),
                groupe_sigle=groupe_sigle,
            )

        except Exception as e:
            logger.warning(f"Erreur parsing acteur : {e}")
            return None


# ─── Collecteur Scrutins ─────────────────────────────────────────────────────

class ScrutinsCollector(BaseCollector):
    """
    Collecte les scrutins publics de la 17e législature.
    Source : ZIP Scrutins.json.zip
    """

    URL_ZIP = (
        "https://data.assemblee-nationale.fr/static/openData/repository/17/"
        "loi/scrutins/Scrutins.json.zip"
    )

    def __init__(self):
        super().__init__()
        self.scrutins: list[Scrutin] = []

    def collecter(self, limite: Optional[int] = None) -> list[Scrutin]:
        """Télécharge et parse tous les scrutins du ZIP."""
        logger.info("Début collecte des scrutins")

        try:
            zip_file = self._telecharger_zip(self.URL_ZIP)
            if zip_file is None:
                return []

            fichiers_scrutins = [
                f for f in zip_file.namelist()
                if f.startswith("json/") and f.endswith(".json")
            ]

            if limite:
                fichiers_scrutins = fichiers_scrutins[:limite]

            logger.info(f"{len(fichiers_scrutins)} scrutins à parser")

            for chemin in fichiers_scrutins:
                try:
                    data = self._lire_json(zip_file, chemin)
                    if data is None:
                        continue
                    scrutin = self._parser_scrutin(data)
                    if scrutin:
                        self.scrutins.append(scrutin)
                except Exception as e:
                    logger.warning(f"Erreur sur {chemin} : {e}")
                    continue

            logger.success(
                f"Collecte terminée : {len(self.scrutins)} scrutins"
            )
            return self.scrutins

        except Exception as e:
            logger.error(f"Erreur critique : {e}")
            return []

    def _parser_scrutin(self, data: dict) -> Optional[Scrutin]:
        """Parse les données brutes d'un scrutin en objet Scrutin."""
        try:
            s = data.get("scrutin", {})

            uid = s.get("uid", "")
            if not uid:
                return None

            type_vote = s.get("typeVote", {})
            sort      = s.get("sort", {})
            synthese  = s.get("syntheseVote", {})
            decompte  = synthese.get("decompte", {})

            def to_int(val) -> int:
                try:
                    return int(val or 0)
                except (ValueError, TypeError):
                    return 0

            return Scrutin(
                uid=uid,
                numero=s.get("numero"),
                titre=s.get("titre"),
                date=s.get("dateScrutin"),
                legislature=s.get("legislature"),
                type_vote=type_vote.get("libelleTypeVote")
                          if isinstance(type_vote, dict) else None,
                sort=sort.get("code")
                     if isinstance(sort, dict) else None,
                pour=to_int(decompte.get("pour")),
                contre=to_int(decompte.get("contre")),
                abstention=to_int(decompte.get("abstentions")),
                non_votant=to_int(decompte.get("nonVotants")),
            )

        except Exception as e:
            logger.warning(f"Erreur parsing scrutin : {e}")
            return None