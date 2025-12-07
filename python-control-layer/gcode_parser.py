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
    INTERPOLATION = "interpolation"  # G05, G07.1, G12.1, G13.1
    WORKSPACE = "workspace"  # G25, G26
    PROBE = "probe"  # G31, G36, G37, G38
    THREAD = "thread"  # G33, G76, G84.2, G84.3
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
        
        # Control flow
        self.label: Optional[str] = None  # Label for GOTO/GOSUB
        self.goto_target: Optional[str] = None  # GOTO target
        self.gosub_target: Optional[str] = None  # GOSUB target
        
        # Macro-related
        self.macro_call: Optional[str] = None  # Macro name (O code or G65/G66)
        self.macro_params: Dict[str, float] = {}  # Macro parameters
        
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
    
    def is_control_flow(self) -> bool:
        """Check if command is a control flow instruction (GOTO, GOSUB)"""
        return self.goto_target is not None or self.gosub_target is not None
    
    def is_label(self) -> bool:
        """Check if command is a label"""
        return self.label is not None
    
    def is_macro_call(self) -> bool:
        """Check if command is a macro call"""
        return self.macro_call is not None
    
    def has_spindle_speed(self) -> bool:
        """Check if command contains spindle speed (S)"""
        return 'S' in self.parameters
    
    def has_feed_rate(self) -> bool:
        """Check if command contains feed rate (F)"""
        return 'F' in self.parameters
    
    def get_spindle_speed(self) -> Optional[float]:
        """Get spindle speed from command"""
        return self.parameters.get('S')
    
    def get_feed_rate(self) -> Optional[float]:
        """Get feed rate from command"""
        return self.parameters.get('F')
    
    def __repr__(self):
        parts = [f"N{self.n_number or self.line_number}: {self.raw_line}"]
        if self.label:
            parts.append(f"Label={self.label}")
        if self.goto_target:
            parts.append(f"GOTO={self.goto_target}")
        if self.gosub_target:
            parts.append(f"GOSUB={self.gosub_target}")
        if self.macro_call:
            parts.append(f"Macro={self.macro_call}")
        return f"GCodeCommand({', '.join(parts)})"


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
        
        # Advanced interpolation
        'G05': ('High-speed machining/NURBS', GCodeType.INTERPOLATION),
        'G05.1': ('AI Contour Control/Look-Ahead', GCodeType.INTERPOLATION),
        'G07.1': ('Cylindrical interpolation', GCodeType.INTERPOLATION),
        'G12.1': ('Polar interpolation mode on', GCodeType.INTERPOLATION),
        'G13.1': ('Polar interpolation mode off', GCodeType.INTERPOLATION),
        
        # Threading
        'G33': ('Thread cutting constant lead', GCodeType.THREAD),
        'G76': ('Fine boring cycle / Threading cycle', GCodeType.THREAD),
        'G84.2': ('Right-hand tapping', GCodeType.THREAD),
        'G84.3': ('Left-hand tapping', GCodeType.THREAD),
        
        # Workspace limiting
        'G25': ('Spindle speed fluctuation detection off', GCodeType.WORKSPACE),
        'G26': ('Spindle speed fluctuation detection on', GCodeType.WORKSPACE),
        'G22': ('Work area limit on', GCodeType.WORKSPACE),
        'G23': ('Work area limit off', GCodeType.WORKSPACE),
        
        # Probing and measurement
        'G31': ('Skip function / Probe', GCodeType.PROBE),
        'G36': ('Auto tool offset measurement', GCodeType.PROBE),
        'G37': ('Auto tool length measurement', GCodeType.PROBE),
        'G38': ('Tool diameter measurement', GCodeType.PROBE),
        'G38.2': ('Probe toward workpiece', GCodeType.PROBE),
        'G38.3': ('Probe toward workpiece (error if no contact)', GCodeType.PROBE),
        'G38.4': ('Probe away from workpiece', GCodeType.PROBE),
        'G38.5': ('Probe away from workpiece (error if no contact)', GCodeType.PROBE),
        
        # Hole patterns
        'G34': ('Bolt hole circle', GCodeType.CYCLE),
        'G35': ('Bolt hole circle with angle increment', GCodeType.CYCLE),
        
        # Advanced cycles
        'G73': ('High-speed peck drilling', GCodeType.CYCLE),
        'G74': ('Left-hand tapping', GCodeType.CYCLE),
        
        # Coordinate systems (extended)
        'G54.1': ('Extended work coordinate system', GCodeType.COORD_SYSTEM),
        'G107': ('Cylindrical coordinate interpolation', GCodeType.INTERPOLATION),
        
        # Other
        'G04': ('Dwell', GCodeType.OTHER),
        'G09': ('Exact stop', GCodeType.OTHER),
        'G10': ('Programmable data input', GCodeType.OTHER),
        'G12': ('Circular pocket CW', GCodeType.CYCLE),
        'G13': ('Circular pocket CCW', GCodeType.CYCLE),
        'G15': ('Polar coordinate cancel', GCodeType.COORD_SYSTEM),
        'G16': ('Polar coordinate', GCodeType.COORD_SYSTEM),
        'G27': ('Reference point check', GCodeType.OTHER),
        'G28': ('Return to home position', GCodeType.OTHER),
        'G29': ('Return from home position', GCodeType.OTHER),
        'G30': ('Return to 2nd, 3rd, 4th home position', GCodeType.OTHER),
        'G50': ('Scaling cancel', GCodeType.COORD_SYSTEM),
        'G51': ('Scaling', GCodeType.COORD_SYSTEM),
        'G61': ('Exact stop mode', GCodeType.OTHER),
        'G62': ('Auto corner override', GCodeType.OTHER),
        'G63': ('Tapping mode', GCodeType.OTHER),
        'G64': ('Continuous path mode', GCodeType.OTHER),
        'G65': ('Macro call', GCodeType.OTHER),
        'G66': ('Macro modal call', GCodeType.OTHER),
        'G67': ('Macro modal call cancel', GCodeType.OTHER),
        'G68': ('Coordinate rotation', GCodeType.COORD_SYSTEM),
        'G69': ('Coordinate rotation cancel', GCodeType.COORD_SYSTEM),
        'G92': ('Coordinate system offset', GCodeType.COORD_SYSTEM),
        'G98': ('Return to initial point in canned cycle', GCodeType.CYCLE),
        'G99': ('Return to R point in canned cycle', GCodeType.CYCLE),
        
        # Haas-specific codes
        'G47': ('Engraving', GCodeType.OTHER),
        'G71': ('Turning roughing cycle (radial)', GCodeType.CYCLE),
        'G72': ('Turning roughing cycle (facing)', GCodeType.CYCLE),
    }
    
    # M-code command definitions
    M_CODE_DEFS = {
        # Program control
        'M00': 'Program stop',
        'M01': 'Optional stop',
        'M02': 'Program end',
        'M30': 'Program end and reset',
        
        # Spindle control
        'M03': 'Spindle on CW',
        'M04': 'Spindle on CCW',
        'M05': 'Spindle stop',
        'M19': 'Spindle orientation',
        'M21': 'Spindle gear shift low (high torque)',
        'M22': 'Spindle gear shift high (high speed)',
        'M29': 'Rigid tapping mode',
        
        # Tool change
        'M06': 'Tool change',
        
        # Coolant control
        'M07': 'Coolant mist on',
        'M08': 'Coolant flood on',
        'M09': 'Coolant off',
        'M50': 'High-pressure coolant on',
        'M51': 'High-pressure coolant off',
        'M88': 'Through-spindle coolant on',
        'M89': 'Through-tool coolant on',
        
        # Feed override control
        'M36': 'Feed override range limit on',
        'M37': 'Feed override range limit off',
        
        # Subprogram control
        'M98': 'Subprogram call',
        'M99': 'Subprogram return / End main program',
        
        # User-defined M-codes (common ranges)
        'M100': 'User macro 100',
        'M101': 'User macro 101',
        'M102': 'User macro 102',
        'M103': 'User macro 103',
        'M104': 'User macro 104',
        'M105': 'User macro 105',
        'M106': 'User macro 106',
        'M107': 'User macro 107',
        'M108': 'User macro 108',
        'M109': 'User macro 109',
        'M110': 'User macro 110',
        
        # Pallet/part control (Mazak)
        'M200': 'Pallet change',
        'M201': 'Pallet clamp',
        'M202': 'Pallet unclamp',
        'M203': 'Pallet rotate',
        
        # Additional common codes
        'M10': 'Clamp on',
        'M11': 'Clamp off',
        'M12': 'Work piece clamp',
        'M13': 'Work piece unclamp',
        'M60': 'Pallet change',
        'M62': 'Output on',
        'M63': 'Output off',
        'M64': 'Output on immediate',
        'M65': 'Output off immediate',
        
        # Haas-specific codes
        'M130': 'Media player control',
    }
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def parse_line(self, line: str, line_number: int) -> Optional[GCodeCommand]:
        """Parse a single line of G-code"""
        cmd = GCodeCommand(line_number, line)
        
        # Remove comments (both styles: parentheses and semicolon)
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
        
        # Check for GOTO (control flow)
        if 'GOTO' in line:
            goto_match = re.search(r'GOTO\s+(\w+)', line)
            if goto_match:
                cmd.goto_target = goto_match.group(1)
                logger.debug(f"GOTO detected: target={cmd.goto_target}")
        
        # Check for GOSUB (subroutine call)
        if 'GOSUB' in line:
            gosub_match = re.search(r'GOSUB\s+(\w+)', line)
            if gosub_match:
                cmd.gosub_target = gosub_match.group(1)
                logger.debug(f"GOSUB detected: target={cmd.gosub_target}")
        
        # Check for labels (e.g., :LABEL or NLABEL) - must be standalone
        # Exclude G-codes, M-codes, O-codes, and N-numbers
        label_match = re.match(r'^:?([A-Z][A-Z0-9_]*):?\s*$', line)
        if label_match:
            label = label_match.group(1)
            # Exclude if it starts with G, M, O, or N followed by digits
            if not re.match(r'^[GMNO]\d', label):
                cmd.label = label
                logger.debug(f"Label detected: {cmd.label}")
                return cmd
        
        # Check for O-code (macro/program number) - must be standalone
        o_match = re.match(r'^O(\d+)\s*$', line)
        if o_match:
            cmd.macro_call = f"O{o_match.group(1)}"
            logger.debug(f"O-code detected: {cmd.macro_call}")
            return cmd
        
        # Parse line number (N)
        n_match = re.search(r'N(\d+)', line)
        if n_match:
            cmd.n_number = int(n_match.group(1))
            line = re.sub(r'N\d+', '', line)
        
        # Parse G-codes (including decimal forms like G54.1)
        g_matches = re.finditer(r'G(\d+\.?\d*)', line)
        for match in g_matches:
            g_num = match.group(1)
            g_code = f"G{g_num}"
            # Normalize: G0 -> G00, G1 -> G01, etc. (but not G54.1)
            if '.' not in g_num and len(g_num) == 1:
                g_code = f"G0{g_num}"
            cmd.g_codes.append(g_code)
            
            # Check for extended work coordinate system (G54.1 Pxx)
            if g_code == 'G54.1':
                p_match = re.search(r'P(\d+)', line)
                if p_match:
                    cmd.parameters['P'] = float(p_match.group(1))
        
        # Parse M-codes
        m_matches = re.finditer(r'M(\d+)', line)
        for match in m_matches:
            m_num = int(match.group(1))
            # Normalize: M3 -> M03, M21 stays M21, etc.
            if m_num < 10:
                m_code = f"M{m_num:02d}"
            else:
                m_code = f"M{m_num}"
            cmd.m_codes.append(m_code)
        
        # Parse tool number (T)
        t_match = re.search(r'T(\d+)', line)
        if t_match:
            cmd.tool_number = int(t_match.group(1))
        
        # Check for macro calls (G65/G66)
        if 'G65' in cmd.g_codes or 'G66' in cmd.g_codes:
            # P parameter in G65/G66 is the macro number
            p_match = re.search(r'P(\d+)', line)
            if p_match:
                cmd.macro_call = f"O{p_match.group(1)}"
        
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
            
            # For macro calls, also store in macro_params
            if cmd.macro_call and letter not in ['G', 'M', 'N', 'T']:
                cmd.macro_params[letter] = value
        
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
        if m_code in self.M_CODE_DEFS:
            return self.M_CODE_DEFS[m_code]
        
        # Handle user-defined M-codes
        m_num = int(m_code[1:])
        if 100 <= m_num <= 199:
            return f"User macro {m_num}"
        elif 200 <= m_num <= 299:
            return f"Macro call {m_num}"
        
        return "Unknown M-code"
    
    def is_manufacturer_specific(self, g_code: str) -> Tuple[bool, str]:
        """Check if G-code is manufacturer-specific and return manufacturer
        
        Returns:
            Tuple of (is_specific, manufacturer_name)
        """
        # Siemens Sinumerik codes
        siemens_codes = ['G05', 'G107']
        if g_code in siemens_codes:
            return True, "Siemens Sinumerik"
        
        # Heidenhain TNC codes
        heidenhain_codes = ['G05.1']
        if g_code in heidenhain_codes:
            return True, "Heidenhain TNC"
        
        # Fanuc extended codes
        fanuc_codes = ['G54.1', 'G65', 'G66', 'G67']
        if g_code in fanuc_codes:
            return True, "Fanuc (Macro B)"
        
        # Haas codes
        haas_codes = ['G47', 'G71', 'G72']
        if g_code in haas_codes:
            return True, "Haas"
        
        # Okuma OSP codes
        okuma_codes = []  # Add specific Okuma codes here
        if g_code in okuma_codes:
            return True, "Okuma OSP"
        
        return False, ""
    
    def supports_foreign_machine_codes(self) -> List[str]:
        """Return list of supported foreign machine code systems"""
        return [
            "Siemens Sinumerik (G05, G107, CYCLE)",
            "Heidenhain TNC (G05.1, CYCL DEF)",
            "Fanuc Macro B (G65/G66, #variables)",
            "Haas (G47, G71/G72, M130)",
            "Okuma OSP (VC variables, CALL OO)",
            "Mazak Mazatrol (M200+ series)",
            "Estlcam (hobbyist/desktop CNC)"
        ]
