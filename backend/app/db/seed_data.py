from datetime import datetime, timezone, timedelta

from app.db.session import SessionLocal
from app.db import models

# Format: (train_id, name, arr_offset_min, dwell_min, platform, delay_min)
#
# arr_offset_min  — minutes from NOW at seed time (negative = already arrived/departed)
# scheduled_arr   = now + arr_offset_min
# expected_arr    = scheduled_arr + delay_min
#
# Guarantees at any time of day:
#   Platforms  9 / 10 / 11  → OCCUPIED  (train sitting at platform right now)
#   Platforms 12 / 13 / 14  → BOARDING  (train arriving within 20 min)
#   All others              → FREE
TRAINS = [
    # ── DEPARTED ─────────────────────────────────────────────────────────
    ("11007", "Deccan Express",          -280,  8, "1",   0),
    ("12127", "Pune Intercity",          -230,  7, "3",   5),
    ("12109", "Panchavati Express",      -180,  6, "2",   0),
    ("11401", "Nandigram Express",       -140, 10, "4",  12),
    ("12289", "Nagpur Duronto",           -90,  9, "5",   0),
    ("12123", "Deccan Queen",             -65,  8, "6",   3),
    ("11013", "Coimbatore Express",       -42, 12, "7",   0),
    ("12809", "Howrah Mail",              -25, 10, "8",   0),
    # ── OCCUPIED (train is physically at platform right now) ──────────────
    ("11041", "Chennai Express",          -12, 20, "9",   0),  # arr 12 min ago, dep in +8 min
    ("16345", "Netravati Express",         -6, 16, "10",  0),  # arr  6 min ago, dep in +10 min
    ("11301", "Udyan Express",             -3, 15, "11",  0),  # arr  3 min ago, dep in +12 min
    # ── BOARDING (expected arrival within next 20 min) ────────────────────
    ("12101", "Jnaneswari Superdeluxe",    7, 12, "12",  0),   # arrives in  7 min
    ("12321", "Howrah Mumbai Mail",       13, 10, "13",  0),   # arrives in 13 min
    ("11139", "Gadag Express",            19,  8, "14",  0),   # arrives in 19 min
    # ── SCHEDULED (future — various delays, some trigger suggestions) ─────
    # Conflict pair 1: Pushpak Express delayed by 10 min → exp_arr = now+45
    #                  Konkan Kanya departs platform 15 at now+50 → OVERLAP [45,56] ∩ [50,58]
    ("12533", "Pushpak Express",          35, 11, "15",  10),
    ("11035", "Konkan Kanya Express",     50,  8, "15",   0),
    ("12137", "Punjab Mail",              60, 12, "16",   0),
    # Conflict pair 2: Amritsar Express delayed 18 min → exp_arr = now+108
    #                  Golden Temple Mail arrives at now+112 on same platform → OVERLAP [108,118] ∩ [112,120]
    ("11057", "Amritsar Express",         90, 10, "17",  18),
    ("12903", "Golden Temple Mail",      112,  8, "17",   0),  # delay ≥15 → suggestion
    ("12163", "Dadar Chennai Express",   120,  9, "18",   0),
    ("11077", "Jhelum Express",          150, 11, "1",    6),
    ("12618", "Mangala Express",         180, 10, "2",    0),
    ("11019", "Konark Express",          210, 12, "3",   14),
    ("12869", "CSMT Howrah Express",     240, 10, "4",    0),
    ("11015", "Kushinagar Express",      270,  9, "5",    7),
    ("12151", "Samarsata Express",       300, 10, "6",    0),
    ("11003", "Tutari Express",          330,  8, "7",    5),
    ("12117", "Godavari Express",        360,  9, "8",    0),
    ("11091", "Bhuj Express",            390, 11, "9",   22),  # delay ≥15 → suggestion
    ("12107", "Lucknow Express",         420, 10, "10",   0),
    ("12111", "Amravati Express",        450,  9, "11",   9),
    ("11201", "Nagpur Express",          480, 10, "12",   0),
    ("12141", "Patliputra Express",      510, 12, "13",  16),  # delay ≥15 → suggestion
    ("11061", "Pawan Express",           540, 10, "14",   0),
    ("12355", "Archana Express",         570, 11, "15",   4),
    ("12165", "Ratnagiri Express",       600,  9, "16",   0),
    ("11005", "Pune Express",            630,  8, "17",  11),
    ("12871", "Ispat Express",           660, 10, "18",   0),
    ("12953", "August Kranti Express",   690, 11, "1",    0),
    ("11023", "Sahyadri Express",        720,  8, "2",    8),
]


def seed():
    db = SessionLocal()
    try:
        # Clear children before parents (FK order)
        db.query(models.StationTrainSuggestion).delete()
        db.query(models.StationTrainStatus).delete()
        db.query(models.StationTrainRef).delete()
        db.query(models.Platform).delete()
        db.query(models.Station).delete()
        db.commit()

        db.add(models.Station(station_id="CSMT", station_name="Mumbai CSMT",
                              state="Maharashtra", city="Mumbai"))
        db.commit()

        for n in range(1, 19):
            db.add(models.Platform(station_id="CSMT", platform_no=str(n)))
        db.commit()

        now = datetime.now(timezone.utc)

        for train_id, name, offset_min, dwell, platform, delay in TRAINS:
            sched_arr = now + timedelta(minutes=offset_min)
            sched_dep = sched_arr + timedelta(minutes=dwell)
            exp_arr   = sched_arr + timedelta(minutes=delay)
            exp_dep   = sched_dep + timedelta(minutes=delay)

            ref = models.StationTrainRef(
                station_id="CSMT", train_id=train_id, train_name=name,
                arrival_time=sched_arr, departure_time=sched_dep,
            )
            db.add(ref)
            db.flush()  # get the generated station_train_map_id

            # Status at seed time (matches what _compute_status will return dynamically)
            if exp_dep < now:
                state = "departed"
            elif exp_arr <= now <= exp_dep:
                state = "occupied"
            elif timedelta(0) <= (exp_arr - now) <= timedelta(minutes=20):
                state = "boarding"
            else:
                state = "scheduled"

            db.add(models.StationTrainStatus(
                station_train_map_id=ref.station_train_map_id,
                scheduled_platform=platform,
                platform_status=state,
                expected_arrival_time=exp_arr,
                expected_departure_time=exp_dep,
            ))

            # Suggest alt platform for trains delayed ≥ 15 min
            if delay >= 15:
                alt = str((int(platform) % 18) + 1)
                db.add(models.StationTrainSuggestion(
                    station_train_map_id=ref.station_train_map_id,
                    suggested_platform=alt,
                    suggested_arrival_time=exp_arr - timedelta(minutes=delay // 2),
                    suggested_departure_time=exp_dep - timedelta(minutes=delay // 2),
                ))

        db.commit()
        refs = db.query(models.StationTrainRef).count()
        sugg = db.query(models.StationTrainSuggestion).count()
        print(f"[OK] Seeded CSMT - 18 platforms, {refs} trains, {sugg} suggestions")
        print(f"     Occupied : platforms 9, 10, 11")
        print(f"     Boarding : platforms 12, 13, 14")
        print(f"     Free     : all others")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
