"""CNC Controller - Main controller for CNC machine functions"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CNCMode(Enum):
    """CNC operation modes"""
    AUTO = "auto"  # Automatic program execution
    MANUAL = "manual"  # Manual control (jog)
    MDI = "mdi"  # Manual Data Input
    REFERENCE = "reference"  # Homing/Reference point search
    HANDWHEEL = "handwheel"  # Handwheel operation (MPG)
    SINGLE_STEP = "single_step"  # Single block execution
    DRY_RUN = "dry_run"  # Dry run without cutting
    SIMULATION = "simulation"  # Simulation mode


class CNCState(Enum):
    """CNC machine states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    EMERGENCY = "emergency"
    HOMING = "homing"


class SpindleState(Enum):
    """Spindle states"""
    STOPPED = "stopped"
    CW = "clockwise"  # M03
    CCW = "counter_clockwise"  # M04


class CoolantState(Enum):
    """Coolant states"""
    OFF = "off"  # M09
    FLOOD = "flood"  # M08
    MIST = "mist"  # M07
    BOTH = "both"  # M08 + M07


class CNCController:
    """Main CNC controller managing machine state and operations"""
    
    def __init__(self):
        # Machine state
        self.state = CNCState.IDLE
        self.mode = CNCMode.MANUAL
        self.emergency_stop = False
        
        # Position tracking (in mm)
        self.machine_position = {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}
        self.work_position = {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}
        self.remaining_distance = {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}
        
        # Spindle state
        self.spindle_state = SpindleState.STOPPED
        self.spindle_speed = 0  # RPM
        self.spindle_load = 0.0  # Percentage
        self.spindle_override = 100  # Percentage (50-150%)
        
        # Feed rate
        self.feed_rate = 0.0  # mm/min
        self.feed_override = 100  # Percentage (0-150%)
        self.rapid_override = 100  # Percentage (25-100%)
        
        # Coolant
        self.coolant_state = CoolantState.OFF
        
        # Tool information
        self.current_tool = 0
        self.tool_in_spindle = 0
        self.next_tool = 0
        
        # Active G-codes
        self.active_g_codes = {
            "motion": "G00",  # G00, G01, G02, G03
            "plane": "G17",  # G17, G18, G19
            "distance": "G90",  # G90 (absolute), G91 (incremental)
            "feed_mode": "G94",  # G94 (mm/min), G95 (mm/rev)
            "units": "G21",  # G21 (mm), G20 (inch)
            "tool_radius_comp": "G40",  # G40, G41, G42
            "tool_length_comp": "G49",  # G43, G44, G49
            "coord_system": "G54",  # G54-G59
            "cutter_comp": "G64",  # G61, G64
            "spindle_mode": "G97",  # G96 (CSS), G97 (RPM)
        }
        
        # Active M-codes
        self.active_m_codes = {
            "spindle": "M05",  # M03, M04, M05
            "coolant": "M09",  # M07, M08, M09
            "program": "",  # M00, M01, M02, M30
        }
        
        # Modal parameters
        self.s_value = 0  # Spindle speed
        self.f_value = 0.0  # Feed rate
        self.t_value = 0  # Tool number
        
        # Program execution
        self.program_lines: List[str] = []
        self.current_line = 0
        self.program_name = ""
        self.execution_time = 0.0  # seconds
        self.estimated_time = 0.0  # seconds
        
        # Safety limits (in mm)
        self.software_limits = {
            "X_MIN": -500.0, "X_MAX": 500.0,
            "Y_MIN": -500.0, "Y_MAX": 500.0,
            "Z_MIN": -300.0, "Z_MAX": 0.0,
            "A_MIN": -360.0, "A_MAX": 360.0,
            "B_MIN": -120.0, "B_MAX": 120.0,
            "C_MIN": -360.0, "C_MAX": 360.0,
        }
        
        # Error tracking
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        
        logger.info("CNC Controller initialized")
    
    def emergency_stop_active(self) -> bool:
        """Check if emergency stop is active"""
        return self.emergency_stop or self.state == CNCState.EMERGENCY
    
    def set_emergency_stop(self, active: bool):
        """Activate or deactivate emergency stop"""
        self.emergency_stop = active
        if active:
            self.state = CNCState.EMERGENCY
            self.spindle_state = SpindleState.STOPPED
            self.spindle_speed = 0
            logger.critical("EMERGENCY STOP ACTIVATED")
        else:
            self.state = CNCState.IDLE
            logger.info("Emergency stop released")
    
    def set_mode(self, mode: CNCMode):
        """Set operation mode"""
        if self.state == CNCState.RUNNING:
            logger.warning(f"Cannot change mode while running. Current mode: {self.mode.value}")
            return False
        
        self.mode = mode
        logger.info(f"Mode changed to: {mode.value}")
        return True
    
    def start_program(self, program: List[str], program_name: str = ""):
        """Start program execution"""
        if self.emergency_stop_active():
            logger.error("Cannot start program: emergency stop active")
            return False
        
        if self.state == CNCState.RUNNING:
            logger.warning("Program already running")
            return False
        
        self.program_lines = program
        self.program_name = program_name or f"Program_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_line = 0
        self.execution_time = 0.0
        self.state = CNCState.RUNNING
        
        logger.info(f"Starting program: {self.program_name} ({len(program)} lines)")
        return True
    
    def pause_program(self):
        """Pause program execution"""
        if self.state == CNCState.RUNNING:
            self.state = CNCState.PAUSED
            logger.info("Program paused")
            return True
        return False
    
    def resume_program(self):
        """Resume program execution"""
        if self.state == CNCState.PAUSED:
            self.state = CNCState.RUNNING
            logger.info("Program resumed")
            return True
        return False
    
    def stop_program(self):
        """Stop program execution"""
        if self.state in [CNCState.RUNNING, CNCState.PAUSED]:
            self.state = CNCState.STOPPED
            logger.info("Program stopped")
            return True
        return False
    
    def reset(self):
        """Reset machine to initial state"""
        if self.state == CNCState.RUNNING:
            logger.warning("Cannot reset while running")
            return False
        
        self.state = CNCState.IDLE
        self.current_line = 0
        self.errors.clear()
        self.warnings.clear()
        logger.info("CNC Controller reset")
        return True
    
    def set_spindle(self, state: SpindleState, speed: Optional[int] = None):
        """Set spindle state and speed"""
        if self.emergency_stop_active():
            logger.error("Cannot control spindle: emergency stop active")
            return False
        
        self.spindle_state = state
        
        if speed is not None:
            self.spindle_speed = max(0, min(speed, 24000))  # Limit to max 24000 RPM
            self.s_value = self.spindle_speed
        
        logger.info(f"Spindle: {state.value}, Speed: {self.spindle_speed} RPM")
        return True
    
    def set_coolant(self, state: CoolantState):
        """Set coolant state"""
        self.coolant_state = state
        logger.info(f"Coolant: {state.value}")
        return True
    
    def set_feed_rate(self, rate: float):
        """Set feed rate in mm/min"""
        if rate < 0:
            logger.warning(f"Invalid feed rate: {rate}")
            return False
        
        self.feed_rate = min(rate, 15000.0)  # Limit to max 15000 mm/min
        self.f_value = self.feed_rate
        logger.debug(f"Feed rate set to: {self.feed_rate} mm/min")
        return True
    
    def set_feed_override(self, percentage: int):
        """Set feed override (0-150%)"""
        self.feed_override = max(0, min(percentage, 150))
        logger.debug(f"Feed override: {self.feed_override}%")
        return True
    
    def set_spindle_override(self, percentage: int):
        """Set spindle override (50-150%)"""
        self.spindle_override = max(50, min(percentage, 150))
        logger.debug(f"Spindle override: {self.spindle_override}%")
        return True
    
    def set_rapid_override(self, percentage: int):
        """Set rapid override (25-100%)"""
        self.rapid_override = max(25, min(percentage, 100))
        logger.debug(f"Rapid override: {self.rapid_override}%")
        return True
    
    def check_position_limits(self, position: Dict[str, float]) -> Tuple[bool, str]:
        """Check if position is within software limits"""
        for axis, value in position.items():
            min_key = f"{axis}_MIN"
            max_key = f"{axis}_MAX"
            
            if min_key in self.software_limits and max_key in self.software_limits:
                if value < self.software_limits[min_key]:
                    return False, f"Position {axis}={value} below minimum {self.software_limits[min_key]}"
                if value > self.software_limits[max_key]:
                    return False, f"Position {axis}={value} above maximum {self.software_limits[max_key]}"
        
        return True, ""
    
    def update_position(self, machine_pos: Dict[str, float], work_pos: Dict[str, float]):
        """Update current position"""
        self.machine_position.update(machine_pos)
        self.work_position.update(work_pos)
    
    def add_error(self, code: str, message: str):
        """Add error to error log"""
        error = {
            "timestamp": datetime.now().isoformat(),
            "code": code,
            "message": message,
            "line": self.current_line if self.program_lines else None
        }
        self.errors.append(error)
        logger.error(f"CNC Error {code}: {message}")
        
        if len(self.errors) > 100:  # Keep only last 100 errors
            self.errors = self.errors[-100:]
    
    def add_warning(self, code: str, message: str):
        """Add warning to warning log"""
        warning = {
            "timestamp": datetime.now().isoformat(),
            "code": code,
            "message": message,
            "line": self.current_line if self.program_lines else None
        }
        self.warnings.append(warning)
        logger.warning(f"CNC Warning {code}: {message}")
        
        if len(self.warnings) > 100:  # Keep only last 100 warnings
            self.warnings = self.warnings[-100:]
    
    def get_status(self) -> Dict:
        """Get comprehensive machine status"""
        return {
            "state": self.state.value,
            "mode": self.mode.value,
            "emergency_stop": self.emergency_stop,
            "position": {
                "machine": self.machine_position.copy(),
                "work": self.work_position.copy(),
                "remaining": self.remaining_distance.copy()
            },
            "spindle": {
                "state": self.spindle_state.value,
                "speed": self.spindle_speed,
                "load": self.spindle_load,
                "override": self.spindle_override
            },
            "feed": {
                "rate": self.feed_rate,
                "override": self.feed_override,
                "rapid_override": self.rapid_override
            },
            "coolant": self.coolant_state.value,
            "tool": {
                "current": self.current_tool,
                "in_spindle": self.tool_in_spindle,
                "next": self.next_tool
            },
            "active_codes": {
                "g_codes": self.active_g_codes.copy(),
                "m_codes": self.active_m_codes.copy()
            },
            "modal": {
                "S": self.s_value,
                "F": self.f_value,
                "T": self.t_value
            },
            "program": {
                "name": self.program_name,
                "current_line": self.current_line,
                "total_lines": len(self.program_lines),
                "execution_time": self.execution_time,
                "estimated_time": self.estimated_time
            },
            "errors": self.errors[-10:],  # Last 10 errors
            "warnings": self.warnings[-10:]  # Last 10 warnings
        }
