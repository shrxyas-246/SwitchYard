#is the connection machinery from the diagram earlier: it builds the engine (the pool that talks to Postgres), 
# the SessionLocal factory (which hands out a session per request), the Base class (parent of all table models), 
# and the get_db() helper. This is the heart of the DB layer.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base
from app.config.settings import settings
# Central parent class for all ORM models.
# SQLAlchemy collects all classes inheriting from Base and uses
#Base contains Base.metadata(master list of all tables inherited base into class)
Base=declarative_base()#without Base python sees everything as normal class
#Therefore when class Train() no table called train is created 
#but when Train(Base) then alchemy runs CREATE TABLE train due to the inherited Base method


engine=create_engine(settings.database_url,pool_pre_ping=True)
SessionLocal=sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db=SessionLocal()
    try:
      yield db
    finally:
        db.close()
        
