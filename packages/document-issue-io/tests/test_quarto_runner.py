import pathlib
import subprocess
from unittest.mock import Mock

import pytest
import yaml
from document_issue import demo_document_issue
from document_issue_io import markdown_document_issue as markdown
from document_issue_io import utils


@pytest.mark.parametrize(
    ("returncode", "stdout", "expected"),
    [(0, b"1.7.22\n", "1.7.22"), (1, b"", None), (0, b"not a version", None)],
)
def test_check_quarto_version(monkeypatch, returncode, stdout, expected):
    run = Mock(return_value=subprocess.CompletedProcess([], returncode, stdout))
    monkeypatch.setattr(subprocess, "run", run)
    assert markdown.check_quarto_version() == expected


def test_check_quarto_version_missing_executable(monkeypatch):
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=FileNotFoundError))
    assert markdown.check_quarto_version() is None


def test_run_quarto_checks_failure_in_document_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(markdown, "check_quarto_version", lambda: "1.7.22")
    error = subprocess.CalledProcessError(1, ["quarto", "render"])
    run = Mock(side_effect=error)
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        markdown.run_quarto(tmp_path / "document.md", tmp_path / "document.pdf")
    run.assert_called_once_with(
        ["quarto", "render", "document.md", "-o", "document.pdf"],
        cwd=tmp_path,
        check=True,
    )


@pytest.mark.parametrize(
    "install", [utils.install_document_issue_quarto_extension, utils.update_document_issue_quarto_extension]
)
def test_extension_failure_is_not_ignored(monkeypatch, install):
    run = Mock(side_effect=subprocess.CalledProcessError(1, ["quarto"]))
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        install()
    assert run.call_args.kwargs["check"] is True


@pytest.mark.parametrize("fails", [False, True])
def test_relative_output_and_config_are_ready_before_render(monkeypatch, tmp_path, fails):
    monkeypatch.chdir(tmp_path)
    output = pathlib.Path("nested")
    output.mkdir()
    monkeypatch.setattr(markdown, "install_or_update_document_issue_quarto_extensions", lambda: None)
    monkeypatch.setattr(markdown, "title_block_a4", Mock())

    def render(fpth_md_output, fpth_pdf):
        assert fpth_md_output == tmp_path / "nested/document.md"
        assert fpth_pdf == tmp_path / "nested/document.pdf"
        assert fpth_md_output.is_file()
        config = yaml.safe_load(pathlib.Path("_quarto.yaml").read_text())
        assert config["project"]["render"] == ["document.md"]
        assert config["format"] == "document-issue-report-pdf"
        if fails:
            raise subprocess.CalledProcessError(1, ["quarto", "render"])

    monkeypatch.setattr(markdown, "run_quarto", render)
    if fails:
        with pytest.raises(subprocess.CalledProcessError):
            markdown.generate_document_issue_pdf(demo_document_issue(), output / "document.pdf")
    else:
        markdown.generate_document_issue_pdf(demo_document_issue(), output / "document.pdf")
    assert pathlib.Path.cwd() == tmp_path
