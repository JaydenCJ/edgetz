"""Support ``python -m edgetz`` as an alias for the ``edgetz`` script."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
