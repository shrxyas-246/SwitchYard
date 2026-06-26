from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.db import models

def _now():
    return datetime.now(timezone.utc)

def _compute_status(ea, ed, now):
    """Dynamically derive platform status from expected timestamps vs current time."""
    if ea is None or ed is None:
        return None
    if ed < now:
        return "departed"
    if ea <= now <= ed:
        return "occupied"
    if timedelta(0) <= (ea - now) <= timedelta(minutes=20):
        return "boarding"
    return "scheduled"

def get_states(db: Session):
    rows = db.query(models.Station.state).distinct().order_by(models.Station.state).all()
    return [r[0] for r in rows]

def get_cities(db: Session, state: str):
    rows = (db.query(models.Station.city)
              .filter(models.Station.state == state)
              .distinct().order_by(models.Station.city).all())
    return [r[0] for r in rows]

def get_stations(db: Session, state: str, city: str):
    rows = (db.query(models.Station)
              .filter(models.Station.state == state, models.Station.city == city)
              .order_by(models.Station.station_name).all())
    return [{"station_id": s.station_id, "station_name": s.station_name} for s in rows]

def get_platform_view(db: Session, station_id: str):
    now = _now()
    platforms = db.query(models.Platform).filter(models.Platform.station_id == station_id).all()

    statuses = (db.query(models.StationTrainStatus, models.StationTrainRef)
                  .join(models.StationTrainRef,
                        models.StationTrainStatus.station_train_map_id
                        == models.StationTrainRef.station_train_map_id)
                  .filter(models.StationTrainRef.station_id == station_id).all())

    occupied, boarding = set(), set()
    for st, _ in statuses:
        ea, ed = st.expected_arrival_time, st.expected_departure_time
        # FIX: this block must be inside the for loop (was at wrong indent level before)
        if ea and ed and ea <= now <= ed:
            occupied.add(st.scheduled_platform)
        elif ea and now < ea <= now + timedelta(minutes=20):
            boarding.add(st.scheduled_platform)

    view = []
    for p in sorted(platforms, key=lambda x: int(x.platform_no)):
        if p.platform_no in occupied:
            status = "occupied"
        elif p.platform_no in boarding:
            status = "boarding"
        else:
            status = "free"
        view.append({"platform_no": p.platform_no, "status": status})
    return view

def get_stats(db: Session, station_id: str):
    view = get_platform_view(db, station_id)
    total = len(view)
    occupied = sum(1 for p in view if p["status"] == "occupied")
    now = _now()
    # Count trains whose expected arrival falls within the next hour
    arriving = (db.query(models.StationTrainStatus)
                  .join(models.StationTrainRef,
                        models.StationTrainStatus.station_train_map_id
                        == models.StationTrainRef.station_train_map_id)
                  .filter(
                      models.StationTrainRef.station_id == station_id,
                      models.StationTrainStatus.expected_arrival_time >= now,
                      models.StationTrainStatus.expected_arrival_time <= now + timedelta(hours=1),
                  )
                  .count())
    return {"total_platforms": total, "free": total - occupied,
            "occupied": occupied, "arriving_next_hour": arriving}

def get_trains(db: Session, station_id: str, next_hour: bool = False):
    now = _now()
    q = (db.query(models.StationTrainRef, models.StationTrainStatus)
         .outerjoin(models.StationTrainStatus,
                    models.StationTrainRef.station_train_map_id
                    == models.StationTrainStatus.station_train_map_id)
         .filter(models.StationTrainRef.station_id == station_id))
    if next_hour:
        q = q.filter(models.StationTrainRef.arrival_time >= now,
                     models.StationTrainRef.arrival_time <= now + timedelta(hours=1))
    q = q.order_by(models.StationTrainRef.arrival_time)
    return [{
        "train_id": ref.train_id,
        "train_name": ref.train_name,
        "arrival_time": ref.arrival_time,
        "departure_time": ref.departure_time,
        "expected_arrival_time": st.expected_arrival_time if st else None,
        "platform": st.scheduled_platform if st else None,
        # FIX: compute status live from timestamps instead of reading the frozen DB column
        "status": _compute_status(
            st.expected_arrival_time if st else None,
            st.expected_departure_time if st else None,
            now,
        ),
    } for ref, st in q.all()]

def get_suggestions(db: Session, station_id: str):
    rows = (db.query(models.StationTrainSuggestion, models.StationTrainRef)
              .join(models.StationTrainRef,
                    models.StationTrainSuggestion.station_train_map_id
                    == models.StationTrainRef.station_train_map_id)
              .filter(models.StationTrainRef.station_id == station_id)
              .order_by(models.StationTrainSuggestion.suggested_arrival_time).all())
    return [{
        "train_id": ref.train_id,
        "train_name": ref.train_name,
        "suggested_platform": sug.suggested_platform,
        "suggested_arrival_time": sug.suggested_arrival_time,
        "suggested_departure_time": sug.suggested_departure_time,
    } for sug, ref in rows]
