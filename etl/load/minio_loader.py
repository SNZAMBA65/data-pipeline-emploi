"""
Chargement des données brutes dans MinIO (Data Lake).
Stocke les données au format JSON dans des buckets organisés.
"""

import json
from datetime import datetime
from loguru import logger
from minio import Minio
from minio.error import S3Error
import io
import os
from dotenv import load_dotenv

load_dotenv()


class MinioLoader:
    """
    Charge les données brutes dans MinIO.
    Compatible avec AWS S3 — même API boto3/minio.
    """

    def __init__(self):
        self.endpoint   = os.getenv("MINIO_ENDPOINT", "localhost:9000") \
                            .replace("http://", "").replace("https://", "")
        self.access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
        self.secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")
        self.bucket_raw = os.getenv("MINIO_BUCKET_RAW", "raw-data")
        self.client     = None
        logger.info("Initialisation de MinioLoader")

    def connecter(self) -> bool:
        """
        Établit la connexion à MinIO et crée les buckets si nécessaire.

        Returns:
            True si connexion réussie, False sinon
        """
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=False,  # HTTP en local, HTTPS en prod
            )

            # Crée le bucket s'il n'existe pas
            if not self.client.bucket_exists(self.bucket_raw):
                self.client.make_bucket(self.bucket_raw)
                logger.info(f"Bucket '{self.bucket_raw}' créé")
            else:
                logger.info(f"Bucket '{self.bucket_raw}' déjà existant")

            logger.success("Connexion MinIO établie")
            return True

        except S3Error as e:
            logger.error(f"Erreur S3 MinIO : {e}")
            return False

        except Exception as e:
            logger.error(f"Erreur connexion MinIO : {e}")
            return False

    def charger_json(
        self,
        data: list | dict,
        chemin_objet: str,
    ) -> bool:
        """
        Sérialise et charge des données JSON dans MinIO.

        Args:
            data: Données à charger (liste ou dict)
            chemin_objet: Chemin dans le bucket (ex: deputés/2024-01-01.json)

        Returns:
            True si succès, False sinon
        """
        if self.client is None:
            logger.error("Client MinIO non initialisé — appelez connecter()")
            return False

        try:
            # Sérialise en JSON
            contenu = json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
                default=str,  # gère les types non sérialisables
            ).encode("utf-8")

            taille = len(contenu)

            # Upload dans MinIO
            self.client.put_object(
                bucket_name=self.bucket_raw,
                object_name=chemin_objet,
                data=io.BytesIO(contenu),
                length=taille,
                content_type="application/json",
            )

            logger.success(
                f"Chargé dans MinIO : {chemin_objet} "
                f"({taille / 1024:.1f} Ko)"
            )
            return True

        except S3Error as e:
            logger.error(f"Erreur S3 upload '{chemin_objet}' : {e}")
            return False

        except Exception as e:
            logger.error(f"Erreur upload '{chemin_objet}' : {e}")
            return False

    def charger_deputes(self, deputes: list) -> bool:
        """Charge les députés bruts dans MinIO."""
        date = datetime.now().strftime("%Y-%m-%d")
        data = [vars(d) for d in deputes]
        return self.charger_json(data, f"deputes/raw_{date}.json")

    def charger_scrutins(self, scrutins: list) -> bool:
        """Charge les scrutins bruts dans MinIO."""
        date = datetime.now().strftime("%Y-%m-%d")
        data = [vars(s) for s in scrutins]
        return self.charger_json(data, f"scrutins/raw_{date}.json")

    def charger_groupes(self, groupes: list) -> bool:
        """Charge les groupes politiques dans MinIO."""
        date = datetime.now().strftime("%Y-%m-%d")
        data = [
            {
                "slug":        g.slug,
                "nom":         g.nom,
                "sigle":       g.sigle,
                "president":   g.president,
                "nb_membres":  g.nb_membres,
                "declaration": g.declaration,
                "url":         g.url,
            }
            for g in groupes
        ]
        return self.charger_json(data, f"groupes/raw_{date}.json")