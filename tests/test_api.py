from unittest.mock import patch

import pytest


class TestAuthentication:
    def test_api_requires_login(self, client):
        response = client.get("/api/records/topography")
        assert response.status_code == 401
        assert response.get_json()["error"] == "Authentication required."

    def test_index_redirects_to_login(self, client):
        response = client.get("/")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_login_success(self, client):
        response = client.post(
            "/login",
            data={"username": "testadmin", "password": "testpass"},
            follow_redirects=False,
        )
        assert response.status_code == 302

        with client.session_transaction() as sess:
            assert sess.get("authenticated") is True

    def test_login_failure(self, client):
        response = client.post(
            "/login",
            data={"username": "testadmin", "password": "wrong"},
        )
        assert response.status_code == 200
        assert b"Invalid username or password" in response.data


class TestRecordsAPI:
    @patch("app.database.get_topography_data")
    def test_topography_pagination(self, mock_get, auth_client):
        mock_get.return_value = {
            "items": [{"sheetNum": "AP24", "sheetName": "MERLIMAU", "sheetScale": "1:50000", "release_year": 2017}],
            "total": 23,
            "page": 2,
            "limit": 8,
            "total_pages": 3,
        }

        response = auth_client.get("/api/records/topography?page=2&limit=8")
        assert response.status_code == 200

        data = response.get_json()
        assert data["total"] == 23
        assert data["page"] == 2
        assert data["total_pages"] == 3
        assert len(data["items"]) == 1

        mock_get.assert_called_once_with(
            search_query=None,
            release_year=None,
            page=2,
            limit=8,
        )

    @patch("app.database.get_dted_data")
    def test_dted_search_and_level_filter(self, mock_get, auth_client):
        mock_get.return_value = {
            "items": [],
            "total": 0,
            "page": 1,
            "limit": 10,
            "total_pages": 1,
        }

        response = auth_client.get("/api/records/dted?search=E101&level=2")
        assert response.status_code == 200

        mock_get.assert_called_once_with(
            search_query="E101",
            level=2,
            page=1,
            limit=10,
        )

    def test_invalid_category(self, auth_client):
        response = auth_client.get("/api/records/invalid")
        assert response.status_code == 400
        assert response.get_json()["error"] == "Invalid category."


class TestRecordCrudAPI:
    @patch("app.create_topography_record")
    def test_create_topography_admin(self, mock_create, auth_client):
        response = auth_client.post(
            "/api/records/topography",
            json={
                "sheetNum": "AP99",
                "sheetName": "TEST",
                "sheetScale": "1:50000",
                "release_year": 2020,
            },
        )
        assert response.status_code == 201
        mock_create.assert_called_once_with("AP99", "TEST", "1:50000", 2020)

    @patch("app.create_landused_record")
    def test_create_landused_admin(self, mock_create, auth_client):
        mock_create.return_value = 12
        response = auth_client.post(
            "/api/records/landused",
            json={"landused_id": 12, "category": "FOREST"},
        )
        assert response.status_code == 201
        mock_create.assert_called_once_with("FOREST", 12)

    @patch("app.update_landused_record")
    def test_update_landused_admin(self, mock_update, auth_client):
        mock_update.return_value = True
        response = auth_client.put(
            "/api/records/landused/5",
            json={"category": "UPDATED"},
        )
        assert response.status_code == 200
        mock_update.assert_called_once_with("5", "UPDATED")

    @patch("app.delete_dted_record")
    def test_delete_dted_admin(self, mock_delete, auth_client):
        mock_delete.return_value = True
        response = auth_client.delete("/api/records/dted/E101")
        assert response.status_code == 200
        mock_delete.assert_called_once_with("E101")

    def test_create_requires_admin(self, user_client):
        response = user_client.post(
            "/api/records/topography",
            json={
                "sheetNum": "AP99",
                "sheetName": "TEST",
                "sheetScale": "1:50000",
                "release_year": 2020,
            },
        )
        assert response.status_code == 403


class TestFiltersAPI:
    @patch("app.database.get_filter_options")
    def test_filters_returns_years_and_levels(self, mock_filters, auth_client):
        mock_filters.return_value = {
            "release_years": [2019, 2018],
            "dted_levels": [2],
        }

        response = auth_client.get("/api/filters")
        assert response.status_code == 200
        data = response.get_json()
        assert data["release_years"] == [2019, 2018]
        assert data["dted_levels"] == [2]

    def test_filters_requires_auth(self, client):
        response = client.get("/api/filters")
        assert response.status_code == 401
