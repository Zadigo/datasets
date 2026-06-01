import pytest
from app import app, load_files
from fastapi.testclient import TestClient

client = TestClient(app)


class TestGetPlayers:
    def test_get_players_no_query(self):
        response = client.get("/v1/players")
        assert response.status_code == 200
        assert "results" in response.json()


class TestGetPlayer:
    @pytest.mark.asyncio
    async def test_get_player_valid(self):
        await load_files()
        
        response = client.get("/v1/players/azarenka")
        assert response.status_code == 200
        assert "results" in response.json()
        assert len(response.json()["results"]) > 0

    def test_get_player_invalid(self):
        response = client.get("/v1/players/azarenka")
        assert response.status_code == 200
        assert "results" in response.json()
        assert len(response.json()["results"]) > 0

    def test_get_player_invalid(self):
        response = client.get("/v1/players/non_existent_player")
        assert response.status_code == 404
        assert "detail" in response.json()
