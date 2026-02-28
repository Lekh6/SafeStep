from __future__ import annotations

from dataclasses import dataclass

from .tracking import Box, iou


@dataclass
class VehicleMotion:
    speed_prev: float
    speed_now: float
    box_prev: Box
    box_now: Box


def detect_accident(motion_a: VehicleMotion, motion_b: VehicleMotion) -> bool:
    overlap_now = iou(motion_a.box_now, motion_b.box_now)
    had_motion_drop = (
        motion_a.speed_prev > 6
        and motion_b.speed_prev > 6
        and motion_a.speed_now < 1
        and motion_b.speed_now < 1
    )
    return overlap_now > 0.2 and had_motion_drop
