# Bookly

Bookly is a REST API for a book catalog and review service. Authenticated users can publish books, attach tags, and leave ratings. Accounts are verified by email, sessions use short-lived JWTs with refresh and server-side revocation, and access is split between regular users and admins.

The API is versioned under `/api/v1` and ships with interactive OpenAPI docs at `/docs`.

## What it covers

- **Accounts.** Signup, login, email verification, password reset, and logout.
- **Books.** Create, read, update, and delete catalog entries, plus a per-user submission list.
- **Reviews.** Rate a book from 1 to 5 and write a review. Listing every review is limited to admins. A user can delete only their own review.
- **Tags.** Create and manage tags, then attach them to a book through a many-to-many link.
- **Access control.** Routes require a verified account. Role checks distinguish `user` and `admin`.
- **Background email.** Verification, password-reset, and welcome messages are sent through Celery so the request is not blocked on SMTP.

## Stack

| Layer | Choice |
| --- | --- |
| API | FastAPI, Pydantic |
| Database | PostgreSQL via SQLModel and async SQLAlchemy (`asyncpg`) |
| Migrations | Alembic |
| Auth | JWT access and refresh tokens, bcrypt password hashes, signed email links |
| Revocation | Redis blocklist of token IDs (`jti`) |
| Email | FastAPI-Mail over SMTP, dispatched by Celery |
| Broker | Redis |

## How a request moves

```mermaid
flowchart LR
    Client[Client] --> API[FastAPI]
    API --> Auth[JWT and role checks]
    Auth --> Redis[(Redis blocklist)]
    API --> Services[Route services]
    Services --> DB[(PostgreSQL)]
    API --> Celery[Celery worker]
    Celery --> SMTP[SMTP]
```

Protected routes decode the bearer token, reject refresh tokens where an access token is required, and check Redis before the handler runs. Domain logic lives in service classes (`UserService`, `BookService`, `ReviewService`, `TagService`). SQLModel models own the tables and relationships. Domain failures are raised as typed exceptions and mapped to consistent JSON responses.

## API

All routes are prefixed with `/api/v1`. Protected routes expect `Authorization: Bearer <access_token>`.

### Auth — `/auth`

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `POST` | `/signup` | Public | Create an account and email a verification link |
| `GET` | `/verify/{token}` | Public | Mark the account verified |
| `POST` | `/login` | Public | Return an access token and a refresh token |
| `GET` | `/refresh_token` | Refresh token | Issue a new access token |
| `GET` | `/me` | Verified user | Current user, with their books and reviews |
| `GET` | `/logout` | Access token | Revoke the current token |
| `POST` | `/password-reset-request` | Public | Email a reset link |
| `POST` | `/password-reset-confirm/{token}` | Public | Set a new password |
| `POST` | `/send_email` | Public | Send a message through the mail worker |

Access tokens expire after one hour. Refresh tokens expire after two days. Logout stores the token’s `jti` in Redis until the access token would have expired.

### Books — `/books`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | List books, newest first |
| `POST` | `/` | Add a book owned by the current user |
| `GET` | `/{book_uid}` | Book detail, including reviews and tags |
| `PUT` | `/{book_uid}` | Update a book |
| `DELETE` | `/{book_uid}` | Delete a book |
| `GET` | `/user/{user_uid}` | Books submitted by one user |

### Reviews — `/reviews`

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/` | Admin | List every review |
| `GET` | `/{review_uid}` | Verified user | Fetch one review |
| `POST` | `/book/{book_uid}` | Verified user | Add a review to a book |
| `DELETE` | `/{review_uid}` | Review author | Delete that review |

### Tags — `/tags`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | List tags |
| `POST` | `/` | Create a tag |
| `PUT` | `/{tag_uid}` | Rename a tag |
| `DELETE` | `/{tag_uid}` | Delete a tag |
| `POST` | `/book/{book_uid}/tags` | Attach tags to a book, creating any that do not exist yet |

## Data model

- **User** — profile, role (`user` by default), verification flag, password hash. A user has many books and reviews.
- **Book** — title, author, publisher, language, page count, and publication date. Belongs to the user who created it.
- **Review** — rating and text, linked to one user and one book.
- **Tag** — name. Books and tags share a `booktag` association table.

## Project layout

```
src/
  __init__.py          # FastAPI app and router registration
  config.py            # Settings loaded from .env
  errors.py            # Domain exceptions and JSON handlers
  middleware.py        # Request timing, CORS, trusted hosts
  mail.py              # SMTP client
  celery_tasks.py      # Background email task
  auth/                # Signup, login, tokens, roles
  books/               # Catalog routes and service
  reviews/             # Review routes and service
  tags/                # Tag routes and service
  db/                  # Engine, models, Redis blocklist
migrations/            # Alembic revisions
```

## Getting started

Python 3.10 or newer, PostgreSQL, and Redis.

The database URL must use the async driver, and the engine connects with SSL:

```text
postgresql+asyncpg://USER:PASSWORD@HOST:5432/bookly
```

That matches a hosted Postgres instance (Neon, Supabase, RDS, and similar). A local server without SSL will refuse the connection until `connect_args` in `src/db/main.py` is adjusted.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install fastapi uvicorn sqlmodel "sqlalchemy[asyncio]" asyncpg alembic \
  pydantic-settings "passlib[bcrypt]" pyjwt "itsdangerous" fastapi-mail \
  celery redis asgiref
```

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/bookly
JWT_SECRET_KEY=replace-with-a-long-random-string
JWT_ALGORITHM=HS256

REDIS_HOST=localhost
REDIS_PORT=6379

MAIL_USERNAME=your-smtp-user
MAIL_PASSWORD=your-smtp-password
MAIL_FROM=you@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.example.com
MAIL_FROM_NAME=Bookly
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
USE_CREDENTIALS=True
VALIDATE_CERTS=True

DOMAIN=localhost:8000
```

`DOMAIN` is the host used inside verification and password-reset links.

Apply the schema, then start the API and the worker in separate terminals:

```bash
alembic upgrade head
uvicorn src:app --reload
celery -A src.celery_tasks.celery_app worker --loglevel=info
```

On Windows, start the worker with the solo pool:

```bash
celery -A src.celery_tasks.celery_app worker --loglevel=info --pool=solo
```

- API: [http://localhost:8000](http://localhost:8000)
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

Trusted hosts are limited to `localhost` and `127.0.0.1`. Add any other host in `src/middleware.py` before deploying.

### Schema changes

Models live in `src/db/models.py`. After editing them:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

## Error shape

Domain errors return a stable body instead of a framework default:

```json
{
  "message": "Book not found",
  "error_code": "book_not_found"
}
```

Auth failures also include a `resolution` field when the client should request a new token or finish email verification. Database and unexpected server errors return `error_code: "server_error"`.
