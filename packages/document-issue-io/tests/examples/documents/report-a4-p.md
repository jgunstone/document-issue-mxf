---
title: "report-a4-p"
---

::: {.callout-note collapse="true" icon=false}

## code

```py
# note. the tests are in the document-issue-io package
import shutil
import pathlib
from document_issue import demo_document_issue
from document_issue_io import generate_document_issue_pdf

fdir_output = pathlib.Path("tests/test-outputs")
fdir_render = fdir_output / "report-a4-p"

shutil.rmtree(fdir_render, ignore_errors=True)
fdir_render.mkdir(parents=True, exist_ok=True)
document_issue = demo_document_issue()

document_issue.format_configuration.output_author = False
document_issue.format_configuration.output_checked_by = False
fpth_pdf = fdir_render / f"{document_issue.document_code}.pdf"
generate_document_issue_pdf(
    document_issue=document_issue,
    fpth_pdf=fpth_pdf,
)
assert not (
    fpth_pdf.with_suffix(".log")
).is_file()  # log file should be deleted if Quarto PDF compilation is successful


print(fpth_pdf, fpth_pdf.is_file())
#> tests/test-outputs/report-a4-p/06667-MXF-XX-XX-SH-M-20003.pdf True

```

:::

```{=html}
<embed src="test-outputs/03870-MXF-XX-XX-IS-J-00132.pdf" width="600px" height="1000px" />
```
