# Ledger Web Application - User Guide

## Introduction
Welcome to Ledger Web! This application is a powerful, modern double-entry accounting web interface inspired by plain-text accounting tools like `hledger` and `ledger-cli`.

## 1. Getting Started
1. **Register an Account**: Open the web application (default: `http://localhost:8000`) and register a new user account.
2. **Create a Journal**: A Journal acts as a separate accounting book. You can create multiple journals for different purposes (e.g., "Personal Finances", "Business LLC").
3. **Select your active Journal**: You can switch between active journals from the dropdown in the sidebar.

## 2. Managing Accounts
Before creating transactions, you need to set up your chart of accounts.
- Accounts follow a hierarchical naming convention separated by colons (e.g., `assets:bank:checking` or `expenses:food:groceries`).
- Navigate to the **Accounts** page via the sidebar to add new accounts.
- Choose the correct Account Type (ASSET, LIABILITY, EQUITY, INCOME, EXPENSE) for each.

## 3. Creating Transactions
All financial movements are recorded as double-entry transactions.
1. Navigate to the **Dashboard** or **Transactions** page and click **Add Transaction**.
2. Enter the Date, Description (and optional Payee).
3. Add **Entries** for the transaction. 
   - *Example for buying groceries*: Add a positive amount (debit) to `expenses:groceries` and a negative amount (credit) to `assets:checking`.
4. **Crucial Rule**: The sum of all amounts in a transaction MUST exactly equal zero! 

## 4. Reports and Dashboards
Ledger Web automatically calculates real-time reports based on your transactions:
- **Dashboard**: Gives a quick glance at your Net Worth, Income/Expense trends, and recent transactions.
- **Balance Sheet**: Lists your total Assets against Liabilities and Equity.
- **Income Statement**: Shows your revenue versus expenses over a specific date range.
- **Cash Flow**: Tracks the inflow and outflow of your liquid assets.
- **ROI Tracking**: View historical performance for investments or foreign currencies if you have recorded transactions with a "cost basis".

## 5. Exporting Data and Backups
Your financial data belongs to you! You can export your data at any time.
1. Look for the **Export Data** section in the sidebar.
2. Click **Export All (ZIP)**.
3. This will instantly download a ZIP archive containing individual CSV files for your Accounts, Transactions, and Budgets, along with a full `journal_backup.json` file which can be used to fully restore your journal in the future.
4. You can also import external CSV files via the **Upload Transaction** tool!



----------------------------------

***

## **2. Setup Instructions & Documentation**

### **2.1 Running with Docker (Recommended)**
The easiest way to run Ledger Web is using Docker Compose:
1. Ensure you have Docker and Docker Compose installed.
2. Clone this repository and open a terminal in the project directory.
3. Run the following command:
   ```bash
   docker compose up -d --build
   ```
4. Access the web application at **http://localhost:8000**
5. Stop the application using `docker compose down`.

### **2.2 Local Development Setup**
If you prefer running natively without Docker:
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your database settings.
4. Apply database migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### **2.3 API Documentation**
Ledger Web automatically generates complete interactive API documentation! Once the server is running, you can access:
- **Swagger UI (Interactive API Docs):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc (Detailed API Reference):** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### **2.4 User Guide**
For instructions on how to use the accounting features, view the [User Guide](USER_GUIDE.md).

***
