"""SQLite persistence. Money is stored as decimal strings, never floats."""
from __future__ import annotations

import sqlite3
import threading
from decimal import Decimal

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
  id TEXT PRIMARY KEY, holder_name TEXT NOT NULL, home_currency TEXT NOT NULL,
  reserve_min TEXT NOT NULL, institution TEXT);
CREATE TABLE IF NOT EXISTS balances (
  account_id TEXT NOT NULL REFERENCES accounts(id), currency TEXT NOT NULL, amount TEXT NOT NULL,
  PRIMARY KEY (account_id, currency));
CREATE TABLE IF NOT EXISTS beneficiaries (
  id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), name TEXT NOT NULL,
  currency TEXT NOT NULL, account_number_masked TEXT, country TEXT, kind TEXT,
  blocked INTEGER NOT NULL DEFAULT 0, blocked_reason TEXT, simulate_failure TEXT);
CREATE TABLE IF NOT EXISTS transfers (
  id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), beneficiary_id TEXT,
  provider_id TEXT NOT NULL, idempotency_key TEXT NOT NULL, status TEXT NOT NULL,
  quote_json TEXT, risk_json TEXT, memo TEXT, memo_flagged INTEGER NOT NULL DEFAULT 0,
  due_date TEXT NOT NULL, quote_expires_at TEXT NOT NULL, amount_usd_equiv TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, executed_at TEXT, provider_reference TEXT,
  failure_reason TEXT, created_by TEXT NOT NULL, approved_by TEXT,
  UNIQUE (account_id, idempotency_key));
CREATE TABLE IF NOT EXISTS audit_log (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL,
  tier INTEGER NOT NULL, account_id TEXT, entity_type TEXT, entity_id TEXT,
  payload_json TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
"""

TRANSFER_COLUMNS = (
    "id", "account_id", "beneficiary_id", "provider_id", "idempotency_key", "status", "quote_json", "risk_json",
    "memo", "memo_flagged", "due_date", "quote_expires_at", "amount_usd_equiv", "created_at", "updated_at",
    "executed_at", "provider_reference", "failure_reason", "created_by", "approved_by",
)


class InsufficientFunds(Exception):
    pass


class Database:
    def __init__(self, path: str):
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        with self.lock:
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.executescript(SCHEMA)

    # -- generic helpers -------------------------------------------------
    def _rows(self, sql: str, params=()) -> list[dict]:
        with self.lock:
            return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def _one(self, sql: str, params=()) -> dict | None:
        rows = self._rows(sql, params)
        return rows[0] if rows else None

    def raw_execute(self, sql: str, params=()) -> None:
        """Test-only hook (used to simulate tampering with the audit log)."""
        with self.lock:
            self._conn.execute(sql, params)

    # -- seed ------------------------------------------------------------
    def is_seeded(self) -> bool:
        return self._one("SELECT COUNT(*) AS n FROM accounts")["n"] > 0

    def seed(self, data: dict) -> None:
        with self.lock:
            self._conn.execute("BEGIN")
            try:
                for a in data["accounts"]:
                    self._conn.execute("INSERT INTO accounts VALUES (?,?,?,?,?)",
                                       (a["id"], a["holder_name"], a["home_currency"], a["reserve_min"], a.get("institution")))
                for b in data["balances"]:
                    self._conn.execute("INSERT INTO balances VALUES (?,?,?)", (b["account_id"], b["currency"], b["amount"]))
                for b in data["beneficiaries"]:
                    self._conn.execute(
                        "INSERT INTO beneficiaries VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (b["id"], b["account_id"], b["name"], b["currency"], b.get("account_number_masked"),
                         b.get("country"), b.get("kind"), int(b.get("blocked", 0)), b.get("blocked_reason"),
                         b.get("simulate_failure")))
                self._conn.execute("COMMIT")
            except Exception:
                self._conn.execute("ROLLBACK")
                raise

    # -- accounts --------------------------------------------------------
    def get_account(self, account_id: str) -> dict | None:
        return self._one("SELECT * FROM accounts WHERE id=?", (account_id,))

    def get_balances(self, account_id: str) -> list[dict]:
        return self._rows("SELECT currency, amount FROM balances WHERE account_id=? ORDER BY currency", (account_id,))

    def list_beneficiaries(self, account_id: str) -> list[dict]:
        return self._rows("SELECT * FROM beneficiaries WHERE account_id=? ORDER BY id", (account_id,))

    def get_beneficiary(self, account_id: str, beneficiary_id: str | None) -> dict | None:
        if not beneficiary_id:
            return None
        return self._one("SELECT * FROM beneficiaries WHERE account_id=? AND id=?", (account_id, beneficiary_id))

    # -- transfers -------------------------------------------------------
    def insert_transfer(self, row: dict) -> None:
        cols = ", ".join(TRANSFER_COLUMNS)
        marks = ", ".join("?" for _ in TRANSFER_COLUMNS)
        with self.lock:
            self._conn.execute(f"INSERT INTO transfers ({cols}) VALUES ({marks})",
                               tuple(row.get(c) for c in TRANSFER_COLUMNS))

    def get_transfer(self, transfer_id: str) -> dict | None:
        return self._one("SELECT * FROM transfers WHERE id=?", (transfer_id,))

    def get_transfer_by_idempotency(self, account_id: str, key: str) -> dict | None:
        return self._one("SELECT * FROM transfers WHERE account_id=? AND idempotency_key=?", (account_id, key))

    def list_transfers(self, account_id: str) -> list[dict]:
        return self._rows("SELECT * FROM transfers WHERE account_id=? ORDER BY created_at DESC, id DESC", (account_id,))

    def _update_transfer_nolock(self, transfer_id: str, **fields) -> None:
        bad = set(fields) - set(TRANSFER_COLUMNS)
        if bad:
            raise ValueError(f"Unknown transfer columns: {bad}")
        sets = ", ".join(f"{k}=?" for k in fields)
        self._conn.execute(f"UPDATE transfers SET {sets} WHERE id=?", (*fields.values(), transfer_id))

    def update_transfer(self, transfer_id: str, **fields) -> None:
        with self.lock:
            self._update_transfer_nolock(transfer_id, **fields)

    def daily_executed_usd(self, account_id: str, day_iso: str) -> Decimal:
        rows = self._rows(
            "SELECT amount_usd_equiv FROM transfers WHERE account_id=? AND status='EXECUTED_SIMULATED' "
            "AND substr(executed_at,1,10)=?", (account_id, day_iso))
        return sum((Decimal(r["amount_usd_equiv"]) for r in rows), Decimal(0))

    def debit_and_mark_executed(self, transfer_id: str, account_id: str, currency: str, amount: Decimal, **fields) -> None:
        """Atomic: debit balance and mark executed in one transaction; refuses if funds are short."""
        with self.lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                row = self._conn.execute("SELECT amount FROM balances WHERE account_id=? AND currency=?",
                                         (account_id, currency)).fetchone()
                current = Decimal(row["amount"]) if row else Decimal(0)
                if current < amount:
                    raise InsufficientFunds(f"Balance {current} {currency} is below {amount} {currency}")
                self._conn.execute("UPDATE balances SET amount=? WHERE account_id=? AND currency=?",
                                   (format(current - amount, "f"), account_id, currency))
                self._update_transfer_nolock(transfer_id, **fields)
                self._conn.execute("COMMIT")
            except Exception:
                self._conn.execute("ROLLBACK")
                raise

    # -- audit -----------------------------------------------------------
    def audit_last_hash(self) -> str | None:
        row = self._one("SELECT hash FROM audit_log ORDER BY seq DESC LIMIT 1")
        return row["hash"] if row else None

    def audit_insert(self, e: dict) -> int:
        with self.lock:
            cur = self._conn.execute(
                "INSERT INTO audit_log (ts, actor, action, tier, account_id, entity_type, entity_id, payload_json, prev_hash, hash) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (e["ts"], e["actor"], e["action"], e["tier"], e["account_id"], e["entity_type"], e["entity_id"],
                 e["payload_json"], e["prev_hash"], e["hash"]))
            return int(cur.lastrowid)

    def audit_all(self, account_id: str | None = None) -> list[dict]:
        if account_id is None:
            return self._rows("SELECT * FROM audit_log ORDER BY seq")
        return self._rows("SELECT * FROM audit_log WHERE account_id=? ORDER BY seq", (account_id,))
