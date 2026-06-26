"""
Platform Allocation Engine  —  the decision-making brain of Switchyard.

WHAT THIS FILE DOES
-------------------
When a train is delayed its expected arrival shifts forward in time.
That shifted window may now collide with another train already booked
on the same platform.  This engine:

  Step 1  Build an occupancy map  — which platform is busy when?
  Step 2  Detect conflicts        — which delayed trains clash on their assigned platform?
  Step 3  Find free platforms     — which platforms are completely empty during the clash?
  Step 4  Score alternatives      — rank the free options by proximity to the original
  Step 5  Return suggestions      — one best suggestion per conflicted train

RESOLUTION STRATEGIES (new)
---------------------------
A conflict can be fixed in more than one way.  Step 5 now compares several
strategies, each priced in the SAME unit — minutes of added delay — and keeps
the cheapest:

  A  Relocate the delayed train   — move it to the nearest free platform   (0 added delay)
  B  Relocate the on-time train   — move the train it clashed with instead  (0 added delay)
  C  Hold the on-time train        — share the platform in turn             (costs that train delay)

The option with the least added delay wins; ties prefer moving the already-delayed
train, then the nearest platform.  (A fuller set — swapping two trains, or cascading
holds across many trains at once — belongs in the optimiser phase, not this greedy pass.)

The whole pipeline is pure Python logic on top of data already in the DB.
No ML, no external API — every decision is traceable to a timestamp comparison.
"""

from datetime import datetime, timezone, timedelta
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.db import models



#  NamedTuple gives us lightweight, readable, immutable records.
#  Think of them as typed structs — cleaner than plain dicts for structured data.


class Window(NamedTuple):
    """
    One booking slot on a platform — the time range a train physically occupies it.
    Half-open interval: the train arrives at `start` and is gone by `end`.
    `train_id` lets us skip a train's own window when checking for conflicts.
    """
    start:    datetime
    end:      datetime
    train_id: str
    # NEW (defaulted, so old positional construction still works): carry enough
    # identity to also propose a move/hold for THIS train, not just the delayed one.
    ref_id:     int = 0    # station_train_map_id
    train_name: str = ""   # human-friendly name for the reason text


class Conflict(NamedTuple):
    """
    A delayed train whose shifted time window overlaps with a window
    already booked on the same platform.
    """
    ref_id:       int           # station_train_map_id — PK linking ref + status tables
    train_id:     str
    train_name:   str
    platform:     str           # the originally assigned platform
    exp_arr:      datetime      # expected (delayed) arrival
    exp_dep:      datetime      # expected (delayed) departure
    clashes_with: list[Window]  # the other trains already on that platform


class Suggestion(NamedTuple):
    """
    The engine's output: move this train to `suggested_platform` instead.
    Arrival / departure times stay the same (the delay already shifted them).
    `reason` is a human-readable explanation for the station manager.
    """
    ref_id:                  int
    train_id:                str
    train_name:              str
    suggested_platform:      str
    suggested_arrival_time:  datetime
    suggested_departure_time: datetime
    reason:                  str
    # NEW (defaulted, backward-compatible): which strategy produced this and what
    # it cost in added delay minutes.  Lets the API/UI show "relocate" vs "hold".
    kind:                    str = "relocate"   # "relocate" | "reassign_other" | "hold"
    delay_cost_minutes:      int = 0

#  occupancy_map = { "1": [Window(...)], "2": [Window(...), Window(...)], ... }
#  Think of it as a timetable pinned to each physical platform:
#  "platform 9 is busy from 15:24 to 15:40 (Chennai Express)
#   and again from 17:50 to 18:00 (Bhuj Express)."


def build_occupancy_map(db: Session, station_id: str) -> dict[str, list[Window]]:
    now = datetime.now(timezone.utc)

    # Join station_train_status ← station_train_ref so we get both
    # the time windows (status table) and the train_id (ref table).
    # Filter: only trains that have NOT yet departed — a departed train
    # no longer holds its platform.
    rows = (
        db.query(models.StationTrainStatus, models.StationTrainRef)
          .join(
              models.StationTrainRef,
              models.StationTrainStatus.station_train_map_id
              == models.StationTrainRef.station_train_map_id,
          )
          .filter(
              models.StationTrainRef.station_id == station_id,
              models.StationTrainStatus.expected_departure_time > now,
          )
          .all()
    )

    occupancy: dict[str, list[Window]] = {}

    for st, ref in rows:
        plat = st.scheduled_platform

        # setdefault: if key doesn't exist yet, create it with an empty list,
        # then append.  Equivalent to: if plat not in occupancy: occupancy[plat]=[]
        occupancy.setdefault(plat, []).append(
            Window(
                start=st.expected_arrival_time,
                end=st.expected_departure_time,
                train_id=ref.train_id,
                ref_id=st.station_train_map_id,        # NEW
                train_name=ref.train_name or ref.train_id,  # NEW
            )
        )

    # Sort each platform's windows by start time.
    # This makes the list easy to reason about visually and allows
    # future optimisation (binary search) if the train count grows large.
    for windows in occupancy.values():
        windows.sort(key=lambda w: w.start)

    return occupancy

#  Two intervals [A_start, A_end) and [B_start, B_end) overlap when:
#      A starts before B ends   AND   B starts before A ends
#  The inverse condition "no overlap" is:  A_end <= B_start  OR  B_end <= A_start
#  so overlap = NOT that = A_start < B_end AND B_start < A_end


def _overlaps(a_start: datetime, a_end: datetime,
               b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end



#  A train is "conflicted" when BOTH are true:
#    • It is delayed  (expected_arrival > scheduled_arrival)
#    • Its delayed window overlaps with another window on the SAME platform
#  We skip the train's own window (identified by train_id) to avoid a
#  train flagging itself as a conflict.


def find_conflicts(
    db: Session,
    station_id: str,
    occupancy: dict[str, list[Window]],
    min_delay_minutes: int = 1,
) -> list[Conflict]:

    now = datetime.now(timezone.utc)

    # Pull every train that:
    #   (a) belongs to this station
    #   (b) has a delay of at least `min_delay_minutes`
    #       — detected by comparing expected_arrival to scheduled arrival_time
    #   (c) has not yet departed (we can still act on it)
    delayed_rows = (
        db.query(models.StationTrainStatus, models.StationTrainRef)
          .join(
              models.StationTrainRef,
              models.StationTrainStatus.station_train_map_id
              == models.StationTrainRef.station_train_map_id,
          )
          .filter(
              models.StationTrainRef.station_id == station_id,
              models.StationTrainStatus.expected_arrival_time
              > models.StationTrainRef.arrival_time + timedelta(minutes=min_delay_minutes),
              models.StationTrainStatus.expected_departure_time > now,
          )
          .all()
    )

    conflicts: list[Conflict] = []

    for st, ref in delayed_rows:
        plat = st.scheduled_platform

        # Get every OTHER window booked on this platform
        platform_windows = occupancy.get(plat, [])

        clashing: list[Window] = [
            w for w in platform_windows
            if w.train_id != ref.train_id                          # skip self
            and _overlaps(
                st.expected_arrival_time, st.expected_departure_time,
                w.start, w.end,
            )
        ]

        # Only report trains that actually clash with something
        if clashing:
            conflicts.append(Conflict(
                ref_id=ref.station_train_map_id,
                train_id=ref.train_id,
                train_name=ref.train_name or ref.train_id,
                platform=plat,
                exp_arr=st.expected_arrival_time,
                exp_dep=st.expected_departure_time,
                clashes_with=clashing,
            ))

    return conflicts


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 3 — FIND FREE PLATFORMS FOR A GIVEN WINDOW
#
#  "Free" means: the platform has ZERO bookings that overlap [window_start, window_end).
#  We exclude the conflicted train's own platform because we're looking for alternatives.
#
#  `all_platforms` is the master list from the platforms table — it includes
#  platforms with no bookings at all, which a dict lookup would miss entirely.
# ─────────────────────────────────────────────────────────────────────────────

def find_free_platforms(
    all_platforms: list[str],
    occupancy: dict[str, list[Window]],
    window_start: datetime,
    window_end: datetime,
    exclude_platform: str,
) -> list[str]:

    free: list[str] = []

    for plat in all_platforms:
        if plat == exclude_platform:
            continue  # skip the platform that has the conflict

        windows = occupancy.get(plat, [])  # empty list = totally free platform

        # `all(...)` returns True if the condition holds for every window.
        # If ANY window overlaps, this platform is NOT free → skip it.
        if all(not _overlaps(window_start, window_end, w.start, w.end)
               for w in windows):
            free.append(plat)

    return free


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 4 — SCORE CANDIDATE PLATFORMS
#
#  We want to move the train as short a distance as possible.
#  Rationale: closer platforms = shorter crew walk, clearer signage,
#  less passenger confusion.
#
#  We model platforms as a ring (1 … N → 1 …) and compute the minimum
#  arc distance between the original and the candidate.
#
#  Example with 18 platforms:
#    original=1, candidate=18 → linear distance 17, ring distance min(17,1) = 1
#    original=9, candidate=14 → linear distance  5, ring distance min( 5,13)= 5
#
#  Lower score = closer = better.
# ─────────────────────────────────────────────────────────────────────────────

def _score(candidate: str, original: str, total_platforms: int) -> int:
    orig = int(original)
    cand = int(candidate)
    linear   = abs(cand - orig)
    ring_gap = total_platforms - linear       # the "other way around" the ring
    return min(linear, ring_gap)


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 4b — RESOLUTION STRATEGY HELPERS  (new)
#
#  A conflict can be solved several ways.  Each helper supports one strategy,
#  and every strategy is ultimately priced in the same unit — added delay
#  minutes — so generate_suggestions() can compare them and pick the cheapest.
# ─────────────────────────────────────────────────────────────────────────────

def _minutes_between(later: datetime, earlier: datetime) -> int:
    """Whole minutes from `earlier` to `later` (clamped at 0)."""
    return max(0, int((later - earlier).total_seconds() // 60))


def _slot_is_clear(
    occupancy: dict[str, list[Window]],
    platform: str,
    start: datetime,
    end: datetime,
    ignore_ids: set[str],
) -> bool:
    """
    True if `platform` has no booking overlapping [start, end), ignoring the
    trains in `ignore_ids` (the ones we're already rearranging).  Used so a
    'hold' suggestion doesn't silently create a fresh clash with a THIRD train.
    """
    for w in occupancy.get(platform, []):
        if w.train_id in ignore_ids:
            continue
        if _overlaps(start, end, w.start, w.end):
            return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
#  STEP 5 — MAIN PIPELINE: generate_suggestions
#
#  Ties steps 1-4 together and returns a Suggestion for each conflicted train.
#  This is the function the API route will call.
#
#  For every conflict it now assembles a menu of candidate fixes (Options A/B/C),
#  prices each as a cost tuple (added_delay_minutes, strategy_rank, distance),
#  and keeps the cheapest.  strategy_rank breaks ties: prefer moving the already
#  delayed train (0) over moving a punctual train (1) over holding one (2).
# ─────────────────────────────────────────────────────────────────────────────

def generate_suggestions(db: Session, station_id: str) -> list[Suggestion]:

    # Fetch the master platform list once — needed for Step 3
    all_platforms: list[str] = [
        str(p.platform_no)
        for p in (
            db.query(models.Platform)
              .filter(models.Platform.station_id == station_id)
              .order_by(models.Platform.platform_no)
              .all()
        )
    ]
    total = len(all_platforms)

    # Steps 1 and 2
    occupancy = build_occupancy_map(db, station_id)
    conflicts = find_conflicts(db, station_id, occupancy)

    suggestions: list[Suggestion] = []

    for conflict in conflicts:
        # Each entry is (cost_key, Suggestion); cost_key = (delay_min, rank, distance)
        options: list[tuple[tuple[int, int, int], Suggestion]] = []

        # ── Option A — relocate the DELAYED train to a free platform ──────────
        # Step 3 — which platforms are completely free?
        free_platforms = find_free_platforms(
            all_platforms,
            occupancy,
            conflict.exp_arr,
            conflict.exp_dep,
            conflict.platform,
        )

        if free_platforms:
            # Step 4 — pick the closest free platform
            best = min(free_platforms, key=lambda p: _score(p, conflict.platform, total))

            # Build a human-readable reason so the station manager understands WHY
            clash_ids = ", ".join(w.train_id for w in conflict.clashes_with)
            reason = (
                f"Platform {conflict.platform} is occupied by train(s) {clash_ids} "
                f"during the delay window - reassign to platform {best}."
            )

            options.append((
                (0, 0, _score(best, conflict.platform, total)),
                Suggestion(
                    ref_id=conflict.ref_id,
                    train_id=conflict.train_id,
                    train_name=conflict.train_name,
                    suggested_platform=best,
                    suggested_arrival_time=conflict.exp_arr,
                    suggested_departure_time=conflict.exp_dep,
                    reason=reason,
                    kind="relocate",
                    delay_cost_minutes=0,
                ),
            ))

        # ── Option B — relocate the ON-TIME train it clashes with instead ─────
        # Sometimes the punctual train is the easier one to move (it has a free
        # platform; the delayed one might not).  Still zero added delay.
        for other in conflict.clashes_with:
            free_for_other = find_free_platforms(
                all_platforms, occupancy, other.start, other.end, conflict.platform,
            )
            if free_for_other:
                best_o = min(free_for_other, key=lambda p: _score(p, conflict.platform, total))
                reason = (
                    f"Keep delayed train {conflict.train_id} on platform {conflict.platform}; "
                    f"move {other.train_id} to platform {best_o} instead."
                )
                options.append((
                    (0, 1, _score(best_o, conflict.platform, total)),
                    Suggestion(
                        ref_id=other.ref_id,
                        train_id=other.train_id,
                        train_name=other.train_name or other.train_id,
                        suggested_platform=best_o,
                        suggested_arrival_time=other.start,
                        suggested_departure_time=other.end,
                        reason=reason,
                        kind="reassign_other",
                        delay_cost_minutes=0,
                    ),
                ))

        # ── Option C — HOLD the on-time train until the platform clears ───────
        # Let the two trains share the platform in turn: the on-time train waits
        # until the delayed train has departed.  Costs that train some delay.
        for other in conflict.clashes_with:
            new_arr = max(other.start, conflict.exp_dep)   # wait for delayed train to leave
            shift = _minutes_between(new_arr, other.start)
            if shift <= 0:
                continue
            new_dep = other.end + (new_arr - other.start)  # preserve the dwell length

            # Only valid if holding doesn't immediately bump into a THIRD train.
            if _slot_is_clear(
                occupancy, conflict.platform, new_arr, new_dep,
                ignore_ids={conflict.train_id, other.train_id},
            ):
                reason = (
                    f"Hold {other.train_id} until {new_arr:%H:%M} so delayed train "
                    f"{conflict.train_id} can keep platform {conflict.platform} "
                    f"(+{shift} min to {other.train_id})."
                )
                options.append((
                    (shift, 2, 0),
                    Suggestion(
                        ref_id=other.ref_id,
                        train_id=other.train_id,
                        train_name=other.train_name or other.train_id,
                        suggested_platform=conflict.platform,
                        suggested_arrival_time=new_arr,
                        suggested_departure_time=new_dep,
                        reason=reason,
                        kind="hold",
                        delay_cost_minutes=shift,
                    ),
                ))

        # ── Choose the cheapest option ───────────────────────────────────────
        if not options:
            # No workable fix right now — we cannot help this train.
            # In a real system we'd escalate this to the dispatcher.
            continue

        _cost, chosen = min(options, key=lambda o: o[0])
        suggestions.append(chosen)

    return suggestions


# ─────────────────────────────────────────────────────────────────────────────
#  BONUS — refresh_suggestions
#
#  Persist the engine's output back to station_train_suggestion so the
#  existing /suggestions API endpoint continues to work unchanged.
#  Call this whenever you want to "refresh" the stored suggestions
#  (e.g. on a schedule, or when a new delay is reported).
# ─────────────────────────────────────────────────────────────────────────────

def refresh_suggestions(db: Session, station_id: str) -> int:
    """
    Recompute and overwrite suggestions for this station.
    Returns the count of suggestions written.
    """
    # Collect the map_ids that belong to this station
    ref_ids = [
        row.station_train_map_id
        for row in (
            db.query(models.StationTrainRef.station_train_map_id)
              .filter(models.StationTrainRef.station_id == station_id)
              .all()
        )
    ]

    # Wipe existing rows — we're replacing them wholesale
    if ref_ids:
        (
            db.query(models.StationTrainSuggestion)
              .filter(models.StationTrainSuggestion.station_train_map_id.in_(ref_ids))
              .delete(synchronize_session=False)
        )

    # Run the pipeline and write each result
    suggestions = generate_suggestions(db, station_id)
    for s in suggestions:
        db.add(models.StationTrainSuggestion(
            station_train_map_id=s.ref_id,
            suggested_platform=s.suggested_platform,
            suggested_arrival_time=s.suggested_arrival_time,
            suggested_departure_time=s.suggested_departure_time,
        ))

    db.commit()
    return len(suggestions)
