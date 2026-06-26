from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import crud
from app.db.session import get_db
from app.logic.allocator import generate_suggestions, refresh_suggestions

router = APIRouter(prefix="/api", tags=["dashboard"])
#defining the states endpoint
@router.get("/states")
def states(db : Session= Depends(get_db)):
    return crud.get_states(db)

@router.get("/cities")
def cities(state: str, db: Session = Depends(get_db)):
    return crud.get_cities(db, state)


@router.get("/stations")
def stations(state: str, city: str, db: Session = Depends(get_db)):
    return crud.get_stations(db, state, city)


@router.get("/stations/{station_id}/stats")
def stats(station_id: str, db: Session = Depends(get_db)):
    return crud.get_stats(db, station_id)


@router.get("/stations/{station_id}/platforms")
def platforms(station_id: str, db: Session = Depends(get_db)):
    return crud.get_platform_view(db, station_id)


@router.get("/stations/{station_id}/trains")
def trains(station_id: str, next_hour: bool = False, db: Session = Depends(get_db)):
    return crud.get_trains(db, station_id, next_hour)


@router.get("/stations/{station_id}/suggestions")
def suggestions(station_id: str, db: Session = Depends(get_db)):
    # Live engine call — computes suggestions fresh on every request
    results = generate_suggestions(db, station_id)
    return [
        {
            "train_id":                s.train_id,
            "train_name":              s.train_name,
            "suggested_platform":      s.suggested_platform,
            "suggested_arrival_time":  s.suggested_arrival_time,
            "suggested_departure_time": s.suggested_departure_time,
            "reason":                  s.reason,
        }
        for s in results
    ]


@router.post("/stations/{station_id}/suggestions/refresh")
def refresh(station_id: str, db: Session = Depends(get_db)):
    # Persists engine output to DB (useful for audit logs or offline viewing)
    count = refresh_suggestions(db, station_id)
    return {"station_id": station_id, "suggestions_written": count}