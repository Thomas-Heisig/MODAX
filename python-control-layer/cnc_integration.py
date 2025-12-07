"""CNC Integration - Integrates CNC functionality with MODAX control layer"""
import logging
from typing import Dict, List, Optional
from cnc_controller import CNCController, CNCMode, CNCState, SpindleState, CoolantState
from gcode_parser import GCodeParser, GCodeCommand
from motion_controller import MotionController
from tool_manager import ToolManager, Tool
from coordinate_system import CoordinateSystemManager
from cnc_cycles import CNCCycles

logger = logging.getLogger(__name__)


class CNCIntegration:
    """Integrates all CNC components into a unified system"""
    
    def __init__(self):
        # Initialize all CNC components
        self.controller = CNCController()
        self.parser = GCodeParser()
        self.motion = MotionController()
        self.tools = ToolManager()
        self.coords = CoordinateSystemManager()
        self.cycles = CNCCycles()
        
        # Execution state
        self.is_executing = False
        self.current_program: List[GCodeCommand] = []
        self.execution_index = 0
        
        logger.info("CNC Integration initialized")
    
    def load_program(self, gcode_program: str, program_name: str = "") -> bool:
        """Load and parse a G-code program"""
        try:
            # Parse program
            commands = self.parser.parse_program(gcode_program)
            
            if not commands:
                logger.error("No valid commands in program")
                return False
            
            # Validate commands
            errors = []
            for cmd in commands:
                valid, cmd_errors = self.parser.validate_command(cmd)
                if not valid:
                    errors.extend([f"Line {cmd.line_number}: {err}" for err in cmd_errors])
            
            if errors:
                logger.error(f"Program validation failed with {len(errors)} errors")
                for error in errors[:10]:  # Show first 10 errors
                    logger.error(error)
                return False
            
            # Store parsed program
            self.current_program = commands
            self.execution_index = 0
            
            # Update controller
            program_lines = [cmd.raw_line for cmd in commands]
            self.controller.start_program(program_lines, program_name)
            
            logger.info(f"Program loaded: {len(commands)} commands")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load program: {e}")
            return False
    
    def execute_command(self, command: GCodeCommand) -> bool:
        """Execute a single G-code command"""
        try:
            # Update controller line number
            self.controller.current_line = command.line_number
            
            # Process G-codes
            for g_code in command.g_codes:
                self._execute_g_code(g_code, command)
            
            # Process M-codes
            for m_code in command.m_codes:
                self._execute_m_code(m_code, command)
            
            # Process tool selection
            if command.tool_number is not None:
                self.tools.select_next_tool(command.tool_number)
            
            # Update modal parameters
            if 'S' in command.parameters:
                self.controller.s_value = int(command.parameters['S'])
            if 'F' in command.parameters:
                self.controller.f_value = command.parameters['F']
            
            return True
            
        except Exception as e:
            error_msg = f"Line {command.line_number}: Execution error - {str(e)}"
            logger.error(error_msg)
            self.controller.add_error("EXEC_ERROR", error_msg)
            return False
    
    def _execute_g_code(self, g_code: str, command: GCodeCommand):
        """Execute a G-code"""
        
        # Motion codes
        if g_code in ['G00', 'G0']:
            self._execute_rapid_move(command)
            self.controller.active_g_codes["motion"] = g_code
            
        elif g_code in ['G01', 'G1']:
            self._execute_linear_move(command)
            self.controller.active_g_codes["motion"] = g_code
            
        elif g_code in ['G02', 'G2']:
            self._execute_circular_move(command, clockwise=True)
            self.controller.active_g_codes["motion"] = g_code
            
        elif g_code in ['G03', 'G3']:
            self._execute_circular_move(command, clockwise=False)
            self.controller.active_g_codes["motion"] = g_code
        
        # Plane selection
        elif g_code in ['G17', 'G18', 'G19']:
            self.motion.set_plane(g_code)
            self.controller.active_g_codes["plane"] = g_code
        
        # Units
        elif g_code in ['G20', 'G21']:
            self.controller.active_g_codes["units"] = g_code
            logger.info(f"Units: {'inch' if g_code == 'G20' else 'metric'}")
        
        # Distance mode
        elif g_code == 'G90':
            self.motion.set_distance_mode(absolute=True)
            self.controller.active_g_codes["distance"] = g_code
            
        elif g_code == 'G91':
            self.motion.set_distance_mode(absolute=False)
            self.controller.active_g_codes["distance"] = g_code
        
        # Feed rate mode
        elif g_code in ['G94', 'G95', 'G96', 'G97']:
            self.controller.active_g_codes["feed_mode"] = g_code
            logger.info(f"Feed mode: {g_code}")
        
        # Tool compensation
        elif g_code in ['G40', 'G41', 'G42']:
            self.tools.set_tool_radius_compensation(g_code)
            self.controller.active_g_codes["tool_radius_comp"] = g_code
            
        elif g_code in ['G43', 'G44', 'G49']:
            if g_code == 'G49':
                self.tools.set_tool_length_compensation(0, g_code)
            else:
                tool_num = command.parameters.get('H', self.controller.current_tool)
                self.tools.set_tool_length_compensation(int(tool_num), g_code)
            self.controller.active_g_codes["tool_length_comp"] = g_code
        
        # Coordinate systems
        elif g_code in self.coords.WORK_COORDS:
            self.coords.set_active_coordinate_system(g_code)
            self.controller.active_g_codes["coord_system"] = g_code
            
        elif g_code == 'G52':
            # Local coordinate system
            offsets = command.get_target_position()
            if offsets:
                self.coords.set_local_offset(offsets)
            else:
                self.coords.cancel_local_offset()
                
        elif g_code == 'G92':
            # Coordinate system shift
            position = command.get_target_position()
            if position:
                self.coords.set_g92_offset(position)
        
        # Coordinate transformations
        elif g_code == 'G68':
            # Coordinate rotation
            x = command.parameters.get('X', 0.0)
            y = command.parameters.get('Y', 0.0)
            r = command.parameters.get('R', 0.0)
            self.coords.set_rotation(x, y, r)
            
        elif g_code == 'G69':
            # Cancel rotation
            self.coords.cancel_rotation()
        
        elif g_code == 'G51':
            # Coordinate scaling
            center = command.get_target_position()
            p = command.parameters.get('P', 1.0)
            factors = {'X': p, 'Y': p, 'Z': p}
            self.coords.set_scaling(center, factors)
            
        elif g_code == 'G50':
            # Cancel scaling
            self.coords.cancel_scaling()
        
        # Canned cycles
        elif g_code == 'G80':
            self.cycles.cancel_cycle()
            
        elif g_code in ['G81', 'G82', 'G83', 'G84', 'G85', 'G86', 'G87', 'G88', 'G89']:
            params = {
                'X': command.parameters.get('X', 0.0),
                'Y': command.parameters.get('Y', 0.0),
                'Z': command.parameters.get('Z', 0.0),
                'R': command.parameters.get('R', 0.0),
                'F': command.parameters.get('F', self.controller.f_value),
                'P': command.parameters.get('P', 0.0),
                'Q': command.parameters.get('Q', 5.0),
            }
            self.cycles.set_cycle(g_code, params)
        
        # Other codes
        elif g_code == 'G04':
            # Dwell
            p = command.parameters.get('P', 0.0)
            logger.info(f"Dwell {p} seconds")
        
        else:
            logger.warning(f"G-code {g_code} not fully implemented")
    
    def _execute_m_code(self, m_code: str, command: GCodeCommand):
        """Execute an M-code"""
        
        # Spindle control
        if m_code == 'M03':
            speed = self.controller.s_value
            self.controller.set_spindle(SpindleState.CW, speed)
            self.controller.active_m_codes["spindle"] = m_code
            
        elif m_code == 'M04':
            speed = self.controller.s_value
            self.controller.set_spindle(SpindleState.CCW, speed)
            self.controller.active_m_codes["spindle"] = m_code
            
        elif m_code == 'M05':
            self.controller.set_spindle(SpindleState.STOPPED)
            self.controller.active_m_codes["spindle"] = m_code
        
        # Tool change
        elif m_code == 'M06':
            tool_num = self.controller.t_value
            if tool_num > 0:
                self.tools.change_tool(tool_num)
                self.controller.current_tool = tool_num
        
        # Coolant control
        elif m_code == 'M07':
            self.controller.set_coolant(CoolantState.MIST)
            self.controller.active_m_codes["coolant"] = m_code
            
        elif m_code == 'M08':
            self.controller.set_coolant(CoolantState.FLOOD)
            self.controller.active_m_codes["coolant"] = m_code
            
        elif m_code == 'M09':
            self.controller.set_coolant(CoolantState.OFF)
            self.controller.active_m_codes["coolant"] = m_code
        
        # Program control
        elif m_code == 'M00':
            logger.info("Program stop (M00)")
            self.controller.pause_program()
            
        elif m_code == 'M01':
            logger.info("Optional stop (M01)")
            # Check if optional stop is enabled
            
        elif m_code in ['M02', 'M30']:
            logger.info(f"Program end ({m_code})")
            self.controller.stop_program()
        
        else:
            logger.warning(f"M-code {m_code} not fully implemented")
    
    def _execute_rapid_move(self, command: GCodeCommand):
        """Execute rapid positioning (G00)"""
        target = command.get_target_position()
        if target:
            move = self.motion.calculate_linear_move(target, 0, is_rapid=True)
            logger.debug(f"Rapid move to {target}")
            # In real system, would send to motion controller
    
    def _execute_linear_move(self, command: GCodeCommand):
        """Execute linear interpolation (G01)"""
        target = command.get_target_position()
        feed = command.parameters.get('F', self.controller.f_value)
        
        if target:
            self.controller.set_feed_rate(feed)
            move = self.motion.calculate_linear_move(target, feed, is_rapid=False)
            logger.debug(f"Linear move to {target} at F{feed}")
            # In real system, would send to motion controller
    
    def _execute_circular_move(self, command: GCodeCommand, clockwise: bool):
        """Execute circular interpolation (G02/G03)"""
        target = command.get_target_position()
        feed = command.parameters.get('F', self.controller.f_value)
        
        # Get center offset or radius
        center_offset = {
            'I': command.parameters.get('I', 0.0),
            'J': command.parameters.get('J', 0.0),
            'K': command.parameters.get('K', 0.0)
        }
        radius = command.parameters.get('R')
        
        if target:
            self.controller.set_feed_rate(feed)
            move = self.motion.calculate_circular_move(
                target, center_offset, feed, clockwise, radius
            )
            direction = "CW" if clockwise else "CCW"
            logger.debug(f"Circular move {direction} to {target}")
            # In real system, would send to motion controller
    
    def get_comprehensive_status(self) -> Dict:
        """Get complete CNC system status"""
        return {
            "controller": self.controller.get_status(),
            "motion": {
                "position": self.motion.current_position,
                "plane": self.motion.active_plane,
                "absolute_mode": self.motion.absolute_mode,
            },
            "tools": {
                "in_spindle": self.tools.tool_in_spindle,
                "next_tool": self.tools.next_tool,
                "tool_list": self.tools.get_tool_list()[:5],  # First 5 tools
                "magazine": self.tools.get_magazine_status(),
                "compensation": {
                    "radius": self.tools.radius_comp_mode,
                    "length_offset": self.tools.length_comp_offset
                }
            },
            "coordinates": self.coords.get_transformation_status(),
            "cycles": {
                "active": self.cycles.active_cycle.value if self.cycles.active_cycle else None,
                "parameters": self.cycles.cycle_parameters
            },
            "program": {
                "loaded": len(self.current_program) > 0,
                "total_commands": len(self.current_program),
                "current_index": self.execution_index
            }
        }
    
    def initialize_demo_tools(self):
        """Initialize some demo tools for testing"""
        demo_tools = [
            Tool(1, "End Mill 10mm", "end_mill", 10.0, 75.0, 4, "carbide", "TiAlN", 
                 expected_life=120.0),
            Tool(2, "Drill 8mm", "drill", 8.0, 80.0, 2, "HSS", "TiN",
                 expected_life=90.0),
            Tool(3, "Face Mill 50mm", "face_mill", 50.0, 100.0, 6, "carbide", "TiAlN",
                 expected_life=150.0),
            Tool(4, "Tap M10", "tap", 10.0, 70.0, 1, "HSS", "none",
                 expected_life=60.0),
            Tool(5, "End Mill 6mm", "end_mill", 6.0, 60.0, 4, "carbide", "TiN",
                 expected_life=100.0),
        ]
        
        for tool in demo_tools:
            self.tools.add_tool(tool)
            # Load into magazine
            self.tools.load_tool_to_magazine(tool.number, tool.number)
        
        logger.info(f"Initialized {len(demo_tools)} demo tools")


# Global CNC integration instance
_cnc_integration: Optional[CNCIntegration] = None


def get_cnc_integration() -> CNCIntegration:
    """Get or create CNC integration instance"""
    global _cnc_integration
    if _cnc_integration is None:
        _cnc_integration = CNCIntegration()
        _cnc_integration.initialize_demo_tools()
    return _cnc_integration
