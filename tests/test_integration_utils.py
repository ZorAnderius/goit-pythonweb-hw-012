import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.mark.asyncio
async def test_healthcheck_success(client, mock_db):
    mock_db.execute.return_value.scalar_one_or_none.return_value = 1

    response = client.get("/api/healthchecker")

    assert response.status_code == 200
    assert response.json() == {"message": "Healthy"}


@pytest.mark.asyncio
async def test_healthcheck_db_not_configured(client, mock_db):
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    with patch("src.api.utils.get_db", return_value=mock_db):
        with pytest.raises(Exception):
            await client()

@pytest.mark.asyncio
async def test_healthchecker_db_connection_error(client, mock_db):
    mock_db.execute.side_effect = Exception("Connection error")
    with patch("src.api.utils.get_db", return_value=mock_db):
        with pytest.raises(Exception):
            await client()
