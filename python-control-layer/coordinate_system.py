"""Coordinate System Manager - Manages work coordinates, transformations, and offsets"""
import logging
import math
from typing import Dict, Optional, Tuple
from copy import deepcopy

logger = logging.getLogger(__name__)


class CoordinateSystemManager:
    """Manages coordinate systems and transformations"""

    # Coordinate system identifiers
    MACHINE_COORDS = "G53"
    WORK_COORDS = ["G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3"]

    def __init__(self):
        # Work coordinate system offsets (from machine zero)
        self.work_offsets: Dict[str, Dict[str, float]] = {
            coord_sys: {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}
            for coord_sys in self.WORK_COORDS
        }

        # Active coordinate system
        self.active_coord_system = "G54"

        # Local coordinate system (G52)
        self.local_offset = {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}
        self.local_active = False

        # Coordinate system shift (G92)
        self.g92_offset = {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}
        self.g92_active = False

        # Coordinate rotation (G68/G69)
        self.rotation_active = False
        self.rotation_center = {"X": 0.0, "Y": 0.0}
        self.rotation_angle = 0.0  # degrees

        # Coordinate scaling (G50/G51)
        self.scaling_active = False
        self.scaling_center = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        self.scaling_factors = {"X": 1.0, "Y": 1.0, "Z": 1.0}

        # Coordinate mirroring
        self.mirror_active = False
        self.mirror_axes = {"X": False, "Y": False, "Z": False}

        # Polar coordinates (G15/G16)
        self.polar_active = False
        self.polar_center = {"X": 0.0, "Y": 0.0}

        logger.info("Coordinate System Manager initialized")

    def set_active_coordinate_system(self, coord_sys: str) -> bool:
        """Set active work coordinate system (G54-G59)"""
        if coord_sys in self.WORK_COORDS:
            self.active_coord_system = coord_sys
            logger.info(f"Active coordinate system: {coord_sys}")
            return True

        logger.error(f"Invalid coordinate system: {coord_sys}")
        return False

    def set_work_offset(self, coord_sys: str, axis: str, value: float) -> bool:
        """Set work coordinate system offset"""
        if coord_sys not in self.WORK_COORDS:
            logger.error(f"Invalid coordinate system: {coord_sys}")
            return False

        if axis not in ["X", "Y", "Z", "A", "B", "C"]:
            logger.error(f"Invalid axis: {axis}")
            return False

        self.work_offsets[coord_sys][axis] = value
        logger.info(f"{coord_sys} {axis} offset set to {value}")
        return True

    def set_work_offsets(self, coord_sys: str, offsets: Dict[str, float]) -> bool:
        """Set multiple work coordinate system offsets"""
        if coord_sys not in self.WORK_COORDS:
            logger.error(f"Invalid coordinate system: {coord_sys}")
            return False

        for axis, value in offsets.items():
            if axis in ["X", "Y", "Z", "A", "B", "C"]:
                self.work_offsets[coord_sys][axis] = value

        logger.info(f"{coord_sys} offsets set: {offsets}")
        return True

    def get_work_offset(self, coord_sys: Optional[str] = None) -> Dict[str, float]:
        """Get work coordinate system offset"""
        if coord_sys is None:
            coord_sys = self.active_coord_system

        if coord_sys in self.work_offsets:
            return self.work_offsets[coord_sys].copy()

        return {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}

    def set_local_offset(self, offsets: Dict[str, float]):
        """Set local coordinate system offset (G52)"""
        self.local_offset.update(offsets)
        self.local_active = True
        logger.info(f"Local coordinate offset set: {offsets}")

    def cancel_local_offset(self):
        """Cancel local coordinate system (G52 with no parameters)"""
        self.local_offset = {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}
        self.local_active = False
        logger.info("Local coordinate offset cancelled")

    def set_g92_offset(self, position: Dict[str, float]):
        """Set coordinate system shift (G92)"""
        self.g92_offset.update(position)
        self.g92_active = True
        logger.info(f"G92 coordinate shift set: {position}")

    def cancel_g92_offset(self):
        """Cancel G92 offset"""
        self.g92_offset = {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}
        self.g92_active = False
        logger.info("G92 offset cancelled")

    def set_rotation(self, center_x: float, center_y: float, angle: float):
        """Set coordinate rotation (G68)"""
        self.rotation_center = {"X": center_x, "Y": center_y}
        self.rotation_angle = angle
        self.rotation_active = True
        logger.info(f"Coordinate rotation: center=({center_x}, {center_y}), angle={angle}°")

    def cancel_rotation(self):
        """Cancel coordinate rotation (G69)"""
        self.rotation_active = False
        self.rotation_angle = 0.0
        logger.info("Coordinate rotation cancelled")

    def rotate_point(self, x: float, y: float) -> Tuple[float, float]:
        """Apply rotation to a point"""
        if not self.rotation_active or self.rotation_angle == 0:
            return x, y

        # Translate to rotation center
        dx = x - self.rotation_center["X"]
        dy = y - self.rotation_center["Y"]

        # Rotate
        angle_rad = math.radians(self.rotation_angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a

        # Translate back
        return rx + self.rotation_center["X"], ry + self.rotation_center["Y"]

    def set_scaling(self, center: Dict[str, float], factors: Dict[str, float]):
        """Set coordinate scaling (G51)"""
        self.scaling_center.update(center)
        self.scaling_factors.update(factors)
        self.scaling_active = True
        logger.info(f"Coordinate scaling: center={center}, factors={factors}")

    def cancel_scaling(self):
        """Cancel coordinate scaling (G50)"""
        self.scaling_active = False
        self.scaling_factors = {"X": 1.0, "Y": 1.0, "Z": 1.0}
        logger.info("Coordinate scaling cancelled")

    def scale_coordinate(self, axis: str, value: float) -> float:
        """Apply scaling to a coordinate"""
        if not self.scaling_active or axis not in self.scaling_factors:
            return value

        center = self.scaling_center.get(axis, 0.0)
        factor = self.scaling_factors.get(axis, 1.0)

        return center + (value - center) * factor

    def set_mirror(self, axes: Dict[str, bool]):
        """Set coordinate mirroring"""
        self.mirror_axes.update(axes)
        self.mirror_active = any(axes.values())
        logger.info(f"Coordinate mirroring: {axes}")

    def cancel_mirror(self):
        """Cancel coordinate mirroring"""
        self.mirror_axes = {"X": False, "Y": False, "Z": False}
        self.mirror_active = False
        logger.info("Coordinate mirroring cancelled")

    def mirror_coordinate(self, axis: str, value: float, center: float = 0.0) -> float:
        """Apply mirroring to a coordinate"""
        if not self.mirror_active or not self.mirror_axes.get(axis, False):
            return value

        return 2 * center - value

    def set_polar_mode(self, active: bool, center: Optional[Dict[str, float]] = None):
        """Set polar coordinate mode (G15/G16)"""
        self.polar_active = active

        if center:
            self.polar_center.update(center)

        mode = "activated" if active else "deactivated"
        logger.info(f"Polar coordinate mode {mode}")

    def polar_to_cartesian(self, radius: float, angle: float) -> Tuple[float, float]:
        """Convert polar coordinates to Cartesian"""
        angle_rad = math.radians(angle)
        x = self.polar_center["X"] + radius * math.cos(angle_rad)
        y = self.polar_center["Y"] + radius * math.sin(angle_rad)
        return x, y

    def cartesian_to_polar(self, x: float, y: float) -> Tuple[float, float]:
        """Convert Cartesian coordinates to polar"""
        dx = x - self.polar_center["X"]
        dy = y - self.polar_center["Y"]
        radius = math.sqrt(dx ** 2 + dy ** 2)
        angle = math.degrees(math.atan2(dy, dx))
        return radius, angle

    def machine_to_work(self, machine_pos: Dict[str, float]) -> Dict[str, float]:
        """Convert machine coordinates to work coordinates"""
        work_pos = {}

        # Get active work offset
        work_offset = self.get_work_offset()

        for axis in ["X", "Y", "Z", "A", "B", "C"]:
            # Start with machine position
            pos = machine_pos.get(axis, 0.0)

            # Subtract work offset
            pos -= work_offset.get(axis, 0.0)

            # Subtract local offset if active
            if self.local_active:
                pos -= self.local_offset.get(axis, 0.0)

            # Subtract G92 offset if active
            if self.g92_active:
                pos -= self.g92_offset.get(axis, 0.0)

            work_pos[axis] = pos

        # Apply transformations (only to linear axes)
        if self.rotation_active and "X" in work_pos and "Y" in work_pos:
            work_pos["X"], work_pos["Y"] = self.rotate_point(work_pos["X"], work_pos["Y"])

        if self.scaling_active:
            for axis in ["X", "Y", "Z"]:
                if axis in work_pos:
                    work_pos[axis] = self.scale_coordinate(axis, work_pos[axis])

        if self.mirror_active:
            for axis in ["X", "Y", "Z"]:
                if axis in work_pos:
                    work_pos[axis] = self.mirror_coordinate(axis, work_pos[axis])

        return work_pos

    def work_to_machine(self, work_pos: Dict[str, float]) -> Dict[str, float]:
        """Convert work coordinates to machine coordinates"""
        machine_pos = deepcopy(work_pos)

        # Reverse transformations (only to linear axes)
        if self.mirror_active:
            for axis in ["X", "Y", "Z"]:
                if axis in machine_pos:
                    machine_pos[axis] = self.mirror_coordinate(axis, machine_pos[axis])

        if self.scaling_active:
            for axis in ["X", "Y", "Z"]:
                if axis in machine_pos:
                    center = self.scaling_center.get(axis, 0.0)
                    factor = self.scaling_factors.get(axis, 1.0)
                    if abs(factor) > 1e-10:
                        machine_pos[axis] = center + (machine_pos[axis] - center) / factor

        if self.rotation_active and "X" in machine_pos and "Y" in machine_pos:
            # Rotate in opposite direction
            dx = machine_pos["X"] - self.rotation_center["X"]
            dy = machine_pos["Y"] - self.rotation_center["Y"]

            angle_rad = math.radians(-self.rotation_angle)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            rx = dx * cos_a - dy * sin_a
            ry = dx * sin_a + dy * cos_a

            machine_pos["X"] = rx + self.rotation_center["X"]
            machine_pos["Y"] = ry + self.rotation_center["Y"]

        # Get active work offset
        work_offset = self.get_work_offset()

        # Add offsets
        for axis in ["X", "Y", "Z", "A", "B", "C"]:
            pos = machine_pos.get(axis, 0.0)

            # Add G92 offset if active
            if self.g92_active:
                pos += self.g92_offset.get(axis, 0.0)

            # Add local offset if active
            if self.local_active:
                pos += self.local_offset.get(axis, 0.0)

            # Add work offset
            pos += work_offset.get(axis, 0.0)

            machine_pos[axis] = pos

        return machine_pos

    def get_transformation_status(self) -> Dict:
        """Get status of all transformations"""
        return {
            "active_coord_system": self.active_coord_system,
            "work_offset": self.get_work_offset(),
            "local_offset": {
                "active": self.local_active,
                "values": self.local_offset.copy() if self.local_active else None
            },
            "g92_offset": {
                "active": self.g92_active,
                "values": self.g92_offset.copy() if self.g92_active else None
            },
            "rotation": {
                "active": self.rotation_active,
                "center": self.rotation_center.copy() if self.rotation_active else None,
                "angle": self.rotation_angle if self.rotation_active else None
            },
            "scaling": {
                "active": self.scaling_active,
                "center": self.scaling_center.copy() if self.scaling_active else None,
                "factors": self.scaling_factors.copy() if self.scaling_active else None
            },
            "mirror": {
                "active": self.mirror_active,
                "axes": self.mirror_axes.copy() if self.mirror_active else None
            },
            "polar": {
                "active": self.polar_active,
                "center": self.polar_center.copy() if self.polar_active else None
            }
        }
