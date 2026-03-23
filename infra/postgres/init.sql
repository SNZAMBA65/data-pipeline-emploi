-- ================================================================
-- Schéma du Data Warehouse : offres d'emploi Data Science
-- ================================================================

CREATE TABLE IF NOT EXISTS job_offers (
    id              SERIAL PRIMARY KEY,
    source          VARCHAR(50)  NOT NULL,         -- 'wttj', 'aijobs', 'adzuna'
    external_id     VARCHAR(255) UNIQUE,           -- identifiant côté source
    title           VARCHAR(255) NOT NULL,
    company         VARCHAR(255),
    location        VARCHAR(255),
    country         VARCHAR(10)  DEFAULT 'FR',
    contract_type   VARCHAR(100),                  -- CDI, CDD, Freelance...
    salary_min      NUMERIC(10,2),
    salary_max      NUMERIC(10,2),
    salary_currency VARCHAR(10)  DEFAULT 'EUR',
    description     TEXT,
    skills          TEXT[],                        -- tableau de compétences
    url             TEXT,
    published_at    TIMESTAMP,
    scraped_at      TIMESTAMP    DEFAULT NOW(),
    is_remote       BOOLEAN      DEFAULT FALSE
);

-- Index pour accélérer les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_jobs_source     ON job_offers(source);
CREATE INDEX IF NOT EXISTS idx_jobs_location   ON job_offers(location);
CREATE INDEX IF NOT EXISTS idx_jobs_published  ON job_offers(published_at);
CREATE INDEX IF NOT EXISTS idx_jobs_contract   ON job_offers(contract_type);