import pytest
from app import load_files, get_redis_client


async def test_load_files():
    db = get_redis_client()
    await load_files()
    assert db.exists('wta-players:azarenka_corrected') == 1
    assert db.hget('wta-players:azarenka_corrected', 'path') is not None
