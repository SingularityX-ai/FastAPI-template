import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status


@pytest.mark.anyio
async def test_health(client: AsyncClient, fastapi_app: FastAPI) -> None:
    """
    Checks the health endpoint.

    :param client: Client for the app.
    :type client: AsyncClient
    :param fastapi_app: Current FastAPI application.
    :type fastapi_app: FastAPI
    :raises AssertionError: If the response status code is not 200 (OK).
    """
    url = fastapi_app.url_path_for('health_check')
    response = await client.get(url)
    assert response.status_code == status.HTTP_200_OK
