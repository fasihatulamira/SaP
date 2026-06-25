-- SaP LISTMAP database schema
-- Run: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS listmap
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE listmap;

-- Topography map sheets
CREATE TABLE IF NOT EXISTS topography (
  sheetNum     VARCHAR(45)  NOT NULL,
  sheetName    VARCHAR(255) NOT NULL,
  sheetScale   VARCHAR(45)  NOT NULL,
  release_year INT          NOT NULL,
  PRIMARY KEY (sheetNum),
  INDEX idx_topography_release_year (release_year),
  INDEX idx_topography_sheet_name (sheetName)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Digital Terrain Elevation Data files
CREATE TABLE IF NOT EXISTS dted (
  id_name VARCHAR(255) NOT NULL,
  level   INT          NOT NULL,
  PRIMARY KEY (id_name),
  INDEX idx_dted_level (level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Land use classification categories
CREATE TABLE IF NOT EXISTS landused (
  landused_id INT          NOT NULL AUTO_INCREMENT,
  category    VARCHAR(255) NOT NULL,
  PRIMARY KEY (landused_id),
  INDEX idx_landused_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Sjungu map sheets
CREATE TABLE IF NOT EXISTS sjung (
  sheetNum   VARCHAR(255) NOT NULL,
  sheetName  VARCHAR(45)  NOT NULL,
  sheetScale VARCHAR(45)  NOT NULL,
  PRIMARY KEY (sheetNum),
  INDEX idx_sjung_sheet_name (sheetName)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Audit log for exports and sensitive actions
CREATE TABLE IF NOT EXISTS audit_log (
  id          INT          NOT NULL AUTO_INCREMENT,
  username    VARCHAR(100) NOT NULL,
  role        VARCHAR(20)  NOT NULL,
  action      VARCHAR(50)  NOT NULL,
  report_ref  VARCHAR(50)  NULL,
  item_count  INT          NOT NULL DEFAULT 0,
  details     JSON         NULL,
  created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_audit_created (created_at DESC),
  INDEX idx_audit_username (username),
  INDEX idx_audit_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Optional: full-text indexes for faster text search on large datasets.
-- Uncomment after initial import if search performance becomes an issue.
-- ALTER TABLE topography ADD FULLTEXT INDEX ft_topography_search (sheetNum, sheetName);
-- ALTER TABLE dted ADD FULLTEXT INDEX ft_dted_id_name (id_name);
-- ALTER TABLE landused ADD FULLTEXT INDEX ft_landused_category (category);
-- ALTER TABLE sjung ADD FULLTEXT INDEX ft_sjung_search (sheetNum, sheetName);
