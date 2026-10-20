"""Migration tests use disposable SQLite databases only, never app.db."""

import os
import re
import sqlite3
import subprocess
import sys

import pytest
from sqlalchemy import Integer, MetaData, create_engine
from sqlalchemy.orm import Session

from document_issue.enums import DocumentTypeEnum
from document_issue_api import migrate as migration_module
from document_issue_api.migrate import MigrationError, migrate
from document_issue_api.models import Base, Document


TYPE = next(iter(DocumentTypeEnum)).value


@pytest.fixture
def legacy(tmp_path):
    path = tmp_path / "legacy.sqlite"
    url = f"sqlite:///{path}"
    metadata = MetaData()
    for table in Base.metadata.sorted_tables:
        table.to_metadata(metadata)
    document = metadata.tables["document"]
    document._columns.remove(document.c.document_type)
    document.c.document_code.type = Integer()
    for name in ("project_id", "document_code", "date_string_format", "output_author", "output_checked_by"):
        document.c[name].nullable = True
    engine = create_engine(url)
    metadata.create_all(engine)
    engine.dispose()
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO project (id, project_number, project_name) VALUES (7, 42, 'Migration project')")
        db.execute("INSERT INTO role (id, role_name) VALUES (8, 'Checker')")
        db.execute(
            "INSERT INTO document "
            "(id, project_id, document_code, date_string_format, output_author, output_checked_by, notes, "
            "name_nomenclature, document_description, document_source, paper_size, scale, originator) "
            "VALUES (11, 7, 'A-001', '%Y-%m-%d', 1, 0, '[\"preserved\"]', "
            "'originator-number', 'Description', 'DS', 'A4', 'nts', 'Max Fordham LLP')"
        )
        db.execute("INSERT INTO issue (id, document_id, revision) VALUES (12, 11, 'P01')")
        db.execute("INSERT INTO document_role (document_id, role_id) VALUES (11, 8)")
        db.execute("CREATE INDEX custom_document_description ON document(document_description)")
    return path, url


def snapshot(path):
    with sqlite3.connect(path) as db:
        return "\n".join(db.iterdump())


def test_dry_run_apply_preserves_relationships_and_is_idempotent(legacy, client, monkeypatch):
    path, url = legacy
    before = snapshot(path)
    assert "no changes" in migrate(url, document_type=TYPE)
    assert snapshot(path) == before
    assert "applied" in migrate(url, document_type=TYPE, apply=True, backup_confirmed=True)
    after = snapshot(path)
    assert "Already current" in migrate(url, apply=True, backup_confirmed=True)
    assert snapshot(path) == after
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert db.execute("SELECT id, document_id, revision FROM issue").fetchall() == [(12, 11, "P01")]
        assert db.execute("SELECT * FROM document_role").fetchall() == [(11, 8)]
        assert db.execute("SELECT id, document_code, document_type FROM document").fetchall() == [(11, "A-001", TYPE)]
        assert db.execute(
            "SELECT 1 FROM sqlite_schema WHERE name='custom_document_description'"
        ).fetchone()
        info = {row[1]: row for row in db.execute("PRAGMA table_info(document)")}
        assert info["document_code"][2] == "VARCHAR"
        for name in ("project_id", "document_code", "document_type", "date_string_format",
                     "output_author", "output_checked_by"):
            assert info[name][3] == 1
    from document_issue_api import database
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(url, connect_args={"check_same_thread": False})
    monkeypatch.setattr(database, "create_session", sessionmaker(bind=engine))
    response = client.get("/document/11")
    assert response.status_code == 200, response.text
    assert response.json()["notes"] == ["preserved"]
    assert response.json()["document_name"] == "A-001"
    engine.dispose()


def test_full_document_fields_and_text_codes(legacy):
    _, url = legacy
    migrate(url, document_type=TYPE, apply=True, backup_confirmed=True)
    engine = create_engine(url)
    with Session(engine) as session:
        item = Document(
            id=20, project_id=7, document_code="000123", document_type=TYPE,
            name_nomenclature="custom", document_description="Description",
            document_source="source.xlsx", paper_size="A3", scale="1:50",
            notes=["note"], originator="ORG", date_string_format="%d/%m/%Y",
            output_author=False, output_checked_by=True,
        )
        session.add(item)
        session.commit()
        session.expire_all()
        saved = session.get(Document, 20)
        for key, value in {
            "document_code": "000123", "document_type": TYPE, "name_nomenclature": "custom",
            "document_description": "Description", "document_source": "source.xlsx",
            "paper_size": "A3", "scale": "1:50", "notes": ["note"], "originator": "ORG",
            "date_string_format": "%d/%m/%Y", "output_author": False, "output_checked_by": True,
        }.items():
            assert getattr(saved, key) == value
    engine.dispose()


@pytest.mark.parametrize(("assignment", "message"), [
    ("document_code=123", "Leading zeros"),
    ("document_code=1.5", "Leading zeros"),
    ("document_code=NULL", "NULL document_code"),
    ("project_id=NULL", "NULL project_id"),
    ("date_string_format=NULL", "NULL date_string_format"),
    ("output_author=NULL", "NULL output_author"),
    ("output_checked_by=2", "Invalid output_checked_by"),
    ("project_id=999", "foreign-key"),
    ("document_description=NULL", "domain validation"),
    ("notes='not json'", "domain validation"),
    ("originator='Unknown'", "domain validation"),
])
def test_invalid_rows_unchanged(legacy, assignment, message):
    path, url = legacy
    with sqlite3.connect(path) as db:
        db.execute(f"UPDATE document SET {assignment}")
    before = snapshot(path)
    with pytest.raises(MigrationError, match=message):
        migrate(url, document_type=TYPE, apply=True, backup_confirmed=True)
    assert snapshot(path) == before


def test_explicit_backfill_and_backup_required(legacy):
    path, url = legacy
    before = snapshot(path)
    with pytest.raises(MigrationError, match="explicit --document-type"):
        migrate(url)
    with pytest.raises(MigrationError, match="backup"):
        migrate(url, document_type=TYPE, apply=True)
    with pytest.raises(MigrationError, match="Invalid document type"):
        migrate(url, document_type="guess")
    assert snapshot(path) == before


def test_custom_schema_refused_without_changes(legacy):
    path, url = legacy
    with sqlite3.connect(path) as db:
        db.execute("ALTER TABLE document ADD COLUMN custom TEXT")
    before = snapshot(path)
    with pytest.raises(MigrationError, match="custom schema"):
        migrate(url, document_type=TYPE, apply=True, backup_confirmed=True)
    assert snapshot(path) == before


def test_duplicate_rows_refused_without_changes(legacy):
    path, url = legacy
    # Simulate an older/custom database missing its unique constraint.
    with sqlite3.connect(path) as db:
        ddl = db.execute("SELECT sql FROM sqlite_schema WHERE name='document'").fetchone()[0]
        ddl = re.sub(r",\s*UNIQUE \(project_id, document_code\)", "", ddl)
        db.execute("ALTER TABLE document RENAME TO old_document")
        db.execute(ddl)
        db.execute("INSERT INTO document SELECT * FROM old_document")
        db.execute("DROP TABLE old_document")
        db.execute(
            "INSERT INTO document (id, project_id, document_code, date_string_format, output_author, output_checked_by)"
            " VALUES (99, 7, 'A-001', '%Y', 0, 0)"
        )
    before = snapshot(path)
    with pytest.raises(MigrationError):
        migrate(url, document_type=TYPE, apply=True, backup_confirmed=True)
    assert snapshot(path) == before


def test_cli_defaults_to_dry_run(legacy):
    path, url = legacy
    before = snapshot(path)
    result = subprocess.run(
        [sys.executable, "-m", "document_issue_api.migrate", "--database-url", url,
         "--document-type", TYPE],
        capture_output=True, text=True, env=os.environ.copy(), check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Preflight passed; no changes" in result.stdout
    assert snapshot(path) == before


def test_non_sqlite_and_missing_file_refused(tmp_path):
    with pytest.raises(MigrationError, match="Only file-backed"):
        migrate("postgresql://localhost/database")
    path = tmp_path / "absent.db"
    with pytest.raises(MigrationError, match="does not exist"):
        migrate(f"sqlite:///{path}")
    assert not path.exists()


def test_transaction_rolls_back_created_table_on_copy_failure(legacy, monkeypatch):
    path, url = legacy
    before = snapshot(path)
    original = migration_module._ddl

    def failing_ddl(table, name=None):
        sql = original(table, name)
        if name:
            position = sql.rindex(")")
            sql = sql[:position] + ", CHECK (id < 0)" + sql[position:]
        return sql

    monkeypatch.setattr(migration_module, "_ddl", failing_ddl)
    with pytest.raises(MigrationError, match="no changes committed"):
        migrate(url, document_type=TYPE, apply=True, backup_confirmed=True)
    assert snapshot(path) == before


def test_transaction_rolls_back_after_original_table_was_dropped(legacy, monkeypatch):
    path, url = legacy
    before = snapshot(path)
    original = migration_module._preflight

    def fail_recreating_index(connection, document_type):
        table, names, indexes, current = original(connection, document_type)
        return table, names, [*indexes, ("CREATE INDEX broken ON document(missing_column)",)], current

    monkeypatch.setattr(migration_module, "_preflight", fail_recreating_index)
    with pytest.raises(MigrationError, match="no changes committed"):
        migrate(url, document_type=TYPE, apply=True, backup_confirmed=True)
    assert snapshot(path) == before


def test_empty_legacy_needs_no_backfill(legacy):
    path, url = legacy
    with sqlite3.connect(path) as db:
        db.execute("DELETE FROM issue")
        db.execute("DELETE FROM document_role")
        db.execute("DELETE FROM document")
    assert "applied" in migrate(url, apply=True, backup_confirmed=True)


@pytest.mark.parametrize("sql", [
    "CREATE VIEW custom_view AS SELECT * FROM document",
    "CREATE TRIGGER custom_trigger AFTER UPDATE ON document BEGIN SELECT 1; END",
])
def test_custom_dependencies_refused(legacy, sql):
    path, url = legacy
    with sqlite3.connect(path) as db:
        db.execute(sql)
    before = snapshot(path)
    with pytest.raises(MigrationError, match="triggers/views"):
        migrate(url, document_type=TYPE, apply=True, backup_confirmed=True)
    assert snapshot(path) == before
