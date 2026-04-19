-- ================================================================
-- Schéma du Data Warehouse — Assemblée nationale française
-- 17e législature · Pipeline Data Cloud · DPIA 1
-- ================================================================

-- Groupes politiques
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
);

-- Députés actifs de la 17e législature
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
    groupe_sigle           VARCHAR(20) REFERENCES groupes_politiques(sigle),
    groupe_nom             VARCHAR(200),
    url_photo              TEXT,
    collecte_le            TIMESTAMP DEFAULT NOW()
);

-- Scrutins publics
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
);

-- Index pour accélérer les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_deputes_groupe  ON deputes(groupe_sigle);
CREATE INDEX IF NOT EXISTS idx_deputes_civilite ON deputes(civilite);
CREATE INDEX IF NOT EXISTS idx_scrutins_date   ON scrutins(date);
CREATE INDEX IF NOT EXISTS idx_scrutins_sort   ON scrutins(sort);
CREATE INDEX IF NOT EXISTS idx_scrutins_annee  ON scrutins(annee);