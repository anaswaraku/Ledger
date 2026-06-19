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
* **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "id": "7bf3ad9d-f685-4ceb-8515-3ccb0f55fb34",
    "email": "user@example.com"
  }
  ```
* **Error Responses**:
  - `400 Bad Request`: Returned if the email address is already registered:
    ```json
    { "detail": "Email already registered." }
    ```
  - `422 Unprocessable Content`: Returned if password/email formats are invalid.

### 2.2 POST `/api/v1/auth/login`
* **Summary**: Authenticate a user and retrieve a JWT bearer token.
* **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
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
  - `401 Unauthorized`: Invalid password or username:
    ```json
    { "detail": "Incorrect email or password." }
    ```

### 2.3 POST `/api/v1/auth/logout`
* **Summary**: Log out current authenticated session.
* **Auth Required**: Yes
* **Success Response (200 OK)**:
  ```json
  {
    "message": "Successfully logged out"
  }
  ```

---

## 3. Journals Router (`/api/v1/journals`)

Manage accounting books (Journals) owned by the user. All endpoints require JWT authentication.

### 3.1 GET `/api/v1/journals`
* **Summary**: List all journals owned by the user.
* **Success Response (200 OK)**:
  ```json
  [
    {
      "id": "e2ba34fe-98ef-4da0-9b43-433b7cfebc32",
      "name": "Personal Finances",
      "description": "Ledger for daily bank accounts and credit cards",
      "created_at": "2026-06-19T10:15:30Z"
    }
  ]
  ```

### 3.2 POST `/api/v1/journals`
* **Summary**: Create a new journal.
* **Request Body**:
  ```json
  {
    "name": "Business LLC",
    "description": "Ledger for commercial business activities"
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "id": "fa87c8d9-2eef-4171-aa15-cc70bf9d91fa",
    "name": "Business LLC",
    "description": "Ledger for commercial business activities",
    "created_at": "2026-06-19T10:16:00Z"
  }
  ```

### 3.3 GET `/api/v1/journals/{journal_id}`
* **Summary**: Retrieve a journal's details.
* **Success Response (200 OK)**:
  ```json
  {
    "id": "fa87c8d9-2eef-4171-aa15-cc70bf9d91fa",
    "name": "Business LLC",
    "description": "Ledger for commercial business activities",
    "created_at": "2026-06-19T10:16:00Z"
  }
  ```
* **Error Responses**:
  - `404 Not Found`: If the journal does not exist or belongs to another user:
    ```json
    { "detail": "Journal not found." }
    ```

### 3.4 PUT `/api/v1/journals/{journal_id}`
* **Summary**: Update journal details.
* **Request Body**:
  ```json
  {
    "name": "Primary Business Ledger",
    "description": "Updated description"
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "id": "fa87c8d9-2eef-4171-aa15-cc70bf9d91fa",
    "name": "Primary Business Ledger",
    "description": "Updated description",
    "created_at": "2026-06-19T10:16:00Z"
  }
  ```

### 3.5 DELETE `/api/v1/journals/{journal_id}`
* **Summary**: Delete a journal (and cascades to delete all transaction records).
* **Success Response (204 No Content)**: Returns empty response on success.

---

## 4. Accounts Router (`/api/v1/accounts`)

Manage account codes (Assets, Expenses, Liabilities) inside a journal. All endpoints require JWT authentication.

### 4.1 GET `/api/v1/accounts`
* **Summary**: Get all accounts registered inside a journal.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Success Response (200 OK)**:
  ```json
  [
    {
      "id": "d1c01e3b-9e2e-4cf8-a901-8fbbf719c2fb",
      "journal_id": "fa87c8d9-2eef-4171-aa15-cc70bf9d91fa",
      "name": "assets:bank:checking",
      "account_type": "ASSET"
    }
  ]
  ```

### 4.2 POST `/api/v1/accounts`
* **Summary**: Create a new hierarchical account.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
* **Request Body**:
  ```json
  {
    "name": "expenses:food:groceries",
    "account_type": "EXPENSE"
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "id": "cc89cde8-a9fe-443b-abef-7f55bdf91f2c",
    "journal_id": "fa87c8d9-2eef-4171-aa15-cc70bf9d91fa",
    "name": "expenses:food:groceries",
    "account_type": "EXPENSE"
  }
  ```
* **Error Responses**:
  - `400 Bad Request`: If the account name fails structure validation (e.g. contains invalid spaces or unrecognised top-level classification: Assets, Liabilities, Equity, Income, Expenses):
    ```json
    { "detail": "Invalid account type name." }
    ```

---

## 5. Transactions Router (`/api/v1/transactions`)

Execute and search double-entry transaction records. All endpoints require JWT authentication.

### 5.1 GET `/api/v1/transactions`
* **Summary**: Get all transactions in a journal.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `payee` (string, Optional, filters by matching payee name)
* **Success Response (200 OK)**:
  ```json
  [
    {
      "id": "18fbf7de-ee2f-410a-ba8c-8fcdcbef9c1a",
      "journal_id": "fa87c8d9-2eef-4171-aa15-cc70bf9d91fa",
      "date": "2026-06-19",
      "description": "Weekly food grocery run",
      "payee": "Whole Foods",
      "created_at": "2026-06-19T10:20:00Z",
      "entries": [
        {
          "id": "c1f7b8e9-ab8e-4aee-aa88-dfcc89eef39a",
          "transaction_id": "18fbf7de-ee2f-410a-ba8c-8fcdcbef9c1a",
          "account_id": "cc89cde8-a9fe-443b-abef-7f55bdf91f2c",
          "amount": 50.00,
          "currency": "USD",
          "cost_amount": null,
          "cost_currency": null,
          "account_name": "expenses:food:groceries"
        },
        {
          "id": "d98fbcfc-feef-4da3-aa99-ffcfebcd9e22",
          "transaction_id": "18fbf7de-ee2f-410a-ba8c-8fcdcbef9c1a",
          "account_id": "d1c01e3b-9e2e-4cf8-a901-8fbbf719c2fb",
          "amount": -50.00,
          "currency": "USD",
          "cost_amount": null,
          "cost_currency": null,
          "account_name": "assets:bank:checking"
        }
      ]
    }
  ]
  ```

### 5.2 POST `/api/v1/transactions`
* **Summary**: Post a new double-entry transaction.
* **Request Body**:
  ```json
  {
    "journal_id": "fa87c8d9-2eef-4171-aa15-cc70bf9d91fa",
    "date": "2026-06-19",
    "description": "Grocery run",
    "payee": "Whole Foods",
    "entries": [
      {
        "account_id": "cc89cde8-a9fe-443b-abef-7f55bdf91f2c",
        "amount": 50.00,
        "currency": "USD"
      },
      {
        "account_id": "d1c01e3b-9e2e-4cf8-a901-8fbbf719c2fb",
        "amount": -50.00,
        "currency": "USD"
      }
    ]
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "id": "18fbf7de-ee2f-410a-ba8c-8fcdcbef9c1a",
    "journal_id": "fa87c8d9-2eef-4171-aa15-cc70bf9d91fa",
    "date": "2026-06-19",
    "description": "Grocery run",
    "payee": "Whole Foods",
    "created_at": "2026-06-19T10:20:00Z",
    "entries": [
      {
        "id": "c1f7b8e9-ab8e-4aee-aa88-dfcc89eef39a",
        "transaction_id": "18fbf7de-ee2f-410a-ba8c-8fcdcbef9c1a",
        "account_id": "cc89cde8-a9fe-443b-abef-7f55bdf91f2c",
        "amount": 50.0,
        "currency": "USD",
        "cost_amount": null,
        "cost_currency": null,
        "account_name": null
      },
      {
        "id": "d98fbcfc-feef-4da3-aa99-ffcfebcd9e22",
        "transaction_id": "18fbf7de-ee2f-410a-ba8c-8fcdcbef9c1a",
        "account_id": "d1c01e3b-9e2e-4cf8-a901-8fbbf719c2fb",
        "amount": -50.0,
        "currency": "USD",
        "cost_amount": null,
        "cost_currency": null,
        "account_name": null
      }
    ]
  }
  ```
* **Error Responses**:
  - `400 Bad Request / 422 Unprocessable Content`: If the transaction entries do not sum to exactly zero (violating double-entry bookkeeping):
    ```json
    { "detail": "Transaction does not balance for currency USD. Imbalance: +10.0000000000" }
    ```

---

## 6. Financial Reports Router (`/api/v1/reports`)

Query real-time report summaries. All endpoints require JWT authentication.

### 6.1 GET `/api/v1/reports/balance-sheet`
* **Summary**: Generate a balance sheet report.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `date` (date, Optional, As of date. Defaults to today)
* **Success Response (200 OK)**:
  ```json
  {
    "date": "2026-06-19",
    "assets": {
      "assets:bank:checking": 1050.00
    },
    "liabilities": {
      "liabilities:creditcard": 50.00
    },
    "equity": {
      "equity:opening": 1000.00
    },
    "net": 1000.00
  }
  ```
* **Error Responses**:
  - `400 Bad Request`: If report contains multiple currencies and historical exchange rates are missing:
    ```json
    {
      "detail": {
        "error": "calculating_error",
        "message": "Report cannot be generated due to missing exchange rates.",
        "missing_rates": [["EUR", "USD", "2026-06-19"]]
      }
    }
    ```

### 6.2 GET `/api/v1/reports/roi`
* **Summary**: Get ROI (Return on Investment) for assets with a cost basis.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `date` (date, Optional, Defaults to today)
* **Success Response (200 OK)**:
  ```json
  {
    "as_of": "2026-06-19",
    "assets": [
      {
        "account_name": "assets:investments:crypto",
        "commodity": "BTC",
        "quantity": 0.5,
        "cost_basis": 15000.00,
        "cost_commodity": "USD",
        "current_price": 40000.00,
        "current_value": 20000.00,
        "net_return": 5000.00,
        "roi_percent": 33.3333333333
      }
    ]
  }
  ```

---

## 7. Plotting HTML Charts Router (`/api/v1/name`)

Serves HTML content generated by Plotly for HTMX dynamic frontend swap bindings. All endpoints require JWT authentication.

### 7.1 GET `/api/v1/name/htmx-activity`
* **Summary**: Get a dynamic bar and pie chart representing account entry activities.
* **Query Parameters**:
  - `journal_id` (UUID, Required)
  - `account_type` (string, Required, e.g. `EXPENSE`)
* **Success Response (200 OK, HTML Response)**:
  ```html
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white border border-gray-200 rounded-xl shadow-sm p-4">
          <!-- Plotly JavaScript SVG Bar Chart -->
      </div>
  </div>
  ```

---

## 8. Deprecated Endpoints (`/api/v1/charts`)

> [!WARNING]
> **Deprecated System Routes**:
> The `/api/v1/charts` endpoints are **deprecated** in favor of the active `/api/v1/name` plotting endpoints which return client-ready HTML layouts instead of raw data. They have not been removed to support legacy clients.

### 8.1 GET `/api/v1/charts/monthly-overview` [DEPRECATED]
* **Summary**: Get monthly income vs expenses overview raw dataset.
* **Status**: **DEPRECATED**
* **Success Response (200 OK)**:
  ```json
  {
    "months": ["2026-05", "2026-06"],
    "income": [5000.0, 5200.0],
    "expenses": [3000.0, 3100.0]
  }
  ```

### 8.2 GET `/api/v1/charts/balance-trend` [DEPRECATED]
* **Summary**: Get balance trend dataset for assets, liabilities, and net worth.
* **Status**: **DEPRECATED**
* **Success Response (200 OK)**:
  ```json
  {
    "dates": ["2026-05-31", "2026-06-19"],
    "assets": [20000.0, 20500.0],
    "liabilities": [5000.0, 4800.0],
    "net_worth": [15000.0, 15700.0]
  }
  ```
