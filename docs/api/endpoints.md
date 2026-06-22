# Ledger Web Application - REST API Endpoints Specification

This document details every HTTP REST endpoint in the Ledger Web Application, including query parameters, JSON request/response formats, specific error code definitions, and deprecated routes.

---

## 1. Global API Error Response Codes Reference

Ledger Web exposes consistent HTTP error states to clients:

| Status Code | Code Meaning in Ledger Web | Common Causes & Response Formats |
| :--- | :--- | :--- |
| **`400 Bad Request`** | Application validation or processing logic failed. | Double-entry transaction imbalance, missing historical market exchange rates for reports, or uploading an invalid file format.<br/>*Format*: `{"detail": "..."}` or `{"detail": {"error": "calculating_error", "message": "...", "missing_rates": [...]}}` |
| **`401 Unauthorized`** | Authentication credentials (JWT) are missing or invalid. | The `Authorization: Bearer <token>` header was not provided, has expired, or is malformed.<br/>*Format*: `{"detail": "Not authenticated"}` |
| **`402 Payment Required`** | Reserved for future premium subscription features. | Not currently raised by endpoints in the community ledger version. |
| **`403 Forbidden`** | Client lacks access rights to retrieve the requested resource. | Used during token boundary verification or unauthenticated secure operations.<br/>*Format*: `{"detail": "Forbidden"}` |
| **`404 Not Found`** | Resource does not exist, or belongs to another user. | **Security Privacy Guard**: If a user queries a `journal_id` or `transaction_id` that does not belong to their account, the application returns a `404` error instead of a `403` to prevent database resource enumeration.<br/>*Format*: `{"detail": "Journal not found."}` |
| **`422 Unprocessable Content`** | Request payloads or parameters failed structural parsing constraints. | FastAPI returns this when query params/body fields fail validation (e.g. negative numbers where positive is expected, or missing required fields).<br/>*Format*: `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` |

---

## 2. Authentication Router (`/api/v1/auth`)

Endpoints for registering, logging in, and logging out users.

### 2.1 POST `/api/v1/auth/register`
* **Summary**: Register a new user account.
* **Description**: Creates a new user account with the given email and password. Passwords are hashed with Argon2 before storage. Returns the created user object (without the password hash).
* **Request Body**:
  ```json
  {
    "email": "alice@example.com",
    "password": "securepassword123"
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "alice@example.com",
    "created_at": "2026-06-19T11:39:21.947Z"
  }
  ```
* **Error Responses**:
  - `400 Bad Request` — Email is already registered:
    ```json
    { "detail": "Email already registered." }
    ```
  - `422 Unprocessable Content` — Missing or malformed fields:
    ```json
    { "detail": [{ "loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error.email" }] }
    ```

### 2.2 POST `/api/v1/auth/login`
* **Summary**: Log in and receive a JWT access token.
* **Description**: Authenticates the user by email and password. Returns a signed JWT Bearer token valid for `ACCESS_TOKEN_EXPIRE_MINUTES` minutes (default: 30). Include this token in the `Authorization: Bearer <token>` header on all protected endpoints.
* **Request Body**:
  ```json
  {
    "email": "alice@example.com",
    "password": "securepassword123"
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```
* **Error Responses**:
  - `401 Unauthorized` — Incorrect email or password:
    ```json
    { "detail": "Incorrect email or password." }
    ```
  - `422 Unprocessable Content` — Missing fields:
    ```json
    { "detail": [{ "loc": ["body", "password"], "msg": "field required", "type": "missing" }] }
    ```

### 2.3 POST `/api/v1/auth/logout`
* **Summary**: Log out (client should discard the token).
* **Description**: Signals a logout intent. Because JWT is stateless, the server does not invalidate the token — the client is responsible for discarding it. A server-side token blacklist is planned for a future release.
* **Auth**: Required (`Authorization: Bearer <token>`).
* **Error Responses**:
  - `401 Unauthorized` — Token missing or expired:
    ```json
    { "detail": "Not authenticated" }
    ```

---

## 3. Journals Router (`/api/v1/journals`)

Manage accounting books (Journals) owned by the user. All endpoints require JWT authentication.

### 3.1 GET `/api/v1/journals`
* **Summary**: List all journals owned by the current user.
* **Description**: Returns all accounting journals belonging to the authenticated user. Each journal is an isolated ledger containing its own accounts, transactions, and budgets.
* **Auth**: Required.
* **Success Response (200 OK)**:
  ```json
  [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "owner_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "string",
      "description": "string",
      "base_currency": "string",
      "created_at": "2026-06-19T11:40:09.678Z",
      "updated_at": "2026-06-19T11:40:09.678Z"
    }
  ]
  ```
* **Error Responses**:
  - `401 Unauthorized` — Token missing or expired:
    ```json
    { "detail": "Not authenticated" }
    ```

### 3.2 POST `/api/v1/journals`
* **Summary**: Create a new accounting journal.
* **Description**: Creates a new journal (ledger book) for the authenticated user. All accounts, transactions, and budgets are scoped to a journal.
* **Auth**: Required.
* **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "base_currency": "USD"
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "owner_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "string",
    "description": "string",
    "base_currency": "string",
    "created_at": "2026-06-19T11:40:09.683Z",
    "updated_at": "2026-06-19T11:40:09.683Z"
  }
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `422 Unprocessable Content` — Missing required field `name`:
    ```json
    { "detail": [{ "loc": ["body", "name"], "msg": "field required", "type": "missing" }] }
    ```

### 3.3 GET `/api/v1/journals/{journal_id}`
* **Summary**: Get a specific journal by ID.
* **Description**: Returns full metadata for a single journal. Returns `404` if the journal does not exist or belongs to another user (privacy guard — ownership is not revealed to the caller).
* **Auth**: Required.
* **Path Parameters**:
  - `journal_id` (UUID, Required): ID of the journal to retrieve.
* **Success Response (200 OK)**:
  ```json
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "owner_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "string",
    "description": "string",
    "base_currency": "string",
    "created_at": "2026-06-19T11:40:09.654Z",
    "updated_at": "2026-06-19T11:40:09.654Z"
  }
  ```
* **Error Responses**:
  - `401 Unauthorized` — Token missing or expired:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal not found or belongs to another user:
    ```json
    { "detail": "Journal not found." }
    ```
  - `422 Unprocessable Content` — Invalid UUID format:
    ```json
    { "detail": [{ "loc": ["path", "journal_id"], "msg": "value is not a valid uuid", "type": "type_error.uuid" }] }
    ```

### 3.4 PATCH `/api/v1/journals/{journal_id}`
* **Summary**: Update a specific journal by ID.
* **Description**: Partially updates a journal's name, description, or base currency. All fields are optional — only provided fields are updated.
* **Auth**: Required.
* **Path Parameters**:
  - `journal_id` (UUID, Required): ID of the journal to update.
* **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "base_currency": "string"
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "owner_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "string",
    "description": "string",
    "base_currency": "string",
    "created_at": "2026-06-19T11:40:30.439Z",
    "updated_at": "2026-06-19T11:40:30.439Z"
  }
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal not found or belongs to another user:
    ```json
    { "detail": "Journal not found." }
    ```
  - `422 Unprocessable Content`:
    ```json
    { "detail": [{ "loc": ["path", "journal_id"], "msg": "value is not a valid uuid", "type": "type_error.uuid" }] }
    ```

### 3.5 DELETE `/api/v1/journals/{journal_id}`
* **Summary**: Delete a specific journal by ID.
* **Description**: Permanently deletes the journal and all associated accounts, transactions, and budgets. This action cannot be undone.
* **Auth**: Required.
* **Path Parameters**:
  - `journal_id` (UUID, Required): ID of the journal to delete.
* **Success Response (204 No Content)**: Returns empty body on success.
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal not found or belongs to another user:
    ```json
    { "detail": "Journal not found." }
    ```

---

## 4. Accounts Router (`/api/v1/accounts`)

Manage account codes (Assets, Expenses, Liabilities) inside a journal. All endpoints require JWT authentication.

### 4.1 POST `/api/v1/accounts`
* **Summary**: Create a new account in a journal.
* **Description**: Creates a new account within the specified journal. Account names should use a colon-separated hierarchy (e.g., `assets:bank:checking`). The `account_type` must be one of: `ASSET`, `LIABILITY`, `EQUITY`, `INCOME`, `EXPENSE`.
* **Auth**: Required.
* **Request Body**:
  ```json
  {
    "name": "string",
    "account_type": "ASSET",
    "journal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "name": "string",
    "account_type": "ASSET",
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "journal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "created_at": "2026-06-19T11:43:07.080Z"
  }
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal not found or belongs to another user:
    ```json
    { "detail": "Journal not found." }
    ```
  - `422 Unprocessable Content` — Invalid `account_type` value:
    ```json
    { "detail": [{ "loc": ["body", "account_type"], "msg": "value is not a valid enumeration member", "type": "type_error.enum" }] }
    ```

### 4.2 GET `/api/v1/accounts`
* **Summary**: List all accounts in a journal.
* **Description**: Returns all accounts belonging to the specified journal, sorted by account name. Used to populate account selection dropdowns in the transaction entry UI.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Success Response (200 OK)**:
  ```json
  [
    {
      "name": "string",
      "account_type": "ASSET",
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "journal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "created_at": "2026-06-19T11:43:07.132Z"
    }
  ]
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal not found:
    ```json
    { "detail": "Journal not found." }
    ```

### 4.3 GET `/api/v1/accounts/search`
* **Summary**: Auto-suggest accounts by name prefix.
* **Description**: Returns accounts whose name starts with the given prefix `q`. Used for live autocomplete in the transaction entry form. Matching is case-insensitive.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `q` (String, Required): Account name prefix. minLength: 1.
* **Success Response (200 OK)**:
  ```json
  [
    {
      "name": "assets:bank:checking",
      "account_type": "ASSET",
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "journal_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "created_at": "2026-06-01T09:00:00.000Z"
    }
  ]
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `422 Unprocessable Content` — `q` param missing or empty:
    ```json
    { "detail": [{ "loc": ["query", "q"], "msg": "field required", "type": "missing" }] }
    ```

### 4.4 GET `/api/v1/accounts/{account_id}/register`
* **Summary**: Get account register (transaction history with running balance).
* **Description**: Returns a chronological list of all transaction entries touching the given account, along with a running balance after each entry. Returns `404` if the account does not exist within the journal.
* **Auth**: Required.
* **Path Parameters**:
  - `account_id` (UUID, Required): ID of the account.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Success Response (200 OK)**:
  ```json
  [
    {
      "transaction_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "date": "2026-06-15",
      "payee": "Supermart",
      "description": "Weekly groceries",
      "amount": "-75.00",
      "running_balance": "1925.00"
    }
  ]
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Account not found in this journal:
    ```json
    { "detail": "Account not found." }
    ```

---

## 5. Transactions Router (`/api/v1/transactions`)

Execute and search double-entry transaction records. All endpoints require JWT authentication.

### 5.1 GET `/api/v1/transactions`
* **Summary**: List transactions in a journal.
* **Description**: Returns a paginated list of transactions in the journal, with optional filters by date range, payee, or description. Each transaction includes its posting entries.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required): Journal to query.
  - `skip` (Integer, Optional, Default: 0): Minimum: 0.
  - `limit` (Integer, Optional, Default: 50): Minimum: 1, Maximum: 200.
  - `date_from` (Date string, Optional)
  - `date_to` (Date string, Optional)
  - `payee` (String, Optional)
  - `description` (String, Optional)
* **Success Response (200 OK)**:
  ```json
  [
    {
      "date": "2026-06-19",
      "description": "string",
      "payee": "string",
      "code": "string",
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "journal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "created_at": "2026-06-19T11:41:19.486Z",
      "entries": []
    }
  ]
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal not found:
    ```json
    { "detail": "Journal not found." }
    ```

### 5.2 POST `/api/v1/transactions`
* **Summary**: Create a new double-entry transaction.
* **Description**: Creates a new transaction in the specified journal. The request body must include a list of at least two posting entries whose amounts sum to exactly zero (debits == credits). All account IDs must belong to the journal. Validates balance using the double-entry domain rule before persisting.
* **Auth**: Required.
* **Request Body**:
  ```json
  {
    "date": "2026-06-19",
    "description": "string",
    "payee": "string",
    "code": "string",
    "journal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "entries": [
      {
        "account_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "amount": 0,
        "currency": "USD",
        "cost_amount": 0,
        "cost_currency": "string"
      }
    ]
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "date": "2026-06-19",
    "description": "string",
    "payee": "string",
    "code": "string",
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "journal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "created_at": "2026-06-19T11:41:19.495Z",
    "entries": []
  }
  ```
* **Error Responses**:
  - `400 Bad Request` — Transaction entries do not sum to zero:
    ```json
    { "detail": "Transaction entries do not balance. Sum must equal zero." }
    ```
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal or account not found:
    ```json
    { "detail": "Journal not found." }
    ```
  - `422 Unprocessable Content` — Missing required fields:
    ```json
    { "detail": [{ "loc": ["body", "date"], "msg": "field required", "type": "missing" }] }
    ```

### 5.3 GET `/api/v1/transactions/recent`
* **Summary**: List recent transactions in a journal.
* **Description**: Returns the most recent transactions in the journal. Used to populate the dashboard's recent activity panel.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Success Response (200 OK)**:
  ```json
  [
    {
      "date": "2026-06-19",
      "description": "string",
      "payee": "string",
      "code": "string",
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "journal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "created_at": "2026-06-19T11:41:19.440Z",
      "entries": []
    }
  ]
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal not found:
    ```json
    { "detail": "Journal not found." }
    ```

### 5.4 GET `/api/v1/transactions/{txn_id}`
* **Summary**: Get a single transaction by ID.
* **Description**: Returns the full details of a transaction, including all posting entries. Returns `404` if the transaction does not exist or belongs to a different journal.
* **Auth**: Required.
* **Path Parameters**:
  - `txn_id` (UUID, Required): ID of the transaction.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Success Response (200 OK)**:
  ```json
  {
    "date": "2026-06-19",
    "description": "string",
    "payee": "string",
    "code": "string",
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "journal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "created_at": "2026-06-19T11:42:13.604Z",
    "entries": []
  }
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Transaction not found in journal:
    ```json
    { "detail": "Transaction not found." }
    ```

### 5.5 PUT `/api/v1/transactions/{txn_id}`
* **Summary**: Update transaction metadata (date, description, payee, code).
* **Description**: Updates the header fields of an existing transaction. Posting entries cannot be changed via this endpoint — delete and recreate the transaction if entries must change.
* **Auth**: Required.
* **Path Parameters**:
  - `txn_id` (UUID, Required): ID of the transaction to update.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Request Body**:
  ```json
  {
    "date": "2026-06-19",
    "description": "string",
    "payee": "string",
    "code": "string"
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "date": "2026-06-19",
    "description": "string",
    "payee": "string",
    "code": "string",
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "journal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "created_at": "2026-06-19T11:42:13.610Z",
    "entries": []
  }
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Transaction not found:
    ```json
    { "detail": "Transaction not found." }
    ```

### 5.6 DELETE `/api/v1/transactions/{txn_id}`
* **Summary**: Delete a transaction and all its entries.
* **Description**: Permanently deletes a transaction and all associated ledger entries. The transaction must exist in the specified journal, and the user must own the journal.
* **Auth**: Required.
* **Path Parameters**:
  - `txn_id` (UUID, Required): ID of the transaction to delete.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Success Response (204 No Content)**: Returns empty response on success.
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal or transaction not found:
    ```json
    { "detail": "Journal not found." }
    ```
    or
    ```json
    { "detail": "Transaction not found." }
    ```
  - `422 Unprocessable Content` — Missing required parameters:
    ```json
    { "detail": [{ "loc": ["query", "journal_id"], "msg": "field required", "type": "missing" }] }
    ```

---

## 6. Financial Reports Router (`/api/v1/reports`)

Query real-time report summaries. All endpoints require JWT authentication.

### 6.1 GET `/api/v1/reports/balance-sheet`
* **Summary**: Generate a balance sheet report.
* **Description**: Returns a balance sheet snapshot at the given date.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `date` (date, Optional): As of date (default: today).
* **Success Response (200 OK)**:
  ```json
  {
    "date": "2026-06-19",
    "assets": {
      "assets:bank:checking": "2000.00",
      "assets:cash": "500.00"
    },
    "liabilities": {
      "liabilities:creditcard": "-800.00"
    },
    "equity": {
      "equity:opening-balances": "-1700.00"
    },
    "net": "0.00"
  }
  ```
* **Error Responses**:
  - `400 Bad Request` — Missing exchange rates for multi-currency journal:
    ```json
    { "detail": { "error": "calculating_error", "message": "Report cannot be generated due to missing exchange rates.", "missing_rates": ["BTC/USD"] } }
    ```
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal not found:
    ```json
    { "detail": "Journal not found." }
    ```

### 6.2 GET `/api/v1/reports/income-statement`
* **Summary**: Generate an income statement report.
* **Description**: Returns an income statement for a specific period.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `date_from` (date, Required)
  - `date_to` (date, Required)
* **Success Response (200 OK)**:
  ```json
  {
    "date_from": "2026-01-01",
    "date_to": "2026-06-30",
    "income": {
      "income:salary": "6000.00",
      "income:freelance": "1200.00"
    },
    "expenses": {
      "expenses:food": "800.00",
      "expenses:rent": "1500.00"
    },
    "total_income": "7200.00",
    "total_expenses": "2300.00",
    "net_income": "4900.00"
  }
  ```
* **Error Responses**:
  - `400 Bad Request` — Missing exchange rates:
    ```json
    { "detail": { "error": "calculating_error", "message": "Report cannot be generated due to missing exchange rates.", "missing_rates": ["EUR/USD"] } }
    ```
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found`:
    ```json
    { "detail": "Journal not found." }
    ```

### 6.3 GET `/api/v1/reports/cash-flow`
* **Summary**: Generate a cash-flow report for a specific period.
* **Description**: Returns a cash flow statement showing beginning balance, total inflows (asset increases), total outflows (asset decreases), net cash flow, and ending balance for the specified date range.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `date_from` (date, Required)
  - `date_to` (date, Required)
* **Success Response (200 OK)**:
  ```json
  {
    "date_from": "2026-01-01",
    "date_to": "2026-06-30",
    "beginning_balance": "5000.00",
    "inflows": {
      "assets:bank:savings": "1200.00"
    },
    "outflows": {
      "assets:bank:checking": "-800.00"
    },
    "net_cash_flow": "400.00",
    "ending_balance": "5400.00"
  }
  ```
* **Error Responses**:
  - `400 Bad Request` — Missing exchange rates:
    ```json
    { "detail": { "error": "calculating_error", "message": "Report cannot be generated due to missing exchange rates.", "missing_rates": ["BTC/USD"] } }
    ```
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found`:
    ```json
    { "detail": "Journal not found." }
    ```

### 6.4 GET `/api/v1/reports/net-worth`
* **Summary**: Get current net worth.
* **Description**: Returns the total assets, total liabilities, and calculated net worth (assets minus liabilities) for the journal as of today. Used for the dashboard net-worth display widget.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Success Response (200 OK)**:
  ```json
  {
    "assets": "22500.00",
    "liabilities": "5800.00",
    "net_worth": "16700.00"
  }
  ```
* **Error Responses**:
  - `400 Bad Request` — Missing exchange rates:
    ```json
    { "detail": { "error": "calculating_error", "message": "Report cannot be generated due to missing exchange rates.", "missing_rates": ["ETH/USD"] } }
    ```
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found`:
    ```json
    { "detail": "Journal not found." }
    ```

### 6.5 GET `/api/v1/reports/monthly-income`
* **Summary**: Get current month income total.
* **Description**: Returns the total income posted to all income-type accounts for the current calendar month. Used for the dashboard monthly income widget.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Success Response (200 OK)**:
  ```json
  {
    "monthly_income": "6200.00"
  }
  ```
* **Error Responses**:
  - `400 Bad Request` — Missing exchange rates:
    ```json
    { "detail": { "error": "calculating_error", "message": "Report cannot be generated due to missing exchange rates.", "missing_rates": ["EUR/USD"] } }
    ```
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found`:
    ```json
    { "detail": "Journal not found." }
    ```

### 6.6 GET `/api/v1/reports/roi`
* **Summary**: Generate ROI report.
* **Description**: Returns the ROI for all asset accounts with a cost basis.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `date` (date, Optional): As of date (default: today).
* **Success Response (200 OK)**:
  ```json
  {
    "date": "2026-06-19",
    "assets": [
      {
        "account_name": "assets:crypto:btc",
        "commodity": "BTC",
        "cost_commodity": "USD",
        "quantity": "0.5",
        "cost_basis": "15000.00",
        "current_value": "17500.00",
        "gain": "2500.00",
        "roi_percent": "16.67"
      }
    ],
    "is_complete": true,
    "missing_rates": []
  }
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found`:
    ```json
    { "detail": "Journal not found." }
    ```

### 6.7 GET `/api/v1/reports/roi-timeline`
* **Summary**: Month-by-month ROI timeline with exchange rate.
* **Description**: Returns month-by-month cumulative cost basis, current value, net return, and exchange rate for a specific investment commodity pair. Used by the dual-axis bar+line chart on the ROI page.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `commodity` (String, Required): The asset commodity, e.g. BTC.
  - `cost_commodity` (String, Required): The cost currency, e.g. USD.
* **Success Response (200 OK)**:
  ```json
  {
    "timeline": [
      {
        "month": "2026-01",
        "cum_cost": "5000.00",
        "current_value": "5800.00",
        "net_return": "800.00",
        "exchange_rate": "35000.00"
      },
      {
        "month": "2026-02",
        "cum_cost": "10000.00",
        "current_value": "12000.00",
        "net_return": "2000.00",
        "exchange_rate": "38000.00"
      }
    ]
  }
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found`:
    ```json
    { "detail": "Journal not found." }
    ```

### 6.8 GET `/api/v1/reports/htmx/roi-chart`
* **Summary**: HTMX ROI chart fragment.
* **Description**: Returns a Plotly-rendered HTML fragment showing ROI % over time for all asset pairs in the journal. Intended to be injected into the page via HTMX `hx-swap`. Returns an empty state message if no ROI data is available.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Success Response (200 OK, `text/html`)**: Plotly chart rendered as an HTML `<div>` fragment.
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```

---

## 7. Plotting HTML Charts Router (`/api/v1/name`)

Serves HTML content generated by Plotly for HTMX dynamic frontend swap bindings. All endpoints require JWT authentication.

### 7.1 GET `/api/v1/name/`
* **Summary**: List account names by type.
* **Description**: Returns a flat list of account names for all accounts of the given type in the journal. Used to populate dropdowns and chart labels.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `account_type` (String, Required): One of `ASSET`, `LIABILITY`, `EQUITY`, `INCOME`, `EXPENSE`.
* **Success Response (200 OK)**:
  ```json
  ["assets:bank:checking", "assets:cash", "assets:crypto:btc"]
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `422 Unprocessable Content` — Invalid `account_type`:
    ```json
    { "detail": [{ "loc": ["query", "account_type"], "msg": "value is not a valid enumeration member", "type": "type_error.enum" }] }
    ```

### 7.2 GET `/api/v1/name/count`
* **Summary**: Get transaction counts and amounts by account.
* **Description**: Returns a list of account names with their total transaction entry count and cumulative amount. Used to build the activity bar chart and pie chart on the journal dashboard.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `account_type` (String, Required): One of `ASSET`, `LIABILITY`, `EQUITY`, `INCOME`, `EXPENSE`.
* **Success Response (200 OK)**:
  ```json
  [
    {
      "name": "expenses:food",
      "count": 12,
      "amount": "843.50"
    },
    {
      "name": "expenses:rent",
      "count": 6,
      "amount": "9000.00"
    }
  ]
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```

### 7.3 GET `/api/v1/name/htmx-activity`
* **Summary**: Get HTMX activity chart fragment.
* **Description**: Returns a Plotly-rendered HTML fragment containing a bar chart (transaction count per account) and a pie chart (amount distribution by account) for the given account type. Injected via HTMX `hx-swap`.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `account_type` (String, Required): One of `ASSET`, `LIABILITY`, `EQUITY`, `INCOME`, `EXPENSE`.
* **Success Response (200 OK, `text/html`)**: Two Plotly charts rendered as HTML `<div>` elements inside a grid layout.
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```

### 7.4 GET `/api/v1/name/htmx-market-price`
* **Summary**: Market price history chart.
* **Description**: Returns a Plotly-rendered line chart HTML fragment showing historical price data for all currency pairs stored in the system. Does not require a `journal_id` — market prices are global. Injected via HTMX `hx-swap`.
* **Auth**: Required.
* **Success Response (200 OK, `text/html`)**: Plotly line chart rendered as an HTML `<div>` fragment.
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```

---

## 8. Charts Router (`/api/v1/charts`)

> [!NOTE]
> The `/api/v1/charts` router (`app/api/v1/routers/charts.py`) exists in the codebase but is **not registered** in `app/main.py` and therefore its endpoints are **not reachable** in the running application. These endpoints are documented here for completeness. They are active code — not deprecated — and may be registered in a future release.

### 8.1 GET `/api/v1/charts/monthly-overview` [UNREGISTERED]
* **Summary**: Get monthly income vs expenses overview dataset.
* **Description**: Returns monthly totals for income and expenses across the given date range. Produces a dataset suitable for a bar/line chart.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `date_from` (date, Optional)
  - `date_to` (date, Optional)
* **Success Response (200 OK)**:
  ```json
  {
    "months": ["2026-04", "2026-05", "2026-06"],
    "income": [5000.0, 5200.0, 6100.0],
    "expenses": [3000.0, 3100.0, 2900.0]
  }
  ```

### 8.2 GET `/api/v1/charts/balance-trend` [UNREGISTERED]
* **Summary**: Get balance trend for assets, liabilities, and net worth.
* **Description**: Returns point-in-time asset, liability, and net-worth totals across the given date range.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `date_from` (date, Optional)
  - `date_to` (date, Optional)
* **Success Response (200 OK)**:
  ```json
  {
    "dates": ["2026-04-30", "2026-05-31", "2026-06-19"],
    "assets": [20000.0, 20500.0, 21000.0],
    "liabilities": [5000.0, 4800.0, 4600.0],
    "net_worth": [15000.0, 15700.0, 16400.0]
  }
  ```

### 8.3 GET `/api/v1/charts/expense-breakdown` [UNREGISTERED]
* **Summary**: Get expense breakdown by account.
* **Description**: Returns the total amount spent per expense account within the given date range. Used for pie/donut chart visualisations.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `date_from` (date, Optional)
  - `date_to` (date, Optional)
* **Success Response (200 OK)**:
  ```json
  {
    "accounts": ["expenses:food", "expenses:rent", "expenses:transport"],
    "amounts": [843.50, 9000.00, 320.00]
  }
  ```

---

## 9. Files Router (`/api/v1/files`)

Endpoints for uploading and importing journal data and transaction files.

### 9.1 POST `/api/v1/files/`
* **Summary**: Upload journal backup (JSON) or import transactions (CSV).
* **Description**: Accepts either a JSON backup file (to restore a journal) or a CSV file (to import transactions). When uploading a JSON backup, `journal_id` is optional — a new journal will be created from the backup. When uploading a CSV, `journal_id` is required.
* **Auth**: Required.
* **Request Body** (`multipart/form-data`):
  - `file` (File, Required)
  - `journal_id` (UUID, Optional)
* **Success Response (201 Created)** — Journal created from backup:
  ```json
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "owner_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "name": "My Ledger 2026",
    "description": "Personal finances",
    "base_currency": "USD",
    "created_at": "2026-06-19T11:46:06.534Z",
    "updated_at": "2026-06-19T11:46:06.534Z"
  }
  ```
* **Error Responses**:
  - `400 Bad Request` — Unsupported file format or malformed backup JSON:
    ```json
    { "detail": "Invalid backup file format." }
    ```
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `422 Unprocessable Content` — Missing `file` field:
    ```json
    { "detail": [{ "loc": ["body", "file"], "msg": "field required", "type": "missing" }] }
    ```

### 9.2 POST `/api/v1/files/import-csv`
* **Summary**: Import transactions from a bank CSV file.
* **Description**: Parses a standard bank export CSV and creates double-entry transactions in the journal. Each CSV row creates one transaction — debiting `debit_account_id` and crediting `credit_account_id`. Rows that cannot be parsed are skipped and reported in `errors`.
* **Auth**: Required.
* **Request Body** (`multipart/form-data`):
  - `journal_id` (UUID, Required)
  - `debit_account_id` (UUID, Required)
  - `credit_account_id` (UUID, Required)
  - `file` (File, Required)
* **Success Response (200 OK)**:
  ```json
  {
    "imported": 15,
    "skipped": 2,
    "errors": ["Row 4: Could not parse date '2026-13-01'", "Row 9: Amount field is empty"]
  }
  ```
* **Error Responses**:
  - `400 Bad Request` — File is not valid CSV:
    ```json
    { "detail": "File must be a valid CSV." }
    ```
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal or account not found:
    ```json
    { "detail": "Journal not found." }
    ```

### 9.3 POST `/api/v1/files/import-accounts-csv`
* **Summary**: Import accounts from a CSV file.
* **Description**: Parses a CSV file containing account names and types and bulk-creates accounts in the specified journal. Accounts that already exist are skipped.
* **Auth**: Required.
* **Request Body** (`multipart/form-data`):
  - `journal_id` (UUID, Required)
  - `file` (File, Required)
* **Success Response (200 OK)**:
  ```json
  {
    "imported": 10,
    "skipped": 2,
    "errors": []
  }
  ```
* **Error Responses**:
  - `400 Bad Request` — File is not valid CSV:
    ```json
    { "detail": "File must be a valid CSV." }
    ```
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal not found:
    ```json
    { "detail": "Journal not found." }
    ```

### 9.4 GET `/api/v1/files/export`
* **Summary**: Export journal data (CSV, JSON, or ZIP).
* **Description**: Exports journal data as a downloadable file. Use `format=csv` for spreadsheet-compatible exports, `format=json` for a full JSON backup file, or `format=zip` to download all journal data packed in a zip file. The `entity` parameter controls which resources (transactions, accounts, or all) are included.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `format` (String, Optional, Default: `csv`): `csv`, `json`, or `zip`.
  - `entity` (String, Optional, Default: `transactions`): `transactions`, `accounts`, or `all`.
* **Success Response (200 OK)**: Returns a file download stream (`text/csv`, `application/json`, or `application/zip`).
* **Error Responses**:
  - `400 Bad Request` — Unsupported format value:
    ```json
    { "detail": "Invalid export format. Must be 'csv', 'json', or 'zip'." }
    ```
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal not found:
    ```json
    { "detail": "Journal not found." }
    ```

---

## 10. Currencies Router (`/api/v1/currencies`)

Endpoints for adding, listing, and managing historical market exchange rates.

### 10.1 POST `/api/v1/currencies/prices`
* **Summary**: Add or update a historical market price.
* **Description**: Records an exchange rate for a currency pair on a specific date. Used as the source of exchange rates for ROI, budget, and multi-currency report calculations. If a rate already exists for the same pair and date, it is updated.
* **Auth**: Required.
* **Request Body**:
  ```json
  {
    "currency_from": "BTC",
    "currency_to": "USD",
    "price": 35000.00,
    "date": "2026-06-19"
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "currency_from": "BTC",
    "currency_to": "USD",
    "price": "35000.00",
    "date": "2026-06-19",
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `422 Unprocessable Content` — Missing required fields:
    ```json
    { "detail": [{ "loc": ["body", "price"], "msg": "field required", "type": "missing" }] }
    ```

### 10.2 GET `/api/v1/currencies/prices`
* **Summary**: List all historical market prices.
* **Description**: Returns all stored exchange rate records, paginated. Used by the market price management UI and the `htmx-market-price` chart endpoint.
* **Auth**: Required.
* **Query Parameters**:
  - `skip` (Integer, Optional, Default: 0): Minimum: 0.
  - `limit` (Integer, Optional, Default: 100): Minimum: 1, Maximum: 500.
* **Success Response (200 OK)**:
  ```json
  [
    {
      "currency_from": "BTC",
      "currency_to": "USD",
      "price": "35000.00",
      "date": "2026-06-19",
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
  ]
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```

### 10.3 DELETE `/api/v1/currencies/prices/{price_id}`
* **Summary**: Delete a historical market price.
* **Description**: Permanently removes a market price record by its ID. Note that deleting a price that is referenced by ROI or budget calculations may cause those reports to become incomplete (`is_complete: false`).
* **Auth**: Required.
* **Path Parameters**:
  - `price_id` (UUID, Required): ID of the price to delete.
* **Success Response (204 No Content)**: Returns empty body on success.
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Price record not found:
    ```json
    { "detail": "Market price not found." }
    ```

### 10.4 GET `/api/v1/currencies/convert`
* **Summary**: Convert between currencies on a specific date.
* **Description**: Looks up the stored exchange rate for a currency pair on the given date and returns the converted amount. Used by the currency conversion UI widget. Returns `400` if no rate is found for the given pair and date.
* **Auth**: Required.
* **Query Parameters**:
  - `amount` (Number, Required): Amount to convert.
  - `currency_from` (String, Required): minLength: 1, maxLength: 10.
  - `currency_to` (String, Required): minLength: 1, maxLength: 10.
  - `date` (date, Optional): Date of rate (default: today).
* **Success Response (200 OK)**:
  ```json
  {
    "amount": "100.00",
    "currency_from": "USD",
    "currency_to": "EUR",
    "rate": "0.91",
    "converted_amount": "91.00",
    "date": "2026-06-19"
  }
  ```
* **Error Responses**:
  - `400 Bad Request` — No exchange rate found for the pair on the given date:
    ```json
    { "detail": "No exchange rate found for USD/EUR on 2026-06-19." }
    ```
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `422 Unprocessable Content` — Missing required parameters:
    ```json
    { "detail": [{ "loc": ["query", "amount"], "msg": "field required", "type": "missing" }] }
    ```

---

## 11. Budgets Router (`/api/v1/budgets`)

Endpoints for creating, listing, and managing budget targets.

### 11.1 POST `/api/v1/budgets/`
* **Summary**: Create a new budget target.
* **Description**: Creates a spending budget for a specific account over a date range. The `period` field is a human-readable label (e.g., `monthly`, `Q1 2026`). After creation, the budget tracks actual spend against the target using journal entries.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Request Body**:
  ```json
  {
    "account_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "amount": 1500.00,
    "currency": "USD",
    "period": "monthly",
    "start_date": "2026-06-01",
    "end_date": "2026-06-30"
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "budget_amount": "1500.00",
    "currency": "USD",
    "spend_amount": "843.50",
    "difference": "656.50",
    "start_date": "2026-06-01",
    "end_date": "2026-06-30",
    "is_complete": true,
    "missing_rates": []
  }
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Journal or account not found:
    ```json
    { "detail": "Account not found." }
    ```
  - `422 Unprocessable Content` — Missing required fields:
    ```json
    { "detail": [{ "loc": ["body", "amount"], "msg": "field required", "type": "missing" }] }
    ```

### 11.2 GET `/api/v1/budgets/`
* **Summary**: List all budgets in a journal.
* **Description**: Returns all budget targets created within the journal, along with current spend and remaining difference for each.
* **Auth**: Required.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Success Response (200 OK)**:
  ```json
  [
    {
      "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "budget_amount": "1500.00",
      "currency": "USD",
      "spend_amount": "843.50",
      "difference": "656.50",
      "start_date": "2026-06-01",
      "end_date": "2026-06-30",
      "is_complete": true,
      "missing_rates": []
    }
  ]
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found`:
    ```json
    { "detail": "Journal not found." }
    ```

### 11.3 GET `/api/v1/budgets/{budget_id}`
* **Summary**: Get a specific budget and its spending status.
* **Description**: Returns the budget target for a specific budget ID, along with the actual spend accrued during the budget period and the remaining `difference`. `is_complete: false` means market rates needed for currency conversion are missing.
* **Auth**: Required.
* **Path Parameters**:
  - `budget_id` (UUID, Required): ID of the budget.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Success Response (200 OK)**:
  ```json
  {
    "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "budget_amount": "1500.00",
    "currency": "USD",
    "spend_amount": "843.50",
    "difference": "656.50",
    "start_date": "2026-06-01",
    "end_date": "2026-06-30",
    "is_complete": true,
    "missing_rates": []
  }
  ```
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Budget not found in journal:
    ```json
    { "detail": "Budget not found." }
    ```

### 11.4 DELETE `/api/v1/budgets/{budget_id}`
* **Summary**: Delete a budget target.
* **Description**: Permanently removes a budget target. Existing transactions in the journal are not affected.
* **Auth**: Required.
* **Path Parameters**:
  - `budget_id` (UUID, Required): ID of the budget to delete.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Success Response (204 No Content)**: Returns empty body on success.
* **Error Responses**:
  - `401 Unauthorized`:
    ```json
    { "detail": "Not authenticated" }
    ```
  - `404 Not Found` — Budget not found:
    ```json
    { "detail": "Budget not found." }
    ```

---

> [!NOTE]
> No endpoints in this application are marked as deprecated. The `/api/v1/charts` router exists in source code but is **not registered** and therefore not reachable. See [Section 8](#8-charts-router-apiv1charts) for its documentation.
