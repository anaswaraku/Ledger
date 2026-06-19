# Ledger Web Application - Dependency Map

This document lists all third-party libraries utilized by the Ledger Web Application, including their purpose and license categorization.

---

## Third-Party Libraries Dependency Reference

| Library Name | Version / Specifier | Primary Purpose | License Type |
| :--- | :--- | :--- | :--- |
| **fastapi[all]** | Standard package | Web Framework (routing, dependency injection, openapi generation) | MIT |
| **sqlalchemy[asyncio]** | Standard package | SQL Toolkit & Object Relational Mapper (ORM) supporting async operations | MIT |
| **asyncpg** | Standard package | Asynchronous PostgreSQL database client driver | Apache 2.0 |
| **psycopg2-binary** | Standard package | Synchronous PostgreSQL database client driver (used for Alembic migrations) | LGPLv3 (with SSL exceptions) |
| **alembic** | Standard package | Database schema migration management tool | MIT |
| **pydantic-settings** | Standard package | Setting and environment variable management using Pydantic schemas | MIT |
| **python-dotenv** | Standard package | Loads key-value pairs from `.env` files into environment variables | BSD 3-Clause |
| **passlib[argon2]** | Standard package | Password hashing utilities supporting Argon2 and bcrypt | BSD |
| **PyJWT** | Standard package | JSON Web Token (JWT) encoding and decoding library for authentication | MIT |
| **jinja2** | Standard package | Modern and designer-friendly HTML templating engine for Python | BSD 3-Clause |
| **pytest** | Standard package | Unit and functional testing framework | MIT |
| **pytest-asyncio** | Standard package | Testing library for asynchronous Python code and pytest integrations | Apache 2.0 |
| **httpx** | Standard package | Async HTTP client for Python (used for API integration testing) | BSD 3-Clause |
| **aiosqlite** | Standard package | Asynchronous database driver for SQLite (used in unit testing) | MIT |
| **plotly[express]** | Standard package | Graphic library for generating interactive charts (balance sheets, ROI trend lines) | MIT |
| **pandas** | Standard package | Data manipulation and analysis library (used for preparing chart datasets) | BSD 3-Clause |
