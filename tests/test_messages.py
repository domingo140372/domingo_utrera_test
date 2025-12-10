import pytest


@pytest.mark.asyncio
async def test_send_clean_message(client):
    msg = {
        "session_id": "session-test",
        "content": "Hola buenos días",
        "sender": "user"
    }

    response = await client.post("/messages/", json=msg)
    assert response.status_code == 201

    data = response.json()

    assert data["content"] == msg["content"]
    assert data["sender"] == msg["sender"]
    assert data["session_id"] == msg["session_id"]



@pytest.mark.asyncio
async def test_send_insult_message(client):
    msg = {
        "session_id": "test-session",
        "content": "Eres un feo",
        "sender": "user"
    }

    response = await client.post("/messages/", json=msg)

    assert response.status_code == 400
    assert "insulto" in response.json()["detail"]


@pytest.mark.asyncio
async def test_send_groseria_message(client):
    msg = {
        "session_id": "test-session",
        "content": "maldito sea",
        "sender": "user"
    }

    response = await client.post("/messages/", json=msg)

    assert response.status_code == 400
    assert "grosería" in response.json()["detail"]
