"""In-memory study store with TTL, session binding and limits (accepted loss on restart)."""
from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field

MAX_STUDIES = 100
TTL_SECONDS = 1800
CHALLENGE_TTL = 10
ANALYSES_PER_SESSION_PER_10MIN = 5
SURVEYS_PER_SESSION_PER_10MIN = 30  # surveys are cheaper, coarser and labelled unconfirmed; enough for one full plate of 24 slots


@dataclass
class Study:
    id: str
    session: str
    address: str
    block: str
    storey: int
    created: float
    touched: float
    state: str = "created"  # created | placed | needs_confirmation | ready | analysing | analysed
    placement: dict | None = None
    placement_revision: int = 0
    confirmed_revision: int | None = None
    challenge: tuple[str, float, int] | None = None  # (token, expires, revision)
    result: dict | None = None
    scene_glb: bytes | None = None
    exports: dict = field(default_factory=dict)
    error: str | None = None


class Store:
    def __init__(self):
        self._lock = threading.Lock()
        self._studies: dict[str, Study] = {}
        self._analysis_log: dict[str, list[float]] = {}
        self._survey_log: dict[str, list[float]] = {}

    def _sweep(self):
        now = time.time()
        dead = [k for k, s in self._studies.items() if now - s.touched > TTL_SECONDS]
        for k in dead:
            del self._studies[k]

    def create(self, session: str, address: str, block: str, storey: int) -> Study:
        with self._lock:
            self._sweep()
            if len(self._studies) >= MAX_STUDIES:
                oldest = min(self._studies.values(), key=lambda s: s.touched)
                del self._studies[oldest.id]
            sid = secrets.token_urlsafe(12)
            now = time.time()
            st = Study(id=sid, session=session, address=address, block=block, storey=storey, created=now, touched=now)
            self._studies[sid] = st
            return st

    def get(self, sid: str, session: str) -> Study | None:
        with self._lock:
            self._sweep()
            st = self._studies.get(sid)
            if st is None:
                return None
            if st.session != session:
                return "forbidden"  # type: ignore[return-value]
            st.touched = time.time()
            return st

    def allow_analysis(self, session: str) -> bool:
        return self._allow(self._analysis_log, session, ANALYSES_PER_SESSION_PER_10MIN)[0]

    def allow_survey(self, session: str) -> tuple[bool, int, int]:
        """(allowed, remaining after this call, seconds until the oldest entry expires)."""
        return self._allow(self._survey_log, session, SURVEYS_PER_SESSION_PER_10MIN)

    def _allow(self, book: dict[str, list[float]], session: str, limit: int) -> tuple[bool, int, int]:
        with self._lock:
            now = time.time()
            log = [t for t in book.get(session, []) if now - t < 600]
            reset = int(600 - (now - log[0])) + 1 if log else 0
            if len(log) >= limit:
                book[session] = log
                return False, 0, reset
            log.append(now)
            book[session] = log
            return True, limit - len(log), reset

    def count(self) -> int:
        with self._lock:
            return len(self._studies)
