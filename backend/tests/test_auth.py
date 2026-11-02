import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # 1. Register a new user
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password123!",
            "display_name": "Test User"
        }
    )
    assert reg_res.status_code == 201, reg_res.text
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == "test@example.com"
    assert reg_data["user"]["display_name"] == "Test User"

    # 2. Duplicate registration fails with 409
    dup_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "Password123!",
            "display_name": "Test User 2"
        }
    )
    assert dup_res.status_code == 409

    # 3. Login with correct password
    login_res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "Password123!"
        }
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token

    # 4. Login with wrong password fails
    wrong_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword!"
        }
    )
    assert wrong_login.status_code == 401

    # 5. Get current user profile (/me)
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "test@example.com"

    # 6. Refresh token
    refresh_token = login_res.cookies.get("refresh_token")
    if refresh_token:
        refresh_res = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_token}
        )
        assert refresh_res.status_code == 200
        new_token = refresh_res.json()["access_token"]
        assert new_token

    # 7. Logout
    logout_res = await client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
