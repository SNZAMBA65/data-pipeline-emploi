# Pipeline Data Cloud — Assemblée nationale française
## 17e législature · Analyse des données parlementaires

> **Projet #2 — Mastère DPIA 1 · Directeur de Projet en Intelligence Artificielle**  
> Samir NZAMBA · L'École Multimédia · Paris · 2025-2026

---

## Présentation

Ce projet implémente un pipeline de données cloud complet autour des données parlementaires françaises de la **17e législature** (depuis juillet 2024). Il couvre l'ensemble de la chaîne de valeur data : collecte, stockage brut, transformation, stockage structuré, orchestration, monitoring et visualisation.

Les données sont collectées via deux approches complémentaires :
- **API officielle** de l'Assemblée nationale (`data.assemblee-nationale.fr`) — députés et scrutins publics au format ZIP JSON
- **Scraping HTML** du site institutionnel (`assemblee-nationale.fr`) — groupes politiques et composition de l'hémicycle

---

## Stack technique

| Composant | Technologie | Rôle |
|---|---|---|
| Collecte | Python · requests · BeautifulSoup | Scraping HTML + API ZIP officielle |
| Data Lake | MinIO | Stockage des données brutes (compatible S3) |
| Data Warehouse | PostgreSQL 15 | Stockage des données transformées |
| Orchestration | Apache Airflow 2.9 | Planification et exécution du pipeline |
| Monitoring | Prometheus + Grafana | Métriques infrastructure et pipeline |
| Dashboard | Streamlit | Visualisation interactive des données |
| Tests | pytest + pytest-cov | Tests unitaires et couverture |
| CI/CD | GitHub Actions | Intégration continue automatisée |
| Conteneurisation | Docker + Docker Compose | Infrastructure complète en local |

---

## Architecture
```
┌─────────────────────────────────────────────────────────┐
│                     SOURCES DE DONNÉES                   │
│  API officielle AN (ZIP)    Scraping HTML (groupes)      │
└──────────────────┬──────────────────────────────────────┘
                   │ Extract
                   ▼
┌─────────────────────────────────────────────────────────┐
│                    DATA LAKE · MinIO                     │
│         Stockage brut JSON · bucket raw-jobs            │
└──────────────────┬──────────────────────────────────────┘
                   │ Transform
                   ▼
┌─────────────────────────────────────────────────────────┐
│               TRANSFORMATION · DataCleaner               │
│    Nettoyage · enrichissement · mapping groupes         │
└──────────────────┬──────────────────────────────────────┘
                   │ Load
                   ▼
┌─────────────────────────────────────────────────────────┐
│               DATA WAREHOUSE · PostgreSQL                │
│     deputes · scrutins · groupes_politiques             │
└──────────┬───────────────────────────┬──────────────────┘
           │                           │
           ▼                           ▼
┌──────────────────┐       ┌──────────────────────────────┐
│ Dashboard        │       │ Monitoring                    │
│ Streamlit        │       │ Prometheus + Grafana          │
└──────────────────┘       └──────────────────────────────┘
           ▲
┌──────────────────────────────────────────────────────────┐
│              ORCHESTRATION · Apache Airflow               │
│   6 tâches · DAG quotidien · XCom · retries             │
└──────────────────────────────────────────────────────────┘
```

---

## Données collectées

### Députés — 17e législature
- **575 députés actifs** rattachés à leur groupe politique
- Informations : identité civile, date et lieu de naissance, profession, groupe politique, photo
- Source : ZIP officiel `AMO10_deputes_actifs_mandats_actifs_organes`

### Scrutins publics
- **5 828 scrutins** · juillet 2024 — mars 2026
- Informations : titre, date, résultat (adopté/rejeté), votes pour/contre/abstentions, taux de participation
- Source : ZIP officiel `scrutins`

### Groupes politiques
- **12 groupes** · composition réelle de l'hémicycle
- Source : scraping HTML `assemblee-nationale.fr/dyn/les-groupes-politiques`

| Groupe | Sigle | Sièges |
|---|---|---|
| Rassemblement National | RN | 122 |
| Ensemble pour la République | EPR | 90 |
| La France insoumise - NFP | LFI-NFP | 71 |
| Socialistes et apparentés | SOC | 69 |
| Droite Républicaine | DR | 48 |
| Écologiste et Social | ECO | 38 |
| Les Démocrates | DEM | 36 |
| Horizons & Indépendants | HOR | 35 |
| Libertés, Indépendants, Outre-mer | LIOT | 22 |
| Gauche Démocrate et Républicaine | GDR | 17 |
| Union des droites pour la République | UDR | 17 |
| Députés non inscrits | NI | 10 |

---

## Structure du projet
```
data-pipeline-emploi/
├── dags/
│   └── dag_assemblee_nationale.py   # DAG Airflow — 6 tâches
├── dashboards/
│   └── streamlit/
│       └── app.py                   # Dashboard principal
├── data/
│   └── processed/                   # Visualisations PNG (notebooks)
├── docs/
│   ├── architecture.md              # Architecture détaillée
│   ├── etl.md                       # Documentation ETL
│   └── dashboard.md                 # Documentation dashboard
├── etl/
│   ├── scrapers/
│   │   ├── nosdeputes_scraper.py    # Collecte API ZIP (députés + scrutins)
│   │   └── groupes_scraper.py       # Scraping HTML groupes politiques
│   ├── transform/
│   │   └── cleaner.py               # Transformation et nettoyage
│   ├── load/
│   │   ├── minio_loader.py          # Chargement Data Lake MinIO
│   │   └── postgres_loader.py       # Chargement Data Warehouse PostgreSQL
│   ├── pipeline.py                  # Pipeline ETL CLI
│   └── fix_groupes.py               # Correction mapping groupes → députés
├── infra/
│   ├── grafana/
│   │   └── provisioning/            # Dashboards et datasources Grafana
│   ├── postgres/
│   │   └── init.sql                 # Schéma initial PostgreSQL
│   └── prometheus/
│       └── prometheus.yml           # Configuration scraping Prometheus
├── notebooks/
│   ├── 01_exploration.ipynb         # Exploration des données brutes
│   ├── 02_analyse_scrutins.ipynb    # Analyse des scrutins publics
│   └── 03_analyse_deputes.ipynb     # Analyse démographique des députés
├── tests/
│   ├── test_scraper.py              # Tests unitaires scrapers
│   ├── test_cleaner.py              # Tests unitaires DataCleaner
│   └── test_loaders.py              # Tests unitaires loaders + intégration
├── .github/
│   └── workflows/
│       └── ci.yml                   # Pipeline CI/CD GitHub Actions
├── docker-compose.yml               # Infrastructure complète
├── requirements.txt                 # Dépendances Python
└── README.md
```

---

## Installation et démarrage complet

### Prérequis
- Docker Desktop (démarré et opérationnel)
- Python 3.11+
- Git

### Étape 1 — Cloner le dépôt
```bash
git clone https://github.com/SNZAMBA65/data-pipeline-emploi.git
cd data-pipeline-emploi
```

### Étape 2 — Environnement virtuel Python
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Linux / macOS
pip install -r requirements.txt
```

### Étape 3 — Variables d'environnement

Créer un fichier `.env` à la racine du projet avec vos propres identifiants :
```env
MINIO_ROOT_USER=votre_user_minio
MINIO_ROOT_PASSWORD=votre_mot_de_passe_minio
POSTGRES_DB=jobs_db
POSTGRES_USER=votre_user_postgres
POSTGRES_PASSWORD=votre_mot_de_passe_postgres
```

> ⚠️ **Important** : choisissez librement vos identifiants. Ces valeurs seront automatiquement utilisées par tous les services Docker (MinIO, PostgreSQL, Grafana, Airflow). Ne commitez jamais ce fichier — il est exclu par `.gitignore`.

> ℹ️ Le nom de la base de données `jobs_db` doit rester tel quel, il est référencé dans le code.

### Étape 4 — Démarrer l'infrastructure Docker
```bash
docker compose up -d
```

Attendre 30 secondes que tous les services soient prêts, puis vérifier :
```bash
docker compose ps
```

Tous les services doivent afficher le statut **Up** :
- `minio` — Data Lake
- `postgres_jobs` — Data Warehouse
- `pgadmin` — Interface PostgreSQL
- `prometheus` — Collecte de métriques
- `postgres_exporter` — Exporter métriques PostgreSQL
- `grafana` — Dashboards monitoring
- `postgres_airflow` — Base interne Airflow
- `airflow_webserver` — Interface Airflow
- `airflow_scheduler` — Planificateur Airflow

### Étape 5 — Lancer le pipeline ETL

Cette étape collecte les données depuis l'API officielle et le scraping HTML, les charge dans MinIO puis dans PostgreSQL :
```bash
python etl/pipeline.py
```

Le pipeline affiche la progression en temps réel via des logs colorés. À la fin, le résumé indique le nombre de groupes, députés et scrutins collectés et chargés.

### Étape 6 — Corriger le mapping des groupes politiques

Cette étape établit le lien entre chaque député et son groupe politique depuis les mandats officiels de l'API :
```bash
python etl/fix_groupes.py
```

À la fin du script, 575 députés doivent être rattachés à leur groupe politique avec les bons effectifs. Le log de fin affiche la répartition complète par groupe.

### Étape 7 — Configurer Grafana

Ouvrir **http://localhost:3000** (admin / admin), puis :

1. Aller dans **Connections** → **Data sources** → **PostgreSQL**
2. Renseigner le mot de passe PostgreSQL que vous avez défini dans votre `.env` (champ `POSTGRES_PASSWORD`)
3. Cliquer **Save & test** — le message `Database Connection OK` doit apparaître

Le dashboard de monitoring se charge automatiquement depuis le provisioning.

> ⚠️ Cette étape est à répéter à chaque redémarrage de Docker. Grafana ne persiste pas les mots de passe entre les sessions — c'est une limitation connue de Grafana avec les datasources provisionnées.

### Étape 8 — Activer le DAG Airflow

Ouvrir **http://localhost:8080** (admin / admin), puis :

1. Localiser le DAG `pipeline_assemblee_nationale`
2. Cliquer sur le toggle pour l'activer (passe de **Paused** à **Active**)
3. Le pipeline s'exécutera automatiquement chaque jour à 6h00

Pour déclencher une exécution manuelle immédiate, cliquer sur **Trigger DAG** (icône ▶).

### Étape 9 — Lancer le dashboard Streamlit
```bash
streamlit run dashboards/streamlit/app.py
```

Ouvrir **http://localhost:8501** dans le navigateur.

---

## Accès aux interfaces

| Interface | URL | Identifiants |
|---|---|---|
| Dashboard Streamlit | http://localhost:8501 | — |
| Grafana | http://localhost:3000 | admin / admin |
| Airflow | http://localhost:8080 | admin / admin |
| MinIO Console | http://localhost:9001 | Ceux définis dans votre `.env` |
| pgAdmin | http://localhost:5050 | admin@admin.com / admin |
| Prometheus | http://localhost:9090 | — |

> Les identifiants MinIO et PostgreSQL correspondent aux valeurs que vous avez définies dans votre fichier `.env`.

---

## Pipeline ETL — Options CLI
```bash
# Pipeline complet (défaut)
python etl/pipeline.py

# Limiter le nombre de scrutins collectés
python etl/pipeline.py --scrutins-limite 500

# Limiter le nombre de députés collectés
python etl/pipeline.py --deputes-limite 200

# Ignorer le chargement MinIO
python etl/pipeline.py --skip-minio

# Ignorer le chargement PostgreSQL
python etl/pipeline.py --skip-postgres
```

---

## DAG Airflow — Architecture des tâches

Le DAG orchestre 6 tâches avec passage de données via XCom :
```
scraper_groupes (t1)
        │
        ├──► collecter_deputes (t2) ──┐
        │                             ▼
        └──► collecter_scrutins (t3) ─► load_minio (t4) ─► transform (t5) ─► load_postgres (t6)
```

- **t1** : Scraping HTML des 12 groupes politiques
- **t2 + t3** : Collecte parallèle des députés et scrutins via API ZIP (optimisation de performance)
- **t4** : Chargement des données brutes dans MinIO (Data Lake)
- **t5** : Transformation et nettoyage via DataCleaner
- **t6** : Chargement des données propres dans PostgreSQL (Data Warehouse)

Configuration : 2 retries automatiques · délai de 5 minutes entre retries · schedule quotidien à 6h00.

---

## Tests
```bash
# Lancer tous les tests
pytest tests/ -v

# Avec rapport de couverture
pytest tests/ --cov=etl --cov-report=term-missing
```

**Résultats : 37/37 tests passés**

Les tests couvrent :
- **Scrapers** : parsing des dataclasses `Depute` et `Scrutin`, gestion des valeurs XML nulles, attributs complets
- **DataCleaner** : nettoyage de texte, calcul d'âge, transformation des données, méthodes disponibles
- **Loaders** : connexion MinIO, connexion PostgreSQL, chargement des données
- **Intégration** : importabilité de tous les modules, attributs des dataclasses, cohérence du pipeline

---

## Monitoring

### Prometheus — http://localhost:9090
Collecte les métriques toutes les 15 secondes depuis trois sources :
- `prometheus` — métriques internes Prometheus
- `postgres` — métriques PostgreSQL via postgres-exporter (port 9187)
- `minio` — métriques MinIO stockage et requêtes (authentification publique)

Vérifier que les trois targets sont **UP** : **Status** → **Targets**

### Grafana — http://localhost:3000
Dashboard provisionné automatiquement avec :
- KPIs : nombre de députés, scrutins, taux d'adoption, groupes politiques
- Scrutins publics par mois (barres bleues)
- Taux de participation moyen par mois (courbe rouge)
- Évolution du taux d'adoption mensuel
- Bilan annuel des scrutins (table avec heatmap)

---

## CI/CD — GitHub Actions

Le pipeline se déclenche automatiquement à chaque push ou pull request sur `main` :

1. Checkout du code
2. Configuration Python 3.11
3. Installation des dépendances (`requirements.txt`)
4. Exécution des 37 tests pytest
5. Génération du rapport de couverture
6. Upload de l'artefact `coverage.xml`

---

## Procédure de redémarrage

Après un redémarrage machine, dans l'ordre :
```bash
# 1. Démarrer Docker Desktop et attendre que l'icône soit stable

# 2. Démarrer les conteneurs
cd data-pipeline-emploi
source venv/Scripts/activate   # Windows
docker compose up -d

# 3. Ressaisir le mot de passe PostgreSQL dans Grafana
#    → http://localhost:3000
#    → Connections → Data sources → PostgreSQL
#    → Champ Password → votre POSTGRES_PASSWORD → Save & test

# 4. Lancer le dashboard
streamlit run dashboards/streamlit/app.py
```

---

## Contexte académique

| | |
|---|---|
| **Formation** | Mastère DPIA 1 — Directeur de Projet en Intelligence Artificielle |
| **École** | L'École Multimédia · Paris |
| **Projet** | Projet #2 — Infrastructure Data Cloud |
| **Année** | 2025-2026 |
| **Auteur** | Samir NZAMBA |

---

## Licence

Données source : [Licence Ouverte / Open Licence](https://www.etalab.gouv.fr/licence-ouverte-open-licence) — Assemblée nationale française.

Code source : usage académique.