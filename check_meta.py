import json

from instagram import check_connection


if __name__ == "__main__":
    print(json.dumps(check_connection(), ensure_ascii=False, indent=2))
