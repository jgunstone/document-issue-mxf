import shutil
import subprocess

from tests.constants import FDIR_EXAMPLES_DOC_ISSUE_REPORT
from tests.utils_check_doc_properties import check_quarto_doc_properties


def test_quarto_doc_properties(example_output):
    FDIR_EXAMPLE_DATA = FDIR_EXAMPLES_DOC_ISSUE_REPORT / "quarto-doc-properties"
    FDIR_TESTDATA = example_output("quarto-doc-properties")
    FDIR_TESTDATA.mkdir(exist_ok=True)
    shutil.copytree(FDIR_EXAMPLE_DATA, FDIR_TESTDATA, dirs_exist_ok=True)
    FPTH_INPUT = FDIR_TESTDATA / "document.qmd"
    FPTH_OUTPUT = FDIR_TESTDATA / "document.pdf"
    FPTH_OUTPUT.unlink(missing_ok=True)
    subprocess.run(
        ["quarto", "render", "document.qmd", "-M", "latex-auto-install:false"],
        cwd=FDIR_TESTDATA,
        check=True,
    )
    assert FPTH_OUTPUT.is_file()
    assert not (FDIR_TESTDATA / "document.log").exists()
    check_quarto_doc_properties(FPTH_INPUT, FPTH_OUTPUT)
