from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from app.db.session import Base


class Station(Base):
    __tablename__ = "stations"

    station_id = Column(String, primary_key=True, index=True)
    station_name = Column(String, nullable=False)
    state = Column(String, nullable=False)
    city = Column(String, nullable=False)


class Platform(Base):
    __tablename__ = "platforms"

    platform_id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, ForeignKey("stations.station_id"), nullable=False)
    platform_no = Column(String, nullable=False)

#THis is for train and related info linked to station
class StationTrainRef(Base):
    __tablename__ = "station_train_ref"

    station_train_map_id = Column(Integer, primary_key=True, index=True)#unique key to identify train arriving at which station
    station_id = Column(String, ForeignKey("stations.station_id"), nullable=False)
    train_id = Column(String, nullable=False)
    train_name = Column(String, nullable=True)            # NEW
    arrival_time = Column(DateTime(timezone=True), nullable=True)
    departure_time = Column(DateTime(timezone=True), nullable=True)

#This is for station and related info linked to train
class StationTrainStatus(Base):
    __tablename__ = "station_train_status"

    station_train_map_id = Column(
        Integer,
        ForeignKey("station_train_ref.station_train_map_id"),#since there is no knowledge of station id here
        primary_key=True,#incoming train needs to know which station_id it is gonna occupy hence use the station id in trainref using join in db query
    )
    scheduled_platform = Column(String, nullable=True)
    platform_status = Column(String, nullable=True)
    expected_arrival_time = Column(DateTime(timezone=True), nullable=True)     
    expected_departure_time = Column(DateTime(timezone=True), nullable=True)   


class StationTrainSuggestion(Base):
    __tablename__ = "station_train_suggestion"

    suggestion_id = Column(Integer, primary_key=True, index=True)
    station_train_map_id = Column(
        Integer,
        ForeignKey("station_train_ref.station_train_map_id"),
        nullable=False,
    )
    suggested_platform = Column(String, nullable=True)
    suggested_arrival_time = Column(DateTime(timezone=True), nullable=True)    
    suggested_departure_time = Column(DateTime(timezone=True), nullable=True)  
    