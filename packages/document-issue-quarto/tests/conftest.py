import shutil

import pytest

from tests.constants import FDIR_TESTS


@pytest.fixture
def example_output():
    """Keep fresh render artifacts where the documentation examples consume them."""

    def prepare_output(*parts):
        output = (FDIR_TESTS / "test-outputs").joinpath(*parts)
        if output.exists():
            shutil.rmtree(output)
        output.mkdir(parents=True)
        return output

    return prepare_output
