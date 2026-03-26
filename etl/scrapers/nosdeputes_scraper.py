"""
Collecteurs de données pour l'Assemblée nationale française.
Source : data.assemblee-nationale.fr (Licence Ouverte / Open Licence)

Architecture :
    BaseCollector          → gestion HTTP, téléchargement ZIP
    ├── DeputesCollector   → collecte les députés (un JSON par acteur)
    └── ScrutinsCollector  → collecte les scrutins/votes (un JSON par scrutin)
"""

import io
import json
import zipfile
import requests
from loguru import logger
from fake_useragent import UserAgent
from dataclasses import dataclass
from typing import Optional


# ─── Modèles de données ───────────────────────────────────────────────────────

@dataclass
class Depute:
    """Représente un député de l'Assemblée nationale."""
    uid: str
    nom: str
    prenom: str
    civilite: Optional[str]              = None
    date_naissance: Optional[str]        = None
    lieu_naissance: Optional[str]        = None
    departement_naissance: Optional[str] = None
    profession: Optional[str]            = None
    url_photo: Optional[str]             = None


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

        Args:
            url: URL du fichier ZIP

        Returns:
            ZipFile ouvert en mémoire, ou None en cas d'erreur
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
        """
        Lit et parse un fichier JSON depuis un ZIP ouvert.

        Args:
            zip_file: ZipFile ouvert
            chemin: Chemin du fichier JSON dans le ZIP

        Returns:
            Données JSON parsées, ou None en cas d'erreur
        """
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
    Collecte les députés depuis l'OpenData de l'Assemblée nationale.

    Le ZIP contient un fichier JSON par acteur dans json/acteur/PA{id}.json.
    Structure d'un fichier :
        {
          "acteur": {
            "uid": {"#text": "PA267551"},
            "etatCivil": {
              "ident": {"civ": "M.", "prenom": "Jacques", "nom": "Lamblin"},
              "infoNaissance": {"dateNais": "1952-08-29", "villeNais": "Nancy"}
            },
            "profession": {"libelleCourant": "Vétérinaire"}
          }
        }
    """

    URL_ZIP = (
        "https://data.assemblee-nationale.fr/static/openData/repository/17/"
        "amo/tous_acteurs_mandats_organes_xi_legislature/"
        "AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip"
    )

    def __init__(self):
        super().__init__()
        self.deputes: list[Depute] = []

    def collecter(self, limite: Optional[int] = None) -> list[Depute]:
        """
        Télécharge et parse tous les acteurs du ZIP.

        Args:
            limite: Nombre maximum de députés (None = tous)

        Returns:
            Liste d'objets Depute
        """
        logger.info("Début collecte des députés — Assemblée nationale OpenData")

        try:
            zip_file = self._telecharger_zip(self.URL_ZIP)
            if zip_file is None:
                return []

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

                    depute = self._parser_depute(data)
                    if depute:
                        self.deputes.append(depute)

                except Exception as e:
                    logger.warning(f"Erreur sur {chemin} : {e}")
                    continue

            logger.success(f"Collecte terminée : {len(self.deputes)} députés")
            return self.deputes

        except Exception as e:
            logger.error(f"Erreur critique : {e}")
            return []

    def _extraire_valeur(self, valeur) -> Optional[str]:
        """
        Extrait une valeur string depuis un champ qui peut être
        un dict XML nul {"@xsi:nil": "true"} ou une chaîne.

        Args:
            valeur: La valeur brute du JSON

        Returns:
            Chaîne extraite ou None
        """
        if valeur is None:
            return None
        if isinstance(valeur, dict):
            if valeur.get("@xsi:nil") == "true":
                return None
            return valeur.get("#text")
        return str(valeur) if valeur else None

    def _parser_depute(self, data: dict) -> Optional[Depute]:
        """
        Parse les données brutes d'un acteur en objet Depute.
        Gère les champs nuls au format XML {"@xsi:nil": "true"}.

        Args:
            data: Dictionnaire brut depuis le JSON

        Returns:
            Objet Depute ou None si données invalides
        """
        try:
            acteur = data.get("acteur", {})

            # uid peut être un dict {"#text": "PA..."} ou une chaîne
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

            # Profession
            profession_data = acteur.get("profession", {})
            profession = None
            if isinstance(profession_data, dict):
                profession = self._extraire_valeur(
                    profession_data.get("libelleCourant")
                )

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
            )

        except Exception as e:
            logger.warning(f"Erreur parsing acteur : {e}")
            return None


# ─── Collecteur Scrutins ─────────────────────────────────────────────────────

class ScrutinsCollector(BaseCollector):
    """
    Collecte les scrutins depuis l'OpenData de l'Assemblée nationale.

    Le ZIP contient un fichier JSON par scrutin dans json/VTANR5L17V{n}.json.
    Structure d'un fichier :
        {
          "scrutin": {
            "uid": "VTANR5L17V2657",
            "numero": "2657",
            "dateScrutin": "2025-06-24",
            "legislature": "17",
            "typeVote": {"libelleTypeVote": "scrutin public ordinaire"},
            "sort": {"code": "adopté"},
            "titre": "...",
            "syntheseVote": {
              "decompte": {
                "pour": "312", "contre": "214",
                "abstentions": "18", "nonVotants": "6"
              }
            }
          }
        }
    """

    URL_ZIP = (
        "https://data.assemblee-nationale.fr/static/openData/repository/17/"
        "loi/scrutins/Scrutins.json.zip"
    )

    def __init__(self):
        super().__init__()
        self.scrutins: list[Scrutin] = []

    def collecter(self, limite: Optional[int] = None) -> list[Scrutin]:
        """
        Télécharge et parse tous les scrutins du ZIP.

        Args:
            limite: Nombre maximum de scrutins (None = tous)

        Returns:
            Liste d'objets Scrutin
        """
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

            logger.success(f"Collecte terminée : {len(self.scrutins)} scrutins")
            return self.scrutins

        except Exception as e:
            logger.error(f"Erreur critique : {e}")
            return []

    def _parser_scrutin(self, data: dict) -> Optional[Scrutin]:
        """
        Parse les données brutes d'un scrutin en objet Scrutin.

        Args:
            data: Dictionnaire brut depuis le JSON

        Returns:
            Objet Scrutin ou None si données invalides
        """
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
                """Convertit une valeur en entier de façon sécurisée."""
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