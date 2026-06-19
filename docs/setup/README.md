# Ledger Web Application - Development Setup Guide

This document provides step-by-step instructions for installing, configuring, and running the Ledger Web Application in a local development environment.

---

## 1. Prerequisites

Before setting up the project, ensure you have the following installed on your system:

- **Python**: Version 3.11 or 3.12+
- **Database**: PostgreSQL (version 15+ recommended) or **Docker Desktop** to run database containers.
- **Git**: For cloning the repository.

---

## 2. Installation Steps (Local Environment)

### Step 1: Clone the Repository
Clone the repository to your local machine and navigate into the project root directory:
```bash
git clone <repository-url>
cd Ledger
```

### Step 2: Create a Virtual Environment
It is recommended to use a Python virtual environment to isolate the project dependencies:

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
Install all required Python packages using `requirements.txt`:
```bash
pip install -r requirements.txt
```

> [!NOTE]
> The dependencies include `psycopg2-binary` (used by Alembic for synchronous migrations) and `asyncpg` (used by the application itself for asynchronous database operations).

### Step 4: Configure Environment Variables
Copy the template `.env.example` file to create your local configuration:
```bash
cp .env.example .env
```
Open the newly created `.env` file in your editor and configure the variables described in the next section.

---

## 3. Environment Variables Reference

The application uses Pydantic Settings to load configuration dynamically from the `.env` file. Below is the list of all supported environment variables:

| Variable Name | Description | Example / Default Value | Production Recommendations |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | The title displayed in the application API and interface. | `Ledger Web Application` | Customize as needed. |
| `POSTGRES_HOST` | Hostname of the PostgreSQL database server. | `localhost` (local) or `ledger_db` (docker) | Secure private hostname. |
| `POSTGRES_PORT` | Port number the database server is listening on. | `5432` | Standard PostgreSQL port. |
| `POSTGRES_DB` | Name of the database to connect to. | `ledger` | Dedicated production database name. |
| `POSTGRES_USER` | Username for database authentication. | `postgres` (or `ledge_users`) | Avoid using root/admin accounts. |
| `POSTGRES_PASSWORD` | Password for database authentication. | `postgres` (or `ledgeweb`) | Use a strong, randomly generated password. |
| `SECRET_KEY` | Symmetric key used to sign and verify JWT authentication tokens. | `your_super_secret_jwt_key` | **CRITICAL:** Must be a long, randomly generated cryptographically secure hex string. |
| `ALGORITHM` | Algorithm used for JWT signature encoding. | `HS256` | Standard signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Number of minutes before a user's JWT access token expires. | `30` | Keep low for security (e.g. 15-60 mins). |

### Generating a Secure SECRET_KEY
For local development or production, you can generate a cryptographically secure hex key by running:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the generated string and set it as the value for `SECRET_KEY` in your `.env` file.

---

## 4. Local Database Migrations (Alembic)

The database schema is managed using **Alembic**.

### Database Driver Architecture
Please note how database drivers are used in the application:
1. **Application Runtime**: The application uses the asynchronous driver `postgresql+asyncpg` for high performance (`app/infrastructure/db/database.py`).
2. **Migrations (Alembic)**: Alembic operates synchronously and uses the synchronous driver `postgresql+psycopg2` (`alembic/env.py`).
3. **Automated Tests**: Unit and integration tests run against an in-memory SQLite database using `sqlite+aiosqlite` via test dependency overrides.

### Applying Migrations
Before running the application for the first time, or after pulling code changes containing new migrations, you must apply them to configure your database schema:
```bash
alembic upgrade head
```

### Common Migration Commands
Use the following commands to manage the database schema during development:

* **View applied migration status:**
  ```bash
  alembic current
  ```

* **Generate an autodetected migration (after modifying SQLAlchemy models in `app/domain/models/`):**
  ```bash
  alembic revision --autogenerate -m "description of changes"
  ```
  *(Always inspect the generated file in `alembic/versions/` before applying it).*

* **Rollback the last applied migration:**
  ```bash
  alembic downgrade -1
  ```

* **Rollback all migrations (resets database schema):**
  ```bash
  alembic downgrade base
  ```

---

## 5. Running the Application

Once dependencies are installed, environment variables configured, and database migrations applied, start the development server.

### Local Development Mode
Start the FastAPI application using `uvicorn` with hot-reloading enabled:
```bash
uvicorn app.main:app --reload
```
The application will start, and the web interface will be accessible at:
- **Web Application Portal:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Static ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 6. Alternative Setup: Running with Docker Compose

If you have Docker and Docker Compose installed, you can launch the complete system (FastAPI application and PostgreSQL database instance) with a single command. Docker Compose automatically handles starting the database container, mounting volumes for persistent data, and mapping ports.

1. Ensure your `.env` file has been created.
2. In the project root, run:
   ```bash
   docker compose up -d --build
   ```
3. Docker Compose will automatically run the FastAPI container on [http://localhost:8000](http://localhost:8000) and link it to the DB container.
4. Apply database migrations inside the running container (or let Docker handle DB initialization):
   ```bash
   docker compose exec app alembic upgrade head
   ```
5. View container logs using:
   ```bash
   docker compose logs -f
   ```
6. Stop and remove containers:
   ```bash
   docker compose down
   ```

---

## 7. Troubleshooting

### 1. Database Connection Errors
* **Error:** `OperationalError: (psycopg2.OperationalError) connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused`
  * **Fix:** Ensure your PostgreSQL server is active and running on port 5432. If you are running PostgreSQL via Docker, verify the container is active with `docker ps`.
* **Error:** `role "..." does not exist` or `database "..." does not exist`
  * **Fix:** Verify `POSTGRES_USER` and `POSTGRES_DB` match the existing database credentials and that the database actually exists. You may need to create the database manually using `createdb ledger` or `psql -c "CREATE DATABASE ledger;"`.

### 2. Driver Errors during Pip Install
* **Error:** Compilation failure while installing `psycopg2` or missing pg_config tools.
  * **Fix:** We use `psycopg2-binary` in `requirements.txt` to avoid requiring local Postgres development headers during development installation. If you still encounter compile errors, ensure you are running in a clean virtual environment or install the PostgreSQL development packages on your operating system (e.g., `libpq-dev` on Debian/Ubuntu).
