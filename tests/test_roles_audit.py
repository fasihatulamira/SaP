from io import BytesIO
from unittest.mock import patch

from auth import resolve_role


class TestRoles:
    def test_resolve_admin_role(self):
        from config import Config

        Config.AUTH_ADMIN_USERNAME = "testadmin"
        Config.AUTH_ADMIN_PASSWORD = "testpass"
        assert resolve_role("testadmin", "testpass") == "admin"

    def test_resolve_user_role(self):
        from config import Config

        Config.AUTH_USER_USERNAME = "testuser"
        Config.AUTH_USER_PASSWORD = "userpass"
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

    @patch("app.log_event", return_value=1)
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

    @patch("app.log_event", return_value=2)
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
    @patch("app._store_audit_document")
    @patch("app.log_event")
    @patch("app.build_export_workbook")
    def test_export_xlsx_returns_file(self, mock_build, mock_log, mock_store, auth_client):
        mock_build.return_value = BytesIO(b"fake-xlsx")
        mock_log.return_value = 42

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
        mock_store.assert_called_once()
        assert mock_store.call_args[0][0] == 42

    def test_export_xlsx_requires_selection(self, auth_client):
        response = auth_client.post(
            "/api/export/xlsx",
            json={"topography": [], "dted": [], "landused": [], "sjungu": []},
        )
        assert response.status_code == 400


class TestAuditDocumentAPI:
    @patch("app._store_audit_document", return_value=True)
    @patch("app.log_event", return_value=99)
    def test_user_can_archive_pdf_document(self, mock_log, mock_store, user_client):
        from werkzeug.datastructures import FileStorage

        pdf = FileStorage(
            stream=BytesIO(b"%PDF-1.4 fake"),
            filename="report.pdf",
            content_type="application/pdf",
        )
        response = user_client.post(
            "/api/audit/document",
            data={
                "action": "export_pdf",
                "report_ref": "LM-1",
                "item_count": "2",
                "report_title": "Test Report",
                "filename": "report.pdf",
                "file": pdf,
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert response.get_json()["id"] == 99
        mock_log.assert_called_once()
        mock_store.assert_called_once()

    def test_invalid_action_for_document_rejected(self, auth_client):
        from werkzeug.datastructures import FileStorage

        pdf = FileStorage(stream=BytesIO(b"%PDF"), filename="x.pdf", content_type="application/pdf")
        response = auth_client.post(
            "/api/audit/document",
            data={"action": "clear_selection", "file": pdf},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_user_cannot_download_audit_document(self, user_client):
        response = user_client.get("/api/audit/1/document")
        assert response.status_code == 403

    @patch("app.database.get_audit_document")
    def test_admin_can_download_audit_document(self, mock_get, auth_client):
        mock_get.return_value = {
            "id": 1,
            "audit_id": 7,
            "filename": "report.pdf",
            "mime_type": "application/pdf",
            "file_size": 5,
            "file_data": b"%PDF-",
            "created_at": "2026-07-30 10:00:00",
        }
        response = auth_client.get("/api/audit/7/document")
        assert response.status_code == 200
        assert response.content_type.startswith("application/pdf")
        assert response.data == b"%PDF-"

    @patch("app.database.get_audit_document", return_value=None)
    def test_missing_audit_document_returns_404(self, mock_get, auth_client):
        response = auth_client.get("/api/audit/999/document")
        assert response.status_code == 404
