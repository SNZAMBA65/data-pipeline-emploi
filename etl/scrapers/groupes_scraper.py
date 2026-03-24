"""
Scraper HTML des groupes politiques de l'Assemblée nationale.
Source : assemblee-nationale.fr (pages statiques — licence ouverte)

Flux :
    1. Scrape la page listant tous les groupes (assemblee-nationale.fr/dyn/les-groupes-politiques)
    2. Pour chaque groupe, scrape sa page de détail sur www2.assemblee-nationale.fr
    3. Extrait le nom, sigle, président et membres visibles statiquement
    Note : la liste complète des membres est chargée en JavaScript —
           l'enrichissement complet se fait via le ZIP officiel dans le pipeline ETL.
"""

import time
import requests
from bs4 import BeautifulSoup
from loguru import logger
from fake_useragent import UserAgent
from dataclasses import dataclass, field
from typing import Optional


# ─── Modèle de données ───────────────────────────────────────────────────────

@dataclass
class GroupePolitique:
    """Représente un groupe politique à l'Assemblée nationale."""
    slug: str
    nom: str
    sigle: str
    president: Optional[str]       = None
    nb_membres: Optional[int]      = None
    membres_noms: list             = field(default_factory=list)
    declaration: Optional[str]     = None
    url: Optional[str]             = None


# ─── Scraper ─────────────────────────────────────────────────────────────────

class GroupesScraper:
    """
    Scrape les groupes politiques depuis assemblee-nationale.fr.
    Utilise BeautifulSoup pour parser le HTML statique.
    """

    PAGE_GROUPES  = "https://www.assemblee-nationale.fr/dyn/les-groupes-politiques"
    BASE_URL_W2   = "https://www2.assemblee-nationale.fr"
    DELAY         = 1.5

    # Slugs à exclure (pas des vrais groupes politiques)
    SLUGS_EXCLUS  = {"modifications-a-la-composition-des-groupes"}

    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.session.headers.update({
            "User-Agent": self.ua.random,
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Accept": "text/html,application/xhtml+xml,*/*",
            "Referer": "https://www.assemblee-nationale.fr",
        })
        self.groupes: list[GroupePolitique] = []
        logger.info("Initialisation de GroupesScraper")

    # ── Méthode principale ────────────────────────────────────────────────────

    def collecter(self) -> list[GroupePolitique]:
        """
        Collecte tous les groupes politiques.

        Returns:
            Liste d'objets GroupePolitique
        """
        logger.info("Début du scraping des groupes politiques")

        try:
            urls_groupes = self._extraire_urls_groupes()

            if not urls_groupes:
                logger.error("Aucun groupe trouvé")
                return []

            logger.info(f"{len(urls_groupes)} groupes à scraper")

            for url in urls_groupes:
                try:
                    time.sleep(self.DELAY)
                    groupe = self._scraper_groupe(url)
                    if groupe:
                        self.groupes.append(groupe)
                        logger.info(
                            f"  [{groupe.sigle:10}] {groupe.nom[:45]:45} "
                            f"— {groupe.nb_membres or 0} membres visibles"
                        )
                except Exception as e:
                    logger.warning(f"Erreur sur {url} : {e}")
                    continue

            logger.success(f"Scraping terminé : {len(self.groupes)} groupes")
            return self.groupes

        except Exception as e:
            logger.error(f"Erreur critique : {e}")
            return []

    # ── Extraction des URLs ───────────────────────────────────────────────────

    def _extraire_urls_groupes(self) -> list[str]:
        """
        Scrape la page principale pour extraire les URLs de chaque groupe.

        Returns:
            Liste d'URLs des pages de groupes
        """
        urls = []

        try:
            logger.debug(f"GET {self.PAGE_GROUPES}")
            response = self.session.get(self.PAGE_GROUPES, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            liens = soup.find_all(
                "a",
                href=lambda h: h and "les-groupes-politiques/" in str(h)
                and h != self.PAGE_GROUPES
            )

            vus = set()
            for lien in liens:
                href = lien.get("href", "")
                slug = href.rstrip("/").split("/")[-1]

                if (
                    slug
                    and slug not in vus
                    and slug not in self.SLUGS_EXCLUS
                    and slug != "les-groupes-politiques"
                ):
                    vus.add(slug)
                    urls.append(href)

            logger.debug(f"{len(urls)} URLs extraites")

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau : {e}")

        except Exception as e:
            logger.error(f"Erreur extraction URLs : {e}")

        return urls

    # ── Scraping d'un groupe ──────────────────────────────────────────────────

    def _scraper_groupe(self, url: str) -> Optional[GroupePolitique]:
        """
        Scrape la page d'un groupe.

        Args:
            url: URL de la page du groupe

        Returns:
            Objet GroupePolitique ou None en cas d'erreur
        """
        try:
            logger.debug(f"GET {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            slug = url.rstrip("/").split("/")[-1]

            nom       = self._extraire_nom(soup, slug)
            sigle     = self._extraire_sigle(slug, nom)
            president = self._extraire_president(soup)
            membres   = self._extraire_membres(soup)
            declaration = self._extraire_declaration(soup)

            return GroupePolitique(
                slug=slug,
                nom=nom,
                sigle=sigle,
                president=president,
                nb_membres=len(membres),
                membres_noms=membres,
                declaration=declaration,
                url=url,
            )

        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP {e.response.status_code} sur {url}")
            return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"Erreur réseau sur {url} : {e}")
            return None

        except Exception as e:
            logger.warning(f"Erreur scraping {url} : {e}")
            return None

    # ── Méthodes d'extraction ─────────────────────────────────────────────────

    def _extraire_nom(self, soup: BeautifulSoup, slug: str) -> str:
        """Extrait le nom du groupe depuis le H1 de la page."""
        try:
            h1 = soup.find("h1")
            if h1:
                return h1.get_text(strip=True)
        except Exception:
            pass
        return slug.replace("-", " ").title()

    def _extraire_sigle(self, slug: str, nom: str) -> str:
        """
        Retourne le sigle officiel depuis un mapping connu,
        ou le calcule depuis le nom.
        """
        sigles_connus = {
            "rassemblement-national":                                  "RN",
            "ensemble-pour-la-republique":                             "EPR",
            "la-france-insoumise-nouveau-front-populaire":             "LFI-NFP",
            "socialistes-et-apparentes":                               "SOC",
            "droite-republicaine":                                     "DR",
            "les-democrates":                                          "DEM",
            "ecologiste-et-social":                                    "ECO",
            "horizons-independants":                                   "HOR",
            "libertes-independants-outre-mer-et-territoires":          "LIOT",
            "gauche-democrate-et-republicaine":                        "GDR",
            "union-des-droites-pour-la-republique":                    "UDR",
            "deputes-non-inscrits":                                    "NI",
        }

        if slug in sigles_connus:
            return sigles_connus[slug]

        mots = [m for m in nom.split() if len(m) > 2 and m[0].isupper()]
        return "".join(m[0] for m in mots[:4]) if mots else slug[:6].upper()

    def _extraire_president(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extrait le nom du président depuis le texte statique de la page.
        """
        try:
            texte_complet = soup.get_text(separator="\n", strip=True)
            lignes = texte_complet.split("\n")

            for i, ligne in enumerate(lignes):
                if "président" in ligne.lower() and i + 1 < len(lignes):
                    candidat = lignes[i + 1].strip()
                    if (
                        candidat
                        and len(candidat) < 60
                        and " " in candidat
                        and candidat[0].isupper()
                    ):
                        return candidat

        except Exception:
            pass

        return None

    def _extraire_membres(self, soup: BeautifulSoup) -> list[str]:
        """
        Tente d'extraire les membres visibles statiquement.
        Note : la liste complète est chargée en JavaScript —
               l'enrichissement complet se fait via le ZIP officiel.

        Args:
            soup: Page parsée

        Returns:
            Liste partielle des noms visibles statiquement
        """
        membres = []

        try:
            texte_page = soup.get_text(separator="\n", strip=True)
            lignes = texte_page.split("\n")

            # Mots clés de navigation à ignorer
            mots_nav = [
                "Accueil", "Séance", "Commission", "Document", "Rapport",
                "Budget", "Question", "Assemblée", "Groupe", "Député",
                "Législ", "Visite", "Boutique", "Abonner", "Contacter",
                "Mentions", "Accessib", "Réseau", "Archives", "Compte",
            ]

            for ligne in lignes:
                ligne = ligne.strip()
                if (
                    4 < len(ligne) < 50
                    and " " in ligne
                    and ligne[0].isupper()
                    and not any(nav in ligne for nav in mots_nav)
                    and ligne not in membres
                ):
                    membres.append(ligne)

            # Garde les 10 premiers pour éviter le bruit
            membres = membres[:10]

        except Exception as e:
            logger.warning(f"Erreur extraction membres : {e}")

        return membres

    def _extraire_declaration(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extrait la déclaration politique du groupe si visible.

        Args:
            soup: Page parsée

        Returns:
            Texte de la déclaration ou None
        """
        try:
            # Cherche un paragraphe long qui ressemble à une déclaration
            for p in soup.find_all("p"):
                texte = p.get_text(strip=True)
                if len(texte) > 100:
                    return texte[:500]

        except Exception:
            pass

        return None

    # ── Utilitaire ────────────────────────────────────────────────────────────

    def construire_mapping_slug_sigle(self) -> dict[str, str]:
        """
        Construit un dictionnaire slug → sigle.

        Returns:
            Dict {slug: sigle}
        """
        return {g.slug: g.sigle for g in self.groupes}

    def to_dict_list(self) -> list[dict]:
        """
        Convertit la liste des groupes en liste de dictionnaires.
        Utile pour la sérialisation JSON vers MinIO.

        Returns:
            Liste de dicts
        """
        return [
            {
                "slug":        g.slug,
                "nom":         g.nom,
                "sigle":       g.sigle,
                "president":   g.president,
                "nb_membres":  g.nb_membres,
                "declaration": g.declaration,
                "url":         g.url,
            }
            for g in self.groupes
        ]