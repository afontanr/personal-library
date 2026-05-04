from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_books_base_url: str = "https://www.googleapis.com/books/v1"
    amazon_image_base_url: str = "https://images-na.ssl-images-amazon.com/images/P"
    http_timeout: float = 10.0
