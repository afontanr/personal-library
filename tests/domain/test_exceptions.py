from personal_library.domain.exceptions import BookNotFoundError, BookRepositoryError


def test_book_not_found_error_is_exception():
    error = BookNotFoundError(isbn="9788466341172")
    assert isinstance(error, Exception)
    assert error.isbn == "9788466341172"
    assert "9788466341172" in str(error)


def test_book_repository_error_is_exception():
    error = BookRepositoryError("upstream timeout")
    assert isinstance(error, Exception)
    assert "upstream timeout" in str(error)
