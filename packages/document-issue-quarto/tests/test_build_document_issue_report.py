import shutil
import subprocess

from tests.constants import (
    FDIR_EXAMPLES_DOC_ISSUE_REPORT,
    FDIR_ROOT,
)

# TODO:
# move examples to examples dir in root and setup to work with the documentation workflow.
# perhaps you could ignore folders suffixed with `_` in the `test_build_examples` fn


def test_install_extension(tmp_path):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "a4-portrait-report"
    FDIR_TESTDATA = tmp_path / "a4-portrait-report"
    FDIR_TESTDATA.mkdir(exist_ok=True)
    shutil.copytree(FDIR_EXAMPLE_DATA, FDIR_TESTDATA, dirs_exist_ok=True)
    FDIR_EXTENSION_INSTALL_PTH = FDIR_TESTDATA / "_extensions" / "document-issue-report"
    if FDIR_EXTENSION_INSTALL_PTH.exists():
        shutil.rmtree(FDIR_EXTENSION_INSTALL_PTH)
    subprocess.run(
        ["quarto", "add", str(FDIR_ROOT), "--no-prompt"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FDIR_EXTENSION_INSTALL_PTH.exists()


def test_build_schedule_a4_portrait(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "a4-portrait-report"
    FDIR_TESTDATA = example_output("document-issue-report", "a4-portrait-report")
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
        ["quarto", "render", "document.md", "--to", "document-issue-report-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful


def test_build_schedule_a4_portrait_draft(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "a4-portrait-draft-report"
    FDIR_TESTDATA = example_output("document-issue-report", "a4-portrait-draft-report")
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
        ["quarto", "render", "document.md", "--to", "document-issue-report-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful


def test_build_schedule_a3_landscape(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "a3-landscape-report"
    FDIR_TESTDATA = example_output("document-issue-report", "a3-landscape-report")
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
        ["quarto", "render", "document.md", "--to", "document-issue-report-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful


def test_build_schedule_disclaimer_page(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "disclaimer-page"
    FDIR_TESTDATA = example_output("document-issue-report", "disclaimer-page")
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
        ["quarto", "render", "document.md", "--to", "document-issue-report-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful


def test_build_schedule_document_properties(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "document-properties"
    FDIR_TESTDATA = example_output("document-issue-report", "document-properties")
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
        ["quarto", "render", "document.md", "--to", "document-issue-report-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful


def test_build_schedule_footer(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "footer"
    FDIR_TESTDATA = example_output("document-issue-report", "footer")
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
        ["quarto", "render", "document.md", "--to", "document-issue-report-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful


def test_build_schedule_images(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "images"
    FDIR_TESTDATA = example_output("document-issue-report", "images")
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
        ["quarto", "render", "document.md", "--to", "document-issue-report-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful


def test_build_schedule_product_output(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "product-output"
    FDIR_TESTDATA = example_output("document-issue-report", "product-output")
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
        ["quarto", "render", "document.md", "--to", "document-issue-report-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful


def test_build_schedule_resource_path(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "resource-path"
    FDIR_TESTDATA = example_output("document-issue-report", "resource-path")
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
        ["quarto", "render", "document.md", "--to", "document-issue-report-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful


def test_build_schedule_table_of_contents(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "table-of-contents"
    FDIR_TESTDATA = example_output("document-issue-report", "table-of-contents")
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
        ["quarto", "render", "document.md", "--to", "document-issue-report-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful


def test_build_schedule_tables(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "tables"
    FDIR_TESTDATA = example_output("document-issue-report", "tables")
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
        ["quarto", "render", "document.md", "--to", "document-issue-report-pdf",
         "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful


def test_build_docissue_in_quarto_yaml(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "docissue-in-quarto-yaml"
    FDIR_TESTDATA = example_output("document-issue-report", "docissue-in-quarto-yaml")
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
        ["quarto", "render", "document.md", "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.exists()
    FPTH_LOG = FDIR_TESTDATA / "document.log"
    assert not FPTH_LOG.exists()  # log file should be deleted if Quarto PDF compilation is successful
