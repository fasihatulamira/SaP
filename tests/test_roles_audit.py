from io import BytesIO
from unittest.mock import patch

from auth import resolve_role


class TestRoles:
    def test_resolve_admin_role(self):
        assert resolve_role("testadmin", "testpass") == "admin"

    def test_resolve_user_role(self):
        assert resolve_role("testuser", "userpass") == "user"

    def test_resolve_invalid_credentials(self):
        assert resolve_role("wrong", "creds") is None

    def test_me_endpoint(self, auth_client):
        response = auth_client.get("/api/me")
        assert response.status_code == 200
        data = response.get_json()
        assert data["username"] == "testadmin"
        assert data["role"] == "admin"


class TestAuditAPI:
    def test_user_cannot_list_audit_logs(self, user_client):
        response = user_client.get("/api/audit")
        assert response.status_code == 403

    @patch("app.database.get_audit_logs")
    def test_admin_can_list_audit_logs(self, mock_logs, auth_client):
        mock_logs.return_value = [
            {
                "id": 1,
                "username": "testadmin",
                "role": "admin",
                "action": "export_xlsx",
                "report_ref": "LM-2026-TEST",
                "item_count": 3,
                "details": None,
                "created_at": "2026-06-10 12:00:00",
            }
        ]
        response = auth_client.get("/api/audit")
        assert response.status_code == 200
        assert len(response.get_json()["items"]) == 1

    @patch("app.log_event")
    def test_user_can_create_audit_entry(self, mock_log, user_client):
        response = user_client.post(
            "/api/audit",
            json={"action": "export_xlsx", "report_ref": "LM-1", "item_count": 2},
        )
        assert response.status_code == 200
        mock_log.assert_called_once()

    def test_invalid_audit_action_rejected(self, auth_client):
        response = auth_client.post("/api/audit", json={"action": "hack"})
        assert response.status_code == 400

    @patch("app.log_event")
    def test_user_can_create_report_audit_entry(self, mock_log, user_client):
        response = user_client.post(
            "/api/audit",
            json={"action": "create_report", "report_ref": "LM-1", "item_count": 2},
        )
        assert response.status_code == 200
        mock_log.assert_called_once()


class TestAuthAudit:
    @patch("audit.log_event")
    def test_login_failure_is_audited(self, mock_log, client):
        response = client.post(
            "/login",
            data={"username": "testadmin", "password": "wrong"},
        )
        assert response.status_code == 200
        mock_log.assert_called_once()
        assert mock_log.call_args[0][0] == "login_failed"


class TestExcelExport:
    @patch("app.log_event")
    @patch("app.build_export_workbook")
    def test_export_xlsx_returns_file(self, mock_build, mock_log, auth_client):
        mock_build.return_value = BytesIO(b"fake-xlsx")

        response = auth_client.post(
            "/api/export/xlsx",
            json={
                "topography": [{"sheetNum": "AP24", "sheetName": "X", "sheetScale": "1:50k", "release_year": 2017}],
                "dted": [],
                "landused": [],
                "sjungu": [],
                "report_ref": "LM-TEST",
            },
        )

        assert response.status_code == 200
        assert "spreadsheetml" in response.content_type
        mock_log.assert_called_once()

    def test_export_xlsx_requires_selection(self, auth_client):
        response = auth_client.post(
            "/api/export/xlsx",
            json={"topography": [], "dted": [], "landused": [], "sjungu": []},
        )
        assert response.status_code == 400
