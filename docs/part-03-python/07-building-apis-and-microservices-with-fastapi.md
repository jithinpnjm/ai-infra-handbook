---
id: "c03-07"
title: "3.7 Building APIs and microservices with FastAPI"
sidebar_label: "3.7 Building APIs and microservices with FastAPI"
sidebar_position: 7
description: "FastAPI and ASGI for infrastructure and AI services: routing, validation, dependencies, errors, auth, databases, background work, streaming, testing, deployment and observability"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "Mac"
---

# 3.7 Building APIs and microservices with FastAPI

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Python 3.11+, `pip install fastapi uvicorn[standard] pydantic httpx pytest`; Docker/kind optional |
| Part | Part 3: Python for infrastructure |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Almost every platform component eventually grows an HTTP API: an inventory service in front of NetBox and Redfish, a job-submission gateway over Slurm or Kubernetes, a webhook receiver for Alertmanager, a model-serving front end that does authentication, batching and streaming before calling Triton or vLLM, an internal control plane for GPU quotas, an "agent" that exposes health and metrics. FastAPI is the dominant Python framework for these: it is asynchronous (ASGI), type-driven (request validation and OpenAPI documentation come from Python type hints and pydantic models), and fast enough for most control-plane and many data-plane services. This chapter teaches FastAPI end to end with an infrastructure and inference bias: architecture (WSGI vs ASGI), routing and validation, dependency injection, error handling, authentication and security, databases, background and long-running work, streaming responses, testing, packaging and deployment on containers and Kubernetes (probes, graceful shutdown), and observability.

## Prerequisites and outcomes

You should know functions, classes, typing and pydantic basics (3.1 to 3.4), concurrency and asyncio (3.6), HTTP basics (2.10).

After this chapter you can:

- Explain WSGI vs ASGI, how an ASGI server (uvicorn/hypercorn) runs a FastAPI app, and how sync (`def`) and async (`async def`) endpoints are executed.
- Build REST APIs with routing, path/query/header/cookie/body parameters, pydantic request and response models, status codes, error responses and OpenAPI docs.
- Use dependency injection (`Depends`) for configuration, database sessions, authentication and shared clients; use lifespan events for startup and shutdown.
- Structure an application with `APIRouter`, settings, layers (routes, services, repositories), versioning and pagination.
- Implement authentication and authorisation (API keys, OAuth2 password/bearer with JWT, mTLS at the proxy), CORS, rate limiting hooks, input hardening.
- Connect to SQL (SQLAlchemy/SQLModel, async) and NoSQL databases; manage migrations and connection pools.
- Handle background and long-running work (BackgroundTasks, task queues, job-status endpoints), streaming (Server-Sent Events, chunked responses, WebSockets), file uploads/downloads.
- Test with `TestClient`/`httpx`, dependency overrides and fixtures; load test.
- Package, containerise and deploy behind a proxy; implement health/readiness probes, graceful shutdown, metrics and tracing; understand scaling and performance trade-offs.

## 1. Architecture: from WSGI to ASGI

**WSGI** (PEP 3333, Flask/Django classic) is a synchronous interface: one request occupies one worker thread/process until it finishes; concurrency comes from many workers (gunicorn). **ASGI** is the asynchronous successor: an event-loop-based interface supporting `async def` handlers, long-lived connections (WebSockets, SSE), and background tasks. FastAPI is built on **Starlette** (ASGI toolkit) and **pydantic** (validation); it adds routing declarations, dependency injection and automatic OpenAPI.

```mermaid
flowchart LR
  C["Client / Ingress / API gateway"] --> S["ASGI server\nuvicorn (uvloop, httptools)"]
  S --> M["Middleware stack\n(CORS, auth, logging, metrics, gzip)"]
  M --> R["Router: match path + method"]
  R --> D["Dependencies (Depends)\nauth, settings, DB session"]
  D --> V["Validate request\n(pydantic)"]
  V --> H["Endpoint function\nasync def or def"]
  H --> O["Validate/serialize response\n(response_model)"]
  O --> C
```

- **`async def` endpoints** run directly on the event loop: great for awaiting non-blocking I/O (`httpx.AsyncClient`, async DB drivers), terrible if they perform blocking calls or heavy CPU (they stall every request). **`def` endpoints** run in a **thread pool** (anyio, 40 threads by default), so blocking libraries are acceptable but concurrency is bounded by the pool. Rule: use `async def` only when everything you await is truly async; otherwise use `def` (or `await asyncio.to_thread(...)` / `run_in_threadpool` inside async code). Never call `requests.get`, `time.sleep`, `subprocess.run`, or heavy NumPy inside `async def`.
- Run with **uvicorn** (`uvicorn app.main:app --host 0.0.0.0 --port 8000`) or **gunicorn with uvicorn workers** (`gunicorn -k uvicorn.workers.UvicornWorker -w 4`) to use multiple cores: each worker is a separate process with its own event loop and memory (state is not shared; models loaded per worker multiply memory; GPU services typically run one worker per GPU). `--workers`, `--limit-concurrency`, `--timeout-keep-alive`, `--proxy-headers` (behind a proxy), `--log-config`, and graceful shutdown `--timeout-graceful-shutdown` matter in production.
- **Performance**: FastAPI + uvicorn handles thousands of simple requests per second per core; real latency is dominated by what the handler does (database, downstream calls, model inference). For ML inference prefer dedicated serving runtimes (Triton, vLLM, TGI, TorchServe, Ray Serve, KServe) behind a thin FastAPI gateway for auth, validation, routing, rate limiting, and request shaping.

## 2. A first application

```python
# app/main.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Fleet API", version="1.0.0", description="Inventory and job gateway")

class NodeIn(BaseModel):
    name: str = Field(pattern=r"^[a-z0-9-]{3,63}$")
    rack: str
    gpus: int = Field(8, ge=1, le=16)

class Node(NodeIn):
    id: int

DB: dict[int, Node] = {}                       # demo only: real services use a database

@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}

@app.post("/nodes", response_model=Node, status_code=status.HTTP_201_CREATED)
async def create_node(node: NodeIn) -> Node:
    if any(n.name == node.name for n in DB.values()):
        raise HTTPException(status.HTTP_409_CONFLICT, f"node {node.name} exists")
    new = Node(id=len(DB) + 1, **node.model_dump())
    DB[new.id] = new
    return new

@app.get("/nodes/{node_id}", response_model=Node)
async def get_node(node_id: int) -> Node:
    try:
        return DB[node_id]
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "node not found") from None

@app.get("/nodes", response_model=list[Node])
async def list_nodes(rack: str | None = None, limit: int = 100, offset: int = 0) -> list[Node]:
    items = [n for n in DB.values() if rack in (None, n.rack)]
    return items[offset: offset + limit]
```

```bash
uvicorn app.main:app --reload                        # development with autoreload
curl -s localhost:8000/nodes -X POST -H 'content-type: application/json' -d '{"name":"gpu01","rack":"r1"}' | jq
# interactive docs: http://localhost:8000/docs (Swagger UI), /redoc, machine-readable /openapi.json
```

What FastAPI did for you: parsed and validated the JSON body into `NodeIn` (returning 422 with details for errors), converted types, documented the endpoint in OpenAPI, filtered the response through `response_model`, set the status code, and generated interactive docs.

## 3. Requests: routing and parameters

### Path, query, header, cookie, form and body

```python
from fastapi import Path, Query, Header, Cookie, Body, Form, File, UploadFile, Depends
from typing import Annotated

@app.get("/racks/{rack}/nodes/{name}")
async def get(
    rack: Annotated[str, Path(min_length=1, max_length=32)],          # path parameter (from the URL template)
    name: str,
    verbose: Annotated[bool, Query(description="include details")] = False,        # query ?verbose=true
    tags: Annotated[list[str] | None, Query()] = None,                              # ?tags=a&tags=b
    x_request_id: Annotated[str | None, Header()] = None,            # header X-Request-Id (underscores converted)
    session: Annotated[str | None, Cookie()] = None,
): ...

@app.post("/jobs")
async def submit(job: JobIn, priority: Annotated[int, Body(ge=0, le=10)] = 5): ...    # multiple body params embed by key
@app.post("/upload")
async def upload(file: UploadFile, desc: Annotated[str, Form()]):       # multipart/form-data; spooled to disk if large
    data = await file.read()                                              # or stream chunks: await file.read(1<<20)
```

- A parameter name appearing in the path template is a **path parameter**; scalar types without a body model become **query parameters**; pydantic models become the **JSON body**. `Annotated[..., Query/Path/Header/...]` adds validation and documentation (since FastAPI 0.95 this style is preferred over default-valued `Query(...)`). In *Building Python Web APIs with FastAPI* Chapters 2 and 3 (`todo.py` and `model.py`), `Path(..., title="The ID of the todo to retrieve", gt=0, le=1000)` marks a path parameter as required (using ellipsis `...` as the first argument) with numeric bounds (`gt`, `ge`, `lt`, `le`), while nested Pydantic models (`class Item(BaseModel): item: str; status: str` nested inside `class Todo(BaseModel): id: int; item: Item` with `Config.schema_extra` / `model_config = ConfigDict(json_schema_extra={"example": ...})`) validate hierarchical JSON payloads and populate the interactive **Swagger UI** (`/docs`) and **ReDoc** (`/redoc`) documentation pages automatically.
- **Enums and literals** restrict values: `class State(StrEnum): ...`; invalid values yield 422.
- **Path order matters**: define fixed paths (`/nodes/summary`) before parameterised ones (`/nodes/{id}`).
- **Query parameter models** (0.115+): group query params into a pydantic model with `Annotated[Filter, Query()]`.
- **Pagination**: `limit`/`offset` or cursor-based (`page_token`); cap `limit` (`Query(le=1000)`); return total counts or `next` tokens; stable ordering.
- **Idempotency**: accept an `Idempotency-Key` header on POSTs that create resources; store results by key.

### Request and response models

Pydantic models define the schema. Separate **input**, **stored** and **output** models (`NodeIn`, `NodeDB`, `NodeOut`—or in `FA` Chapter 3, `Todo`, `TodoItem`, and `class TodoItems(BaseModel): todos: List[TodoItem]` passed to `@todo_router.get("/todo", response_model=TodoItems)` so `retrieve_todo()` returns only the `TodoItem` descriptions without exposing internal `id` fields) so clients can't set server-controlled fields (id, owner, timestamps) and secrets never leak (mass-assignment protection). `response_model` filters/validates what you return (use `response_model_exclude_none=True`, `response_model_by_alias`, and `model_config = {"from_attributes": True}` to serialise ORM objects).

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator

class JobIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    image: str
    gpus: int = 1
    command: list[str]
    env: dict[str, str] = {}

    @model_validator(mode="after")
    def check(self):
        if self.gpus > 8 and "multi-node" not in self.name:
            raise ValueError("more than 8 GPUs requires a multi-node job name")
        return self

class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    state: Literal["queued", "running", "failed", "done"]
    created_at: datetime
```

Return types can be annotated directly (`-> JobOut`); FastAPI uses them as the response model. Use `JSONResponse`, `PlainTextResponse`, `StreamingResponse`, `FileResponse`, `RedirectResponse`, `ORJSONResponse`/`UJSONResponse` (faster JSON) for custom behaviour.

## 4. Dependency injection

`Depends` declares reusable components resolved per request (and cached within a request): configuration, database sessions, authenticated users, rate-limit checks, shared clients. Dependencies can be functions, classes, generators (with cleanup after `yield`), and can themselves depend on others.

```python
from fastapi import Depends
from functools import lru_cache
from collections.abc import AsyncIterator

class Settings(BaseSettings):                       # pydantic-settings
    db_url: str
    api_keys: set[str] = set()
    model_config = SettingsConfigDict(env_prefix="FLEET_")

@lru_cache
def get_settings() -> Settings: return Settings()

async def get_db(settings: Annotated[Settings, Depends(get_settings)]) -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:           # setup
        yield session                               # injected into the endpoint
    # teardown after the response (commit/rollback/close)

async def require_key(x_api_key: Annotated[str, Header()], s: Annotated[Settings, Depends(get_settings)]):
    if x_api_key not in s.api_keys:                 # use secrets.compare_digest for constant-time comparison
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid API key", headers={"WWW-Authenticate": "ApiKey"})

@app.get("/nodes", dependencies=[Depends(require_key)])          # applies without injecting a value
async def list_nodes(db: Annotated[AsyncSession, Depends(get_db)]): ...
router = APIRouter(prefix="/v1", dependencies=[Depends(require_key)])    # applies to all routes in a router
app = FastAPI(dependencies=[Depends(require_key)])                        # global
```

Benefits: testability (`app.dependency_overrides[get_db] = fake_db` swaps components in tests), consistency, and separation of concerns. Use **class-based dependencies** or `lru_cache`d factories for expensive shared objects (HTTP client pools, ML models), but create heavy resources once in **lifespan**, not per request.

### Lifespan: startup and shutdown

```python
from contextlib import asynccontextmanager
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=10, limits=httpx.Limits(max_connections=200))
    app.state.model = load_model()               # blocking? run in thread: await asyncio.to_thread(load_model)
    app.state.ready = True
    yield                                         # application serves requests
    app.state.ready = False
    await app.state.http.aclose()                 # clean shutdown: close pools, flush logs/metrics, release GPU

app = FastAPI(lifespan=lifespan)
```

(The older `@app.on_event("startup")` hooks are deprecated in favour of lifespan.) Store shared objects on `app.state`, access via `request.app.state`.

## 5. Errors, validation and middleware

- **Validation errors** (422) are automatic; customise with `@app.exception_handler(RequestValidationError)` to return your error schema.
- **`HTTPException(status_code, detail, headers)`** for expected errors; define domain exceptions and map them: 

```python
class NodeNotFound(Exception):
    def __init__(self, name): self.name = name

@app.exception_handler(NodeNotFound)
async def nf_handler(request: Request, exc: NodeNotFound):
    return JSONResponse(status_code=404, content={"error": "node_not_found", "node": exc.name, "request_id": request.state.request_id})
```

- Use consistent error bodies (RFC 9457 `application/problem+json`: type, title, status, detail, instance), correct status codes (400 vs 422 vs 409 vs 429; 401 vs 403; 502/503/504 for upstream problems), never leak stack traces or secrets; log unexpected exceptions with a request id (a catch-all `Exception` handler returns 500).
- **Middleware**: `@app.middleware("http")` or Starlette classes: request ids, timing, logging, CORS (`CORSMiddleware` with explicit origins), GZip, trusted hosts, HTTPS redirect, `ProxyHeadersMiddleware` (behind a load balancer), body size limits (a proxy/ASGI setting), authentication for whole apps. Pure ASGI middleware is faster than `BaseHTTPMiddleware` (which has quirks with streaming and background tasks).

```python
import time, uuid, logging
log = logging.getLogger("access")

@app.middleware("http")
async def access_log(request: Request, call_next):
    rid = request.headers.get("x-request-id", uuid.uuid4().hex)
    request.state.request_id = rid
    t0 = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("unhandled error rid=%s path=%s", rid, request.url.path); raise
    response.headers["x-request-id"] = rid
    log.info("rid=%s %s %s %d %.1fms", rid, request.method, request.url.path, response.status_code, (time.perf_counter() - t0) * 1000)
    return response
```

## 6. Structuring applications

```text
fleet/
├── pyproject.toml
├── src/fleet/
│   ├── main.py            # app factory: create_app(), lifespan, middleware, routers
│   ├── config.py          # Settings
│   ├── deps.py            # shared dependencies (auth, db)
│   ├── api/
│   │   ├── v1/
│   │   │   ├── nodes.py   # APIRouter: HTTP concerns only
│   │   │   └── jobs.py
│   ├── schemas/           # pydantic models (API contracts)
│   ├── services/          # business logic (pure-ish, testable)
│   ├── repositories/      # DB access
│   ├── models/            # ORM tables
│   └── clients/           # outbound HTTP clients (redfish, slurm)
└── tests/
```

- `APIRouter(prefix="/nodes", tags=["nodes"])`, then `app.include_router(nodes.router, prefix="/v1")`. In *Building Python Web APIs with FastAPI* Chapter 5's Event Planner architecture (`planner/`), the application is organized into `database/connection.py`, `models/events.py` (`Event` with `id`, `title`, `image`, `description`, `tags: List[str]`, `location`, `creator`), `models/users.py` (`User`, `NewUser`, `UserSignIn` with `EmailStr`), `routes/events.py` (`event_router = APIRouter(tags=["Events"])`), and `routes/users.py` (`user_router = APIRouter(tags=["User"])` with `/user/signup` and `/user/signin`), registered in `main.py` via `app.include_router(user_router, prefix="/user")` and `app.include_router(event_router, prefix="/event")`. Keep route functions thin: parse/validate → call a service → map to a response. Business logic in services (no FastAPI imports), data access in repositories: easy unit tests.
- **App factory** (`def create_app(settings=None) -> FastAPI`) lets tests build isolated apps.
- **Versioning**: URL prefix (`/v1`), deprecate with `deprecated=True` and `Sunset` headers; evolve schemas additively; keep OpenAPI as the contract and test for breaking changes (e.g. `oasdiff`).
- **Configuration**: environment variables via pydantic-settings (12-factor); secrets from files/secret managers; no config in code.
- **Mounting** sub-apps and static files (`app.mount("/static", StaticFiles(...))`); server-side HTML rendering (`FA` Chapter 4) uses `Jinja2Templates(directory="templates/")` and `templates.TemplateResponse("todo.html", {"request": request, "todos": todo_list})` with Jinja2 filters (`default`, `escape`, conversion `int`/`float`, `join`, `length`), `{% if %}` / `{% for %}` control blocks, `{% macro %}` reusable components, and `{% extends "home.html" %}` / `{% block content %}` template inheritance for simple status dashboards.

## 7. Authentication and security

- **API keys**: header `X-API-Key`, stored hashed; compare with `secrets.compare_digest`; per-key scopes and rate limits; rotation.
- **Password hashing (`HashPassword` / `passlib[bcrypt]`) and OAuth2 / JWT (`FA` Chapter 7)**:
  - **Hashing passwords (`auth/hash_password.py`):** Never store plaintext passwords in the database. Using `CryptContext(schemes=["bcrypt"], deprecated="auto")` (or `hashlib.pbkdf2_hmac` / `scrypt` / `argon2-cffi`), `create_hash(password: str)` hashes the user's password during `/user/signup`, and `verify_hash(plain_password: str, hashed_password: str)` verifies it during `/user/signin`.
  - **Creating and verifying JWTs (`auth/jwt_handler.py` and `auth/authenticate.py`, using `python-jose`/`PyJWT`/`authlib`):** `create_access_token(user: str)` builds a payload `{"user": user, "expires": time.time() + 3600}` and signs it with `jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")` (or asymmetric `RS256` against an OIDC provider's JWKS), returning `TokenResponse(access_token=access_token, token_type="Bearer")` from `/user/signin` (which accepts `user: OAuth2PasswordRequestForm = Depends()`). On protected routes (`POST /event/new`, `PUT /event/{id}`, `DELETE /event/{id}`), `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/signin")` extracts the `Authorization: Bearer <token>` header, `authenticate(token: str = Depends(oauth2_scheme))` calls `verify_access_token(token)` (checking that `expires` is present and `datetime.utcnow() <= datetime.utcfromtimestamp(expire)`, raising `400`/`403` otherwise) and returns `data["user"]`.
  - **Object-level ownership (`BOLA` protection):** In `create_event(body: Event, user: str = Depends(authenticate))`, the server sets `body.creator = user`; in `update_event` and `delete_event`, the route checks whether `event.creator` differs from `user` and raises `HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Operation not allowed")` so an authenticated user cannot modify or delete another user's resources. For service-to-service calls, use workload identity (Kubernetes service account tokens, SPIFFE) or mTLS terminated at the mesh/ingress.

```python
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
import jwt

oauth2 = OAuth2PasswordBearer(tokenUrl="token", scopes={"jobs:write": "submit jobs", "nodes:read": "read inventory"})

async def current_user(scopes: SecurityScopes, token: Annotated[str, Depends(oauth2)]):
    try:
        claims = jwt.decode(token, key=jwks_key_for(token), algorithms=["RS256"], audience="fleet-api", issuer="https://idp.example.com/")
    except jwt.PyJWTError:
        raise HTTPException(401, "invalid token", headers={"WWW-Authenticate": "Bearer"})
    if not set(scopes.scopes) <= set(claims.get("scope", "").split()):
        raise HTTPException(403, "insufficient scope")
    return claims

@app.post("/jobs", dependencies=[Security(current_user, scopes=["jobs:write"])])
```

- **Transport security**: TLS terminates at the ingress/gateway or uvicorn (`--ssl-keyfile`); redirect HTTP to HTTPS; HSTS; mTLS for internal APIs.
- **Hardening**: validate and bound all inputs (lengths, counts, sizes); `extra="forbid"` on models; limit request body size and upload sizes; avoid SSRF when accepting URLs (allow-lists, block link-local/metadata IPs); parameterised queries only (ORMs); output encoding for HTML; secure cookies (`HttpOnly`, `Secure`, `SameSite`); CSRF protection if cookies are used for auth; CORS only for needed origins; security headers; rate limiting (gateway, `slowapi`, Redis-based limiter); audit logging of mutating calls; dependency scanning; no debug mode in production (`docs_url=None` if the API must not expose docs publicly).
- **OWASP API Top 10** checklist: broken object-level authorisation (check ownership on every `/{id}` access), broken authentication, excessive data exposure (use response models), lack of resources/rate limiting, function-level authorisation, mass assignment, misconfiguration, injection, improper asset management, unsafe consumption of upstream APIs.
- **Secrets**: from environment/secret store, never in the image or repo; `SecretStr` for logging safety.

## 8. Databases

### SQL (SQLAlchemy 2.x / SQLModel)

```python
# async engine and session
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select, String

engine = create_async_engine("postgresql+asyncpg://user:pw@db/fleet", pool_size=10, max_overflow=20, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase): ...
class NodeRow(Base):
    __tablename__ = "nodes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(63), unique=True, index=True)
    rack: Mapped[str] = mapped_column(String(32), index=True)
    gpus: Mapped[int]

@app.get("/nodes", response_model=list[Node])
async def list_nodes(db: Annotated[AsyncSession, Depends(get_db)], rack: str | None = None, limit: int = Query(100, le=1000)):
    stmt = select(NodeRow).order_by(NodeRow.id).limit(limit)
    if rack: stmt = stmt.where(NodeRow.rack == rack)
    return (await db.scalars(stmt)).all()
```

- **SQLModel** (`FA` Chapter 6, by the FastAPI author) merges pydantic and SQLAlchemy models (`class Event(SQLModel, table=True): id: Optional[int] = Field(default=None, primary_key=True); tags: List[str] = Field(sa_column=Column(JSON))` with a partial update schema `class EventUpdate(SQLModel): title: Optional[str] = None ...`), creating tables via `engine_url = create_engine("sqlite:///planner.db", echo=True, connect_args={"check_same_thread": False}); SQLModel.metadata.create_all(engine_url)` and injecting sessions with `def get_session(): with Session(engine_url) as session: yield session`. In `routes/events.py`, CRUD routes run `session.add(new_event); session.commit(); session.refresh(new_event)` (Create), `session.exec(select(Event)).all()` and `session.get(Event, id)` (Read), iterate `event_data = new_data.dict(exclude_unset=True)` with `setattr(event, key, value)` before `session.add(event); session.commit(); session.refresh(event)` (Update), and `session.delete(event); session.commit()` (Delete). Larger systems keep API schemas and ORM models separate.
- **Migrations**: Alembic (`alembic revision --autogenerate`, `upgrade head`); run migrations as a separate job/init step, not at app start in multi-replica deployments.
- **Pools**: size to `workers × pool_size ≤ DB max_connections`; `pool_pre_ping`, timeouts, and a pooler (PgBouncer) for many replicas; avoid sessions shared across requests/tasks; keep transactions short; handle deadlocks/serialization retries; N+1 query avoidance (`selectinload`).
- **Blocking drivers** (psycopg2) inside `def` endpoints are fine (thread pool); with `async def` use async drivers (asyncpg, psycopg3 async, aiomysql).
- **NoSQL (MongoDB with Motor and Beanie ODM, `FA` Chapter 6)**: `class Event(Document):` subclasses Beanie's `Document` (which extends Pydantic `BaseModel`), initialized at startup via `client = AsyncIOMotorClient(settings.DATABASE_URL); await init_beanie(database=client.get_default_database(), document_models=[Event, User])`. A generic `class Database:` repository wraps `await document.create()` (Create), `await self.model.get(id)` and `await self.model.find_all().to_list()` (Read with `PydanticObjectId`), `des_body = {k: v for k, v in body.dict().items() if v is not None}; await doc.update({"$set": des_body})` (Update), and `await doc.delete()` (Delete). Use Redis (`redis.asyncio`) for caches/queues/rate limits, etcd, DynamoDB, or Elasticsearch/OpenSearch. Time-series metrics belong in Prometheus/VictoriaMetrics, not your service database.
- **Caching**: `cachetools`, `aiocache`, Redis; cache-aside with TTLs; ETags/`Cache-Control` for clients; invalidate on writes.

## 9. Long-running, background and streaming work

### Background tasks and queues

`BackgroundTasks` runs a callable **after the response is sent**, in the same process: fine for quick fire-and-forget work (send a notification), but lost if the process restarts and unsuitable for long or critical jobs.

```python
from fastapi import BackgroundTasks
@app.post("/jobs", status_code=202)
async def submit(job: JobIn, bg: BackgroundTasks):
    job_id = create_job_record(job)                   # persist first
    bg.add_task(run_job, job_id)                      # short work only
    return {"id": job_id, "state": "queued", "status_url": f"/jobs/{job_id}"}
```

For durable or heavy work use a **job queue and workers**: Celery, RQ, Dramatiq, Arq (asyncio), Taskiq, Temporal (workflows), Kubernetes Jobs, Slurm submissions. Pattern: `POST` returns **202 Accepted** with a job id; the client polls `GET /jobs/{id}` (or receives a webhook / SSE stream); the worker updates state in a database; make operations idempotent with job keys. Cancellation endpoints (`DELETE /jobs/{id}`), timeouts, retries with backoff and dead-letter handling complete the design.

### Streaming

```python
from fastapi.responses import StreamingResponse
import asyncio, json

async def event_stream(job_id: str, request: Request):
    last = None
    while not await request.is_disconnected():          # stop when the client goes away
        state = await get_state(job_id)
        if state != last:
            yield f"event: state\ndata: {json.dumps(state)}\n\n"        # Server-Sent Events framing
            last = state
        if state["state"] in {"failed", "done"}: break
        await asyncio.sleep(1)

@app.get("/jobs/{job_id}/events")
async def events(job_id: str, request: Request):
    return StreamingResponse(event_stream(job_id, request), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})     # disable proxy buffering
```

- **SSE** (one-way server push over HTTP) suits token streaming from LLMs, log tailing and progress; **WebSockets** (`@app.websocket`) for bidirectional; **chunked/`StreamingResponse`** for large downloads (`async for chunk in aiofiles...`), **`FileResponse`** for static files.
- Proxies and load balancers buffer responses by default and enforce idle timeouts: disable buffering (`X-Accel-Buffering: no`, nginx `proxy_buffering off`), set long read timeouts, send periodic comment/heartbeat lines, and ensure HTTP/2 or keep-alive end to end (chapters 2.10 and 2.20).
- Backpressure: producers should await when clients are slow (the ASGI server applies flow control through `send`); bound queues.

### An inference gateway example

```python
# Thin FastAPI front end over a model server: auth, validation, timeouts, streaming passthrough, metrics
@app.post("/v1/chat", dependencies=[Security(current_user, scopes=["infer"])])
async def chat(req: ChatRequest, request: Request, settings: Annotated[Settings, Depends(get_settings)]):
    if req.max_tokens > settings.max_tokens: raise HTTPException(422, "max_tokens too large")
    client: httpx.AsyncClient = request.app.state.http
    async def gen():
        try:
            async with client.stream("POST", settings.backend_url, json=req.model_dump(), timeout=httpx.Timeout(10, read=300)) as r:
                if r.status_code >= 500: raise HTTPException(502, "backend error")
                async for line in r.aiter_lines():
                    if await request.is_disconnected(): break            # client left: stop consuming (frees GPU time upstream)
                    if line: yield line + "\n\n"
        except httpx.TimeoutException:
            yield 'event: error\ndata: {"error":"upstream_timeout"}\n\n'
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})
```

For batching, queue incoming requests into an `asyncio.Queue`, group them (up to N items or T ms) and send a single batched call to the model; return results through per-request futures (dynamic batching: Triton/vLLM do this better, but gateways may implement tiered logic). Add concurrency limits per user/tenant, token-based rate limits, request cancellation propagation, and metrics (TTFT, tokens/s).

## 10. Testing

```python
# tests/test_nodes.py
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from fleet.main import create_app
from fleet.deps import get_db

@pytest.fixture
def client():
    app = create_app(settings=Settings(db_url="sqlite+aiosqlite://", api_keys={"k"}))
    app.dependency_overrides[get_db] = fake_db            # swap the DB
    with TestClient(app) as c:                             # runs lifespan startup/shutdown
        c.headers["x-api-key"] = "k"
        yield c

def test_create_and_get(client):
    r = client.post("/v1/nodes", json={"name": "gpu01", "rack": "r1"})
    assert r.status_code == 201
    nid = r.json()["id"]
    assert client.get(f"/v1/nodes/{nid}").json()["name"] == "gpu01"

def test_validation(client):
    assert client.post("/v1/nodes", json={"name": "x"}).status_code == 422

def test_auth(client):
    client.headers.pop("x-api-key"); assert client.get("/v1/nodes").status_code in (401, 403, 422)

@pytest.mark.anyio
async def test_async():
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as ac:
        assert (await ac.get("/healthz")).json() == {"status": "ok"}
```

Test layers: unit tests for services/repositories (pure Python, fakes), API tests with `TestClient` (in-process, no network) or async `httpx.AsyncClient(app=app, base_url="http://app")` with `conftest.py` `@pytest.fixture(scope="session")` (`event_loop`, `default_client`, `access_token`, `mock_event` in `FA` Chapter 8's `test_login.py` and `test_routes.py`, measured via `coverage run -m pytest`, `coverage report`, and `coverage html` -> `htmlcov/index.html`) and dependency overrides, integration tests with real DB containers (`testcontainers`), contract tests against the OpenAPI schema (`schemathesis` fuzzes endpoints from the spec), load tests (`locust`, `k6`, `wrk`, `hey`) for latency percentiles and saturation, and security tests (authz matrices). Run in CI with coverage (chapter 3.9).

## 11. Deployment and operations

### Packaging

```dockerfile
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ src/
USER 10001
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"
CMD ["uvicorn", "fleet.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*", "--timeout-graceful-shutdown", "25"]
```

- Always include a `.dockerignore` file (`venv`, `.env`, `.git`, `__pycache__`) so local virtual environments and secrets are never copied into the image build context, and use `docker-compose.yml` (`api` service with `env_file: .env.prod` + `database` service with a persistent volume `data:/data/db`, `FA` Chapter 9) for local multi-container verification before deploying to Kubernetes (using managed cloud databases like Cloud SQL / RDS / Atlas in production rather than unbacked container storage).
- One uvicorn process per container; scale with replicas (Kubernetes HPA on CPU/RPS/queue depth/custom metrics); use gunicorn+uvicorn workers only when you want multi-process per container.
- Set `--limit-concurrency` or rely on the proxy to shed load; configure `--timeout-keep-alive` above the load balancer's idle timeout to avoid races.
- Multi-stage builds, non-root, read-only root file system, dropped capabilities (chapter 2.21).

### Kubernetes deployment essentials

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: fleet-api }
spec:
  replicas: 3
  strategy: { rollingUpdate: { maxSurge: 1, maxUnavailable: 0 } }
  selector: { matchLabels: { app: fleet-api } }
  template:
    metadata: { labels: { app: fleet-api } }
    spec:
      terminationGracePeriodSeconds: 40
      containers:
      - name: api
        image: registry.example.com/fleet-api:1.4.2
        ports: [ { containerPort: 8000 } ]
        env:
        - { name: FLEET_DB_URL, valueFrom: { secretKeyRef: { name: fleet-db, key: url } } }
        resources: { requests: { cpu: 250m, memory: 256Mi }, limits: { memory: 512Mi } }
        startupProbe:   { httpGet: { path: /healthz, port: 8000 }, failureThreshold: 30, periodSeconds: 2 }
        readinessProbe: { httpGet: { path: /readyz, port: 8000 }, periodSeconds: 5 }
        livenessProbe:  { httpGet: { path: /healthz, port: 8000 }, periodSeconds: 10, timeoutSeconds: 2, failureThreshold: 3 }
        lifecycle: { preStop: { exec: { command: ["sleep", "5"] } } }      # let endpoints deregister before SIGTERM handling
```

- **Liveness** (`/healthz`): process is alive and the event loop responsive; keep it cheap and independent of dependencies (otherwise a DB blip restarts every pod). **Readiness** (`/readyz`): can serve traffic now (model loaded, DB reachable, not draining); flip to not-ready on shutdown. **Startup** probe for slow model loads.
- **Graceful shutdown**: on SIGTERM uvicorn stops accepting connections and waits for in-flight requests up to the graceful timeout; align `terminationGracePeriodSeconds`, `preStop` sleep, LB deregistration delay and `--timeout-graceful-shutdown`; for streaming endpoints decide whether to cut or drain long-lived streams.
- **Resources**: memory limits for models and caches; for GPU inference services request `nvidia.com/gpu`; one worker per GPU; avoid CPU limits that throttle event loops (prefer requests).
- **Autoscaling** on concurrency or queue length rather than CPU for I/O-bound services; KEDA for event-driven scaling.
- **Config and rollout**: ConfigMaps/Secrets, immutable image tags/digests, canary or blue/green via ingress/mesh/Argo Rollouts, DB migrations as pre-deploy Jobs with backward-compatible schema changes (expand/contract).

### Observability

- **Logs**: structured JSON to stdout with request id, user/tenant, route, status, latency; redact secrets; sample noisy logs (chapter 3.5).
- **Metrics**: `prometheus-fastapi-instrumentator` or `starlette-exporter` expose `/metrics` (request counts, latencies by route/status, in-flight); add business metrics (jobs by state, queue depth, tokens/s, GPU utilisation from DCGM). Use the RED method (rate, errors, duration) and alert on SLOs (chapter 2.31).
- **Tracing**: OpenTelemetry instrumentation (`opentelemetry-instrumentation-fastapi`, `-httpx`, `-sqlalchemy`) propagates `traceparent` through downstream calls; export to Tempo/Jaeger/OTLP collector.
- **Health endpoints, build info endpoint** (`/version` with git SHA), and debug endpoints behind auth.
- **Profiling**: `py-spy`, `pyinstrument` middleware in staging, `uvicorn --log-level debug`, slow-request logs.

### Performance checklist

Use async drivers and shared `httpx.AsyncClient`; orjson responses for large JSON; avoid per-request model loading; pagination and streaming for big results; gzip/br compression at the proxy; connection pool tuning; keep the event loop free (offload CPU/blocking to threads/processes/queues); cache expensive lookups; measure with load tests and profile before optimising; remember pydantic validation of huge payloads costs CPU (limit sizes; consider `model_validate_json` and `TypeAdapter`).

## 12. Lab

First, run the self-checking Python lab (`code/part03/python_fastapi_microservices_lab.py`) locally. It verifies nested `Todo` / `TodoItem` models and `response_model` field filtering (`FA` Ch. 2 & 3), `HashPassword` password hashing and `create_access_token` / `verify_access_token` JWT validation and expiration (`FA` Ch. 7), `EventPlannerRepository` SQLite CRUD, partial `EventUpdate` (`exclude_unset`), and creator ownership (`BOLA`) enforcement (`FA` Ch. 5–8), and Server-Sent Events (`SSE`) framing and stream termination.

```bash
python3 code/part03/python_fastapi_microservices_lab.py
```

Next, on any machine with Python 3.11+ (all interactive shell steps below are `untested here`), work through these exercises:

1. **Hello API**: build the Fleet API with in-memory storage; explore `/docs` and `/openapi.json`; trigger 422 errors; add pagination and filtering; write requests with `curl` and `httpx`.
2. **Models and validation**: split schemas into In/DB/Out; use `extra="forbid"`, validators, enums; prove mass assignment is blocked; return `problem+json` errors via exception handlers.
3. **Dependencies and lifespan**: implement settings, API-key auth, a DB session dependency (SQLite then PostgreSQL in Docker), a shared `httpx.AsyncClient` in lifespan; override dependencies in tests; add request-id middleware and structured logs.
4. **Async vs sync**: write one endpoint with `async def` + `time.sleep(2)` and one with `def` + `time.sleep(2)`; load test with 50 concurrent requests (`hey`/`wrk`); observe the event-loop stall vs the thread pool; fix with `await asyncio.sleep` / `to_thread`.
5. **Database**: SQLAlchemy async models, Alembic migration, CRUD with pagination, unique-constraint conflict mapped to 409, transaction rollback on errors; test with `testcontainers`.
6. **Auth**: implement JWT bearer auth with scopes against a local Keycloak or a mocked JWKS; write an authorization matrix test (user A cannot read user B's jobs).
7. **Jobs**: implement `POST /jobs` (202) with a worker (Arq/RQ + Redis) and `GET /jobs/{id}`; add SSE progress streaming and cancellation; kill the worker mid-job and observe retry/idempotency behaviour; compare with `BackgroundTasks` losing work on restart.
8. **Inference gateway**: put a mock streaming backend (or vLLM/TGI if a GPU is available) behind the gateway; implement token streaming passthrough with disconnect handling, per-tenant concurrency limits and request timeouts; measure TTFT and throughput; test through nginx with and without `proxy_buffering off`.
9. **Testing**: reach 90% coverage with `pytest`; add `schemathesis run http://localhost:8000/openapi.json`; add a contract test that fails on removing a field.
10. **Deploy**: containerise; deploy to kind with probes, a PodDisruptionBudget, HPA and ingress; perform a rolling update during a load test and verify zero failed requests; send SIGTERM and verify graceful shutdown timing.
11. **Observability**: add `/metrics`, a Grafana dashboard of RED metrics, OpenTelemetry traces through the gateway to the backend, and an alert on p99 latency.
12. **Clean up.**

## 13. Common mistakes

- Blocking calls in `async def` endpoints; assuming `async` makes blocking code concurrent.
- Using the same pydantic model for DB, input and output (mass assignment, data leaks).
- Loading models or creating clients per request; unbounded caches; global mutable state across workers assumed shared.
- No timeouts on downstream calls; no limits on concurrency, body size or pagination.
- Liveness probes that depend on external services; readiness never flips during shutdown; mismatched grace periods causing dropped requests on deploy.
- Running DB migrations from every replica at startup; connection pool exhaustion (`workers × pool` over database limits).
- Trusting `X-Forwarded-*` headers from the Internet; leaving docs/debug enabled publicly; permissive CORS (`*` with credentials).
- Using `BackgroundTasks` for work that must not be lost; no idempotency for retried POSTs.
- Proxy buffering breaking SSE; idle timeouts killing long streams.
- Leaking stack traces or secrets in error responses and logs.

## 14. Interview angles

- "WSGI vs ASGI? How does uvicorn run FastAPI? What runs sync endpoints?"
- "When do you use `async def` vs `def` in FastAPI?"
- "How does FastAPI validate requests and generate OpenAPI?"
- "Explain dependency injection and how you test with overrides."
- "How would you design a job-submission API for long-running GPU jobs?" (202, queue, status endpoint, idempotency, cancellation.)
- "How do you stream LLM tokens through an API and handle client disconnects?"
- "How do you deploy FastAPI to Kubernetes safely? Probes, graceful shutdown, scaling, config?"
- "How do you secure the API? Authn vs authz, OAuth2/JWT, rate limiting, OWASP API risks."
- "A service hangs under load. How do you debug?" (blocked loop, pool exhaustion, DB pool, downstream timeouts.)

## Exercises

1. **WSGI vs. ASGI, `async def` vs. `def` Execution, and Uvicorn Multi-Worker Sizing (`FA` Chapter 1 & `volume-02`):** (a) Contrast WSGI (PEP 3333) with ASGI, explain what Starlette and Pydantic each contribute to FastAPI, and explain why calling `time.sleep(2)` or `requests.get()` inside an `async def` endpoint stalls all concurrent requests whereas a plain `def` endpoint runs in AnyIO's 40-thread pool; (b) explain why GPU-backed services run one worker process per GPU while CPU-bound control-plane APIs run `gunicorn -k uvicorn.workers.UvicornWorker -w N`.
2. **Routing, Path/Query/Header/Body Validation, and Input/Output Schema Separation (`FA` Chapters 2, 3, 5):** (a) Explain how FastAPI distinguishes path parameters, query parameters, headers, and JSON body payloads in `get(rack, name, verbose, tags, x_request_id)`, and why fixed routes (`/nodes/summary`) must be declared before parameterized routes (`/nodes/{id}`); (b) using `Todo` / `TodoItem` in `code/part03/python_fastapi_microservices.py`, explain why separating `NodeIn` / `JobIn` (`extra="forbid"`) from `NodeOut` / `TodoItems` (`response_model`) prevents mass assignment and sensitive field leaks.
3. **Dependency Injection (`Depends`), Generator Teardown, Lifespan State, and RFC 9457 Error Handling (`FA` Chapters 3, 6, 7):** (a) Trace the lifecycle of a generator dependency (`async def get_db(): async with SessionLocal() as session: yield session`) and an `@asynccontextmanager async def lifespan(app: FastAPI):` managing a shared `httpx.AsyncClient` and ML model on `app.state`; (b) show how `@app.exception_handler(NodeNotFound)` maps domain exceptions to structured `application/problem+json` responses with `x-request-id` correlation headers.
4. **Authentication, Password Hashing (`HashPassword`), OAuth2/JWT Scopes, and Object-Level Ownership (`BOLA`, `FA` Chapter 7):** Using `HashPassword`, `create_access_token()`, `verify_access_token()`, and `EventPlannerRepository` in `code/part03/python_fastapi_microservices.py`, explain: (a) how `/user/signup` hashes passwords and `/user/signin` issues signed JWTs with an `expires` claim verified by `Depends(authenticate)`; and (b) how checking whether `event.creator` matches `user` (and `Security(current_user, scopes=["jobs:write"])` / `secrets.compare_digest` for API keys) prevents Broken Object-Level Authorization (`BOLA`).
5. **SQL (SQLAlchemy / SQLModel) & NoSQL (Beanie) Persistence, Long-Running Jobs (`202 Accepted`), and SSE Token Streaming (`FA` Chapter 6):** (a) Using `EventPlannerRepository.update()`, show how partial `PUT`/`PATCH` updates filter out `None`/unset fields (`{k: v for k, v in body.items() if v is not None}`), why database connection pools must satisfy `workers * pool_size <= max_connections`, and why Alembic migrations must run as a pre-deploy Job rather than inside every pod's startup; (b) using `format_sse_events()`, contrast `BackgroundTasks` with durable job queues returning `202 Accepted`, and explain how `StreamingResponse` (`text/event-stream`, `X-Accel-Buffering: no`, and `await request.is_disconnected()`) streams LLM tokens or job states safely.
6. **Testing with `TestClient` / `httpx.AsyncClient` (`dependency_overrides`) and Production Kubernetes Deployment (`FA` Chapters 8 & 9):** (a) Write a `pytest` fixture that overrides `app.dependency_overrides[get_db] = fake_db` and tests `201`, `422`, and `401/403` responses with `TestClient` and `httpx.AsyncClient`; (b) explain how `startupProbe`, `readinessProbe` (`/readyz`), `livenessProbe` (`/healthz` without DB checks), `preStop: ["sleep", "5"]`, `--timeout-graceful-shutdown 25`, and `terminationGracePeriodSeconds: 40` work together during a zero-downtime Kubernetes rolling update.

## Checkpoint questions (20)

<details>
<summary>1. What does ASGI add over WSGI, what two libraries is FastAPI built on, and how does FastAPI execute `async def` versus `def` endpoints?</summary>

- **WSGI vs ASGI:** WSGI (PEP 3333) is a synchronous request-response interface where each concurrent request ties up a worker thread; **ASGI** (*Asynchronous Server Gateway Interface*) is an event-loop-driven interface supporting `async def` coroutines, WebSockets, Server-Sent Events (`SSE`), and HTTP/2.
- **Foundation:** FastAPI is built on **Starlette** (ASGI web/routing toolkit) and **Pydantic** (data validation and serialization).
- **`async def` vs `def`:** FastAPI runs **`async def`** endpoints directly on the single-threaded event loop (any blocking I/O or CPU work stalls the entire server), whereas it dispatches plain **`def`** endpoints to an external **AnyIO worker thread pool** (40 threads by default).
</details>

<details>
<summary>2. How does FastAPI distinguish path parameters, query parameters, headers, and JSON request bodies, and why does route declaration order matter (`FA` Chapter 2)?</summary>

- Parameter names matching `{param}` in the URL path template are extracted as **path parameters** (`Annotated[str, Path(...)]`).
- Other scalar/list parameters (`int`, `str`, `bool`, `list[str]`) default to **query parameters** (`?limit=100&tags=a&tags=b`, configured via `Query()`).
- Parameters annotated with `Header()` or `Cookie()` read HTTP headers (`x_request_id` automatically matches `X-Request-Id`) or cookies.
- Parameters typed as **Pydantic `BaseModel` subclasses** are parsed and validated from the **JSON request body** (returning HTTP **`422 Unprocessable Entity`** automatically on validation failure).
Because Starlette matches routes in declaration order, fixed paths (`/nodes/summary`) must be declared **before** parameterized paths (`/nodes/{node_id}`).
</details>

<details>
<summary>3. Why should you separate Input (`NodeIn`), Database (`NodeDB`), and Output (`NodeOut` / `TodoItems`) models, and what does `response_model` do (`FA` Chapters 2, 3, 5)?</summary>

Using a single model for input, storage, and output enables **mass assignment** (clients injecting `id`, `is_admin=True`, or `creator` in a POST body) and **excessive data exposure** (returning password hashes or internal IDs in GET responses). Separating `NodeIn` (`extra="forbid"`) from `NodeOut` (or `TodoItems` in `FA` Chapter 3) and declaring `response_model=NodeOut` (or `-> NodeOut`) tells FastAPI to strip any field not declared on the output model, validate the outgoing structure, and publish the exact schema in `/openapi.json`, `/docs` (Swagger UI), and `/redoc`.
</details>

<details>
<summary>4. How does FastAPI Dependency Injection (`Depends`) work, including generator dependencies with `yield` and `app.dependency_overrides` (`FA` Chapters 6, 7, 8)?</summary>

`Depends(fn)` declares a callable (function, coroutine, or class) whose parameters FastAPI resolves recursively (and caches within the same request) before calling the endpoint:
- **Generator dependencies (`yield`):** Code before `yield session` runs as setup before the endpoint; code after `yield` (cleanup, closing `AsyncSession`) runs automatically after the response is sent, exactly like a context manager.
- **Scopes:** Dependencies can be attached to a single parameter, a route decorator (`dependencies=[Depends(require_key)]`), an `APIRouter`, or the entire `FastAPI` app.
- **Testing:** Setting **`app.dependency_overrides[get_db] = fake_db`** swaps out production databases or auth checks across the entire app in unit tests with zero code changes.
</details>

<details>
<summary>5. What is the `lifespan` async context manager in FastAPI, and why should `httpx.AsyncClient` and ML models be initialized there instead of per request?</summary>

Passed as `app = FastAPI(lifespan=lifespan)`, an `@asynccontextmanager async def lifespan(app: FastAPI):` runs its setup code **once before the application starts accepting traffic** and its teardown code after `yield` **once when the server shuts down on `SIGTERM`**. Storing a shared `app.state.http = httpx.AsyncClient(...)` and pre-loaded `app.state.model` in `lifespan` reuses TCP/TLS connection pools and GPU weights across all requests instead of exhausting ephemeral ports or reloading gigabytes of weights on every call.
</details>

<details>
<summary>6. How do custom `@app.exception_handler` functions, RFC 9457 `application/problem+json`, and request-ID middleware work together?</summary>

An `@app.middleware("http")` function reads `request.headers.get("x-request-id")` (or generates a fresh `uuid.uuid4().hex`), attaches it to `request.state.request_id`, logs the request duration, and returns `x-request-id` in the response header. When domain code raises `NodeNotFound(name)`, `@app.exception_handler(NodeNotFound)` returns a structured JSON body (`{"error": "node_not_found", "node": exc.name, "request_id": request.state.request_id}`, or RFC 9457 `problem+json` fields `type`, `title`, `status`, `detail`, `instance`) without leaking internal Python tracebacks.
</details>

<details>
<summary>7. How should a multi-module FastAPI application (`APIRouter`, services, repositories) be structured (`FA` Chapter 5)?</summary>

Split the project into layers:
1. **`api/` or `routes/` (`APIRouter`):** Thin HTTP route handlers (`event_router`, `user_router`, `nodes.router`) mounted via `app.include_router(..., prefix="/v1")` that handle only HTTP status codes and request/response models.
2. **`schemas/`:** Pydantic request/response contracts (`JobIn`, `JobOut`, `EventUpdate`).
3. **`services/`:** Pure business logic (testable without HTTP or FastAPI).
4. **`repositories/` and `models/`:** Database access (`EventPlannerRepository`, SQLAlchemy `NodeRow` / Beanie `Document`).
5. **`main.py`:** `create_app()` factory wiring `lifespan`, middleware, and routers.
</details>

<details>
<summary>8. How do password hashing (`HashPassword` / `bcrypt`), OAuth2 JWT verification (`OAuth2PasswordBearer`), and `secrets.compare_digest` work (`FA` Chapter 7)?</summary>

- **Passwords:** Hash passwords on signup with a slow salted KDF (`bcrypt` via `CryptContext`, `argon2-cffi`, or `pbkdf2_hmac`) and verify with `verify_hash()` on `/user/signin`.
- **API Keys:** Compare fixed API keys in constant time using **`secrets.compare_digest(provided, expected)`** to prevent timing side-channel attacks.
- **OAuth2 / JWT (`OAuth2PasswordBearer`):** Extracts the `Authorization: Bearer <token>` header, verifies the cryptographic signature (`RS256` JWKS or `HS256` `SECRET_KEY`), `iss` (issuer), `aud` (audience), **`exp` / `expires` timestamp**, and required `SecurityScopes` (`401 Unauthorized` if invalid/expired token, `403 Forbidden` if insufficient scope).
</details>

<details>
<summary>9. What is Broken Object-Level Authorization (`BOLA`, OWASP API1), and how does `FA` Chapter 7 prevent it on `PUT` and `DELETE /event/{id}`?</summary>

**Broken Object-Level Authorization (`BOLA`)** occurs when an API verifies that a user is logged in (`Depends(authenticate)`) but fails to verify that the authenticated user **owns or is authorized to access the specific resource `{id}`** requested. In `FA` Chapter 7, `create_event` records `body.creator = user` from the verified JWT, and both `update_event` and `delete_event` explicitly verify that `event.creator` equals `user` (raising `HTTPException(status_code=400, detail="Operation not allowed")` otherwise) before mutating the database.
</details>

<details>
<summary>10. How do SQLAlchemy 2.x (`AsyncSession`), SQLModel (`Session`), and Beanie ODM (`Document`) handle partial updates and connection pooling (`FA` Chapter 6)?</summary>

- **Partial updates (`EventUpdate`):** Filter out unset/`None` fields via `new_data.model_dump(exclude_unset=True)` (or `{k: v for k, v in body.dict().items() if v is not None}`) before applying `setattr(row, k, v)` or MongoDB `{"$set": des_body}` so omitted fields are not overwritten with `None`.
- **Connection pool sizing:** Each uvicorn worker process maintains its own pool (`pool_size=10, max_overflow=20, pool_pre_ping=True`). Ensure **`replicas × workers_per_pod × (pool_size + max_overflow) <= PostgreSQL max_connections`** (or place PgBouncer in front of PostgreSQL), and run **Alembic** schema migrations (`alembic upgrade head`) in a single pre-deploy Job rather than inside every replica's startup.
</details>

<details>
<summary>11. When is FastAPI's `BackgroundTasks` appropriate, and how should long-running GPU or cluster jobs be designed instead?</summary>

- **`BackgroundTasks`** runs in-process immediately after the HTTP response is sent; if the container restarts, scales down, or OOMs, the in-memory task is **permanently lost**, and heavy work competes with live requests for CPU/memory. Use it only for short, expendable notifications.
- **Durable long-running jobs:** Persist the job record first, enqueue the job ID into an external queue (`Redis` + `Arq`/`RQ`/`Celery`, `Temporal`, or a Kubernetes/Slurm Job), and immediately return **`HTTP 202 Accepted`** with `{"id": job_id, "state": "queued", "status_url": f"/jobs/{job_id}"}` so clients can poll `GET /jobs/{id}` or subscribe to an SSE stream.
</details>

<details>
<summary>12. How do Server-Sent Events (`SSE`) work with `StreamingResponse` for LLM token or job streaming, and how do you handle proxy buffering and client disconnects?</summary>

- **SSE framing:** Yield UTF-8 text blocks formatted as `event: state\ndata: {"token": "..."}\n\n` with `media_type="text/event-stream"`.
- **Disable proxy buffering:** Return headers **`{"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}`** so NGINX / Ingress controllers flush each token chunk immediately instead of buffering the stream in RAM.
- **Disconnect detection:** Check **`if await request.is_disconnected(): break`** inside the streaming generator loop so that when a user closes their browser tab or cancels a request, the gateway aborts the upstream `vLLM`/`Triton` stream immediately and frees GPU KV-cache and compute resources.
</details>

<details>
<summary>13. How do you test synchronous and asynchronous FastAPI endpoints, authentication, and OpenAPI contracts (`FA` Chapter 8)?</summary>

1. **In-process tests (`TestClient` and `httpx.AsyncClient`):** Wrap `create_app()` in a `pytest` fixture (`with TestClient(app) as c:` or `async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:` so `lifespan` hooks execute), override `app.dependency_overrides[get_db] = fake_db`, and test happy paths (`200`/`201`), validation failures (`422`), auth failures (`401`/`403`), and BOLA ownership checks.
2. **Coverage & contract fuzzing:** Measure line/branch coverage with `coverage run -m pytest && coverage report` (`pytest --cov`) and fuzz all routes against `/openapi.json` using **`schemathesis`**.
</details>

<details>
<summary>14. Why must Kubernetes `livenessProbe` (`/healthz`) and `readinessProbe` (`/readyz`) have different checks?</summary>

- **`livenessProbe` (`/healthz`):** Tells the kubelet whether the Python process and event loop are wedged and need to be **killed and restarted**. It must be a trivial in-memory return (`{"status": "ok"}`) and **must never query external databases or downstream APIs**—otherwise a transient database blip causes Kubernetes to restart every pod in the fleet simultaneously (a cascading outage).
- **`readinessProbe` (`/readyz`):** Tells the Service/Ingress load balancer whether this pod is currently ready to **receive traffic** (model weights loaded on GPU, database pool initialized, and `app.state.ready` is `True`).
</details>

<details>
<summary>15. How do `preStop`, `--timeout-graceful-shutdown`, and `terminationGracePeriodSeconds` prevent dropped requests during a Kubernetes rolling update?</summary>

When Kubernetes terminates a pod, removing the pod IP from `EndpointSlice`s/kube-proxy/Ingress happens **asynchronously in parallel** with sending `SIGTERM`.
1. A **`lifecycle.preStop` hook (`["sleep", "5"]`)** delays `SIGTERM` for 5 seconds while the pod is marked `Terminating` and removed from load-balancer endpoints, allowing in-flight new connections to drain.
2. Uvicorn receives `SIGTERM`, stops accepting new connections, and finishes in-flight requests up to **`--timeout-graceful-shutdown 25`**.
3. **`terminationGracePeriodSeconds: 40`** is set higher than `5 + 25 = 30s` so `SIGKILL` never fires before uvicorn finishes draining and running `lifespan` shutdown cleanup.
</details>

<details>
<summary>16. Why should a GPU inference FastAPI service run one worker per GPU and avoid tight Kubernetes CPU limits?</summary>

Each uvicorn/gunicorn worker is a **separate OS process** with its own address space; if a container runs 4 workers on 1 GPU, all 4 processes load duplicate copies of the model into VRAM and contend for CUDA contexts (causing CUDA OOMs). Run **one worker process per GPU** (or put FastAPI in front of a dedicated `vLLM`/`Triton` server). On event-loop services, tight Kubernetes `resources.limits.cpu` trigger Linux CFS quota throttling (`cpu.stat` `nr_throttled`) during bursty validation/serialization, spiking p99 tail latency—set accurate CPU `requests` and memory `limits`.
</details>

<details>
<summary>17. What do `--proxy-headers` and `--forwarded-allow-ips` do in uvicorn?</summary>

When uvicorn runs behind an Ingress controller or load balancer, the direct TCP peer IP is the proxy's internal IP and the connection is plain HTTP. Passing **`--proxy-headers --forwarded-allow-ips=<trusted-proxy-cidr>`** tells uvicorn to trust `X-Forwarded-For` and `X-Forwarded-Proto` from trusted proxies only—Never expose `--forwarded-allow-ips=*` directly to the public internet, or clients can spoof their source IP in audit logs and rate limiters.
</details>

<details>
<summary>18. How do you instrument a FastAPI service for the RED metrics method and OpenTelemetry distributed tracing?</summary>

- **RED Metrics (*Rate, Errors, Duration*):** Expose `/metrics` via `prometheus-fastapi-instrumentator` (or `starlette-exporter`) to track `http_requests_total` (by method, route template `/nodes/{id}`—never raw URLs with high-cardinality IDs—and status code), `http_request_duration_seconds_bucket` histograms, and in-flight requests, plus domain gauges/counters (active GPU jobs, tokens/sec).
- **OpenTelemetry Tracing:** Instrument with `opentelemetry-instrumentation-fastapi` and `opentelemetry-instrumentation-httpx` so incoming `traceparent` W3C headers propagate across `httpx.AsyncClient` calls to downstream microservices and export spans via OTLP.
</details>

<details>
<summary>19. How do `Idempotency-Key` headers make `POST /jobs` safe under network retries?</summary>

When a client's `POST /jobs` times out mid-flight, the client cannot tell whether the job was created before the connection dropped. By requiring the client to send a UUID in an **`Idempotency-Key` header** and storing `(idempotency_key, user_id) -> job_response` in Redis/PostgreSQL with a unique constraint, a retried `POST` with the same key returns the existing job record instead of submitting duplicate 64-GPU training jobs.
</details>

<details>
<summary>20. What is the role of `.dockerignore` and `docker-compose.yml` when packaging and testing a FastAPI application (`FA` Chapters 1 & 9)?</summary>

- **`.dockerignore`** excludes local `venv/`, `.env` secret files, `.git/`, and `__pycache__/` from `COPY . .` during `docker build`, preventing credential leaks, bloated image layers, and host-OS binary mismatches inside the container.
- **`docker-compose.yml`** defines multi-container local topologies (`api` built from `Dockerfile` on port `8080` with `env_file: .env.prod` talking over a bridge network to a `database` container backed by a named volume `data:/data/db`) for local end-to-end integration testing before deploying to Kubernetes.
</details>

## Sources and review notes

- **Sources read in full:**
  - `building-python-web-apis-with-fastapi` — Abdulazeez Abdulazeez Adeshina, *Building Python Web APIs with FastAPI*, **Chapters 1 to 9** (`Chapter 1: Getting Started with FastAPI`, `Chapter 2: Routing in FastAPI`, `Chapter 3: Response Models and Error Handling`, `Chapter 4: Templating in FastAPI`, `Chapter 5: Structuring FastAPI Applications`, `Chapter 6: Connecting to a Database`, `Chapter 7: Securing FastAPI Applications`, `Chapter 8: Testing FastAPI Applications`, and `Chapter 9: Deploying FastAPI Applications` read in full): Git/venv/pip/Docker setup, `uvicorn api:app --port 8000 --reload`, `APIRouter`, `Todo`/`TodoItem`/`TodoItems` nested models and `response_model`, `Path(..., title=..., gt=0, le=1000)` and `Query`, Swagger `/docs` and ReDoc `/redoc`, HTTP status codes and `HTTPException`, Jinja2 `Jinja2Templates` filters/macros/inheritance, Event Planner `models/events.py` (`Event`, `EventUpdate`), `models/users.py` (`User`, `UserSignIn`, `TokenResponse`), `routes/events.py`, and `routes/users.py`, SQLModel (`sqlite:///planner.db`, `create_all`, `Session`, `Depends(get_session)`) and MongoDB Beanie (`AsyncIOMotorClient`, `init_beanie`, `Database` CRUD with `PydanticObjectId` and `{"$set": des_body}`), `HashPassword` (`CryptContext` `bcrypt`), `create_access_token` / `verify_access_token` (`jwt`, `SECRET_KEY`, `expires`), `OAuth2PasswordBearer` + `Depends(authenticate)`, creator ownership `BOLA` check (`event.creator` vs `user`), `CORSMiddleware`, `pytest` + `httpx.AsyncClient` fixtures (`conftest.py`, `test_login.py`, `test_routes.py`, `coverage run -m pytest` and `coverage html`), and `.dockerignore`, `Dockerfile`, `docker-compose.yml`, and `.env.prod`.
  - `nvidia-devops` (`volume-02/04-fastapi-microservices-masterclass.md`): WSGI vs ASGI, blocking AI infrastructure API pitfalls (`async def` vs `def`), Pydantic validation at the edge, async handlers, retries, `BackgroundTasks` limits, and production Kubernetes hardening.
- **Run here:** `python3 code/part03/python_fastapi_microservices_lab.py` (4 passed, 0 failed).
- **Explicitly labelled inferences:** The Fleet API (`NodeIn`/`Node`, `JobIn`/`JobOut`), `lifespan` + `Depends` patterns, `StreamingResponse` SSE inference gateway, and Kubernetes `Deployment` probe/graceful-shutdown manifest are the author's constructions applying *Building Python Web APIs with FastAPI* and `volume-02` to AI infrastructure services (plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, and 40).
- **Not verified on live hardware:** Live `uvicorn`, `gunicorn`, `curl`, `docker`, `mongod`, `alembic`, `schemathesis`, and Kubernetes deployment commands (`0.0.0.0:8000`, `8080`, `27017`, `0.95`, `0.115`, `3333`, `9457`, `40` threads, `201`, `202`, `400`, `401`, `403`, `404`, `409`, `422`, `429`, `500`, `502`, `503`, `504`, `250m`, `256Mi`, `512Mi`, `1.4.2`) are marked (`untested here`) where not executed by `python_fastapi_microservices_lab.py`.
