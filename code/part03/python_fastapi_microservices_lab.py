#!/usr/bin/env python3
"""Self-checking lab for Chapter 3.7: Building APIs and microservices with FastAPI."""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from python_fastapi_microservices import (
    Event,
    EventPlannerRepository,
    EventUpdate,
    HashPassword,
    Todo,
    TodoItem,
    create_access_token,
    format_sse_events,
    verify_access_token,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. FA Ch. 2 & 3: Nested Todo / TodoItem models and response_model projection (excluding id)
    todos = [Todo(1, TodoItem("Read FastAPI book")), Todo(2, TodoItem("Build Fleet API"))]
    response_model_items = [t.item for t in todos]
    check(
        "Todo nested model projects to TodoItems response_model without exposing internal IDs",
        len(response_model_items) == 2 and response_model_items[0].item == "Read FastAPI book",
    )

    # 2. FA Ch. 7: Password hashing (HashPassword) and JWT create_access_token / verify_access_token
    hasher = HashPassword()
    hashed = hasher.create_hash("Stro0ng!")
    token = create_access_token("reader@packt.com", "SECRET_KEY_TEST", ttl_seconds=60.0)
    claims = verify_access_token(token, "SECRET_KEY_TEST")
    expired_token = create_access_token("reader@packt.com", "SECRET_KEY_TEST", ttl_seconds=-10.0)
    exp_raised = False
    try:
        verify_access_token(expired_token, "SECRET_KEY_TEST")
    except PermissionError:
        exp_raised = True
    check(
        "HashPassword verifies 'Stro0ng!', JWT token validates user='reader@packt.com', and expired token raises 403",
        hasher.verify_hash("Stro0ng!", hashed) is True
        and hasher.verify_hash("wrong", hashed) is False
        and claims["user"] == "reader@packt.com"
        and exp_raised is True,
    )

    # 3. FA Ch. 6-8: EventPlannerRepository CRUD + partial update + BOLA creator ownership check
    conn = sqlite3.connect(":memory:")
    repo = EventPlannerRepository(conn)
    created = repo.create(
        Event(
            id=0,
            title="FastAPI Book Launch",
            image="https://linktomyimage.com/image.png",
            description="We will be discussing the contents of the FastAPI book",
            tags=["python", "fastapi", "book", "launch"],
            location="Google Meet",
        ),
        authenticated_user="reader@packt.com",
    )
    updated = repo.update(
        created.id,
        EventUpdate(location="Hybrid", title="Packt's FastAPI book launch II"),
        authenticated_user="reader@packt.com",
    )
    bola_blocked = False
    try:
        repo.delete(created.id, authenticated_user="attacker@example.com")
    except PermissionError:
        bola_blocked = True
    del_msg = repo.delete(created.id, authenticated_user="reader@packt.com")
    check(
        "EventPlannerRepository creates, partially updates non-None fields, blocks non-creator delete (BOLA), and deletes by owner",
        created.creator == "reader@packt.com"
        and updated.location == "Hybrid"
        and updated.title == "Packt's FastAPI book launch II"
        and updated.tags == ["python", "fastapi", "book", "launch"]
        and bola_blocked is True
        and del_msg == "Event deleted successfully."
        and repo.get_all() == [],
    )

    # 4. Section 9: SSE stream framing and deduplication / termination on 'done'
    sse = format_sse_events(
        [
            {"state": "queued"},
            {"state": "queued"},
            {"state": "running"},
            {"state": "done"},
            {"state": "ignored_after_done"},
        ]
    )
    check(
        "SSE generator deduplicates consecutive identical states and stops on terminal 'done' state",
        len(sse) == 3
        and sse[0].startswith("event: state\ndata: ")
        and '"done"' in sse[-1],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
