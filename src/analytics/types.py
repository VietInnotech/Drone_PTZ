from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

SchemaName = Literal["drone-ptz-metadata/1"]
CoordinateSpace = Literal["source", "processed"]
TrackingPhaseValue = Literal["idle", "searching", "tracking", "lost"]
PtzControlMode = Literal["onvif", "octagon", "sim"]


class FrameSize(TypedDict):
    w: int
    h: int


class NormalizedBBox(TypedDict):
    x: float
    y: float
    w: float
    h: float


class Velocity(TypedDict):
    x: float
    y: float


class Track(TypedDict):
    id: int
    label: str
    conf: float
    bbox: NormalizedBBox
    velocity: NotRequired[Velocity]
    zones: NotRequired[list[str]]


class PtzCommand(TypedDict):
    pan: float
    tilt: float
    zoom: float


class PtzState(TypedDict):
    control_mode: PtzControlMode
    active: bool
    cmd: PtzCommand


class MetadataTick(TypedDict):
    schema: SchemaName
    type: Literal["metadata_tick"]
    session_id: str
    camera_id: str
    ts_unix_ms: int
    ts_mono_ms: NotRequired[int]
    frame_index: NotRequired[int]
    space: CoordinateSpace
    frame_size: FrameSize
    selected_target_id: int | None
    tracking_phase: TrackingPhaseValue
    ptz: NotRequired[PtzState]
    tracks: list[Track]


class TrackSummary(TypedDict):
    id: int
    label: str
    top_conf: float
    confirmed: bool
    start_ts_unix_ms: int
    end_ts_unix_ms: int | None
    zones: NotRequired[list[str]]
    best_bbox: NotRequired[NormalizedBBox]
    track_id: NotRequired[str]


class TrackEvent(TypedDict):
    schema: SchemaName
    type: Literal["track_event"]
    event: Literal["new", "update", "end"]
    session_id: str
    camera_id: str
    ts_unix_ms: int
    before: TrackSummary | None
    after: TrackSummary
