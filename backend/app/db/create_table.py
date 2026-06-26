from app.db.session import Base,engine
from app.db import models #register all tables by default in models file, runs file top to bottom
def main() -> None:
    print("Creating tables in switchyard...")
    Base.metadata.create_all(bind=engine)
    print("✅ Done — tables created (or already existed).")


if __name__ == "__main__":
    main()