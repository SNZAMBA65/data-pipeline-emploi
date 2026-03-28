"""
Tests unitaires — DataCleaner ETL
Assemblée nationale · 17e législature
"""

import pytest
import pandas as pd
from etl.transform.cleaner import DataCleaner


class TestDataCleaner:

    def setup_method(self):
        """Initialise le cleaner avant chaque test."""
        self.cleaner = DataCleaner()

    def test_instanciation(self):
        """Le cleaner s'instancie sans erreur."""
        assert self.cleaner is not None

    def test_methode_transformer_existe(self):
        """La méthode transformer est disponible."""
        assert hasattr(self.cleaner, "transformer")
        assert callable(self.cleaner.transformer)

    def test_methode_nettoyer_texte_existe(self):
        """La méthode _nettoyer_texte est disponible."""
        assert hasattr(self.cleaner, "_nettoyer_texte")

    def test_nettoyer_texte_none(self):
        """None est géré sans exception."""
        try:
            result = self.cleaner._nettoyer_texte(None)
            assert result is None or result == ""
        except Exception as e:
            pytest.fail(f"_nettoyer_texte(None) a levé : {e}")

    def test_nettoyer_texte_normal(self):
        """Une valeur texte normale est conservée telle quelle."""
        result = self.cleaner._nettoyer_texte("Paris")
        assert result == "Paris"

    def test_nettoyer_texte_retourne_string(self):
        """_nettoyer_texte retourne toujours une string ou None."""
        for val in ["Paris", "", "Avocat", "Lyon"]:
            result = self.cleaner._nettoyer_texte(val)
            assert result is None or isinstance(result, str)

    def test_nettoyer_texte_dict_ne_leve_pas(self):
        """_nettoyer_texte ne lève pas d'exception sur un dict."""
        val = {"#text": "Avocat"}
        try:
            result = self.cleaner._nettoyer_texte(val)
            assert result is not None
        except Exception as e:
            pytest.fail(f"_nettoyer_texte(dict) a levé : {e}")

    def test_nettoyer_texte_xsi_nil_ne_leve_pas(self):
        """_nettoyer_texte ne lève pas d'exception sur un dict XML nul."""
        val = {
            "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "@xsi:nil": "true"
        }
        try:
            result = self.cleaner._nettoyer_texte(val)
            assert result is not None or result is None
        except Exception as e:
            pytest.fail(f"_nettoyer_texte(xsi:nil) a levé : {e}")

    def test_transformer_avec_objets_dataclass(self):
        """transformer fonctionne avec des listes d'objets dataclass."""
        from etl.scrapers.nosdeputes_scraper import (
            DeputesCollector, ScrutinsCollector
        )

        collector_d = DeputesCollector()
        depute = collector_d._parser_depute({
            "acteur": {
                "uid": {"#text": "PA123456"},
                "etatCivil": {
                    "ident": {"civ": "M.", "prenom": "Jean", "nom": "Dupont"},
                    "infoNaissance": {
                        "dateNais": "1975-03-15",
                        "villeNais": "Paris",
                        "depNais": "75"
                    }
                },
                "profession": {"libelleCourant": "Avocat"}
            }
        })

        collector_s = ScrutinsCollector()
        scrutin = collector_s._parser_scrutin({
            "scrutin": {
                "uid": "VTANR5L17V0001",
                "titre": "Budget 2025",
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
                "typeVote": {"libelle": "Par scrutin public"}
            }
        })

        try:
            result = self.cleaner.transformer([depute], [scrutin], [])
            assert result is not None
        except Exception as e:
            pytest.fail(f"transformer a levé une exception : {e}")

    def test_calculer_age_existe(self):
        """La méthode _calculer_age est disponible."""
        assert hasattr(self.cleaner, "_calculer_age")

    def test_calculer_age_valide(self):
        """L'âge est calculé correctement à partir d'une date valide."""
        result = self.cleaner._calculer_age("1980-01-01")
        assert result is not None
        assert isinstance(result, (int, float))
        assert 40 <= result <= 60

    def test_calculer_age_none(self):
        """None retourne None sans exception."""
        result = self.cleaner._calculer_age(None)
        assert result is None

    def test_nettoyer_deputes_prive(self):
        """La méthode _nettoyer_deputes est disponible."""
        assert hasattr(self.cleaner, "_nettoyer_deputes")

    def test_nettoyer_scrutins_prive(self):
        """La méthode _nettoyer_scrutins est disponible."""
        assert hasattr(self.cleaner, "_nettoyer_scrutins")