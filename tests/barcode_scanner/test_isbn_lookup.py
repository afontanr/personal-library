from personal_library.barcode_scanner.isbn_lookup import normalize_isbn_for_api


def test_normalize_strips_hyphens_isbn13():
    assert normalize_isbn_for_api("978-84-663-4117-2") == "9788466341172"


def test_normalize_accepts_plain_isbn13():
    assert normalize_isbn_for_api("9788466341172") == "9788466341172"


def test_normalize_accepts_isbn10_uppercase_x():
    assert normalize_isbn_for_api("846634117X") == "846634117X"


def test_normalize_lowercase_x_to_uppercase():
    assert normalize_isbn_for_api("846634117x") == "846634117X"


def test_normalize_rejects_non_isbn():
    assert normalize_isbn_for_api("ABC-001") is None
    assert normalize_isbn_for_api("123") is None
