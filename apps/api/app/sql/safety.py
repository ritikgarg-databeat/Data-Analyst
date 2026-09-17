"""Statement-level SQL safety checks shared by every engine.

Deliberately a denylist, not an allowlist: DuckDB supports SQL extensions
that don't start with SELECT (e.g. `FROM orders SELECT *`), and a strict
allowlist would either reject those or, worse, swallow a genuine typo (e.g.
"SELCT") behind a generic "not allowed" message instead of the real,
educational parser error from the engine (see docs — query errors should
show the actual engine error, never a fabricated one). So: block statements
that clearly start with a write/DDL/admin keyword, block multi-statement
stacking (which could otherwise smuggle a write statement after a read
one), and let everything else reach the engine to produce its own error.

`EXPLAIN ANALYZE <stmt>` is a special case, not just another keyword: unlike
plain `EXPLAIN` (which only prints a static plan), DuckDB's `EXPLAIN ANALYZE`
genuinely EXECUTES `<stmt>` to gather runtime profiling stats — a denylist
that only inspects the statement's leading token would never see the real
statement hiding after "EXPLAIN ANALYZE", letting any forbidden statement
(CREATE, COPY, INSERT, ...) through. This is enforced here by rejecting
`EXPLAIN ANALYZE` outright and recursively re-checking whatever follows a
plain `EXPLAIN`. This denylist is also not the only safety boundary against
this exact bypass — `DuckDBEngine._connect` additionally disables
`enable_external_access` after materializing the registered dataset tables,
so even an undiscovered bypass of this text-level check can't touch the
filesystem or persist beyond the single throwaway in-memory connection."""

import re

FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "ATTACH",
    "DETACH",
    "COPY",
    "GRANT",
    "REVOKE",
    "VACUUM",
    "SET",
    "CALL",
    "EXPORT",
    "IMPORT",
    "INSTALL",
    "LOAD",
    "MERGE",
    "PRAGMA",
    "RESET",
    "CHECKPOINT",
    "USE",
}

_EXPLAIN_PREFIX = re.compile(r"^EXPLAIN\s+", re.IGNORECASE)
_ANALYZE_PREFIX = re.compile(r"^ANALYZE\b", re.IGNORECASE)


class UnsafeQueryError(ValueError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _strip_comments(sql: str) -> str:
    """Quote-aware: `--` and `/* */` are only treated as comments OUTSIDE a
    single-quoted string literal, so a literal like '10--20 off' is never
    corrupted into an unterminated string (a real, previously-reproduced
    bug — a naive regex has no notion of quote state)."""
    result: list[str] = []
    i = 0
    n = len(sql)
    in_string = False
    while i < n:
        ch = sql[i]
        if in_string:
            result.append(ch)
            if ch == "'":
                if i + 1 < n and sql[i + 1] == "'":  # DuckDB's escaped '' inside a literal
                    result.append(sql[i + 1])
                    i += 2
                    continue
                in_string = False
            i += 1
            continue
        if ch == "'":
            in_string = True
            result.append(ch)
            i += 1
            continue
        if sql.startswith("--", i):
            newline = sql.find("\n", i)
            if newline == -1:
                break
            result.append("\n")
            i = newline + 1
            continue
        if sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def _split_statements(sql: str) -> list[str]:
    """Quote-aware split on `;` — a semicolon inside a single-quoted string
    literal is never treated as a statement separator (a real, previously-
    reproduced bug — a naive `;`-split falsely rejected a valid single
    statement like `SELECT 'a;b' AS x`)."""
    stripped = _strip_comments(sql)
    statements: list[str] = []
    current: list[str] = []
    in_string = False
    i = 0
    n = len(stripped)
    while i < n:
        ch = stripped[i]
        if in_string:
            current.append(ch)
            if ch == "'":
                if i + 1 < n and stripped[i + 1] == "'":
                    current.append(stripped[i + 1])
                    i += 2
                    continue
                in_string = False
            i += 1
            continue
        if ch == "'":
            in_string = True
            current.append(ch)
            i += 1
            continue
        if ch == ";":
            statements.append("".join(current))
            current = []
            i += 1
            continue
        current.append(ch)
        i += 1
    statements.append("".join(current))
    return [s.strip() for s in statements if s.strip()]


def _leading_keyword(statement: str) -> str:
    match = re.match(r"[A-Za-z]+", statement)
    return match.group(0).upper() if match else ""


def assert_safe_query(sql: str) -> str:
    """Returns the single validated statement, or raises UnsafeQueryError.

    Rejects empty input, multiple statements, `EXPLAIN ANALYZE` (which
    executes its wrapped statement), and any statement (or `EXPLAIN`-wrapped
    statement) starting with a write/DDL/admin keyword. Everything else
    (including malformed SQL) is passed through to the engine so its real
    parser error surfaces.
    """
    statements = _split_statements(sql)
    if not statements:
        raise UnsafeQueryError("Query is empty.")
    if len(statements) > 1:
        raise UnsafeQueryError(
            "Only a single SQL statement is allowed per execution — remove the extra statement(s)."
        )

    statement = statements[0]

    # Peel off any number of leading "EXPLAIN " wrappers, rejecting ANALYZE
    # at each level, so the real inner statement's keyword is what's finally
    # checked against FORBIDDEN_KEYWORDS below.
    remaining = statement
    while _leading_keyword(remaining) == "EXPLAIN":
        rest = _EXPLAIN_PREFIX.sub("", remaining, count=1)
        if _ANALYZE_PREFIX.match(rest):
            raise UnsafeQueryError(
                "EXPLAIN ANALYZE is not allowed in the SQL Lab — it actually executes the wrapped "
                "statement rather than just showing its plan. Use plain EXPLAIN instead."
            )
        remaining = rest

    first_word = _leading_keyword(remaining)
    if first_word in FORBIDDEN_KEYWORDS:
        raise UnsafeQueryError(
            f"'{first_word}' statements are not allowed in the SQL Lab — it's read-only. "
            "Write a SELECT query instead."
        )

    return statement
