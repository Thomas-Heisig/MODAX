"""CNC Cycles - Implements fixed cycles for drilling, tapping, boring, and milling"""
import logging
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class CycleType(Enum):
    """Types of canned cycles"""
    # Drilling cycles
    DRILL = "G81"  # Simple drilling
    DRILL_DWELL = "G82"  # Drilling with dwell
    PECK_DRILL = "G83"  # Peck drilling (deep hole)
    TAP = "G84"  # Tapping
    BORE = "G85"  # Boring
    BORE_STOP = "G86"  # Boring with spindle stop
    BACK_BORE = "G87"  # Back boring
    BORE_MANUAL = "G88"  # Boring with manual retract
    BORE_DWELL = "G89"  # Boring with dwell
    
    # Milling cycles
    CIRCULAR_POCKET_CW = "G12"  # Circular pocket clockwise
    CIRCULAR_POCKET_CCW = "G13"  # Circular pocket counter-clockwise
    RECTANGULAR_POCKET = "G26"  # Rectangular pocket (vendor-specific)


class CNCCycles:
    """Implements CNC fixed cycles"""
    
    # Cycle parameters
    DEFAULT_DWELL_TIME = 0.5  # seconds
    DEFAULT_PECK_DEPTH = 5.0  # mm
    DEFAULT_RETRACT_HEIGHT = 2.0  # mm
    
    def __init__(self):
        # Active cycle
        self.active_cycle: Optional[CycleType] = None
        self.cycle_parameters: Dict = {}
        
        # Cycle return mode
        self.return_to_r = True  # True: return to R plane, False: return to initial Z
        
        logger.info("CNC Cycles initialized")
    
    def set_cycle(self, cycle_type: str, parameters: Dict) -> bool:
        """Set active canned cycle"""
        try:
            self.active_cycle = CycleType(cycle_type)
            self.cycle_parameters = parameters.copy()
            logger.info(f"Cycle {cycle_type} activated with parameters: {parameters}")
            return True
        except ValueError:
            logger.error(f"Invalid cycle type: {cycle_type}")
            return False
    
    def cancel_cycle(self):
        """Cancel active cycle (G80)"""
        if self.active_cycle:
            logger.info(f"Cycle {self.active_cycle.value} cancelled")
        self.active_cycle = None
        self.cycle_parameters = {}
    
    def execute_drill_cycle(self, x: float, y: float, z: float, r: float, f: float) -> List[Dict]:
        """Execute simple drilling cycle (G81)
        
        Args:
            x, y: Hole position
            z: Hole bottom (depth)
            r: Retract plane (rapid approach to this height)
            f: Feed rate
        
        Returns:
            List of motion commands
        """
        moves = []
        
        # 1. Rapid to XY position
        moves.append({
            "type": "rapid",
            "target": {"X": x, "Y": y},
            "description": "Rapid to hole position"
        })
        
        # 2. Rapid to R plane
        moves.append({
            "type": "rapid",
            "target": {"Z": r},
            "description": "Rapid to R plane"
        })
        
        # 3. Feed to Z depth
        moves.append({
            "type": "linear",
            "target": {"Z": z},
            "feed_rate": f,
            "description": "Drill to depth"
        })
        
        # 4. Rapid retract
        if self.return_to_r:
            moves.append({
                "type": "rapid",
                "target": {"Z": r},
                "description": "Rapid retract to R"
            })
        else:
            moves.append({
                "type": "rapid",
                "target": {"Z": r + 10.0},  # Initial Z
                "description": "Rapid retract to initial"
            })
        
        logger.debug(f"G81 drilling cycle at X{x} Y{y} Z{z}")
        return moves
    
    def execute_drill_dwell_cycle(
        self,
        x: float, y: float, z: float, r: float, f: float,
        dwell: Optional[float] = None
    ) -> List[Dict]:
        """Execute drilling cycle with dwell (G82)"""
        moves = []
        
        # Drilling movements (same as G81)
        moves.append({"type": "rapid", "target": {"X": x, "Y": y}})
        moves.append({"type": "rapid", "target": {"Z": r}})
        moves.append({"type": "linear", "target": {"Z": z}, "feed_rate": f})
        
        # Dwell at bottom
        dwell_time = dwell if dwell is not None else self.DEFAULT_DWELL_TIME
        moves.append({
            "type": "dwell",
            "duration": dwell_time,
            "description": f"Dwell {dwell_time}s"
        })
        
        # Retract
        retract_z = r if self.return_to_r else r + 10.0
        moves.append({"type": "rapid", "target": {"Z": retract_z}})
        
        logger.debug(f"G82 drilling with dwell at X{x} Y{y} Z{z}")
        return moves
    
    def execute_peck_drill_cycle(
        self,
        x: float, y: float, z: float, r: float, f: float,
        peck_depth: Optional[float] = None,
        retract: Optional[float] = None
    ) -> List[Dict]:
        """Execute peck drilling cycle (G83)"""
        moves = []
        peck = peck_depth if peck_depth is not None else self.DEFAULT_PECK_DEPTH
        retract_amount = retract if retract is not None else self.DEFAULT_RETRACT_HEIGHT
        
        # Rapid to position
        moves.append({"type": "rapid", "target": {"X": x, "Y": y}})
        moves.append({"type": "rapid", "target": {"Z": r}})
        
        # Peck drilling
        current_depth = r
        while current_depth > z:
            # Calculate next peck depth
            next_depth = max(z, current_depth - peck)
            
            # Feed down
            moves.append({
                "type": "linear",
                "target": {"Z": next_depth},
                "feed_rate": f,
                "description": f"Peck to Z{next_depth:.2f}"
            })
            
            # Rapid retract for chip clearing
            if next_depth > z:
                moves.append({
                    "type": "rapid",
                    "target": {"Z": current_depth - peck + retract_amount},
                    "description": "Retract for chip clearing"
                })
                
                # Rapid back down
                moves.append({
                    "type": "rapid",
                    "target": {"Z": next_depth + 1.0},
                    "description": "Rapid back down"
                })
            
            current_depth = next_depth
        
        # Final retract
        retract_z = r if self.return_to_r else r + 10.0
        moves.append({"type": "rapid", "target": {"Z": retract_z}})
        
        logger.debug(f"G83 peck drilling at X{x} Y{y} Z{z}, peck={peck}mm")
        return moves
    
    def execute_tapping_cycle(
        self,
        x: float, y: float, z: float, r: float,
        spindle_rpm: float, pitch: float
    ) -> List[Dict]:
        """Execute tapping cycle (G84)
        
        Args:
            pitch: Thread pitch in mm (e.g., 1.5 for M10x1.5)
        """
        moves = []
        
        # Calculate feed rate from spindle RPM and pitch
        # F = S * P (where S is RPM, P is pitch)
        feed_rate = spindle_rpm * pitch
        
        # Rapid to position
        moves.append({"type": "rapid", "target": {"X": x, "Y": y}})
        moves.append({"type": "rapid", "target": {"Z": r}})
        
        # Tap down (synchronized with spindle)
        moves.append({
            "type": "linear",
            "target": {"Z": z},
            "feed_rate": feed_rate,
            "description": f"Tap down (F={feed_rate:.1f})",
            "synchronized": True
        })
        
        # Dwell to stop spindle
        moves.append({
            "type": "spindle_stop",
            "description": "Stop spindle"
        })
        
        # Reverse spindle
        moves.append({
            "type": "spindle_reverse",
            "description": "Reverse spindle"
        })
        
        # Tap out (synchronized retract)
        retract_z = r if self.return_to_r else r + 10.0
        moves.append({
            "type": "linear",
            "target": {"Z": retract_z},
            "feed_rate": feed_rate,
            "description": f"Tap out (F={feed_rate:.1f})",
            "synchronized": True
        })
        
        # Restore spindle direction
        moves.append({
            "type": "spindle_forward",
            "description": "Restore spindle direction"
        })
        
        logger.debug(f"G84 tapping at X{x} Y{y} Z{z}, pitch={pitch}mm, F={feed_rate:.1f}")
        return moves
    
    def execute_boring_cycle(self, x: float, y: float, z: float, r: float, f: float) -> List[Dict]:
        """Execute boring cycle (G85)"""
        moves = []
        
        # Similar to G81 but with feed-rate retract
        moves.append({"type": "rapid", "target": {"X": x, "Y": y}})
        moves.append({"type": "rapid", "target": {"Z": r}})
        
        # Feed down
        moves.append({
            "type": "linear",
            "target": {"Z": z},
            "feed_rate": f,
            "description": "Bore to depth"
        })
        
        # Feed retract (not rapid, to maintain surface finish)
        retract_z = r if self.return_to_r else r + 10.0
        moves.append({
            "type": "linear",
            "target": {"Z": retract_z},
            "feed_rate": f,
            "description": "Feed retract"
        })
        
        logger.debug(f"G85 boring at X{x} Y{y} Z{z}")
        return moves
    
    def execute_circular_pocket(
        self,
        x: float, y: float,
        diameter: float,
        depth: float,
        tool_diameter: float,
        clockwise: bool = True,
        stepover: float = 0.6,
        stepdown: float = 3.0,
        feed_rate: float = 500.0
    ) -> List[Dict]:
        """Execute circular pocket milling (G12/G13)
        
        Args:
            x, y: Pocket center
            diameter: Pocket diameter
            depth: Pocket depth
            tool_diameter: Tool diameter
            clockwise: True for G12 (CW), False for G13 (CCW)
            stepover: Stepover as fraction of tool diameter (0.0-1.0)
            stepdown: Depth per pass
            feed_rate: Milling feed rate
        """
        moves = []
        
        # Calculate pocket radius
        pocket_radius = diameter / 2
        tool_radius = tool_diameter / 2
        
        # Validate pocket is larger than tool
        if pocket_radius <= tool_radius:
            logger.error(f"Pocket diameter {diameter} too small for tool diameter {tool_diameter}")
            return moves
        
        # Calculate step values
        radial_step = tool_diameter * stepover
        if radial_step <= 0:
            logger.error("Invalid radial step: stepover must be positive")
            return moves
        
        num_passes = int((pocket_radius - tool_radius) / radial_step) + 1
        num_depths = int(abs(depth) / stepdown) + 1
        
        # Rapid to center
        moves.append({"type": "rapid", "target": {"X": x, "Y": y}})
        
        # Mill at each depth
        current_z = 0.0
        for depth_pass in range(num_depths):
            # Calculate current depth
            current_z = max(-abs(depth), current_z - stepdown)
            
            # Plunge at center
            moves.append({
                "type": "linear",
                "target": {"Z": current_z},
                "feed_rate": feed_rate * 0.5,
                "description": f"Plunge to Z{current_z:.2f}"
            })
            
            # Spiral out from center
            for pass_num in range(num_passes):
                current_radius = tool_radius + (pass_num + 1) * radial_step
                current_radius = min(current_radius, pocket_radius - tool_radius)
                
                # Move to start of arc
                if pass_num == 0:
                    moves.append({
                        "type": "linear",
                        "target": {"X": x + current_radius, "Y": y},
                        "feed_rate": feed_rate,
                        "description": f"Move to radius {current_radius:.2f}"
                    })
                
                # Mill full circle
                moves.append({
                    "type": "circular_cw" if clockwise else "circular_ccw",
                    "target": {"X": x + current_radius, "Y": y},
                    "center": {"X": x, "Y": y},
                    "radius": current_radius,
                    "feed_rate": feed_rate,
                    "description": f"Mill circle radius {current_radius:.2f}"
                })
                
                # Step to next radius
                if pass_num < num_passes - 1:
                    next_radius = tool_radius + (pass_num + 2) * radial_step
                    next_radius = min(next_radius, pocket_radius - tool_radius)
                    moves.append({
                        "type": "linear",
                        "target": {"X": x + next_radius, "Y": y},
                        "feed_rate": feed_rate,
                        "description": f"Step to radius {next_radius:.2f}"
                    })
        
        # Retract
        moves.append({"type": "rapid", "target": {"Z": 5.0}})
        
        cycle = "G12" if clockwise else "G13"
        logger.debug(f"{cycle} circular pocket at X{x} Y{y}, D{diameter}, depth{depth}")
        return moves
    
    def execute_rectangular_pocket(
        self,
        x_min: float, y_min: float,
        x_max: float, y_max: float,
        depth: float,
        tool_diameter: float,
        stepover: float = 0.6,
        stepdown: float = 3.0,
        feed_rate: float = 500.0
    ) -> List[Dict]:
        """Execute rectangular pocket milling (G26 or vendor-specific)"""
        moves = []
        
        # Calculate dimensions
        width = x_max - x_min
        height = y_max - y_min
        tool_radius = tool_diameter / 2
        
        # Calculate step values
        lateral_step = tool_diameter * stepover
        num_depths = int(abs(depth) / stepdown) + 1
        
        # Calculate center
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2
        
        # Rapid to center
        moves.append({"type": "rapid", "target": {"X": center_x, "Y": center_y}})
        
        # Mill at each depth
        current_z = 0.0
        for depth_pass in range(num_depths):
            current_z = max(-abs(depth), current_z - stepdown)
            
            # Plunge
            moves.append({
                "type": "linear",
                "target": {"Z": current_z},
                "feed_rate": feed_rate * 0.5
            })
            
            # Mill in zigzag pattern
            num_passes = int(height / (2 * lateral_step)) + 1
            current_y = center_y - height / 2 + tool_radius
            
            for pass_num in range(num_passes):
                # Move to start of pass
                if pass_num == 0:
                    moves.append({
                        "type": "linear",
                        "target": {"X": center_x - width / 2 + tool_radius, "Y": current_y},
                        "feed_rate": feed_rate
                    })
                
                # Mill pass
                if pass_num % 2 == 0:
                    # Left to right
                    moves.append({
                        "type": "linear",
                        "target": {"X": center_x + width / 2 - tool_radius},
                        "feed_rate": feed_rate
                    })
                else:
                    # Right to left
                    moves.append({
                        "type": "linear",
                        "target": {"X": center_x - width / 2 + tool_radius},
                        "feed_rate": feed_rate
                    })
                
                # Step over
                current_y += lateral_step
                if current_y <= center_y + height / 2 - tool_radius:
                    moves.append({
                        "type": "linear",
                        "target": {"Y": current_y},
                        "feed_rate": feed_rate
                    })
        
        # Retract
        moves.append({"type": "rapid", "target": {"Z": 5.0}})
        
        logger.debug(f"Rectangular pocket from ({x_min},{y_min}) to ({x_max},{y_max}), depth{depth}")
        return moves
