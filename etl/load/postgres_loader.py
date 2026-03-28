"""
Chargement des données transformées dans PostgreSQL (Data Warehouse).
"""

import os
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()


class PostgresLoader:
    """
    Charge les données nettoyées dans PostgreSQL.
    Utilise SQLAlchemy pour la gestion des connexions.
    """

    def __init__(self):
        self.host     = os.getenv("POSTGRES_HOST", "localhost")
        self.port     = os.getenv("POSTGRES_PORT", "5432")
        self.db       = os.getenv("POSTGRES_DB", "jobs_db")
        self.user     = os.getenv("POSTGRES_USER", "jobs_user")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.engine   = None
        logger.info("Initialisation de PostgresLoader")

    def connecter(self) -> bool:
        """
        Crée le moteur SQLAlchemy et vérifie la connexion.

        Returns:
            True si succès, False sinon
        """
        try:
            url = (
                f"postgresql+psycopg2://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.db}"
            )
            self.engine = create_engine(url, pool_pre_ping=True)

            # Test de connexion
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.success("Connexion PostgreSQL établie")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Erreur connexion PostgreSQL : {e}")
            return False

        except Exception as e:
            logger.error(f"Erreur inattendue PostgreSQL : {e}")
            return False

    def creer_tables(self) -> bool:
        """
        Crée les tables si elles n'existent pas encore.

        Returns:
            True si succès, False sinon
        """
        if self.engine is None:
            logger.error("Engine non initialisé")
            return False

        try:
            with self.engine.begin() as conn:

                # Table des groupes politiques
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS groupes_politiques (
                        id          SERIAL PRIMARY KEY,
                        sigle       VARCHAR(20)  UNIQUE NOT NULL,
                        nom         VARCHAR(200) NOT NULL,
                        slug        VARCHAR(200),
                        president   VARCHAR(200),
                        nb_membres  INTEGER,
                        declaration TEXT,
                        url         TEXT,
                        collecte_le TIMESTAMP DEFAULT NOW()
                    )
                """))

                # Table des députés
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS deputes (
                        id                     SERIAL PRIMARY KEY,
                        uid                    VARCHAR(20)  UNIQUE NOT NULL,
                        nom                    VARCHAR(100) NOT NULL,
                        prenom                 VARCHAR(100) NOT NULL,
                        nom_complet            VARCHAR(200),
                        civilite               VARCHAR(10),
                        date_naissance         DATE,
                        age                    INTEGER,
                        lieu_naissance         VARCHAR(200),
                        departement_naissance  VARCHAR(200),
                        profession             VARCHAR(200),
                        groupe_sigle           VARCHAR(20)
                                               REFERENCES groupes_politiques(sigle),
                        groupe_nom             VARCHAR(200),
                        url_photo              TEXT,
                        collecte_le            TIMESTAMP DEFAULT NOW()
                    )
                """))

                # Table des scrutins
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS scrutins (
                        id                  SERIAL PRIMARY KEY,
                        uid                 VARCHAR(50)  UNIQUE NOT NULL,
                        numero              INTEGER,
                        titre               TEXT,
                        titre_court         VARCHAR(200),
                        date                DATE,
                        annee               INTEGER,
                        mois                INTEGER,
                        legislature         VARCHAR(10),
                        type_vote           VARCHAR(100),
                        sort                VARCHAR(50),
                        adopte              BOOLEAN,
                        pour                INTEGER DEFAULT 0,
                        contre              INTEGER DEFAULT 0,
                        abstention          INTEGER DEFAULT 0,
                        non_votant          INTEGER DEFAULT 0,
                        total_votants       INTEGER DEFAULT 0,
                        taux_participation  NUMERIC(5,2),
                        collecte_le         TIMESTAMP DEFAULT NOW()
                    )
                """))

            logger.success("Tables créées / vérifiées")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Erreur création tables : {e}")
            return False

    def inserer_groupes(self, groupes: list) -> int:
        """
        Insère les groupes politiques (upsert sur le sigle).

        Returns:
            Nombre de lignes insérées/mises à jour
        """
        if self.engine is None:
            return 0

        count = 0
        try:
            with self.engine.begin() as conn:
                for g in groupes:
                    try:
                        conn.execute(text("""
                            INSERT INTO groupes_politiques
                                (sigle, nom, slug, president,
                                 nb_membres, declaration, url)
                            VALUES
                                (:sigle, :nom, :slug, :president,
                                 :nb_membres, :declaration, :url)
                            ON CONFLICT (sigle) DO UPDATE SET
                                nom        = EXCLUDED.nom,
                                president  = EXCLUDED.president,
                                nb_membres = EXCLUDED.nb_membres,
                                collecte_le = NOW()
                        """), {
                            "sigle":       g.sigle,
                            "nom":         g.nom,
                            "slug":        g.slug,
                            "president":   g.president,
                            "nb_membres":  g.nb_membres,
                            "declaration": g.declaration,
                            "url":         g.url,
                        })
                        count += 1
                    except Exception as e:
                        logger.warning(f"Erreur insertion groupe {g.sigle} : {e}")

            logger.success(f"{count} groupes insérés/mis à jour")

        except SQLAlchemyError as e:
            logger.error(f"Erreur insertion groupes : {e}")

        return count

    def inserer_deputes(self, deputes: list) -> int:
        """
        Insère les députés (upsert sur l'uid).

        Returns:
            Nombre de lignes insérées/mises à jour
        """
        if self.engine is None:
            return 0

        count = 0
        try:
            with self.engine.begin() as conn:
                for d in deputes:
                    try:
                        conn.execute(text("""
                            INSERT INTO deputes
                                (uid, nom, prenom, nom_complet, civilite,
                                 date_naissance, age, lieu_naissance,
                                 departement_naissance, profession,
                                 groupe_sigle, groupe_nom, url_photo)
                            VALUES
                                (:uid, :nom, :prenom, :nom_complet, :civilite,
                                 :date_naissance, :age, :lieu_naissance,
                                 :departement_naissance, :profession,
                                 :groupe_sigle, :groupe_nom, :url_photo)
                            ON CONFLICT (uid) DO UPDATE SET
                                groupe_sigle = EXCLUDED.groupe_sigle,
                                groupe_nom   = EXCLUDED.groupe_nom,
                                age          = EXCLUDED.age,
                                collecte_le  = NOW()
                        """), {
                            "uid":                   d.uid,
                            "nom":                   d.nom,
                            "prenom":                d.prenom,
                            "nom_complet":           d.nom_complet,
                            "civilite":              d.civilite,
                            "date_naissance":        d.date_naissance,
                            "age":                   d.age,
                            "lieu_naissance":        d.lieu_naissance,
                            "departement_naissance": d.departement_naissance,
                            "profession":            d.profession,
                            "groupe_sigle":          d.groupe_sigle,
                            "groupe_nom":            d.groupe_nom,
                            "url_photo":             d.url_photo,
                        })
                        count += 1
                    except Exception as e:
                        logger.warning(f"Erreur insertion député {d.uid} : {e}")

            logger.success(f"{count} députés insérés/mis à jour")

        except SQLAlchemyError as e:
            logger.error(f"Erreur insertion députés : {e}")

        return count

    def inserer_scrutins(self, scrutins: list) -> int:
        """
        Insère les scrutins (upsert sur l'uid).

        Returns:
            Nombre de lignes insérées/mises à jour
        """
        if self.engine is None:
            return 0

        count = 0
        try:
            with self.engine.begin() as conn:
                for s in scrutins:
                    try:
                        conn.execute(text("""
                            INSERT INTO scrutins
                                (uid, numero, titre, titre_court, date,
                                 annee, mois, legislature, type_vote,
                                 sort, adopte, pour, contre, abstention,
                                 non_votant, total_votants, taux_participation)
                            VALUES
                                (:uid, :numero, :titre, :titre_court, :date,
                                 :annee, :mois, :legislature, :type_vote,
                                 :sort, :adopte, :pour, :contre, :abstention,
                                 :non_votant, :total_votants,
                                 :taux_participation)
                            ON CONFLICT (uid) DO UPDATE SET
                                titre              = EXCLUDED.titre,
                                sort               = EXCLUDED.sort,
                                adopte             = EXCLUDED.adopte,
                                collecte_le        = NOW()
                        """), {
                            "uid":               s.uid,
                            "numero":            s.numero,
                            "titre":             s.titre,
                            "titre_court":       s.titre_court,
                            "date":              s.date,
                            "annee":             s.annee,
                            "mois":              s.mois,
                            "legislature":       s.legislature,
                            "type_vote":         s.type_vote,
                            "sort":              s.sort,
                            "adopte":            s.adopte,
                            "pour":              s.pour,
                            "contre":            s.contre,
                            "abstention":        s.abstention,
                            "non_votant":        s.non_votant,
                            "total_votants":     s.total_votants,
                            "taux_participation": s.taux_participation,
                        })
                        count += 1
                    except Exception as e:
                        logger.warning(f"Erreur insertion scrutin {s.uid} : {e}")

            logger.success(f"{count} scrutins insérés/mis à jour")

        except SQLAlchemyError as e:
            logger.error(f"Erreur insertion scrutins : {e}")

        return count