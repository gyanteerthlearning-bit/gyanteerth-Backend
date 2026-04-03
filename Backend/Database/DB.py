from sqlalchemy import create_engine, Column, Integer, String, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool
import socket
import time
import os

# ── Force IPv4-only DNS resolution ───────────────────────────────────────────
# Vercel's serverless runtime (AWS Lambda) cannot open outbound IPv6 sockets.
# Supabase's direct DB host resolves to an IPv6 address, which causes
# "Cannot assign requested address". This patch makes getaddrinfo always
# request AF_INET (IPv4), so psycopg2 only ever tries IPv4 addresses.
_orig_getaddrinfo = socket.getaddrinfo
def _force_ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _force_ipv4_getaddrinfo
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv()
db_url = os.getenv("DATABASE_URL")

if not db_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Please add it in Vercel Project Settings → Environment Variables."
    )

DB_URL = db_url
engine = create_engine(
    DB_URL,
    poolclass=NullPool,           # REQUIRED for Vercel serverless — no persistent connections
    connect_args={
        "connect_timeout": 10,    # fail fast instead of hanging
        "gssencmode": "disable",  # prevents IPv6/GSSAPI negotiation that fails on Vercel
        "sslmode": "require",     # Supabase requires SSL
    },
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

query_times = []

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    query_times.append(total)
