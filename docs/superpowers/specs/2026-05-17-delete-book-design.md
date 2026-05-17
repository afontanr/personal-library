# Delete Book from Collection

## Summary

Allow users to delete a book from their personal collection. The action is available on both the collection list page (via a three-dot menu on each card) and the book detail page (via a delete button next to the save button). A native `<dialog>` modal confirms the action before the hard delete executes.

## API

### `DELETE /api/collection/{isbn}`

- Path param validated by regex: `\d{13}|\d{9}[\dXx]`
- Returns `204 No Content` on success
- Returns `404 { "detail": "Book not found" }` if ISBN not in collection
- Returns `422` for invalid ISBN format

## Domain / Application

- **New use case**: `DeleteBookFromCollection` — receives `isbn_13: str`, delegates to `CollectionRepository.delete()`, raises `BookNotFoundError` if not found
- **New port method**: `CollectionRepository.delete(isbn_13: str) -> None`
- **SQLite adapter**: `DELETE FROM collection_books WHERE isbn_13 = ?` — reading periods cascade via existing `ON DELETE CASCADE`

## Web UI

### List page (`book_list.html`)

- Each `.book-card` gets a three-dot button (`.card-menu-trigger`), absolutely positioned top-right, visible on card hover
- Clicking the trigger toggles a dropdown with one option: "Eliminar"
- Clicking "Eliminar" opens the confirmation dialog

### Detail page (`book_detail.html`)

- A `.btn-delete` button (outline style, danger color) placed next to the save button
- Clicking it opens the confirmation dialog

### Confirmation dialog

- Native `<dialog>` element, rendered in `base.html`
- Title: "Eliminar libro"
- Message: "Estas seguro de que quieres eliminar '<book title>' de tu coleccion?"
- Buttons: "Cancelar" (outline, closes dialog) + "Eliminar" (filled, danger, triggers delete)
- Styled with existing design tokens (parchment, border, Cormorant Garamond headings)

### Toast notification

- `.toast` element, bottom-center, slide-up + fade-in animation
- Error state: warm red background with error message text
- Auto-dismiss after 4 seconds, or on click

## Client-side JS

### Three-dot menu (list page only)

- Clicking `.card-menu-trigger` toggles adjacent dropdown visibility
- Document-level click listener closes dropdown when clicking outside
- Each card carries `data-isbn` and `data-title` attributes

### Dialog flow

1. User clicks "Eliminar" → JS sets dialog message with book title, stores ISBN, calls `dialog.showModal()`
2. "Cancelar" → `dialog.close()`
3. "Eliminar" (inside dialog) → JS disables buttons, fires `DELETE /api/collection/{isbn}`

### Post-delete behavior

- **List page**: Add CSS class to card for fade-out animation. On `animationend`, remove card from DOM. Decrement book count.
- **Detail page**: `window.location.href = '/'`

### Error handling

- Close dialog, create toast element at bottom of `<body>` with error message
- Toast auto-dismisses after 4s; click also dismisses early

## Files to change

| File | Change |
|---|---|
| `src/personal_library/domain/repository.py` | Add `delete` method to `CollectionRepository` port |
| `src/personal_library/application/use_cases/delete_book.py` | New use case |
| `src/personal_library/infrastructure/adapters/db/sqlite_collection_repository.py` | Implement `delete` |
| `src/personal_library/presentation/api/routes/collection.py` | Add `DELETE` route |
| `src/personal_library/presentation/api/schemas.py` | Add `DeleteBookResponse` |
| `src/personal_library/presentation/dependencies.py` | Wire `DeleteBookFromCollection` use case |
| `src/personal_library/presentation/web/templates/base.html` | Add `<dialog>` element (shared) |
| `src/personal_library/presentation/web/templates/book_list.html` | Add three-dot menu to cards |
| `src/personal_library/presentation/web/templates/book_detail.html` | Add delete button |
| `src/personal_library/presentation/web/static/css/styles.css` | Dialog, menu, toast, delete button styles |
| `src/personal_library/presentation/web/static/js/app.js` | Delete logic (menu, dialog, toast, API call) |
| `tests/application/use_cases/test_delete_book.py` | New use case tests |
| `tests/infrastructure/adapters/db/test_sqlite_collection_repository.py` | Add `delete` tests |
| `tests/presentation/api/routes/test_collection.py` | Add `DELETE` route tests |
