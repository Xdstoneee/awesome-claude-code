"""Allow `python -m palantir` invocation."""
from palantir.app import main
import sys
sys.exit(main())
