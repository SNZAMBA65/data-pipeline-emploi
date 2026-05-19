"""
Tests unitaires — Scrapers ETL
Assemblée nationale · 17e législature
"""

import pytest
from etl.scrapers.nosdeputes_scraper import DeputesCollector, ScrutinsCollector


class TestDeputesCollector:

    def test_instanciation(self):
        """Le collecteur s'instancie sans erreur."""
        collector = DeputesCollector()
        assert collector is not None

    def test_parse_depute_valide(self):
        """Un fichier JSON valide produit un objet Depute avec les attributs attendus."""
        collector = DeputesCollector()
        data = {
            "acteur": {
                "uid": {"#text": "PA123456"},
                "etatCivil": {
                    "ident": {
                        "civ": "M.",
                        "prenom": "Jean",
                        "nom": "Dupont"
                    },
                    "infoNaissance": {
                        "dateNais": "1975-03-15",
                        "villeNais": "Paris",
                        "depNais": "75"
                    }
                },
                "profession": {
                    "libelleCourant": "Avocat"
                }
            }
        }
        # On fournit un mapping avec le UID du député de test
        mapping = {"PA123456": "RN"}
        result = collector._parser_depute(data, mapping)
        assert result is not None
        assert hasattr(result, "uid")
        assert hasattr(result, "nom")
        assert hasattr(result, "prenom")
        assert result.uid == "PA123456"
        assert result.nom == "Dupont"
        assert result.prenom == "Jean"
        assert result.civilite == "M."

    def test_parse_depute_nil_xml(self):
        """Les valeurs XML nulles sont correctement gérées."""
        collector = DeputesCollector()
        data = {
            "acteur": {
                "uid": {"#text": "PA999999"},
                "etatCivil": {
                    "ident": {
                        "civ": "Mme",
                        "prenom": "Marie",
                        "nom": "Martin"
                    },
                    "infoNaissance": {
                        "dateNais": {
                            "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                            "@xsi:nil": "true"
                        },
                        "villeNais": "Lyon",
                        "depNais": "69"
                    }
                },
                "profession": {
                    "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                    "@xsi:nil": "true"
                }
            }
        }
        # On fournit un mapping avec le UID du député de test
        mapping = {"PA999999": "SOC"}
        result = collector._parser_depute(data, mapping)
        assert result is not None
        assert hasattr(result, "date_naissance")
        assert result.date_naissance is None or result.date_naissance == ""

    def test_parse_depute_champs_manquants(self):
        """Un JSON incomplet ne lève pas d'exception."""
        collector = DeputesCollector()
        data = {"acteur": {}}
        try:
            result = collector._parser_depute(data, {})
        except Exception as e:
            pytest.fail(f"_parser_depute a levé une exception inattendue : {e}")

    def test_parse_depute_attributs_complets(self):
        """L'objet Depute possède tous les attributs attendus."""
        collector = DeputesCollector()
        data = {
            "acteur": {
                "uid": {"#text": "PA111111"},
                "etatCivil": {
                    "ident": {
                        "civ": "M.",
                        "prenom": "Paul",
                        "nom": "Bernard"
                    },
                    "infoNaissance": {
                        "dateNais": "1980-06-20",
                        "villeNais": "Lyon",
                        "depNais": "69"
                    }
                },
                "profession": {
                    "libelleCourant": "Médecin"
                }
            }
        }
        # On fournit un mapping avec le UID du député de test
        mapping = {"PA111111": "EPR"}
        result = collector._parser_depute(data, mapping)
        attributs = [
            "uid", "nom", "prenom", "civilite",
            "date_naissance", "lieu_naissance", "profession"
        ]
        for attr in attributs:
            assert hasattr(result, attr), f"Attribut manquant : {attr}"


class TestScrutinsCollector:

    def test_instanciation(self):
        """Le collecteur de scrutins s'instancie sans erreur."""
        collector = ScrutinsCollector()
        assert collector is not None

    def test_parse_scrutin_valide(self):
        """Un scrutin JSON valide produit un objet Scrutin avec les attributs attendus."""
        collector = ScrutinsCollector()
        data = {
            "scrutin": {
                "uid": "VTANR5L17V0001",
                "titre": "Vote sur le budget 2025",
                "dateScrutin": "2024-10-15",
                "sort": {"code": "adopté"},
                "syntheseVote": {
                    "nombreVotants": 450,
                    "suffragesExprimes": 420,
                    "nbrSuffragesRequis": 211,
                    "pour": {"total": 250},
                    "contre": {"total": 170},
                    "abstentions": {"total": 30}
                },
                "typeVote": {
                    "libelle": "Par scrutin public"
                }
            }
        }
        result = collector._parser_scrutin(data)
        assert result is not None
        assert hasattr(result, "uid")
        assert hasattr(result, "sort")
        assert hasattr(result, "pour")
        assert hasattr(result, "contre")

    def test_parse_scrutin_sort_rejete(self):
        """Un scrutin rejeté est bien identifié."""
        collector = ScrutinsCollector()
        data = {
            "scrutin": {
                "uid": "VTANR5L17V0002",
                "titre": "Motion de censure",
                "dateScrutin": "2024-11-20",
                "sort": {"code": "rejeté"},
                "syntheseVote": {
                    "nombreVotants": 500,
                    "suffragesExprimes": 480,
                    "nbrSuffragesRequis": 241,
                    "pour": {"total": 200},
                    "contre": {"total": 280},
                    "abstentions": {"total": 20}
                },
                "typeVote": {
                    "libelle": "Par scrutin public"
                }
            }
        }
        result = collector._parser_scrutin(data)
        assert result is not None
        assert hasattr(result, "sort")
        assert result.sort in ["rejeté", "rejete", "non adopté"]

    def test_parse_scrutin_valeurs_numeriques(self):
        """Les votes Pour et Contre sont bien des nombres."""
        collector = ScrutinsCollector()
        data = {
            "scrutin": {
                "uid": "VTANR5L17V0003",
                "titre": "Test numérique",
                "dateScrutin": "2025-01-10",
                "sort": {"code": "adopté"},
                "syntheseVote": {
                    "nombreVotants": 300,
                    "suffragesExprimes": 290,
                    "nbrSuffragesRequis": 146,
                    "pour": {"total": 180},
                    "contre": {"total": 110},
                    "abstentions": {"total": 10}
                },
                "typeVote": {"libelle": "Par scrutin public"}
            }
        }
        result = collector._parser_scrutin(data)
        assert result is not None
        if hasattr(result, "pour") and result.pour is not None:
            assert isinstance(result.pour, (int, float))
        if hasattr(result, "contre") and result.contre is not None:
            assert isinstance(result.contre, (int, float))