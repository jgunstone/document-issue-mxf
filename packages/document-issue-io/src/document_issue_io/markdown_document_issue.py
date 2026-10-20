from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import typing as ty
from enum import Enum

import yaml
from document_issue.document_issue import DocumentIssue
from jinja2 import Environment, FileSystemLoader

from document_issue_io.constants import (
    DIR_TEMPLATES,
    NAME_MD_DOCISSUE_TEMPLATE,
)
from document_issue_io.title_block import (
    title_block_a3,
    title_block_a4,
)
from document_issue_io.utils import (
    FPTH_FOOTER_LOGO,
    change_dir,
    install_or_update_document_issue_quarto_extensions,
)

REGEX_SEMVER = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"


def escape_latex_special_chars(text):
    """Used to escape the special characters in the text for LaTeX.
    Mainly to deal with any text passed to the preamble of the LaTeX document.
    """
    escape_dict = {
        "&": r"\\&",
        "%": r"\\%",
        "$": r"\\$",
        "#": r"\\#",
        "_": r"\\_",
        "{": r"\\{",
        "}": r"\\}",
    }
    for char, escape in escape_dict.items():
        text = text.replace(char, escape)

    # Replace \n that is not preceded by a backslash
    text = re.sub(r"(?<!\\)\n", r"\\\\newline{}", text)
    return text


class MarkdownDocumentIssue:
    """Create structured markdown header from Document object"""

    def __init__(
        self,
        document_issue: DocumentIssue,
        is_draft: bool = False,
    ):
        self.is_draft = is_draft
        self.document_issue = document_issue
        self.file_loader = FileSystemLoader(DIR_TEMPLATES)
        self.env = Environment(loader=self.file_loader)

    @property
    def md_issue_history_col_widths(self):
        col_widths = ': {tbl-colwidths="[12,5,7.5,30,45.5]"}'
        if self.document_issue.format_configuration.output_author:
            col_widths = ': {tbl-colwidths="[12,5,7.5,30,35,10.5]"}'
            if self.document_issue.format_configuration.output_checked_by:
                col_widths = ': {tbl-colwidths="[12,5,7.5,30,30,7,8.5]"}'
        return col_widths

    @property
    def md_issue_history(self):
        return self.document_issue.issue_history_table + "\n\n" + self.md_issue_history_col_widths

    @property
    def md_roles(self):
        return self.document_issue.roles_table

    @property
    def md_notes(self):
        return self.document_issue.notes_table

    @property
    def md_docissue(self):
        template = self.env.get_template(NAME_MD_DOCISSUE_TEMPLATE)
        return template.render(
            title=escape_latex_special_chars(self.document_issue.document_description.replace("\n", " ")),  # TODO: What is title for?
            project=self.document_issue.project_name,
            originator=self.document_issue.originator,
            project_name=escape_latex_special_chars(self.document_issue.project_name),
            project_number=self.document_issue.project_number,
            director_in_charge=self.document_issue.director_in_charge,
            document_description=escape_latex_special_chars(
                self.document_issue.document_description,
            ),
            document_code=self.document_issue.document_code,
            name_nomenclature=self.document_issue.name_nomenclature,
            current_issue_date=self.document_issue.current_issue.date,
            current_issue_revision=self.document_issue.current_issue.revision,
            current_issue_status_code=self.document_issue.current_issue.status_code,
            current_issue_status_description=self.document_issue.current_issue.status_description,
            md_issue_history=self.md_issue_history,
            md_roles=self.md_roles,
            md_notes=self.md_notes,
            is_draft="true" if self.is_draft else "false",
        )  # TODO: add major discipline as "subject" document metadata property

    def to_file(self, fpth: pathlib.Path):
        """Create markdown file from DocumentIssue object."""
        f = open(fpth, "w")
        f.write(self.md_docissue)
        f.close()


def check_quarto_version() -> ty.Union[None, str]:
    """Return the Quarto version, or None if the executable is unavailable or invalid."""
    try:
        completed_process = subprocess.run(["quarto", "--version"], capture_output=True, check=False)
    except FileNotFoundError:
        return None
    if completed_process.returncode != 0:
        return None
    quarto_version = completed_process.stdout.decode("utf-8").strip()
    if not re.match(REGEX_SEMVER, quarto_version):
        return None
    return quarto_version


class OutputFormat(Enum):
    DOCUMENT_ISSUE_NOTE = "document-issue-note-pdf"
    DOCUMENT_ISSUE_REPORT = "document-issue-report-pdf"


class Orientation(Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class PaperSize(Enum):
    A4 = "a4"
    A3 = "a3"


def run_quarto(
    fpth_md_output: pathlib.Path,
    fpth_pdf: pathlib.Path,
) -> subprocess.CompletedProcess:
    """Run quarto to convert markdown to pdf using a specified output format.
    The default output format is the document-issue-pdf quarto extension.
    """
    # TODO: make quarto and latex an optional dependency. check, and flag if not installed.
    check = check_quarto_version()
    if check is None:
        raise ValueError(
            "Quarto is not installed. To run quarto you must have it installed.",
            "You can install by running: pip install quarto",
        )
    cmd = [
        "quarto",
        "render",
        fpth_md_output.name,
        "-o",
        fpth_pdf.name,
    ]
    if fpth_md_output.suffix == ".ipynb":
        cmd += ["--execute", "true"]
    return subprocess.run(cmd, cwd=fpth_md_output.parent, check=True)


# generate_document_issue_docx(document_issue, fpth_docx, *, md_content="")
# generate_document_issue_md(document_issue, fpth_md, *, md_content="")
# ^ TODO: add in future if this functionality is needed


def generate_document_issue_pdf(
    document_issue: DocumentIssue,
    fpth_pdf: pathlib.Path,
    *,
    md_content: str = "",
    output_format: OutputFormat = OutputFormat.DOCUMENT_ISSUE_REPORT,
    orientation: Orientation = Orientation.PORTRAIT,
    paper_size: PaperSize = PaperSize.A4,
    resource_path: list[pathlib.Path] | None = None,
    is_draft: bool = False,
):
    """Generate a PDF document from a DocumentIssue object with any markdown content.
    The output format can be a document issue report or note.
    The orientation can be portrait or landscape.
    The paper size can be A4 or A3.
    """
    # Resolve before changing directory so relative output paths remain valid.
    fpth_pdf = fpth_pdf.resolve()
    fpth_md_output = fpth_pdf.parent / (fpth_pdf.stem + ".md")
    with change_dir(fpth_pdf.parent):
        shutil.copy(src=FPTH_FOOTER_LOGO, dst=FPTH_FOOTER_LOGO.name)
        install_or_update_document_issue_quarto_extensions()
        if output_format == OutputFormat.DOCUMENT_ISSUE_REPORT:
            is_title_page = True
            fpth_output = pathlib.Path("title-page.pdf")
        elif output_format == OutputFormat.DOCUMENT_ISSUE_NOTE:
            is_title_page = False
            fpth_output = pathlib.Path("title-block.pdf")
        else:
            msg = "Other output formats are not supported at this time."
            raise ValueError(msg)
        if orientation == Orientation.PORTRAIT and paper_size == PaperSize.A4:
            title_block_a4(
                document_issue=document_issue,
                fpth_output=fpth_output,
                is_titlepage=is_title_page,
            )
        elif orientation == Orientation.LANDSCAPE and paper_size == PaperSize.A3:
            title_block_a3(
                document_issue=document_issue,
                fpth_output=fpth_output,
                is_titlepage=is_title_page,
            )
        else:
            msg = "Other paper sizes and orientations are not supported at this time."
            raise ValueError(
                msg,
            )
        # Create quarto yaml defining the output format, orientation, and paper size
        quarto_config = {
            # Quarto does not include plain .md files in a project by default.
            "project": {"type": "default", "render": [fpth_md_output.name]},
            "format": output_format.value,
            "classoption": orientation.value,
            "papersize": paper_size.value,
        }
        if resource_path is not None:
            quarto_config["resource-path"] = [str(p) for p in resource_path]
        with open("_quarto.yaml", "w") as config_file:
            yaml.safe_dump(quarto_config, config_file)
        if output_format == OutputFormat.DOCUMENT_ISSUE_REPORT:
            markdown = MarkdownDocumentIssue(document_issue, is_draft).md_docissue + md_content
        elif output_format == OutputFormat.DOCUMENT_ISSUE_NOTE:
            markdown = md_content
        fpth_md_output.write_text(markdown)
        run_quarto(
            fpth_md_output=fpth_md_output,
            fpth_pdf=fpth_pdf,
        )
