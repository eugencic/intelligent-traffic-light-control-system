from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class TrafficDataForAnalytics(_message.Message):
    __slots__ = ["intersection_id", "signal_status_1", "vehicle_count", "incident", "date", "time"]
    INTERSECTION_ID_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_STATUS_1_FIELD_NUMBER: _ClassVar[int]
    VEHICLE_COUNT_FIELD_NUMBER: _ClassVar[int]
    INCIDENT_FIELD_NUMBER: _ClassVar[int]
    DATE_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    intersection_id: int
    signal_status_1: int
    vehicle_count: int
    incident: bool
    date: str
    time: str
    def __init__(self, intersection_id: _Optional[int] = ..., signal_status_1: _Optional[int] = ..., vehicle_count: _Optional[int] = ..., incident: bool = ..., date: _Optional[str] = ..., time: _Optional[str] = ...) -> None: ...

class TrafficDataForAnalyticsReceiveResponse(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class IntersectionRequestForAnalytics(_message.Message):
    __slots__ = ["intersection_id"]
    INTERSECTION_ID_FIELD_NUMBER: _ClassVar[int]
    intersection_id: int
    def __init__(self, intersection_id: _Optional[int] = ...) -> None: ...

class TrafficAnalyticsResponse(_message.Message):
    __slots__ = ["intersection_id", "timestamp", "average_vehicle_count", "peak_hours", "average_incidents"]
    INTERSECTION_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    AVERAGE_VEHICLE_COUNT_FIELD_NUMBER: _ClassVar[int]
    PEAK_HOURS_FIELD_NUMBER: _ClassVar[int]
    AVERAGE_INCIDENTS_FIELD_NUMBER: _ClassVar[int]
    intersection_id: int
    timestamp: str
    average_vehicle_count: float
    peak_hours: str
    average_incidents: float
    def __init__(self, intersection_id: _Optional[int] = ..., timestamp: _Optional[str] = ..., average_vehicle_count: _Optional[float] = ..., peak_hours: _Optional[str] = ..., average_incidents: _Optional[float] = ...) -> None: ...

class AddDataAnalyticsRequest(_message.Message):
    __slots__ = ["intersection_id", "message"]
    INTERSECTION_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    intersection_id: int
    message: str
    def __init__(self, intersection_id: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class AddDataAnalyticsResponse(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class DeleteDataAnalyticsRequest(_message.Message):
    __slots__ = ["intersection_id"]
    INTERSECTION_ID_FIELD_NUMBER: _ClassVar[int]
    intersection_id: int
    def __init__(self, intersection_id: _Optional[int] = ...) -> None: ...

class DeleteDataAnalyticsResponse(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class TrafficAnalyticsServiceStatusRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class TrafficAnalyticsServiceStatusResponse(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...
