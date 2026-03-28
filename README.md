# Assemblée nationale · Pipeline Data Cloud
### 17e législature - Analyse des données parlementaires françaises

**Samir NZAMBA** · Mastère DPIA 1 · L'École Multimédia · Paris · 2025-2026  
Projet #2 - Infrastructure Data Cloud

---

## À propos

Ce projet construit un pipeline de données end-to-end sur les données parlementaires françaises de la 17e législature. L'objectif est de collecter, stocker, transformer et visualiser les données des 575 députés actifs et des 5 828 scrutins publics enregistrés depuis juillet 2024.

La collecte repose sur deux sources complémentaires : l'**API officielle** de l'Assemblée nationale pour les données structurées (députés et scrutins au format ZIP JSON) et du **scraping HTML** pour les groupes politiques, qui ne sont pas exposés via l'API. Les données brutes transitent par un Data Lake MinIO avant d'être nettoyées, enrichies et chargées dans un Data Warehouse PostgreSQL. Le tout est orchestré par Airflow, supervisé par Prometheus et Grafana, et exposé via un dashboard Streamlit interactif.

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
**Infra** : Docker, Docker Compose

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
           (nettoyage, enrichissement, mapping)
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

**575 députés actifs** · 17e législature uniquement  
Identité civile, date et lieu de naissance, profession, groupe politique, photo  
Source : `AMO10_deputes_actifs_mandats_actifs_organes.json.zip`

**5 828 scrutins publics** · juillet 2024 - mars 2026  
Titre, date, résultat, votes pour/contre/abstentions, taux de participation  
Source : `scrutins.json.zip`

**12 groupes politiques** · composition réelle de l'hémicycle  
Source : scraping `assemblee-nationale.fr/dyn/les-groupes-politiques`

| Sigle | Groupe | Sièges |
|---|---|---|
| RN | Rassemblement National | 122 |
| EPR | Ensemble pour la République | 90 |
| LFI-NFP | La France insoumise - Nouveau Front Populaire | 71 |
| SOC | Socialistes et apparentés | 69 |
| DR | Droite Républicaine | 48 |
| ECO | Écologiste et Social | 38 |
| DEM | Les Démocrates | 36 |
| HOR | Horizons & Indépendants | 35 |
| LIOT | Libertés, Indépendants, Outre-mer et Territoires | 22 |
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
│   │   ├── nosdeputes_scraper.py    # Collecte API ZIP - députés et scrutins
│   │   └── groupes_scraper.py       # Scraping HTML - groupes politiques
│   ├── transform/
│   │   └── cleaner.py               # Nettoyage et enrichissement
│   ├── load/
│   │   ├── minio_loader.py          # Chargement Data Lake MinIO
│   │   └── postgres_loader.py       # Chargement Data Warehouse PostgreSQL
│   ├── pipeline.py                  # Pipeline ETL en ligne de commande
│   └── fix_groupes.py               # Mapping député vers groupe politique
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

## Installation et démarrage

L'ordre des étapes est important, respectez-le.

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

Le nom de la base `jobs_db` doit rester tel quel. Toutes les autres valeurs sont libres. Ce fichier ne doit jamais être commité, il est exclu par `.gitignore`.

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

Lancez le pipeline ETL. Il scrape les groupes politiques depuis le site de l'Assemblée nationale, collecte les députés et scrutins via l'API officielle, charge les données brutes dans MinIO et les données transformées dans PostgreSQL :
```bash
python etl/pipeline.py
```

Comptez 2 à 5 minutes selon votre connexion. Le pipeline affiche sa progression en temps réel et se termine par un résumé indiquant le nombre de groupes, députés et scrutins collectés et chargés.

Lancez ensuite le script de mapping. Il lit les mandats officiels dans le ZIP de l'API, identifie le groupe politique actif de chaque député et met à jour PostgreSQL :
```bash
python etl/fix_groupes.py
```

Le script affiche la répartition finale par groupe. Vous devez voir 575 députés mis à jour avec les effectifs suivants : RN 122, EPR 90, LFI-NFP 71, SOC 69, DR 48, ECO 38, DEM 36, HOR 35, LIOT 22, GDR 17, UDR 17, NI 10.

### 7. Configurer Grafana

Ouvrez **http://localhost:3000** et connectez-vous avec `admin / admin`.

Allez dans **Connections > Data sources > PostgreSQL**. Dans le champ **Password**, saisissez la valeur que vous avez définie pour `POSTGRES_PASSWORD` dans votre `.env`. Cliquez **Save & test**, vous devez voir `Database Connection OK`.

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

Ouvrez **http://localhost:8080** et connectez-vous avec `admin / admin`.

Localisez le DAG `pipeline_assemblee_nationale` et activez-le via le toggle, il passe de **Paused** à **Active**. Le pipeline s'exécute ensuite automatiquement chaque jour à 6h00. Pour un déclenchement manuel immédiat, utilisez le bouton **Trigger DAG**.

### 10. Lancer le dashboard Streamlit
```bash
streamlit run dashboards/streamlit/app.py
```

Ouvrez **http://localhost:8501**.

---

## Interfaces disponibles

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
- `02_analyse_scrutins.ipynb` : analyse des 5 828 scrutins publics
- `03_analyse_deputes.ipynb` : analyse démographique des 575 députés

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

**Prometheus** - http://localhost:9090  
Collecte les métriques toutes les 15 secondes depuis trois cibles : Prometheus lui-même, PostgreSQL via le postgres-exporter, et MinIO. Vérifiez que les trois targets sont **UP** dans **Status > Targets**.

**Grafana** - http://localhost:3000  
Dashboard provisionné automatiquement avec les métriques métier du pipeline : KPIs, scrutins par mois, taux de participation, évolution du taux d'adoption et bilan annuel.

---

## Redémarrage

Après un redémarrage machine, dans l'ordre :
```bash
# 1. Démarrer Docker Desktop et attendre que l'icône soit stable

# 2. Lancer les conteneurs
cd data-pipeline-emploi
source venv/Scripts/activate        # Windows
docker compose up -d

# 3. Attendre 30 secondes que tous les services soient prêts

# 4. Ressaisir le mot de passe PostgreSQL dans Grafana
#    http://localhost:3000
#    Connections > Data sources > PostgreSQL
#    Champ Password > votre POSTGRES_PASSWORD > Save & test

# 5. Vérifier qu'Airflow est toujours actif
#    http://localhost:8080
#    Le DAG pipeline_assemblee_nationale doit être en statut Active

# 6. Lancer le dashboard
streamlit run dashboards/streamlit/app.py
```

---

## Contexte académique

Projet réalisé dans le cadre du Mastère DPIA 1 - Directeur de Projet en Intelligence Artificielle à L'École Multimédia (Paris), année 2025-2026.

Données source sous [Licence Ouverte / Open Licence](https://www.etalab.gouv.fr/licence-ouverte-open-licence) - Assemblée nationale française.