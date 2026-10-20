"""Explicit, offline SQLite document migration.

Stop API writers and make a verified SQLite backup before applying (use SQLite's
backup API or ``sqlite3 database.db '.backup backup.db'``, not a live file copy).
The default is a read-only preflight. No startup code calls this module.
NULL format settings are rejected: recover the intended settings explicitly.
Numeric codes must be recovered from an authoritative source into a TEXT column;
casting an integer cannot recover leading zeroes already discarded by SQLite.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

from sqlalchemy import Integer, MetaData, Text
from sqlalchemy.dialects.sqlite import dialect
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateTable

from document_issue.enums import DocumentTypeEnum
from document_issue.document import Document as DomainDocument, FormatConfiguration
from document_issue_api.models import Document


class MigrationError(ValueError):
    """A database needs operator attention before it can be migrated."""


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _normalized(sql: str) -> str:
    # Only compare against generated, simple ORM DDL, not arbitrary parsed SQL.
    sql = re.sub(r'[\s"`\[\]]', "", sql).rstrip(";").upper()
    prefix, _, body = sql.partition("(")
    depth = 0
    parts = []
    start = 0
    for position, character in enumerate(body):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        elif character == "," and depth == 0:
            parts.append(body[start:position])
            start = position + 1
    # SQLAlchemy stores constraints in a set, so their DDL order can vary.
    # Column copying below always uses explicit names rather than column order.
    parts.append(body[start:-1] if body.endswith(")") else body[start:])
    return prefix + "(" + ",".join(sorted(parts)) + ")"


def _target():
    table = Document.__table__.to_metadata(MetaData())
    # Refuse to run with the old application model.
    if "document_type" not in table.c:
        raise MigrationError("Install the updated document ORM before migrating.")
    return table


def _ddl(table, name: str | None = None) -> str:
    # Resolve the foreign-key target without creating or modifying that table.
    metadata = table.metadata
    if "project" not in metadata.tables:
        Document.__table__.metadata.tables["project"].to_metadata(metadata)
    sql = str(CreateTable(table).compile(dialect=dialect()))
    if name:
        sql = sql.replace("CREATE TABLE document", f"CREATE TABLE {_quote(name)}", 1)
    return sql


def _preflight(connection: sqlite3.Connection, document_type: str | None):
    choices = {item.value for item in DocumentTypeEnum}
    if document_type is not None and document_type not in choices:
        raise MigrationError(f"Invalid document type; choose one of {sorted(choices)!r}.")
    target = _target()
    source_sql = connection.execute(
        "SELECT sql FROM sqlite_schema WHERE type='table' AND name='document'"
    ).fetchone()
    if source_sql is None:
        raise MigrationError("No document table found; this command only migrates existing databases.")
    columns = connection.execute("PRAGMA table_xinfo(document)").fetchall()
    names = [row[1] for row in columns]
    expected = set(target.c.keys())
    if set(names) not in (expected, expected - {"document_type"}):
        raise MigrationError("Unsupported document columns; custom schema needs a reviewed manual migration.")
    if any(row[6] for row in columns):
        raise MigrationError("Generated/hidden document columns require a manual migration.")

    # Accept only the known ORM shape, with the legacy code affinity and
    # nullability. Refuse custom constraints/defaults/collations/table options.
    source = target.to_metadata(MetaData())
    if "document_type" not in names:
        source._columns.remove(source.c.document_type)
    for _, name, declared_type, not_null, default, primary_key, _ in columns:
        column = source.c[name]
        if name in {
            "project_id", "document_code", "document_type", "date_string_format",
            "output_author", "output_checked_by",
        }:
            column.nullable = not bool(not_null)
        if name == "document_code" and declared_type.upper() == "INTEGER":
            column.type = Integer()
        elif name == "document_code" and declared_type.upper() == "TEXT":
            column.type = Text()
        if default is not None or bool(column.primary_key) != bool(primary_key):
            raise MigrationError("Unsupported document defaults or primary key; migrate manually.")
    if _normalized(source_sql[0]) != _normalized(_ddl(source)):
        raise MigrationError("Unsupported document table DDL; custom schema requires a reviewed manual migration.")
    dependencies = connection.execute(
        "SELECT type, name FROM sqlite_schema WHERE "
        "(type='trigger' AND tbl_name='document') OR type='view'"
    ).fetchall()
    if dependencies:
        raise MigrationError(f"Review custom triggers/views before migration: {dependencies!r}.")
    if connection.execute("PRAGMA foreign_key_check").fetchone():
        raise MigrationError("Existing foreign-key violations must be repaired before migration.")
    if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise MigrationError("SQLite integrity check failed; restore or repair the database first.")
    required = (
        "document_code", "project_id", "date_string_format",
        "output_author", "output_checked_by",
    )
    for name in required:
        bad = connection.execute(
            f"SELECT id FROM document WHERE {_quote(name)} IS NULL LIMIT 1"
        ).fetchone()
        if bad:
            raise MigrationError(f"Document {bad[0]} has NULL {name}; supply the intended value explicitly.")
    bad = connection.execute(
        "SELECT id, typeof(document_code) FROM document WHERE typeof(document_code) != 'text' LIMIT 1"
    ).fetchone()
    if bad:
        raise MigrationError(
            f"Document {bad[0]} has a stored {bad[1]} code. Leading zeros cannot be recovered. "
            "Restore identifiers from an authoritative source into a TEXT column in a backed-up "
            "database; do not blindly cast numeric codes."
        )
    for name in ("output_author", "output_checked_by"):
        if connection.execute(
            f"SELECT id FROM document WHERE typeof({_quote(name)}) != 'integer' "
            f"OR {_quote(name)} NOT IN (0, 1) LIMIT 1"
        ).fetchone():
            raise MigrationError(f"Invalid {name}; expected Boolean 0 or 1.")
    if connection.execute(
        "SELECT id FROM document WHERE typeof(date_string_format) != 'text' LIMIT 1"
    ).fetchone():
        raise MigrationError("date_string_format must contain text.")
    if connection.execute(
        "SELECT project_id, document_code FROM document "
        "GROUP BY project_id, document_code HAVING COUNT(*) > 1 LIMIT 1"
    ).fetchone():
        raise MigrationError("Duplicate (project_id, document_code); resolve identifiers explicitly.")
    if "document_type" in names:
        placeholders = ",".join("?" for _ in choices)
        if connection.execute(
            f"SELECT id FROM document WHERE document_type IS NULL "
            f"OR document_type NOT IN ({placeholders}) LIMIT 1", tuple(choices),
        ).fetchone():
            raise MigrationError("Invalid or NULL existing document_type; repair explicitly, not via backfill.")
    elif connection.execute("SELECT 1 FROM document LIMIT 1").fetchone() and document_type is None:
        raise MigrationError("Legacy rows need an explicit --document-type backfill value.")
    # A successful migration must not leave document reads failing domain validation.
    # Validate, but never silently replace stored values with model defaults.
    for values in connection.execute(f"SELECT {', '.join(_quote(name) for name in names)} FROM document"):
        stored = dict(zip(names, values, strict=True))
        data = {
            name: stored.get(name) for name in DomainDocument.model_fields
            if name != "format_configuration"
        }
        if "document_type" not in names:
            data["document_type"] = document_type
        data["format_configuration"] = {
            name: stored[name] for name in FormatConfiguration.model_fields
        }
        try:
            data["notes"] = json.loads(stored["notes"]) if stored["notes"] is not None else None
            DomainDocument.model_validate(data)
        except (TypeError, ValueError) as exc:
            raise MigrationError(
                f"Document {stored['id']} fails domain validation; repair its metadata explicitly: {exc}"
            ) from exc
    indexes = connection.execute(
        "SELECT sql FROM sqlite_schema WHERE type='index' AND tbl_name='document' AND sql IS NOT NULL"
    ).fetchall()
    return target, names, indexes, _normalized(source_sql[0]) == _normalized(_ddl(target))


def migrate(database_url: str, *, document_type: str | None = None, apply: bool = False,
            backup_confirmed: bool = False) -> str:
    """Preflight, or atomically rebuild only document; return the action taken.

    Applying requires an explicit acknowledgment of an operator-created backup.
    All original explicit indexes are recreated; unsupported schema is rejected.
    """
    url = make_url(database_url)
    if (
        url.drivername != "sqlite" or not url.database or url.database == ":memory:" or url.query
        or url.host or url.username or url.password or url.port
    ):
        raise MigrationError("Only file-backed sqlite:/// URLs without query options are supported.")
    path = Path(url.database).resolve()
    if not path.is_file():
        raise MigrationError(f"Database does not exist: {path}")
    if apply and not backup_confirmed:
        raise MigrationError("Stop writers and make a verified SQLite backup, then pass --backup-confirmed.")
    uri = path.as_uri() + ("?mode=rw" if apply else "?mode=ro")
    connection = sqlite3.connect(uri, uri=True, isolation_level=None)
    try:
        # Must be changed outside the transaction. This is a dedicated connection;
        # disabling FK enforcement prevents DROP TABLE cascading into children.
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("BEGIN IMMEDIATE" if apply else "BEGIN")
        table, names, indexes, current = _preflight(connection, document_type)
        if current:
            connection.rollback()
            return "Already current; no changes."
        if not apply:
            connection.rollback()
            return "Preflight passed; no changes. Back up the database, then use --apply --backup-confirmed."
        temporary = "_document_migration"
        if connection.execute("SELECT 1 FROM sqlite_schema WHERE name=?", (temporary,)).fetchone():
            raise MigrationError(f"Temporary name {temporary} already exists; investigate before retrying.")
        connection.execute(_ddl(table, temporary))
        destination = ", ".join(_quote(name) for name in table.c.keys())
        expressions = ", ".join(_quote(name) if name in names else "?" for name in table.c.keys())
        parameters = () if "document_type" in names else (document_type,)
        connection.execute(
            f"INSERT INTO {_quote(temporary)} ({destination}) SELECT {expressions} FROM document",
            parameters,
        )
        connection.execute("DROP TABLE document")
        connection.execute(f"ALTER TABLE {_quote(temporary)} RENAME TO document")
        for (sql,) in indexes:
            connection.execute(sql)
        if connection.execute("PRAGMA foreign_key_check").fetchone():
            raise MigrationError("Foreign-key verification failed; migration rolled back.")
        connection.commit()
        return "Migration applied; document IDs, relationships, other tables and explicit indexes preserved."
    except (sqlite3.Error, MigrationError) as exc:
        connection.rollback()
        if isinstance(exc, MigrationError):
            raise
        raise MigrationError(f"SQLite migration failed; no changes committed: {exc}") from exc
    finally:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--document-type", choices=[item.value for item in DocumentTypeEnum])
    parser.add_argument("--apply", action="store_true", help="Apply after a successful preflight (default: dry-run).")
    parser.add_argument("--backup-confirmed", action="store_true", help="Acknowledge a verified backup and stopped writers.")
    args = parser.parse_args()
    try:
        print(migrate(args.database_url, document_type=args.document_type, apply=args.apply,
                      backup_confirmed=args.backup_confirmed))
    except (MigrationError, ValueError) as exc:
        parser.exit(2, f"Migration refused: {exc}\n")


if __name__ == "__main__":
    main()
