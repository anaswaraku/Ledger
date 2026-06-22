# Ledger Web Application — Dependency Map

This document lists all third-party libraries used by the Ledger Web Application, including their installed version (as of latest build), primary purpose, and license type.

> [!NOTE]
> Versions reflect the packages installed inside the Docker application container (`python:3.11-slim` base image). To verify the versions in a running container, run:
> ```bash
> docker compose exec app pip list --format=freeze
> ```
> `requirements.txt` lists unpinned package names; the container resolves them to the specific versions shown below on build.

---

## Third-Party Libraries

| Library | Installed Version | Primary Purpose | License |
| :--- | :--- | :--- | :--- |
| **fastapi[all]** | 0.137.2 | Web framework — routing, dependency injection, OpenAPI/Swagger generation | MIT |
| **starlette** | 1.3.1 | ASGI toolkit underpinning FastAPI (routing, middleware, responses) | BSD 3-Clause |
| **uvicorn** | 0.49.0 | ASGI server — serves the FastAPI application in production | BSD 3-Clause |
| **sqlalchemy[asyncio]** | 2.0.51 | SQL toolkit and async ORM for all database access | MIT |
| **asyncpg** | 0.31.0 | Async PostgreSQL driver used by the application runtime (`postgresql+asyncpg`) | Apache 2.0 |
| **psycopg2-binary** | 2.9.12 | Sync PostgreSQL driver used exclusively by Alembic migrations (`postgresql+psycopg2`) | LGPLv3 |
| **alembic** | 1.18.4 | Database schema migration management — autogenerates and applies schema changes | MIT |
| **pydantic** | 2.13.4 | Data validation and serialisation for request/response schemas | MIT |
| **pydantic-settings** | 2.14.1 | Loads and validates application settings from `.env` files via Pydantic schemas | MIT |
| **python-dotenv** | 1.2.2 | Reads key-value pairs from `.env` files into environment variables | BSD 3-Clause |
| **passlib[argon2]** | 1.7.4 | Password hashing utilities — uses Argon2 algorithm for secure user password storage | BSD |
| **argon2-cffi** | 25.1.0 | C-backed Argon2 implementation used by passlib for password hashing | MIT |
| **PyJWT** | 2.13.0 | Encodes and decodes JSON Web Tokens (JWT) for user authentication | MIT |
| **Jinja2** | 3.1.6 | HTML templating engine for server-rendered pages; used with HTMX for dynamic UI | BSD 3-Clause |
| **pytest** | 9.1.0 | Primary test runner for unit and API integration tests | MIT |
| **pytest-asyncio** | 1.4.0 | Pytest plugin enabling `async def` test functions for async application code | Apache 2.0 |
| **httpx** | 0.28.1 | Async HTTP client used by the test suite to make requests against the FastAPI `TestClient` | BSD 3-Clause |
| **aiosqlite** | 0.22.1 | Async SQLite driver used in tests to run an in-memory database without PostgreSQL | MIT |
| **plotly[express]** | 6.8.0 | Interactive chart generation — renders balance trend lines, activity bar charts, ROI curves, and market price charts as HTMX HTML fragments | MIT |
| **pandas** | 3.0.3 | Data manipulation library — used to prepare and shape datasets before passing them to Plotly | BSD 3-Clause |
| **anyio** | 4.14.0 | Async concurrency backend used internally by Starlette/FastAPI for ASGI compatibility | MIT |

