import shutil
import subprocess

from tests.constants import (
    FDIR_EXAMPLES_DOC_ISSUE_NOTE,
    FDIR_ROOT,
)


def test_install_extension(tmp_path):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_NOTE / "a4-portrait-note"
    FDIR_TESTDATA = tmp_path / "a4-portrait-note"
    FDIR_TESTDATA.mkdir(exist_ok=True)
    shutil.copytree(FDIR_EXAMPLE_DATA, FDIR_TESTDATA, dirs_exist_ok=True)
    FDIR_EXTENSION_INSTALL_PTH = FDIR_TESTDATA / "_extensions" / "document-issue-note"
    if FDIR_EXTENSION_INSTALL_PTH.exists():
        shutil.rmtree(FDIR_EXTENSION_INSTALL_PTH)
    subprocess.run(
        ["quarto", "add", str(FDIR_ROOT), "--no-prompt"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FDIR_EXTENSION_INSTALL_PTH.exists()


def test_build_schedule_a4_portrait(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_NOTE / "a4-portrait-note"
    FDIR_TESTDATA = example_output("document-issue-note", "a4-portrait-note")
    FDIR_TESTDATA.mkdir(exist_ok=True)
    shutil.copytree(FDIR_EXAMPLE_DATA, FDIR_TESTDATA, dirs_exist_ok=True)
    FPTH_OUTPUT = FDIR_TESTDATA / "document.pdf"
    FPTH_OUTPUT.unlink(missing_ok=True)
    subprocess.run(
        ["quarto", "add", str(FDIR_ROOT), "--no-prompt"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    subprocess.run(
        ["quarto", "render", "document.md", "--to", "document-issue-note-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful


def test_build_schedule_a3_landscape(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_NOTE / "a3-landscape-note"
    FDIR_TESTDATA = example_output("document-issue-note", "a3-landscape-note")
    FDIR_TESTDATA.mkdir(exist_ok=True)
    shutil.copytree(FDIR_EXAMPLE_DATA, FDIR_TESTDATA, dirs_exist_ok=True)
    FPTH_OUTPUT = FDIR_TESTDATA / "document.pdf"
    FPTH_OUTPUT.unlink(missing_ok=True)
    subprocess.run(
        ["quarto", "add", str(FDIR_ROOT), "--no-prompt"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    subprocess.run(
        ["quarto", "render", "document.md", "--to", "document-issue-note-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful
