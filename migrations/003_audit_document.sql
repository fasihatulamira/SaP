-- Store archived export/print documents linked to audit_log rows
USE listmap;

CREATE TABLE IF NOT EXISTS audit_document (
  id           INT          NOT NULL AUTO_INCREMENT,
  audit_id     INT          NOT NULL,
  filename     VARCHAR(255) NOT NULL,
  mime_type    VARCHAR(100) NOT NULL,
  file_size    INT          NOT NULL,
  file_data    LONGBLOB     NOT NULL,
  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_audit_document_audit_id (audit_id),
  CONSTRAINT fk_audit_document_audit
    FOREIGN KEY (audit_id) REFERENCES audit_log(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
