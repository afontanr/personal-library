from personal_library.domain.model.text import normalize_text


def test_normalize_text_ignores_case_accents_and_outer_spaces():
    assert normalize_text("  El Señor de los ÁNILLOS ") == "el senor de los anillos"
