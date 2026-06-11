import asyncio
import httpx
import uuid

BASE_URL = "http://127.0.0.1:8000"

async def run_demo():
    print("🚀 Starting Ledger Phase 1 End-to-End Demo...\n")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Register User
        email = f"demo-{uuid.uuid4().hex[:6]}@example.com"
        password = "SecurePassword123!"
        print(f"1️⃣ Registering new user: {email}")
        resp = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        if resp.status_code != 201:
            print(f"❌ Failed to register: {resp.text}")
            return
        user = resp.json()
        print(f"✅ User registered with ID: {user['id']}\n")

        # 2. Login
        print("2️⃣ Logging in to get JWT access token...")
        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Logged in successfully!\n")

        # 3. Create Journal
        print("3️⃣ Creating a new accounting Journal...")
        resp = await client.post("/api/v1/journals/", json={"name": "My Personal Finances", "description": "Demo journal"}, headers=headers)
        journal_id = resp.json()["id"]
        print(f"✅ Journal created with ID: {journal_id}\n")

        # 4. Create Accounts
        print("4️⃣ Creating Accounts (Assets and Expenses)...")
        resp1 = await client.post("/api/v1/accounts/", json={"journal_id": journal_id, "name": "assets:checking", "account_type": "ASSET"}, headers=headers)
        checking_id = resp1.json()["id"]
        
        resp2 = await client.post("/api/v1/accounts/", json={"journal_id": journal_id, "name": "expenses:groceries", "account_type": "EXPENSE"}, headers=headers)
        groceries_id = resp2.json()["id"]
        print(f"✅ Accounts created! \n   - assets:checking ({checking_id})\n   - expenses:groceries ({groceries_id})\n")

        # 5. Create Double-Entry Transaction
        print("5️⃣ Creating a double-entry transaction ($50 for groceries)...")
        txn_data = {
            "journal_id": journal_id,
            "date": "2026-06-11",
            "description": "Weekly grocery run",
            "payee": "Whole Foods",
            "entries": [
                {"account_id": groceries_id, "amount": "50.00", "currency": "USD"},  # Debit (Positive)
                {"account_id": checking_id, "amount": "-50.00", "currency": "USD"}   # Credit (Negative)
            ]
        }
        resp = await client.post("/api/v1/transactions/", json=txn_data, headers=headers)
        if resp.status_code == 201:
            print(f"✅ Transaction created successfully with ID: {resp.json()['id']}\n")
        else:
            print(f"❌ Transaction failed: {resp.text}\n")

        # 6. Fetch Transactions
        print("6️⃣ Fetching all transactions for the journal...")
        resp = await client.get(f"/api/v1/transactions/?journal_id={journal_id}", headers=headers)
        txns = resp.json()
        print(f"✅ Retrieved {len(txns)} transaction(s):")
        for t in txns:
            print(f"   📅 {t['date']} | {t['payee']} | {t['description']}")
            for e in t['entries']:
                print(f"      - Account {e['account_id']}: {e['amount']} {e['currency']}")
        
        print("\n🎉 Phase 1 End-to-End flow works perfectly!")

if __name__ == "__main__":
    asyncio.run(run_demo())
