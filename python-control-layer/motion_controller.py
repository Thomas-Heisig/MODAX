"""Motion Controller - Handles interpolation and path planning"""
import logging
import math
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class InterpolationType(Enum):
    """Types of interpolation"""
    RAPID = "rapid"  # G00
    LINEAR = "linear"  # G01
    CIRCULAR_CW = "circular_cw"  # G02
    CIRCULAR_CCW = "circular_ccw"  # G03
    HELICAL = "helical"  # G02/G03 with Z
    SPLINE = "spline"  # NURBS


class MotionController:
    """Controller for motion interpolation and path planning"""

    # Motion limits
    MAX_FEED_RATE = 15000.0  # mm/min
    MAX_RAPID_RATE = 30000.0  # mm/min
    MAX_ACCELERATION = 5000.0  # mm/s²
    MAX_JERK = 50000.0  # mm/s³

    # Look-ahead buffer
    LOOKAHEAD_BLOCKS = 100  # Number of blocks to look ahead

    def __init__(self):
        # Current state
        self.current_position = {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}
        self.current_feed_rate = 0.0

        # Active plane for circular interpolation
        self.active_plane = "G17"  # G17 (XY), G18 (ZX), G19 (YZ)

        # Distance mode
        self.absolute_mode = True  # G90=True, G91=False

        # Motion queue
        self.motion_queue: List[Dict] = []

        logger.info("Motion Controller initialized")

    def set_plane(self, plane: str):
        """Set active plane for circular interpolation"""
        if plane in ["G17", "G18", "G19"]:
            self.active_plane = plane
            logger.info(f"Active plane set to: {plane}")
            return True
        return False

    def set_distance_mode(self, absolute: bool):
        """Set absolute or incremental positioning"""
        self.absolute_mode = absolute
        mode = "absolute (G90)" if absolute else "incremental (G91)"
        logger.info(f"Distance mode: {mode}")

    def calculate_linear_move(
        self,
        target: Dict[str, float],
        feed_rate: float,
        is_rapid: bool = False
    ) -> Dict:
        """Calculate linear interpolation move"""

        # Calculate actual target position
        if self.absolute_mode:
            actual_target = target.copy()
        else:
            # Incremental mode: add to current position
            actual_target = {
                axis: self.current_position.get(axis, 0.0) + target.get(axis, 0.0)
                for axis in target
            }

        # Calculate distance and direction
        distance = 0.0
        direction = {}

        for axis in ['X', 'Y', 'Z', 'A', 'B', 'C']:
            start = self.current_position.get(axis, 0.0)
            end = actual_target.get(axis, start)
            delta = end - start
            distance += delta ** 2
            direction[axis] = delta

        distance = math.sqrt(distance)

        # Normalize direction
        if distance > 0:
            for axis in direction:
                direction[axis] /= distance

        # Determine move rate
        if is_rapid:
            move_rate = min(self.MAX_RAPID_RATE, feed_rate if feed_rate > 0 else self.MAX_RAPID_RATE)
            move_type = InterpolationType.RAPID
        else:
            move_rate = min(self.MAX_FEED_RATE, feed_rate)
            move_type = InterpolationType.LINEAR

        # Calculate move time
        move_time = (distance / move_rate) * 60.0 if move_rate > 0 else 0.0  # Convert to seconds

        move = {
            "type": move_type.value,
            "start": self.current_position.copy(),
            "target": actual_target,
            "distance": distance,
            "direction": direction,
            "feed_rate": move_rate,
            "time": move_time
        }

        logger.debug(f"Linear move: {distance:.2f}mm at {move_rate:.0f}mm/min ({move_time:.2f}s)")

        return move

    def calculate_circular_move(
        self,
        target: Dict[str, float],
        center_offset: Dict[str, float],
        feed_rate: float,
        clockwise: bool,
        radius: Optional[float] = None
    ) -> Dict:
        """Calculate circular interpolation move"""

        # Determine plane axes
        if self.active_plane == "G17":
            plane_axes = ("X", "Y", "Z")  # XY plane, Z perpendicular
            i_axis, j_axis, _k_axis = "I", "J", "K"
        elif self.active_plane == "G18":
            plane_axes = ("Z", "X", "Y")  # ZX plane, Y perpendicular
            i_axis, j_axis, _k_axis = "K", "I", "J"
        else:  # G19
            plane_axes = ("Y", "Z", "X")  # YZ plane, X perpendicular
            i_axis, j_axis, _k_axis = "J", "K", "I"

        axis1, axis2, axis3 = plane_axes

        # Get start and end points in plane
        start_pos = {
            axis1: self.current_position.get(axis1, 0.0),
            axis2: self.current_position.get(axis2, 0.0),
            axis3: self.current_position.get(axis3, 0.0)
        }

        end_pos = target.copy() if self.absolute_mode else {
            axis: self.current_position.get(axis, 0.0) + target.get(axis, 0.0)
            for axis in target
        }

        # Calculate center point
        if radius is not None:
            # R format: calculate center from radius
            center = self._calculate_center_from_radius(
                start_pos[axis1], start_pos[axis2],
                end_pos.get(axis1, start_pos[axis1]), end_pos.get(axis2, start_pos[axis2]),
                radius, clockwise
            )
        else:
            # IJK format: center offset from start point
            center = {
                axis1: start_pos[axis1] + center_offset.get(i_axis, 0.0),
                axis2: start_pos[axis2] + center_offset.get(j_axis, 0.0)
            }

        # Calculate arc parameters
        start_angle = math.atan2(
            start_pos[axis2] - center[axis2],
            start_pos[axis1] - center[axis1]
        )

        end_angle = math.atan2(
            end_pos.get(axis2, start_pos[axis2]) - center[axis2],
            end_pos.get(axis1, start_pos[axis1]) - center[axis1]
        )

        # Calculate arc angle
        if clockwise:
            if end_angle > start_angle:
                arc_angle = end_angle - start_angle - 2 * math.pi
            else:
                arc_angle = end_angle - start_angle
        else:
            if end_angle < start_angle:
                arc_angle = end_angle - start_angle + 2 * math.pi
            else:
                arc_angle = end_angle - start_angle

        # Calculate radius and arc length in plane
        arc_radius = math.sqrt(
            (start_pos[axis1] - center[axis1]) ** 2 +
            (start_pos[axis2] - center[axis2]) ** 2
        )

        arc_length = abs(arc_angle * arc_radius)

        # Check for helical interpolation (movement in perpendicular axis)
        z_delta = end_pos.get(axis3, start_pos[axis3]) - start_pos[axis3]
        is_helical = abs(z_delta) > 0.001

        # Total distance including helical component
        total_distance = math.sqrt(arc_length ** 2 + z_delta ** 2)

        # Calculate move time
        move_rate = min(self.MAX_FEED_RATE, feed_rate)
        move_time = (total_distance / move_rate) * 60.0 if move_rate > 0 else 0.0

        move_type = InterpolationType.HELICAL if is_helical else (
            InterpolationType.CIRCULAR_CW if clockwise else InterpolationType.CIRCULAR_CCW
        )

        move = {
            "type": move_type.value,
            "start": start_pos,
            "target": end_pos,
            "center": center,
            "radius": arc_radius,
            "start_angle": math.degrees(start_angle),
            "end_angle": math.degrees(end_angle),
            "arc_angle": math.degrees(arc_angle),
            "arc_length": arc_length,
            "distance": total_distance,
            "feed_rate": move_rate,
            "time": move_time,
            "plane": self.active_plane,
            "clockwise": clockwise
        }

        logger.debug(f"Circular move: radius={arc_radius:.2f}mm, arc={arc_length:.2f}mm, "
                    f"angle={math.degrees(arc_angle):.1f}°, time={move_time:.2f}s")

        return move

    def _calculate_center_from_radius(
        self,
        x1: float, y1: float,
        x2: float, y2: float,
        radius: float,
        clockwise: bool
    ) -> Dict[str, float]:
        """Calculate arc center from start, end, and radius"""

        # Midpoint between start and end
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2

        # Distance between start and end
        d = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        # Check if radius is large enough
        if d > 2 * abs(radius):
            logger.warning(f"Radius {radius} too small for arc from ({x1},{y1}) to ({x2},{y2})")
            # Use minimum valid radius
            radius = d / 2

        # Distance from midpoint to center
        h = math.sqrt(radius ** 2 - (d / 2) ** 2) if d < 2 * abs(radius) else 0

        # Direction perpendicular to line from start to end
        dx = (x2 - x1) / d if d > 0 else 0
        dy = (y2 - y1) / d if d > 0 else 0

        # Choose center based on CW/CCW and radius sign
        if (clockwise and radius > 0) or (not clockwise and radius < 0):
            cx = mx - h * dy
            cy = my + h * dx
        else:
            cx = mx + h * dy
            cy = my - h * dx

        return {"X": cx, "Y": cy}

    def calculate_dwell(self, duration: float) -> Dict:
        """Calculate dwell (pause) command"""
        return {
            "type": "dwell",
            "duration": duration,
            "time": duration
        }

    def update_position(self, new_position: Dict[str, float]):
        """Update current position"""
        self.current_position.update(new_position)
        logger.debug(f"Position updated: {self.current_position}")

    def calculate_distance(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """Calculate Euclidean distance between two positions"""
        distance = 0.0
        for axis in ['X', 'Y', 'Z']:
            delta = pos2.get(axis, 0.0) - pos1.get(axis, 0.0)
            distance += delta ** 2
        return math.sqrt(distance)

    def optimize_path(self, moves: List[Dict]) -> List[Dict]:
        """Optimize path with look-ahead and velocity planning"""
        if len(moves) <= 1:
            return moves

        # Simplified velocity planning
        optimized = []

        for i, move in enumerate(moves):
            # Look ahead to next move
            if i < len(moves) - 1:
                next_move = moves[i + 1]

                # Calculate angle between moves
                angle = self._calculate_path_angle(move, next_move)

                # Reduce speed for sharp corners
                if angle > 90:  # Sharp corner
                    move["feed_rate"] *= 0.5
                elif angle > 45:  # Medium corner
                    move["feed_rate"] *= 0.75

            optimized.append(move)

        logger.info(f"Path optimized: {len(optimized)} moves")
        return optimized

    def _calculate_path_angle(self, move1: Dict, move2: Dict) -> float:
        """Calculate angle between two moves"""
        # Simplified: calculate angle between direction vectors
        dir1 = move1.get("direction", {})
        dir2 = move2.get("direction", {})

        if not dir1 or not dir2:
            return 0.0

        # Dot product
        dot = sum(dir1.get(axis, 0) * dir2.get(axis, 0) for axis in ['X', 'Y', 'Z'])

        # Clamp to valid range
        dot = max(-1.0, min(1.0, dot))

        # Angle in degrees
        angle = math.degrees(math.acos(dot))

        return angle
