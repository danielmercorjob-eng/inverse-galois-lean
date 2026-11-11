"""Python worker for cochain algorithms with a time limit."""

import json
import sys

from .group import GroupSpec
from .backends import InvariantError


def main():
    payload = json.load(sys.stdin)
    group = GroupSpec(**payload["group"])
    operation, options = payload["operation"], payload["parameters"]
    from .cochains import compute
    try:
        answer = dict(success=True, result=compute(group, operation, **options))
    except (InvariantError, ValueError, TypeError, OSError) as e:
        answer = dict(success=False, error_type=type(e).__name__, error=str(e))
    print("INVGAL_JSON_BEGIN")
    print(json.dumps(answer))
    print("INVGAL_JSON_END")


if __name__ == "__main__":
    main()
