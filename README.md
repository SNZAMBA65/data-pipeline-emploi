# Assemblée nationale · Pipeline Data Cloud
### 17e législature - Analyse des données parlementaires françaises

**Samir NZAMBA** · Mastère DPIA 1 · Fonderie de l'image · Paris · 2025-2026  
Projet #2 - Infrastructure Data Cloud

---

## À propos

Ce projet construit un pipeline de données end-to-end sur les données parlementaires françaises de la 17e législature. L'objectif est de collecter, stocker, transformer et visualiser les données des 577 députés actifs et des 6 645 scrutins publics enregistrés depuis juillet 2024.

La collecte repose sur deux sources complémentaires : l'**API officielle** de l'Assemblée nationale pour les données structurées (députés et scrutins au format ZIP JSON) et du **scraping HTML** pour les groupes politiques, qui ne sont pas exposés via l'API. Les données brutes transitent par un Data Lake MinIO avant d'être nettoyées, enrichies et chargées dans un Data Warehouse PostgreSQL. Le tout est orchestré par Airflow, supervisé par Prometheus et Grafana, et exposé via un dashboard Streamlit interactif.

L'infrastructure est déployable aussi bien en local via Docker que sur AWS EC2, MinIO étant compatible avec l'API AWS S3.

---

## Stack technique

**Collecte** : Python, requests, BeautifulSoup  
**Data Lake** : MinIO (compatible API AWS S3)  
**Data Warehouse** : PostgreSQL 15  
**Orchestration** : Apache Airflow 2.9  
**Monitoring** : Prometheus, Grafana  
**Dashboard** : Streamlit  
**Tests** : pytest, pytest-cov (37/37)  
**CI/CD** : GitHub Actions  
**Infra locale** : Docker, Docker Compose  
**Infra cloud** : AWS EC2 (Ubuntu 22.04, région eu-west-3 Paris)

---

## Architecture
```
API officielle AN (ZIP)       Scraping HTML (groupes politiques)
         │                                │
         └──────────────┬─────────────────┘
                        │ Extract
                        ▼
                   MinIO · Data Lake
                  (données brutes JSON)
                        │ Transform
                        ▼
                   DataCleaner
           (nettoyage, enrichissement, mapping groupes)
                        │ Load
                        ▼
                PostgreSQL · Data Warehouse
               (deputes / scrutins / groupes)
                    │               │
                    ▼               ▼
              Streamlit        Prometheus + Grafana
              Dashboard            Monitoring
                    ▲
               Apache Airflow
        (orchestration · 6 tâches · quotidien 6h00)
```

---

## Données

**577 députés actifs** · 17e législature uniquement  
Identité civile, date et lieu de naissance, profession, groupe politique, photo  
Source : `AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip`  
Le fichier contient l'ensemble des acteurs parlementaires depuis plusieurs législatures. Le pipeline filtre uniquement les députés avec un mandat actif en 17e législature, ce qui ramène le dataset de 3 114 acteurs à 577 députés actifs.

**6 645 scrutins publics** · juillet 2024 - mars 2026  
Titre, date, résultat, votes pour/contre/abstentions, taux de participation  
Source : `Scrutins.json.zip`

**12 groupes politiques** · composition réelle de l'hémicycle  
Source : scraping `assemblee-nationale.fr/dyn/les-groupes-politiques`

| Sigle | Groupe | Sièges |
|---|---|---|
| RN | Rassemblement National | 122 |
| EPR | Ensemble pour la République | 91 |
| LFI-NFP | La France insoumise - Nouveau Front Populaire | 71 |
| SOC | Socialistes et apparentés | 68 |
| DR | Droite Républicaine | 48 |
| ECO | Écologiste et Social | 38 |
| DEM | Les Démocrates | 37 |
| HOR | Horizons & Indépendants | 35 |
| LIOT | Libertés, Indépendants, Outre-mer et Territoires | 23 |
| GDR | Gauche Démocrate et Républicaine | 17 |
| UDR | Union des droites pour la République | 17 |
| NI | Députés non inscrits | 10 |

---

## Structure du projet
```
data-pipeline-emploi/
├── .github/
│   └── workflows/
│       └── ci.yml                   # Pipeline CI/CD GitHub Actions
├── dags/
│   └── dag_assemblee_nationale.py   # DAG Airflow - 6 tâches
├── dashboards/
│   └── streamlit/
│       └── app.py                   # Dashboard principal Streamlit
├── data/
│   └── processed/                   # Visualisations PNG générées par les notebooks
├── docs/
│   ├── architecture.md
│   ├── etl.md
│   └── dashboard.md
├── etl/
│   ├── scrapers/
│   │   ├── nosdeputes_scraper.py    # Collecte API ZIP - députés actifs avec mapping groupes
│   │   └── groupes_scraper.py       # Scraping HTML - groupes politiques
│   ├── transform/
│   │   └── cleaner.py               # Nettoyage et enrichissement
│   ├── load/
│   │   ├── minio_loader.py          # Chargement Data Lake MinIO
│   │   └── postgres_loader.py       # Chargement Data Warehouse PostgreSQL
│   └── pipeline.py                  # Pipeline ETL en ligne de commande
├── infra/
│   ├── grafana/
│   │   └── provisioning/
│   │       ├── dashboards/          # Dashboard Grafana provisionné
│   │       └── datasources/         # Datasources PostgreSQL et Prometheus
│   ├── postgres/
│   │   └── init.sql                 # Schéma initial PostgreSQL
│   └── prometheus/
│       └── prometheus.yml           # Configuration scraping Prometheus
├── notebooks/
│   ├── 01_exploration.ipynb
│   ├── 02_analyse_scrutins.ipynb
│   └── 03_analyse_deputes.ipynb
├── tests/
│   ├── test_scraper.py
│   ├── test_cleaner.py
│   └── test_loaders.py
├── .env.example                     # Modèle de configuration à copier en .env
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Déploiement local

### Prérequis

- Docker Desktop installé et démarré
- Python 3.11 ou supérieur
- Git

### 1. Cloner le dépôt
```bash
git clone https://github.com/SNZAMBA65/data-pipeline-emploi.git
cd data-pipeline-emploi
```

### 2. Configurer l'environnement

Créez le fichier `.env` avant toute autre étape, Docker en a besoin au démarrage :
```bash
cp .env.example .env
```

Ouvrez `.env` et remplacez les valeurs fictives par les vôtres :
```env
# MinIO - Data Lake local
MINIO_ROOT_USER=votre_user_minio
MINIO_ROOT_PASSWORD=votre_mot_de_passe_minio

# PostgreSQL - Data Warehouse local
POSTGRES_DB=jobs_db
POSTGRES_USER=votre_user_postgres
POSTGRES_PASSWORD=votre_mot_de_passe_postgres
```

Le nom de la base `jobs_db` doit rester tel quel. Ce fichier ne doit jamais être commité, il est exclu par `.gitignore`.

### 3. Créer l'environnement virtuel Python
```bash
python -m venv venv
source venv/Scripts/activate    # Windows
# source venv/bin/activate      # Linux / macOS
pip install -r requirements.txt
```

### 4. Créer le dossier de logs Airflow
```bash
mkdir -p logs/airflow
```

### 5. Démarrer l'infrastructure Docker
```bash
docker compose up -d
```

Attendez environ 30 secondes puis vérifiez que tous les services sont opérationnels :
```bash
docker compose ps
```

Les services suivants doivent afficher le statut **Up** :

| Service | Rôle |
|---|---|
| minio | Data Lake |
| postgres_jobs | Data Warehouse |
| pgadmin | Interface PostgreSQL |
| prometheus | Collecte de métriques |
| postgres_exporter | Export métriques PostgreSQL |
| grafana | Dashboards monitoring |
| postgres_airflow | Base interne Airflow |
| airflow_webserver | Interface Airflow |
| airflow_scheduler | Planificateur Airflow |

`airflow_init` apparaît comme `Exited (0)`, c'est normal, c'est un service d'initialisation one-shot.

### 6. Alimenter la base de données

Le pipeline collecte les groupes politiques par scraping HTML, les 577 députés actifs et leurs groupes via l'API officielle, charge les données brutes dans MinIO et les données transformées dans PostgreSQL — tout en une seule commande :
```bash
python etl/pipeline.py
```

Comptez 2 à 5 minutes selon votre connexion. Le pipeline affiche sa progression en temps réel et se termine par un résumé complet.

### 7. Configurer Grafana

Ouvrez **http://localhost:3000** (admin / admin), allez dans **Connections > Data sources > PostgreSQL** et renseignez le mot de passe défini dans votre `.env` (champ `POSTGRES_PASSWORD`). Cliquez **Save & test**, vous devez voir `Database Connection OK`.

Le dashboard de monitoring est provisionné automatiquement et s'affiche immédiatement.

> Grafana ne persiste pas les mots de passe des datasources entre les sessions Docker. Cette étape est à répéter à chaque redémarrage.

### 8. Configurer pgAdmin (optionnel)

Ouvrez **http://localhost:5050** (admin@admin.com / admin). Ajoutez un nouveau serveur avec ces paramètres :

- **Host** : `postgres_jobs`
- **Port** : `5432`
- **Database** : valeur de `POSTGRES_DB` dans votre `.env`
- **Username** : valeur de `POSTGRES_USER`
- **Password** : valeur de `POSTGRES_PASSWORD`

### 9. Activer le DAG Airflow

Ouvrez **http://localhost:8080** (admin / admin), localisez le DAG `pipeline_assemblee_nationale` et activez-le via le toggle. Le pipeline s'exécute ensuite automatiquement chaque jour à 6h00. Pour un déclenchement manuel, utilisez le bouton **Trigger DAG**.

### 10. Lancer le dashboard Streamlit
```bash
streamlit run dashboards/streamlit/app.py
```

Ouvrez **http://localhost:8501**.

---

## Déploiement AWS EC2

Le projet est conçu pour tourner sur une instance EC2 Ubuntu. MinIO étant compatible avec l'API AWS S3, la migration vers S3 et RDS ne nécessite que des changements de variables d'environnement.

### Prérequis AWS

- Compte AWS actif
- Instance EC2 : Ubuntu 22.04 LTS, type `m7i-flex.large` minimum, 30 Go de stockage
- Région : `eu-west-3` (Paris)
- Groupe de sécurité avec les ports entrants ouverts : 22, 3000, 5050, 8080, 8501, 9000, 9001, 9090

### 1. Connexion à l'instance
```bash
ssh -i votre-cle.pem ubuntu@VOTRE_IP_PUBLIQUE
```

### 2. Installation de Docker
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker ubuntu
newgrp docker
```

### 3. Cloner et configurer
```bash
git clone https://github.com/SNZAMBA65/data-pipeline-emploi.git
cd data-pipeline-emploi
cp .env.example .env
nano .env
```

Renseignez vos identifiants, sauvegardez avec `Ctrl+O` puis `Entrée`, quittez avec `Ctrl+X`.

### 4. Démarrer l'infrastructure
```bash
mkdir -p logs/airflow
sudo chmod -R 777 logs/airflow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker compose up -d
```

Attendez 30 secondes que tous les services démarrent.

### 5. Alimenter la base de données
```bash
python etl/pipeline.py
```

### 6. Lancer le dashboard
```bash
streamlit run dashboards/streamlit/app.py --server.address 0.0.0.0 --server.port 8501
```

Le dashboard est accessible depuis n'importe quel navigateur à l'adresse `http://VOTRE_IP_PUBLIQUE:8501`.

### Interfaces disponibles sur EC2

| Service | URL |
|---|---|
| Streamlit | http://VOTRE_IP_PUBLIQUE:8501 |
| Grafana | http://VOTRE_IP_PUBLIQUE:3000 |
| Airflow | http://VOTRE_IP_PUBLIQUE:8080 |
| MinIO | http://VOTRE_IP_PUBLIQUE:9001 |
| pgAdmin | http://VOTRE_IP_PUBLIQUE:5050 |
| Prometheus | http://VOTRE_IP_PUBLIQUE:9090 |

---

## Interfaces disponibles en local

| Service | URL | Identifiants |
|---|---|---|
| Streamlit | http://localhost:8501 | - |
| Grafana | http://localhost:3000 | admin / admin |
| Airflow | http://localhost:8080 | admin / admin |
| MinIO | http://localhost:9001 | Vos identifiants `.env` |
| pgAdmin | http://localhost:5050 | admin@admin.com / admin |
| Prometheus | http://localhost:9090 | - |

---

## Pipeline ETL - Options CLI
```bash
python etl/pipeline.py                          # pipeline complet
python etl/pipeline.py --scrutins-limite 500    # limite les scrutins collectés
python etl/pipeline.py --deputes-limite 200     # limite les députés collectés
python etl/pipeline.py --skip-minio             # ignore le chargement MinIO
python etl/pipeline.py --skip-postgres          # ignore le chargement PostgreSQL
```

---

## DAG Airflow

Le DAG orchestre 6 tâches avec passage de données via XCom. Les tâches de collecte des députés et des scrutins s'exécutent en parallèle :
```
scraper_groupes (t1)
        │
        ├──► collecter_deputes (t2) ──┐
        │                             ▼
        └──► collecter_scrutins (t3) ─► load_minio (t4) ─► transform (t5) ─► load_postgres (t6)
```

2 retries automatiques, délai de 5 minutes entre chaque tentative, schedule quotidien à 6h00.

---

## Notebooks

Les notebooks sont indépendants et peuvent être lancés dans n'importe quel ordre, une fois la base de données alimentée.
```bash
jupyter notebook
```

- `01_exploration.ipynb` : exploration générale, statistiques descriptives
- `02_analyse_scrutins.ipynb` : analyse des 6 645 scrutins publics
- `03_analyse_deputes.ipynb` : analyse démographique des 577 députés

Les visualisations sont exportées dans `data/processed/`.

---

## Tests
```bash
pytest tests/ -v                                      # 37 tests
pytest tests/ --cov=etl --cov-report=term-missing     # avec couverture
```

37/37 tests passés. Ils couvrent les scrapers, le DataCleaner, les loaders MinIO et PostgreSQL, et l'intégration complète du pipeline.

---

## CI/CD

Le pipeline GitHub Actions se déclenche à chaque push ou pull request sur `main`. Il installe les dépendances, exécute les 37 tests et génère un rapport de couverture uploadé comme artefact.

---

## Monitoring

**Prometheus** : collecte les métriques toutes les 15 secondes depuis trois cibles : Prometheus lui-même, PostgreSQL via le postgres-exporter, et MinIO. Vérifiez que les trois targets sont **UP** dans **Status > Targets**.

**Grafana** : dashboard provisionné automatiquement avec les métriques métier du pipeline : KPIs, scrutins par mois, taux de participation, évolution du taux d'adoption et bilan annuel.

---

## Redémarrage local
```bash
cd data-pipeline-emploi
source venv/Scripts/activate        # Windows
docker compose up -d

# Ressaisir le mot de passe PostgreSQL dans Grafana
# http://localhost:3000
# Connections > Data sources > PostgreSQL > Password > Save & test

streamlit run dashboards/streamlit/app.py
```

## Redémarrage EC2
```bash
ssh -i votre-cle.pem ubuntu@VOTRE_IP_PUBLIQUE
cd data-pipeline-emploi
source venv/bin/activate
docker compose up -d

# Ressaisir le mot de passe PostgreSQL dans Grafana
# http://VOTRE_IP_PUBLIQUE:3000
# Connections > Data sources > PostgreSQL > Password > Save & test

streamlit run dashboards/streamlit/app.py --server.address 0.0.0.0 --server.port 8501
```

---

## Contexte académique

Projet réalisé dans le cadre du Mastère DPIA 1 - Directeur de Projet en Intelligence Artificielle à Fonderie de l'image (Paris), année 2025-2026.

Données source sous [Licence Ouverte / Open Licence](https://www.etalab.gouv.fr/licence-ouverte-open-licence) - Assemblée nationale française.