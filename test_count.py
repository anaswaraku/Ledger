import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

async def test():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
        res = await ac.post('/api/v1/auth/login', data={'username':'test@example.com','password':'password123'})
        token = res.json().get('access_token')
        if not token:
            print("Login failed")
            return
        
        journal_id = '2de1963d-b35a-4cb0-8d2b-5c92d7c59d16'
        res2 = await ac.get(f'/api/v1/name/count?journal_id={journal_id}&account_type=ASSET', headers={'Authorization': f'Bearer {token}'})
        print(res2.status_code)
        print(res2.text)

if __name__ == '__main__':
    asyncio.run(test())
