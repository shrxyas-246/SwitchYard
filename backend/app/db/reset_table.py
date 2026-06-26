from app.db.session import Base, engine
from app.db import models  # noqa: F401 — registers the tables on Base


def main() -> None:
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating with the new schema...")
    Base.metadata.create_all(bind=engine)
    print("✅ Done — schema rebuilt.")


if __name__ == "__main__":
    main()