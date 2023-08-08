try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path  # type: ignore

__all__ = ['Path']
