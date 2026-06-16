# **ledger Web Application - Requirements Document**

## **1. Project Overview**

### **1.1 Purpose**
Recreate ledger—a plain-text double-entry accounting tool—as a modern web application using FastAPI and Python, focusing on professional application development practices.

### **1.2 Target Audience**
- Individual users tracking personal finances
- Small businesses needing lightweight accounting
- Developers interested in plain-text accounting (PTA)
- Users who prefer version-controlled financial data

### **1.3 Key Value Proposition**
- **Plain-text data**: Human-readable journal files controlled by users
- **Double-entry accounting**: Accurate financial tracking
- **Multi-currency support**: Track money, cryptocurrencies, investments
- **Powerful reports**: Balance sheets, income statements, cash flow
- **Web interface**: Modern UI with FastAPI backend
- **Version control friendly**: Git-compatible data format

***

## **2. Functional Requirements**

### **2.1 Core Accounting Features**

#### **FR-1: Journal Entry Management**
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | Create transactions with date, description, payee, accounts, amounts | High |
| FR-1.2 | Support multiple currencies and commodities per transaction | High |
| FR-1.3 | Implement double-entry accounting (balances must equal zero) | High |
| FR-1.4 | Add transaction codes, tags, and notes | Medium |
| FR-1.5 | Support opening/closing balance entries | High |
| FR-1.6 | Edit and delete existing transactions | High |
| FR-1.7 | Batch import transactions from CSV files | High |

#### **FR-2: Account Management**
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | Create and manage accounts (Assets, Liabilities, Equity, Income, Expenses) | High |
| FR-2.2 | Support hierarchical account names (e.g., `assets:bank:checking`) | High |
| FR-2.3 | Display account balance summaries | High |
| FR-2.4 | Show transaction history per account | High |
| FR-2.5 | Auto-suggest account names during entry | Medium |

#### **FR-3: Multi-Currency Support**
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Track multiple currencies (USD, EUR, INR, BTC, etc.) | High |
| FR-3.2 | Store historical market prices | Medium |
| FR-3.3 | Calculate currency conversions | Medium |
| FR-3.4 | Report gains/losses from currency fluctuations | Medium |

### **2.2 Reporting Features**

#### **FR-4: Standard Financial Reports**
| Report | Description | Priority |
|--------|-------------|----------|
| FR-4.1 **Balance Sheet** | Assets vs. Liabilities + Equity | High |
| FR-4.2 **Income Statement** | Revenues vs. Expenses (monthly option) | High |
| FR-4.3 **Cash Flow** | Changes in liquid assets | High |
| FR-4.4 **Account Register** | Transactions with running balance | High |
| FR-4.5 **Account Balance** | Total balances per account | High |
| FR-4.6 **Print Journal** | Full transaction entries export | High |

#### **FR-5: Advanced Reports**
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | Return on Investment (ROI) calculations | Medium |
| FR-5.2 | Budget tracking and variance analysis | Medium |
| FR-5.3 | Payee summaries (who you paid/received from) | Medium |
| FR-5.4 | Tag-based reports | Low |
| FR-5.5 | Activity charts (bar charts, line graphs) | Medium |

### **2.3 Data Management**

#### **FR-6: File Operations**
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-6.1 | Create new journal files | High |
| FR-6.2 | Open and switch between multiple journal files | High |
| FR-6.3 | Export journal to CSV, JSON, HTML, SQL | High |
| FR-6.4 | Import CSV from bank statements | High |
| FR-6.5 | Backup and restore journal files | High |

#### **FR-7: Data Validation**
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-7.1 | Validate double-entry balance (sum = 0) | High |
| FR-7.2 | Check for unclosed accounts | Medium |
| FR-7.3 | Detect duplicate transactions | Medium |
| FR-7.4 | Validate account name formats | Medium |

### **2.4 User Interface**

#### **FR-8: Web Interface**
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-8.1 | Dashboard with account summaries | High |
| FR-8.2 | Transaction entry form with validation | High |
| FR-8.3 | Report viewer with filtering | High |
| FR-8.4 | Account browser with hierarchy | High |
| FR-8.5 | CSV import wizard | Medium |
| FR-8.6 | Search transactions (date, description, payee, tags) | High |

#### **FR-9: Authentication & Security**
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-9.1 | User registration and login | High |
| FR-9.2 | JWT-based authentication | High |
| FR-9.3 | Role-based access (admin, user) | Medium |
| FR-9.4 | Secure password hashing (Argon2/bcrypt) | High |
| FR-9.5 | Session management | High |

***

## **3. Technical Requirements**

### **3.1 Architecture**

#### **TR-1: Project Structure** (Professional FastAPI Pattern)
```
hledger_web/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── dependencies.py            # Dependency injections
│   │
│   ├── api/                       # API layer
│   │   ├── v1/
│   │   │   ├── routers/
│   │   │   │   ├── transactions.py
│   │   │   │   ├── accounts.py
│   │   │   │   ├── reports.py
│   │   │   │   ├── auth.py
│   │   │   │   └── files.py
│   │   │   └── schemas/
│   │   │       ├── transaction.py
│   │   │       ├── account.py
│   │   │       ├── report.py
│   │   │       └── auth.py
│   │
│   ├── application/               # Business logic layer
│   │   ├── services/
│   │   │   ├── transaction_service.py
│   │   │   ├── account_service.py
│   │   │   ├── report_service.py
│   │   │   └── auth_service.py
│   │   └── use_cases/
│   │       ├── create_transaction.py
│   │       ├── generate_balance_sheet.py
│   │       └── import_csv.py
│   │
│   ├── domain/                    # Domain models
│   │   ├── models/
│   │   │   ├── transaction.py
│   │   │   ├── account.py
│   │   │   └── journal.py
│   │   └── rules/
│   │       ├── double_entry.py
│   │       └── account_validation.py
│   │
│   ├── infrastructure/            # External concerns
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   ├── repositories/
│   │   │   │   ├── transaction_repo.py
│   │   │   │   └── account_repo.py
│   │   │   └── migrations/
│   │   ├── external/
│   │   │   └── csv_importer.py
│   │
│   ├── core/                      # Core configuration
│   │   ├── config.py              # Environment settings
│   │   ├── security.py            # JWT, password hashing
│   │   └── logging.py             # Logging configuration
│   │
│   └── templates/                 # Web UI templates
│       ├── index.html
│       ├── transactions/
│       ├── accounts/
│       └── reports/
│
├── tests/
│   ├── __init__.py
│   ├── test_api/
│   ├── test_services/
│   └── test_domain/
│
├── .env                           # Environment variables
├── .gitignore
├── requirements.txt
├── README.md
└── docker-compose.yml
```

#### **TR-2: Technology Stack**
| Component | Technology | Reason |
|-----------|------------|--------|
| **Backend Framework** | FastAPI 0.115+ | High performance, async support, auto docs |
| **Language** | Python 3.12+ | Modern Python, type hints |
| **Database** | PostgreSQL 15+ | Relational data, ACID compliance |
| **ORM** | SQLAlchemy 2.0+ | Async support, type-safe queries |
| **Schema Validation** | Pydantic V2 | Data validation, serialization |
| **Authentication** | PyJWT + Argon2 | JWT tokens, secure password hashing |
| **Web Template** | Jinja2 + HTMX | Server-rendered pages, modern interactions |
| **Testing** | pytest + httpx | Unit tests, API tests |
| **API Documentation** | OpenAPI (auto) | Swagger UI at `/docs` |

### **3.2 API Requirements**

#### **TR-3: RESTful API Endpoints**
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/auth/register` | POST | User registration | No |
| `/api/v1/auth/login` | POST | User login (JWT) | No |
| `/api/v1/auth/logout` | POST | Logout | Yes |
| `/api/v1/transactions` | GET | List transactions | Yes |
| `/api/v1/transactions` | POST | Create transaction | Yes |
| `/api/v1/transactions/{id}` | GET | Get transaction details | Yes |
| `/api/v1/transactions/{id}` | PUT | Update transaction | Yes |
| `/api/v1/transactions/{id}` | DELETE | Delete transaction | Yes |
| `/api/v1/accounts` | GET | List accounts | Yes |
| `/api/v1/accounts` | POST | Create account | Yes |
| `/api/v1/accounts/{name}/register` | GET | Account register report | Yes |
| `/api/v1/reports/balance-sheet` | GET | Balance sheet | Yes |
| `/api/v1/reports/income-statement` | GET | Income statement | Yes |
| `/api/v1/reports/cash-flow` | GET | Cash flow report | Yes |
| `/api/v1/files` | POST | Upload journal file | Yes |
| `/api/v1/files/import-csv` | POST | Import CSV | Yes |
| `/api/v1/files/export` | GET | Export journal (CSV/JSON) | Yes |

#### **TR-4: Request/Response Examples**

**Create Transaction:**
```json
// POST /api/v1/transactions
{
  "date": "2026-01-15",
  "description": "Grocery shopping",
  "payee": "SuperMart",
  "entries": [
    {"account": "expenses:food", "amount": 50.00, "currency": "USD"},
    {"account": "assets:cash", "amount": -50.00, "currency": "USD"}
  ],
  "tags": [" groceries", "weekly"]
}
```

**Response:**
```json
{
  "id": "txn_12345",
  "date": "2026-01-15",
  "description": "Grocery shopping",
  "status": "validated",
  "created_at": "2026-01-15T10:30:00Z"
}
```

**Balance Sheet Report:**
```json
// GET /api/v1/reports/balance-sheet?date=2026-01-15
{
  "date": "2026-01-15",
  "assets": {
    "assets:bank:checking": 2000.00,
    "assets:cash": 50.00
  },
  "liabilities": {
    "liabilities:creditcard": 50.00
  },
  "equity": {
    "equity:opening": 4000.00
  },
  "net": 4000.00
}
```

### **3.3 Database Schema**

#### **TR-5: Core Tables**
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Journal files (user's accounting books)
CREATE TABLE journals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Transactions
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_id UUID REFERENCES journals(id),
    date DATE NOT NULL,
    description VARCHAR(500),
    payee VARCHAR(255),
    code VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Transaction entries (double-entry)
CREATE TABLE transaction_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID REFERENCES transactions(id),
    account VARCHAR(500) NOT NULL,
    amount DECIMAL(28, 10) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD'
);

-- Accounts
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_id UUID REFERENCES journals(id),
    name VARCHAR(500) UNIQUE NOT NULL,
    account_type VARCHAR(50), -- Assets, Liabilities, Equity, Income, Expenses
    created_at TIMESTAMP DEFAULT NOW()
);

-- Market prices (for multi-currency)
CREATE TABLE market_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    currency_from VARCHAR(3),
    currency_to VARCHAR(3),
    price DECIMAL(28, 10),
    date DATE NOT NULL
);
```

### **3.4 Security Requirements**

#### **TR-6: Authentication & Authorization**
| Requirement | Implementation |
|-------------|----------------|
| JWT tokens with 30-minute expiry | `PyJWT` with HS256 algorithm |
| Password hashing | `Argon2` (preferred) or `bcrypt` |
| HTTPBearer authentication | FastAPI `Security` dependency |
| Role-based access control | Middleware checking user roles |
| Input validation | Pydantic schemas for all requests |

### **3.5 Testing Requirements**

#### **TR-7: Test Coverage**
| Test Type | Tools | Coverage Target |
|-----------|-------|-----------------|
| Unit tests | `pytest` | 80% domain logic |
| API tests | `pytest` + `httpx` | All endpoints |
| Database tests | `pytest` + `SQLAlchemy` | Repository layer |
| Integration tests | `docker-compose` | Full stack |
| Type checking | `mypy` | 100% code |

**Example Test:**
```python
# tests/test_domain/test_double_entry.py
def test_transaction_must_balance():
    entries = [
        Entry(account="expenses:food", amount=50.00),
        Entry(account="assets:cash", amount=-50.00),
    ]
    txn = Transaction(date="2026-01-15", entries=entries)
    assert txn.is_balanced() == True
```

### **3.6 Performance Requirements**

#### **TR-8: Performance Targets**
| Metric | Target |
|--------|--------|
| Transaction creation | < 100ms |
| Balance sheet report (10k transactions) | < 500ms |
| API response time (95th percentile) | < 200ms |
| Database queries | Use indexes, < 50ms |
| Concurrent users | 100+ |

***

## **4. Non-Functional Requirements**

### **4.1 Usability**
| ID | Requirement |
|----|-------------|
| NFR-1 | Intuitive UI for non-accountants |
| NFR-2 | Clear error messages with suggestions |
| NFR-3 | Keyboard shortcuts for common actions |
| NFR-4 | Mobile-responsive design |


### **4.2 Documentation**
| ID | Requirement |
|----|-------------|
| NFR-12 | Auto-generated OpenAPI docs at `/docs` |
| NFR-13 | README with setup instructions |
| NFR-14 | Code comments for complex logic |
| NFR-15 | User guide for accounting features |

***

## **5. Implementation Roadmap**

### **Phase 1: Core Foundation**
- [✔️] Project setup with professional structure
- [✔️] Database schema + SQLAlchemy models
- [✔️] User authentication (JWT)
- [✔️] Transaction CRUD endpoints
- [✔️] Double-entry validation logic
- [✔️] Basic unit tests

### **Phase 2: Accounting Features**
- [✔️] Account management
- [✔️] Balance sheet report
- [✔️] Income statement report
- [✔️] Account register report
- [✔️] CSV import/export
- [✔️] Search functionality

### **Phase 3: Advanced Features**
- [ ] Multi-currency support
- [ ] Historical market prices
- [ ] Cash flow report
- [ ] ROI calculations
- [ ] Activity charts (Plotly)
- [ ] Budget tracking

***

## **6. Success Criteria**

| Criterion | Target |
|-----------|--------|
| **Functionality** | Matches 80% of hledger CLI features |
| **Performance** | Handles 25k transactions (like hledger) |
| **Accuracy** | 255 decimal place precision (like hledger) |
| **Test Coverage** | 80%+ unit test coverage |
| **Documentation** | Complete API docs + user guide |

***

## **Next Steps**

This requirements document gives you a complete blueprint. To start building:

1. **Set up the project structure** as shown in TR-1
2. **Install dependencies** from `requirements.txt`
3. **Create database models** using SQLAlchemy
4. **Implement authentication** first (JWT + Argon2)
5. **Build transaction CRUD** with double-entry validation
6. **Add reports** (balance sheet, income statement)
7. **Write tests** for each component

 
