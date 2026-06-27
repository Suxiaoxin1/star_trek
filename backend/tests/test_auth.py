"""认证 API 测试"""
import pytest


@pytest.mark.asyncio
class TestAuth:

    async def test_register_success(self, client):
        """正常注册"""
        resp = await client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@test.com",
            "password": "password123",
            "display_name": "新用户",
            "role": "viewer",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@test.com"
        assert data["role"] == "viewer"

    async def test_register_duplicate_username(self, client):
        """重复用户名注册"""
        await client.post("/api/v1/auth/register", json={
            "username": "dupuser",
            "email": "dup1@test.com",
            "password": "pass123456",
        })
        resp = await client.post("/api/v1/auth/register", json={
            "username": "dupuser",
            "email": "dup2@test.com",
            "password": "pass123456",
        })
        assert resp.status_code == 400
        assert "已存在" in resp.json()["detail"]

    async def test_register_duplicate_email(self, client):
        """重复邮箱注册"""
        await client.post("/api/v1/auth/register", json={
            "username": "user1",
            "email": "same@test.com",
            "password": "pass123456",
        })
        resp = await client.post("/api/v1/auth/register", json={
            "username": "user2",
            "email": "same@test.com",
            "password": "pass123456",
        })
        assert resp.status_code == 400
        assert "已被注册" in resp.json()["detail"]

    async def test_register_short_password(self, client):
        """密码太短"""
        resp = await client.post("/api/v1/auth/register", json={
            "username": "shortpw",
            "email": "shortpw@test.com",
            "password": "12345",  # 少于 6 位
        })
        assert resp.status_code == 422

    async def test_login_success(self, client):
        """正常登录"""
        await client.post("/api/v1/auth/register", json={
            "username": "loginuser",
            "email": "login@test.com",
            "password": "password123",
        })
        resp = await client.post("/api/v1/auth/login", json={
            "username": "loginuser",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client):
        """密码错误"""
        await client.post("/api/v1/auth/register", json={
            "username": "wrongpw",
            "email": "wrongpw@test.com",
            "password": "password123",
        })
        resp = await client.post("/api/v1/auth/login", json={
            "username": "wrongpw",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        """不存在用户登录"""
        resp = await client.post("/api/v1/auth/login", json={
            "username": "ghost",
            "password": "password123",
        })
        assert resp.status_code == 401

    async def test_get_me(self, client, admin_token):
        """获取当前用户信息"""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "test_admin"
        assert data["role"] == "admin"

    async def test_get_me_no_token(self, client):
        """无 token 访问 /me"""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_refresh_token(self, client):
        """刷新令牌"""
        await client.post("/api/v1/auth/register", json={
            "username": "refreshuser",
            "email": "refresh@test.com",
            "password": "password123",
        })
        login_resp = await client.post("/api/v1/auth/login", json={
            "username": "refreshuser",
            "password": "password123",
        })
        refresh_token = login_resp.json()["refresh_token"]

        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_change_password(self, client, admin_token):
        """修改密码"""
        resp = await client.put(
            "/api/v1/auth/change-password",
            params={"old_password": "testpass123", "new_password": "newpass456"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200