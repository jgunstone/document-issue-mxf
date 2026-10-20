import pathlib

FDIR_ROOT = pathlib.Path(__file__).resolve().parent.parent
FDIR_TESTS = FDIR_ROOT / "tests"

FDIR_EXAMPLES = FDIR_TESTS / "examples"
FDIR_EXAMPLES_DOC_ISSUE_NOTE = FDIR_EXAMPLES / "document-issue-note"
FDIR_EXAMPLES_DOC_ISSUE_REPORT = FDIR_EXAMPLES / "document-issue-report"
