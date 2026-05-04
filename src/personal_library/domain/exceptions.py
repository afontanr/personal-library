class BookNotFoundError(Exception):
    def __init__(self, isbn: str) -> None:
        self.isbn = isbn
        super().__init__(f"Book not found for ISBN: {isbn}")


class BookRepositoryError(Exception):
    pass
