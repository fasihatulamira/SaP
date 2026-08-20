-- SaP LISTMAP PostgreSQL schema (Supabase)
-- Same logical structure as schema.sql (MySQL), with quoted camelCase identifiers.
-- Run in Supabase SQL Editor or: psql "$DATABASE_URL" -f schema_postgres.sql

-- Topography map sheets
CREATE TABLE IF NOT EXISTS topography (
  "sheetNum"     VARCHAR(45)  NOT NULL,
  "sheetName"    VARCHAR(255) NOT NULL,
  "sheetScale"   VARCHAR(45)  NOT NULL,
  release_year   INT          NOT NULL,
  PRIMARY KEY ("sheetNum")
);
CREATE INDEX IF NOT EXISTS idx_topography_release_year ON topography (release_year);
CREATE INDEX IF NOT EXISTS idx_topography_sheet_name ON topography ("sheetName");

-- Digital Terrain Elevation Data files
CREATE TABLE IF NOT EXISTS dted (
  id_name VARCHAR(255) NOT NULL,
  level   INT          NOT NULL,
  PRIMARY KEY (id_name)
);
CREATE INDEX IF NOT EXISTS idx_dted_level ON dted (level);

-- Land use classification categories
CREATE TABLE IF NOT EXISTS landused (
  landused_id SERIAL PRIMARY KEY,
  category    VARCHAR(255) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_landused_category ON landused (category);

-- Sjungu map sheets
CREATE TABLE IF NOT EXISTS sjung (
  "sheetNum"   VARCHAR(255) NOT NULL,
  "sheetName"  VARCHAR(45)  NOT NULL,
  "sheetScale" VARCHAR(45)  NOT NULL,
  PRIMARY KEY ("sheetNum")
);
CREATE INDEX IF NOT EXISTS idx_sjung_sheet_name ON sjung ("sheetName");

-- Audit log for exports and sensitive actions
CREATE TABLE IF NOT EXISTS audit_log (
  id          SERIAL PRIMARY KEY,
  username    VARCHAR(100) NOT NULL,
  role        VARCHAR(20)  NOT NULL,
  action      VARCHAR(50)  NOT NULL,
  report_ref  VARCHAR(50)  NULL,
  item_count  INT          NOT NULL DEFAULT 0,
  details     JSONB        NULL,
  created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_username ON audit_log (username);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log (action);

-- Archived export/print documents linked to audit_log
CREATE TABLE IF NOT EXISTS audit_document (
  id           SERIAL PRIMARY KEY,
  audit_id     INT          NOT NULL,
  filename     VARCHAR(255) NOT NULL,
  mime_type    VARCHAR(100) NOT NULL,
  file_size    INT          NOT NULL,
  file_data    BYTEA        NOT NULL,
  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_audit_document_audit_id UNIQUE (audit_id),
  CONSTRAINT fk_audit_document_audit
    FOREIGN KEY (audit_id) REFERENCES audit_log(id)
    ON DELETE CASCADE
);
