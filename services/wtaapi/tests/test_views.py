import pytest
import pathlib
import json
from app import app, load_files
from fastapi.testclient import TestClient
from app import get_redis_client, get_storage_key

client = TestClient(app)


async def load_content():
    await load_files()

    db = get_redis_client()
    path = pathlib.Path('./tests/test_matches.json')
    with path.open() as f:
        content = json.load(f)
        key = get_storage_key('azarenka')
        db.hset(key, key='content', value=json.dumps(content))

    if type(content) == bytes:
        content = json.loads(content)


class TestGetPlayers:
    def test_get_players_no_query(self):
        response = client.get("/v1/players")
        assert response.status_code == 200
        assert "results" in response.json()


class TestGetPlayer:
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


class TestGetPlayerStatistics:
    async def test_get_player_statistics_valid(self):
        await load_content()

        response = client.get("/v1/players/azarenka/statistics")
        assert response.status_code == 200
        assert "years" in response.json()
        assert "surfaces" in response.json()

    # def test_get_player_statistics_invalid(self):
    #     response = client.get("/v1/players/non_existent_player/statistics")
    #     assert response.status_code == 404
    #     assert "detail" in response.json()
