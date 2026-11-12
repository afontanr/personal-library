import pytest

from personal_library.presentation.web.formatting import format_volume


@pytest.mark.parametrize("value, expected", [(2.0, "2"), (3.5, "3.5"), (0.0, "0")])
def test_format_volume(value, expected):
    assert format_volume(value) == expected
