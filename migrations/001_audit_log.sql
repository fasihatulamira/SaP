-- Migration for existing listmap databases (run once if upgrading)
USE listmap;

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
