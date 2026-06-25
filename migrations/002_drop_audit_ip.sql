-- Remove ip_address from audit_log (no longer collected)
USE listmap;

ALTER TABLE audit_log DROP COLUMN ip_address;
