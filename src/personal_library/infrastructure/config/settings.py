from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_books_base_url: str = "https://www.googleapis.com/books/v1"
    amazon_image_base_url: str = "https://m.media-amazon.com/images/P"
    http_timeout: float = 10.0
    database_path: str = "data/library.db"
