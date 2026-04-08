from __future__ import annotations

from seculeti_ctf.app.infrastructure.config import Config
from seculeti_ctf.app.infrastructure.db import UserModel, build_db, init_db


def main() -> None:
    db = build_db(Config.db_url())
    init_db(db)
    try:
        user_count = db.session.query(UserModel).count()
        print(f"users: {user_count}")
    finally:
        db.session.remove()


if __name__ == "__main__":
    main()
