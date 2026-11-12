def format_volume(volume: float) -> str:
    """Render a saga volume without a trailing ".0" (2.0 -> "2", 3.5 -> "3.5")."""
    return str(int(volume)) if float(volume).is_integer() else str(volume)
