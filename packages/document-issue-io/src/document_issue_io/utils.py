import os
import pathlib
import subprocess
from contextlib import contextmanager

from document_issue_io.constants import DIR_MEDIA, DIR_TEMPLATES

FPTH_INSTALL_TAR = DIR_TEMPLATES / "document-issue-quarto.tar.gz"
FPTH_FOOTER_LOGO = DIR_MEDIA / "footer-logo.png"


@contextmanager
def change_dir(directory):
    current_dir = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(current_dir)


def install_document_issue_quarto_extension():
    subprocess.run(["quarto", "add", str(FPTH_INSTALL_TAR), "--no-prompt"], check=True)


def update_document_issue_quarto_extension():
    subprocess.run(["quarto", "update", str(FPTH_INSTALL_TAR), "--no-prompt"], check=True)


def install_or_update_document_issue_quarto_extensions():
    FPTH_DOCUMENT_ISSUE_NOTE_INSTALL_PTH = pathlib.Path.cwd() / "_extensions" / "document-issue-note"
    FPTH_DOCUMENT_ISSUE_REPORT_INSTALL_PTH = pathlib.Path.cwd() / "_extensions" / "document-issue-report"
    if not FPTH_DOCUMENT_ISSUE_NOTE_INSTALL_PTH.exists() or not FPTH_DOCUMENT_ISSUE_REPORT_INSTALL_PTH.exists():
        install_document_issue_quarto_extension()
    else:
        update_document_issue_quarto_extension()
