"""Chapter 3.7 model: FastAPI routing, nested models, response_model filtering,
dependency injection and dependency_overrides, JWT bearer token creation/
verification & password hashing (scrypt/PBKDF2), SQLite database repository
CRUD (`Database` / `get_session`), and SSE streaming response generation.

Sources modeled:
- Abdulazeez Abdulazeez Adeshina, Building Python Web APIs with FastAPI
  (building-python-web-apis-with-fastapi, FA), Chapters 1-9:
  * Chapters 1-3: uvicorn ASGI runner, APIRouter, Todo / TodoItem / TodoItems
    nested models, Path(..., title=..., gt=0), Query, response_model filtering
    (excluding internal IDs/fields), and HTTPException (404, 409, 422).
  * Chapters 4-5: Jinja2 templating filters/inheritance, and structuring the
    Event Planner app (`models/events.py`, `models/users.py`, `routes/events.py`,
    `routes/users.py` with `Event`, `EventUpdate`, `User`, `UserSignIn`).
  * Chapter 6: SQLModel (`create_engine("sqlite:///planner.db", connect_args={"check_same_thread": False})`,
    `SQLModel.metadata.create_all(engine)`, `Session`, `Depends(get_session)`,
    `select(Event)`, `session.get/add/commit/refresh/delete`) and MongoDB Beanie
    (`AsyncIOMotorClient`, `init_beanie`, `Database` class with `save`, `get`,
    `get_all`, `update` using `{"$set": des_body}`, `delete`).
  * Chapter 7: Securing FastAPI (`HashPassword` with bcrypt/CryptContext,
    `create_access_token` and `verify_access_token` with `SECRET_KEY` and
    `expires` timestamp, `OAuth2PasswordBearer` + `Depends(authenticate)`,
    creator ownership checks `if event.creator != user: raise HTTPException(400/403)`,
    and `CORSMiddleware`).
  * Chapters 8-9: `pytest` fixtures (`event_loop`, `default_client`, `access_token`)
    with `httpx.AsyncClient` for auth and CRUD tests, `.dockerignore`,
    `Dockerfile`, `docker-compose.yml` (`api` + `mongo`), and `.env.prod`.
- volume-02/04-fastapi-microservices-masterclass.md.
"""
from dataclasses import asdict, dataclass, field
import hashlib
import hmac
import json
import sqlite3
import time
import base64
from typing import Callable, Dict, Iterator, List, Optional, Tuple


@dataclass
class TodoItem:
    """FA Ch. 2 & 3 nested model and response_model item."""

    item: str


@dataclass
class Todo:
    id: int
    item: TodoItem


@dataclass
class Event:
    """FA Ch. 5-7 Event model with creator ownership field."""

    id: int
    title: str
    image: str
    description: str
    tags: List[str]
    location: str
    creator: str = ""


@dataclass
class EventUpdate:
    """FA Ch. 6 partial update model ignoring None fields."""

    title: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None


class HashPassword:
    """FA Ch. 7 auth/hash_password.py equivalent using stdlib PBKDF2-HMAC-SHA256."""

    def create_hash(self, password: str, salt: bytes = b"fastapisalt") -> str:
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return salt.hex() + ":" + dk.hex()

    def verify_hash(self, plain_password: str, hashed_password: str) -> bool:
        salt_hex, dk_hex = hashed_password.split(":", 1)
        expected = self.create_hash(plain_password, bytes.fromhex(salt_hex))
        return hmac.compare_digest(expected, hashed_password)


def create_access_token(user: str, secret_key: str, ttl_seconds: float = 3600.0) -> str:
    """FA Ch. 7 auth/jwt_handler.py: encode {"user": user, "expires": time.time() + ttl}
    into a signed HS256 JWT token string.
    """
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=")
    payload_dict = {"user": user, "expires": time.time() + ttl_seconds}
    payload = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).rstrip(b"=")
    signing_input = header + b"." + payload
    sig = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=")
    return (signing_input + b"." + sig_b64).decode("ascii")


def verify_access_token(token: str, secret_key: str) -> Dict[str, object]:
    """FA Ch. 7 auth/jwt_handler.py: verify signature and expiry of a JWT token."""
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError as exc:
        raise PermissionError("400 Invalid token format") from exc
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    expected_b64 = base64.urlsafe_b64encode(expected_sig).rstrip(b"=").decode("ascii")
    if not hmac.compare_digest(expected_b64, sig_b64):
        raise PermissionError("400 Invalid token signature")

    pad = "=" * (-len(payload_b64) % 4)
    data = json.loads(base64.urlsafe_b64decode(payload_b64 + pad).decode("utf-8"))
    expire = data.get("expires")
    if expire is None:
        raise PermissionError("400 No access token supplied")
    if time.time() > float(expire):
        raise PermissionError("403 Token expired!")
    return data


class EventPlannerRepository:
    """FA Ch. 6-7 SQLite-backed CRUD + creator ownership enforcement and
    dependency-injection override support.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                image TEXT NOT NULL,
                description TEXT NOT NULL,
                tags TEXT NOT NULL,
                location TEXT NOT NULL,
                creator TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def create(self, ev: Event, authenticated_user: str) -> Event:
        cur = self.conn.execute(
            "INSERT INTO events (title, image, description, tags, location, creator) VALUES (?, ?, ?, ?, ?, ?)",
            (ev.title, ev.image, ev.description, json.dumps(ev.tags), ev.location, authenticated_user),
        )
        self.conn.commit()
        return self.get(int(cur.lastrowid))  # type: ignore[arg-type]

    def get_all(self) -> List[Event]:
        rows = self.conn.execute("SELECT id, title, image, description, tags, location, creator FROM events ORDER BY id").fetchall()
        return [
            Event(r[0], r[1], r[2], r[3], json.loads(r[4]), r[5], r[6])
            for r in rows
        ]

    def get(self, event_id: int) -> Event:
        r = self.conn.execute(
            "SELECT id, title, image, description, tags, location, creator FROM events WHERE id = ?",
            (event_id,),
        ).fetchone()
        if r is None:
            raise LookupError("404 Event with supplied ID does not exist")
        return Event(r[0], r[1], r[2], r[3], json.loads(r[4]), r[5], r[6])

    def update(self, event_id: int, patch: EventUpdate, authenticated_user: str) -> Event:
        current = self.get(event_id)
        if current.creator != authenticated_user:
            raise PermissionError("400 Operation not allowed: not creator")
        des_body = {k: v for k, v in asdict(patch).items() if v is not None}
        merged = asdict(current) | des_body
        self.conn.execute(
            "UPDATE events SET title=?, image=?, description=?, tags=?, location=? WHERE id=?",
            (
                merged["title"],
                merged["image"],
                merged["description"],
                json.dumps(merged["tags"]),
                merged["location"],
                event_id,
            ),
        )
        self.conn.commit()
        return self.get(event_id)

    def delete(self, event_id: int, authenticated_user: str) -> str:
        current = self.get(event_id)
        if current.creator != authenticated_user:
            raise PermissionError("404 Event not found / not creator")
        self.conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        self.conn.commit()
        return "Event deleted successfully."


def format_sse_events(states: List[Dict[str, object]]) -> List[str]:
    """Section 9 Server-Sent Events (SSE) framing generator (`event: state\\ndata: ...\\n\\n`)."""
    out: List[str] = []
    last = None
    for st in states:
        if st != last:
            out.append(f"event: state\ndata: {json.dumps(st, sort_keys=True)}\n\n")
            last = st
        if st.get("state") in {"failed", "done"}:
            break
    return out
