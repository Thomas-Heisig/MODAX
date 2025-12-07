"""G-code Parser - Parses and interprets CNC G-code commands"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class GCodeType(Enum):
    """G-code types"""
    MOTION = "motion"  # G00, G01, G02, G03
    PLANE = "plane"  # G17, G18, G19
    DISTANCE = "distance"  # G90, G91
    FEED_MODE = "feed_mode"  # G94, G95, G96, G97
    UNITS = "units"  # G20, G21
    TOOL_COMP = "tool_comp"  # G40, G41, G42, G43, G44, G49
    COORD_SYSTEM = "coord_system"  # G54-G59, G52, G53, G92
    CYCLE = "cycle"  # G81-G89
    OTHER = "other"


class GCodeCommand:
    """Represents a parsed G-code command"""
    
    def __init__(self, line_number: int, raw_line: str):
        self.line_number = line_number
        self.raw_line = raw_line.strip()
        self.comment = ""
        
        # Command components
        self.g_codes: List[str] = []
        self.m_codes: List[str] = []
        self.parameters: Dict[str, float] = {}
        
        # Special parameters
        self.n_number: Optional[int] = None  # Line number (N)
        self.tool_number: Optional[int] = None  # Tool (T)
        
    def has_motion(self) -> bool:
        """Check if command contains motion G-codes"""
        motion_codes = {'G00', 'G0', 'G01', 'G1', 'G02', 'G2', 'G03', 'G3'}
        return any(g in motion_codes for g in self.g_codes)
    
    def has_coordinates(self) -> bool:
        """Check if command contains coordinate parameters"""
        coord_params = {'X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W'}
        return any(p in self.parameters for p in coord_params)
    
    def get_target_position(self) -> Dict[str, float]:
        """Get target position from command"""
        position = {}
        for axis in ['X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W']:
            if axis in self.parameters:
                position[axis] = self.parameters[axis]
        return position
    
    def __repr__(self):
        return f"GCodeCommand(N{self.n_number or self.line_number}: {self.raw_line})"


class GCodeParser:
    """Parser for G-code programs"""
    
    # G-code command definitions
    G_CODE_DEFS = {
        # Motion commands
        'G00': ('Rapid positioning', GCodeType.MOTION),
        'G0': ('Rapid positioning', GCodeType.MOTION),
        'G01': ('Linear interpolation', GCodeType.MOTION),
        'G1': ('Linear interpolation', GCodeType.MOTION),
        'G02': ('Circular interpolation CW', GCodeType.MOTION),
        'G2': ('Circular interpolation CW', GCodeType.MOTION),
        'G03': ('Circular interpolation CCW', GCodeType.MOTION),
        'G3': ('Circular interpolation CCW', GCodeType.MOTION),
        
        # Plane selection
        'G17': ('XY plane', GCodeType.PLANE),
        'G18': ('ZX plane', GCodeType.PLANE),
        'G19': ('YZ plane', GCodeType.PLANE),
        
        # Units
        'G20': ('Inch units', GCodeType.UNITS),
        'G21': ('Metric units', GCodeType.UNITS),
        
        # Distance mode
        'G90': ('Absolute positioning', GCodeType.DISTANCE),
        'G91': ('Incremental positioning', GCodeType.DISTANCE),
        
        # Feed rate mode
        'G93': ('Inverse time feed', GCodeType.FEED_MODE),
        'G94': ('Feed per minute', GCodeType.FEED_MODE),
        'G95': ('Feed per revolution', GCodeType.FEED_MODE),
        
        # Spindle speed mode
        'G96': ('Constant surface speed', GCodeType.FEED_MODE),
        'G97': ('RPM mode', GCodeType.FEED_MODE),
        
        # Tool radius compensation
        'G40': ('Tool radius compensation off', GCodeType.TOOL_COMP),
        'G41': ('Tool radius compensation left', GCodeType.TOOL_COMP),
        'G42': ('Tool radius compensation right', GCodeType.TOOL_COMP),
        
        # Tool length compensation
        'G43': ('Tool length compensation +', GCodeType.TOOL_COMP),
        'G44': ('Tool length compensation -', GCodeType.TOOL_COMP),
        'G49': ('Tool length compensation cancel', GCodeType.TOOL_COMP),
        
        # Coordinate systems
        'G52': ('Local coordinate system', GCodeType.COORD_SYSTEM),
        'G53': ('Machine coordinate system', GCodeType.COORD_SYSTEM),
        'G54': ('Work coordinate system 1', GCodeType.COORD_SYSTEM),
        'G55': ('Work coordinate system 2', GCodeType.COORD_SYSTEM),
        'G56': ('Work coordinate system 3', GCodeType.COORD_SYSTEM),
        'G57': ('Work coordinate system 4', GCodeType.COORD_SYSTEM),
        'G58': ('Work coordinate system 5', GCodeType.COORD_SYSTEM),
        'G59': ('Work coordinate system 6', GCodeType.COORD_SYSTEM),
        'G59.1': ('Work coordinate system 7', GCodeType.COORD_SYSTEM),
        'G59.2': ('Work coordinate system 8', GCodeType.COORD_SYSTEM),
        'G59.3': ('Work coordinate system 9', GCodeType.COORD_SYSTEM),
        
        # Canned cycles
        'G80': ('Cancel canned cycle', GCodeType.CYCLE),
        'G81': ('Drilling cycle', GCodeType.CYCLE),
        'G82': ('Drilling cycle with dwell', GCodeType.CYCLE),
        'G83': ('Peck drilling cycle', GCodeType.CYCLE),
        'G84': ('Tapping cycle', GCodeType.CYCLE),
        'G85': ('Boring cycle', GCodeType.CYCLE),
        'G86': ('Boring cycle with spindle stop', GCodeType.CYCLE),
        'G87': ('Back boring cycle', GCodeType.CYCLE),
        'G88': ('Boring cycle with manual retract', GCodeType.CYCLE),
        'G89': ('Boring cycle with dwell', GCodeType.CYCLE),
        
        # Other
        'G04': ('Dwell', GCodeType.OTHER),
        'G09': ('Exact stop', GCodeType.OTHER),
        'G10': ('Programmable data input', GCodeType.OTHER),
        'G12': ('Circular pocket CW', GCodeType.CYCLE),
        'G13': ('Circular pocket CCW', GCodeType.CYCLE),
        'G15': ('Polar coordinate cancel', GCodeType.COORD_SYSTEM),
        'G16': ('Polar coordinate', GCodeType.COORD_SYSTEM),
        'G28': ('Return to home position', GCodeType.OTHER),
        'G30': ('Return to 2nd home position', GCodeType.OTHER),
        'G31': ('Probe function', GCodeType.OTHER),
        'G37': ('Tool length measurement', GCodeType.OTHER),
        'G38': ('Tool diameter measurement', GCodeType.OTHER),
        'G50': ('Scaling cancel', GCodeType.COORD_SYSTEM),
        'G51': ('Scaling', GCodeType.COORD_SYSTEM),
        'G61': ('Exact stop mode', GCodeType.OTHER),
        'G64': ('Continuous path mode', GCodeType.OTHER),
        'G68': ('Coordinate rotation', GCodeType.COORD_SYSTEM),
        'G69': ('Coordinate rotation cancel', GCodeType.COORD_SYSTEM),
        'G92': ('Coordinate system offset', GCodeType.COORD_SYSTEM),
    }
    
    # M-code command definitions
    M_CODE_DEFS = {
        'M00': 'Program stop',
        'M01': 'Optional stop',
        'M02': 'Program end',
        'M03': 'Spindle on CW',
        'M04': 'Spindle on CCW',
        'M05': 'Spindle stop',
        'M06': 'Tool change',
        'M07': 'Coolant mist on',
        'M08': 'Coolant flood on',
        'M09': 'Coolant off',
        'M19': 'Spindle orientation',
        'M30': 'Program end and reset',
        'M98': 'Subprogram call',
        'M99': 'Subprogram return',
    }
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def parse_line(self, line: str, line_number: int) -> Optional[GCodeCommand]:
        """Parse a single line of G-code"""
        cmd = GCodeCommand(line_number, line)
        
        # Remove comments
        if '(' in line:
            parts = line.split('(', 1)
            line = parts[0]
            if ')' in parts[1]:
                cmd.comment = parts[1].split(')', 1)[0].strip()
        elif ';' in line:
            parts = line.split(';', 1)
            line = parts[0]
            cmd.comment = parts[1].strip()
        
        # Remove whitespace
        line = line.strip().upper()
        
        # Empty line or comment-only line
        if not line:
            return None
        
        # Parse line number (N)
        n_match = re.search(r'N(\d+)', line)
        if n_match:
            cmd.n_number = int(n_match.group(1))
            line = re.sub(r'N\d+', '', line)
        
        # Parse G-codes
        g_matches = re.finditer(r'G(\d+\.?\d*)', line)
        for match in g_matches:
            g_code = f"G{match.group(1)}"
            # Normalize: G0 -> G00, G1 -> G01, etc.
            if '.' not in g_code and len(match.group(1)) == 1:
                g_code = f"G0{match.group(1)}"
            cmd.g_codes.append(g_code)
        
        # Parse M-codes
        m_matches = re.finditer(r'M(\d+)', line)
        for match in m_matches:
            m_code = f"M{int(match.group(1)):02d}"
            cmd.m_codes.append(m_code)
        
        # Parse tool number (T)
        t_match = re.search(r'T(\d+)', line)
        if t_match:
            cmd.tool_number = int(t_match.group(1))
        
        # Parse parameters (X, Y, Z, A, B, C, I, J, K, R, P, Q, F, S, etc.)
        param_pattern = r'([A-Z])([+-]?\d*\.?\d+)'
        param_matches = re.finditer(param_pattern, line)
        
        for match in param_matches:
            letter = match.group(1)
            value = float(match.group(2))
            
            # Skip G, M, N, T which are already parsed
            if letter in ['G', 'M', 'N', 'T']:
                continue
            
            cmd.parameters[letter] = value
        
        return cmd
    
    def parse_program(self, program: str) -> List[GCodeCommand]:
        """Parse a complete G-code program"""
        self.errors.clear()
        self.warnings.clear()
        
        lines = program.split('\n')
        commands: List[GCodeCommand] = []
        
        for line_num, line in enumerate(lines, 1):
            try:
                cmd = self.parse_line(line, line_num)
                if cmd:
                    commands.append(cmd)
            except Exception as e:
                error_msg = f"Line {line_num}: Parse error - {str(e)}"
                self.errors.append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"Parsed {len(commands)} commands from {len(lines)} lines")
        return commands
    
    def validate_command(self, cmd: GCodeCommand) -> Tuple[bool, List[str]]:
        """Validate a parsed command"""
        errors = []
        
        # Check for unknown G-codes
        for g_code in cmd.g_codes:
            if g_code not in self.G_CODE_DEFS:
                errors.append(f"Unknown G-code: {g_code}")
        
        # Check for unknown M-codes
        for m_code in cmd.m_codes:
            if m_code not in self.M_CODE_DEFS:
                errors.append(f"Unknown M-code: {m_code}")
        
        # Check for conflicting G-codes
        motion_codes = [g for g in cmd.g_codes if g in ['G00', 'G0', 'G01', 'G1', 'G02', 'G2', 'G03', 'G3']]
        if len(motion_codes) > 1:
            errors.append(f"Multiple motion commands in one line: {motion_codes}")
        
        # Check for required parameters in motion commands
        if cmd.has_motion():
            if not cmd.has_coordinates():
                errors.append("Motion command without coordinate parameters")
        
        # Check circular interpolation parameters
        if any(g in cmd.g_codes for g in ['G02', 'G2', 'G03', 'G3']):
            # Need either I,J,K or R parameter
            has_ijk = any(p in cmd.parameters for p in ['I', 'J', 'K'])
            has_r = 'R' in cmd.parameters
            if not (has_ijk or has_r):
                errors.append("Circular interpolation requires I/J/K or R parameter")
        
        return len(errors) == 0, errors
    
    def get_g_code_description(self, g_code: str) -> str:
        """Get description for a G-code"""
        if g_code in self.G_CODE_DEFS:
            return self.G_CODE_DEFS[g_code][0]
        return "Unknown G-code"
    
    def get_m_code_description(self, m_code: str) -> str:
        """Get description for an M-code"""
        return self.M_CODE_DEFS.get(m_code, "Unknown M-code")
