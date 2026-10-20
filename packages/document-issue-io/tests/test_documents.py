import datetime
import shutil

import pytest
from document_issue import demo_document_issue
from document_issue.document_issue import Issue
from document_issue.issue import StatusRevisionEnum
from document_issue_io.markdown_document_issue import (
    Orientation,
    OutputFormat,
    PaperSize,
    generate_document_issue_pdf,
)
from pytest_examples import CodeExample, EvalExample, find_examples

from tests.constants import FDIR_TEST_OUTPUT
from tests.utils_check_doc_properties import check_quarto_doc_properties

FPTH_TEST_DOC_ISSUE = FDIR_TEST_OUTPUT / "document_issue.json"
FPTH_TEST_DOC_ISSUE_SCHEMA = FDIR_TEST_OUTPUT / "document_issue.schema.json"


@pytest.mark.parametrize("example", list(find_examples("tests/examples/documents")), ids=str)
def test_examples(example: CodeExample, eval_example: EvalExample):
    if eval_example.update_examples:
        # eval_example.format(example)
        eval_example.run_print_update(example)
    else:
        # eval_example.lint(example)
        eval_example.run_print_check(example)


def create_test_document_issue():
    return demo_document_issue()


MD = """
# title

1.  One
2.  Two
3.  Three

-   convert this notebook to markdown
-   read `docissue.json`
-   convert using `generate_document_issue_pdf`

## My Project

| Tables   |      Are      | Cool |
|----------|:-------------:|-----:|
| col 1 is |  left-aligned | 1600 |
| col 2 is |    centered   |   12 |
| col 3 is | right-aligned |    1 |
"""


class TestDocumentIssueReport:
    """Test the function `generate_document_issue_pdf`."""

    def test_report_a4_p(self):
        FDIR_RENDER = FDIR_TEST_OUTPUT / "test_report_a4_p"
        shutil.rmtree(FDIR_RENDER, ignore_errors=True)
        FDIR_RENDER.mkdir(parents=True, exist_ok=True)
        document_issue = create_test_document_issue()
        document_issue.format_configuration.output_author = False
        document_issue.format_configuration.output_checked_by = False
        fpth_pdf = FDIR_RENDER / f"{document_issue.document_code}.pdf"
        generate_document_issue_pdf(
            document_issue=document_issue,
            fpth_pdf=fpth_pdf,
        )
        assert fpth_pdf.with_suffix(".md").is_file()
        assert fpth_pdf.is_file()
        assert not (
            fpth_pdf.with_suffix(".log")
        ).is_file()  # log file should be deleted if Quarto PDF compilation is successful
        fpth_md = fpth_pdf.with_suffix(".md")
        checked_props = check_quarto_doc_properties(fpth_md, fpth_pdf)
        assert all(item in ["title", "author"] for item in checked_props)  # , 'subject'
        # TODO: add "subject" as high-level discipline (e.g. mechanical, electrical etc.)

    def test_report_a4_p_draft(self):
        FDIR_RENDER = FDIR_TEST_OUTPUT / "test_report_a4_p_draft"
        shutil.rmtree(FDIR_RENDER, ignore_errors=True)
        FDIR_RENDER.mkdir(parents=True, exist_ok=True)
        document_issue = create_test_document_issue()
        document_issue.format_configuration.output_author = False
        document_issue.format_configuration.output_checked_by = False
        fpth_pdf = FDIR_RENDER / f"{document_issue.document_code}.pdf"
        generate_document_issue_pdf(
            document_issue=document_issue,
            fpth_pdf=fpth_pdf,
            is_draft=True,
        )
        assert fpth_pdf.with_suffix(".md").is_file()
        assert fpth_pdf.is_file()
        assert not (
            fpth_pdf.with_suffix(".log")
        ).is_file()  # log file should be deleted if Quarto PDF compilation is successful
        fpth_md = fpth_pdf.with_suffix(".md")
        checked_props = check_quarto_doc_properties(fpth_md, fpth_pdf)
        assert all(item in ["title", "author"] for item in checked_props)  # , 'subject'
        # TODO: add "subject" as high-level discipline (e.g. mechanical, electrical etc.)

    def test_to_pdf_a3_landscape(self):
        FDIR_RENDER = FDIR_TEST_OUTPUT / "test_to_pdf_a3_landscape"
        shutil.rmtree(FDIR_RENDER, ignore_errors=True)
        FDIR_RENDER.mkdir(parents=True, exist_ok=True)
        document_issue = create_test_document_issue()
        document_issue.format_configuration.output_author = False
        document_issue.format_configuration.output_checked_by = False
        fpth_pdf = FDIR_RENDER / f"{document_issue.document_code}.pdf"
        generate_document_issue_pdf(
            document_issue=document_issue,
            fpth_pdf=fpth_pdf,
            md_content="Test A3 Landscape Document Issue Note",
            orientation=Orientation.LANDSCAPE,
            paper_size=PaperSize.A3,
        )
        assert fpth_pdf.with_suffix(".md").is_file()
        assert fpth_pdf.is_file()
        assert not (
            fpth_pdf.with_suffix(".log")
        ).is_file()  # log file should be deleted if Quarto PDF compilation is successful

    def test_to_pdf_with_markdown_content(self):
        FDIR_RENDER = FDIR_TEST_OUTPUT / "test_to_pdf_with_markdown_content"
        shutil.rmtree(FDIR_RENDER, ignore_errors=True)
        FDIR_RENDER.mkdir(parents=True, exist_ok=True)
        document_issue = create_test_document_issue()
        document_issue.format_configuration.output_author = False
        document_issue.format_configuration.output_checked_by = False
        fpth_pdf = FDIR_RENDER / f"{document_issue.document_code}.pdf"
        generate_document_issue_pdf(
            document_issue=document_issue,
            fpth_pdf=fpth_pdf,
            md_content=MD,
        )
        assert fpth_pdf.is_file()
        # Check that the markdown file created contains the correct content
        assert MD in fpth_pdf.with_suffix(".md").read_text()

    def test_to_pdf_with_author(self):
        FDIR_RENDER = FDIR_TEST_OUTPUT / "test_to_pdf_with_author"
        shutil.rmtree(FDIR_RENDER, ignore_errors=True)
        FDIR_RENDER.mkdir(parents=True, exist_ok=True)
        document_issue = create_test_document_issue()
        document_issue.format_configuration.output_author = True
        document_issue.format_configuration.output_checked_by = False
        fpth_pdf = FDIR_RENDER / f"{document_issue.document_code}.pdf"
        generate_document_issue_pdf(
            document_issue=document_issue,
            fpth_pdf=fpth_pdf,
        )
        assert fpth_pdf.with_suffix(".md").is_file()
        assert fpth_pdf.is_file()
        assert not (
            fpth_pdf.with_suffix(".log")
        ).is_file()  # log file should be deleted if Quarto PDF compilation is successful

    def test_to_pdf_with_author_and_checked_by(self):
        FDIR_RENDER = FDIR_TEST_OUTPUT / "test_to_pdf_with_author_and_checked_by"
        shutil.rmtree(FDIR_RENDER, ignore_errors=True)
        FDIR_RENDER.mkdir(parents=True, exist_ok=True)
        document_issue = create_test_document_issue()
        document_issue.format_configuration.output_author = True
        document_issue.format_configuration.output_checked_by = True
        fpth_pdf = FDIR_RENDER / f"{document_issue.document_code}.pdf"
        generate_document_issue_pdf(
            document_issue=document_issue,
            fpth_pdf=fpth_pdf,
        )
        assert fpth_pdf.with_suffix(".md").is_file()
        assert fpth_pdf.is_file()
        assert not (
            fpth_pdf.with_suffix(".log")
        ).is_file()  # log file should be deleted if Quarto PDF compilation is successful

    def test_to_pdf_loads_of_notes_and_issues(self):
        """Test to make sure that the PDF is created when there are lots of notes and issues.
        Please check the PDF after this test to make sure that the tables are formatted correctly.
        """
        FDIR_RENDER = FDIR_TEST_OUTPUT / "test_to_pdf_loads_of_notes_and_issues"
        shutil.rmtree(FDIR_RENDER, ignore_errors=True)
        FDIR_RENDER.mkdir(parents=True, exist_ok=True)
        document_issue = create_test_document_issue()
        document_issue.document_role = document_issue.document_role * 5
        document_issue.issue_history = document_issue.issue_history * 5
        document_issue.issue_history += [
            Issue(
                author="OH",
                checked_by="JG",
                status_revision=StatusRevisionEnum.S1_P,
                date=datetime.date(2024, 1, 1),
            ),
            Issue(
                author="OH",
                checked_by="JG",
                status_revision=StatusRevisionEnum.S2_P,
                date=datetime.date(2024, 1, 1),
            ),
            Issue(
                author="OH",
                checked_by="JG",
                status_revision=StatusRevisionEnum.S3_P,
                date=datetime.date(2024, 1, 1),
            ),
            Issue(
                author="OH",
                checked_by="JG",
                status_revision=StatusRevisionEnum.S4_P,
                date=datetime.date(2024, 1, 1),
            ),
            Issue(
                author="OH",
                checked_by="JG",
                status_revision=StatusRevisionEnum.S5_P,
                date=datetime.date(2024, 1, 1),
            ),
            Issue(
                author="OH",
                checked_by="JG",
                status_revision=StatusRevisionEnum.S6_P,
                date=datetime.date(2024, 1, 1),
            ),
            Issue(
                author="OH",
                checked_by="JG",
                status_revision=StatusRevisionEnum.S7_P,
                date=datetime.date(2024, 1, 1),
            ),
            Issue(
                author="OH",
                checked_by="JG",
                status_revision=StatusRevisionEnum.S8_P,
                date=datetime.date(2024, 1, 2),
            ),
        ]
        document_issue.notes[2] = document_issue.notes[2] * 5
        document_issue.notes = document_issue.notes * 5
        document_issue.format_configuration.output_author = True
        document_issue.format_configuration.output_checked_by = True
        fpth_pdf = FDIR_RENDER / f"{document_issue.document_code}.pdf"
        generate_document_issue_pdf(
            document_issue=document_issue,
            fpth_pdf=fpth_pdf,
        )
        assert fpth_pdf.with_suffix(".md").is_file()
        assert fpth_pdf.is_file()
        assert not (
            fpth_pdf.with_suffix(".log")
        ).is_file()  # log file should be deleted if Quarto PDF compilation is successful


class TestDocumentIssueNote:
    def test_to_pdf_document_issue_note_a4_portrait(self):
        FDIR_RENDER = FDIR_TEST_OUTPUT / "test_to_pdf_a4_portrait_note"
        shutil.rmtree(FDIR_RENDER, ignore_errors=True)
        FDIR_RENDER.mkdir(parents=True, exist_ok=True)
        document_issue = create_test_document_issue()
        document_issue.format_configuration.output_author = False
        document_issue.format_configuration.output_checked_by = False
        fpth_pdf = FDIR_RENDER / f"{document_issue.document_code}.pdf"
        generate_document_issue_pdf(
            document_issue=document_issue,
            fpth_pdf=fpth_pdf,
            md_content="Test A4 Portrait Document Issue Note",
            output_format=OutputFormat.DOCUMENT_ISSUE_NOTE,
            orientation=Orientation.PORTRAIT,
            paper_size=PaperSize.A4,
        )
        assert fpth_pdf.with_suffix(".md").is_file()
        assert fpth_pdf.is_file()
        assert not (
            fpth_pdf.with_suffix(".log")
        ).is_file()  # log file should be deleted if Quarto PDF compilation is successful

    def test_to_pdf_document_issue_note_a3_landscape(self):
        FDIR_RENDER = FDIR_TEST_OUTPUT / "test_to_pdf_a3_landscape_note"
        shutil.rmtree(FDIR_RENDER, ignore_errors=True)
        FDIR_RENDER.mkdir(parents=True, exist_ok=True)
        document_issue = create_test_document_issue()
        document_issue.format_configuration.output_author = False
        document_issue.format_configuration.output_checked_by = False
        fpth_pdf = FDIR_RENDER / f"{document_issue.document_code}.pdf"
        generate_document_issue_pdf(
            document_issue=document_issue,
            fpth_pdf=fpth_pdf,
            md_content="Test A3 Landscape Document Issue Note",
            output_format=OutputFormat.DOCUMENT_ISSUE_NOTE,
            orientation=Orientation.LANDSCAPE,
            paper_size=PaperSize.A3,
        )
        assert fpth_pdf.with_suffix(".md").is_file()
        assert fpth_pdf.is_file()
        assert not (
            fpth_pdf.with_suffix(".log")
        ).is_file()  # log file should be deleted if Quarto PDF compilation is successful
