"""Tool Manager - Manages CNC tools, tool changes, and compensations"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """Represents a CNC tool"""
    number: int
    name: str
    type: str  # 'drill', 'end_mill', 'face_mill', 'tap', 'reamer', etc.
    diameter: float  # mm
    length: float  # mm
    flutes: int
    material: str  # 'HSS', 'carbide', 'ceramic', etc.
    coating: str  # 'TiN', 'TiAlN', 'none', etc.
    
    # Offsets
    length_offset: float = 0.0  # Z offset in mm
    radius_offset: float = 0.0  # XY offset in mm
    
    # Wear tracking
    cutting_time: float = 0.0  # Total cutting time in minutes
    expected_life: float = 120.0  # Expected life in minutes
    wear_percentage: float = 0.0  # 0-100%
    
    # Status
    is_broken: bool = False
    is_available: bool = True
    last_measured: Optional[str] = None
    
    # Additional data
    manufacturer: str = ""
    part_number: str = ""
    notes: str = ""


class ToolManager:
    """Manages CNC tools and tool operations"""
    
    # Tool change settings
    TOOL_CHANGE_TIME = 6.0  # seconds
    TOOL_MEASURE_TIME = 3.0  # seconds
    
    # Compensation modes
    COMP_OFF = "G40"
    COMP_LEFT = "G41"
    COMP_RIGHT = "G42"
    
    def __init__(self, magazine_capacity: int = 24):
        self.magazine_capacity = magazine_capacity
        self.tools: Dict[int, Tool] = {}
        
        # Current state
        self.tool_in_spindle: Optional[int] = None
        self.next_tool: Optional[int] = None
        
        # Tool radius compensation
        self.radius_comp_mode = self.COMP_OFF
        self.radius_comp_active = False
        
        # Tool length compensation
        self.length_comp_offset = 0.0
        self.length_comp_active = False
        
        # Tool measurement
        self.tool_setter_position = {"X": 0.0, "Y": 0.0, "Z": -100.0}
        
        # Magazine status
        self.magazine_slots: Dict[int, Optional[int]] = {
            slot: None for slot in range(1, magazine_capacity + 1)
        }
        
        logger.info(f"Tool Manager initialized with {magazine_capacity} slot magazine")
    
    def add_tool(self, tool: Tool) -> bool:
        """Add or update a tool in the tool table"""
        if tool.number <= 0 or tool.number > 999:
            logger.error(f"Invalid tool number: {tool.number}")
            return False
        
        self.tools[tool.number] = tool
        logger.info(f"Tool T{tool.number} added: {tool.name} ({tool.type}, Ø{tool.diameter}mm)")
        return True
    
    def remove_tool(self, tool_number: int) -> bool:
        """Remove a tool from the tool table"""
        if tool_number in self.tools:
            tool = self.tools[tool_number]
            del self.tools[tool_number]
            
            # Remove from magazine if present
            for slot, t_num in self.magazine_slots.items():
                if t_num == tool_number:
                    self.magazine_slots[slot] = None
            
            logger.info(f"Tool T{tool_number} removed: {tool.name}")
            return True
        return False
    
    def get_tool(self, tool_number: int) -> Optional[Tool]:
        """Get tool by number"""
        return self.tools.get(tool_number)
    
    def load_tool_to_magazine(self, tool_number: int, slot: int) -> bool:
        """Load a tool into a magazine slot"""
        if slot < 1 or slot > self.magazine_capacity:
            logger.error(f"Invalid magazine slot: {slot}")
            return False
        
        if tool_number not in self.tools:
            logger.error(f"Tool T{tool_number} not found in tool table")
            return False
        
        if self.magazine_slots[slot] is not None:
            logger.warning(f"Magazine slot {slot} already occupied by T{self.magazine_slots[slot]}")
            return False
        
        self.magazine_slots[slot] = tool_number
        logger.info(f"Tool T{tool_number} loaded into magazine slot {slot}")
        return True
    
    def unload_tool_from_magazine(self, slot: int) -> Optional[int]:
        """Unload a tool from a magazine slot"""
        if slot < 1 or slot > self.magazine_capacity:
            logger.error(f"Invalid magazine slot: {slot}")
            return None
        
        tool_number = self.magazine_slots[slot]
        if tool_number is None:
            logger.warning(f"Magazine slot {slot} is empty")
            return None
        
        self.magazine_slots[slot] = None
        logger.info(f"Tool T{tool_number} unloaded from magazine slot {slot}")
        return tool_number
    
    def find_tool_in_magazine(self, tool_number: int) -> Optional[int]:
        """Find which slot contains a tool"""
        for slot, t_num in self.magazine_slots.items():
            if t_num == tool_number:
                return slot
        return None
    
    def change_tool(self, new_tool_number: int) -> bool:
        """Perform tool change (M06)"""
        if new_tool_number not in self.tools:
            logger.error(f"Tool T{new_tool_number} not found in tool table")
            return False
        
        tool = self.tools[new_tool_number]
        
        if not tool.is_available:
            logger.error(f"Tool T{new_tool_number} is not available")
            return False
        
        if tool.is_broken:
            logger.error(f"Tool T{new_tool_number} is marked as broken")
            return False
        
        # Check if tool is in magazine
        slot = self.find_tool_in_magazine(new_tool_number)
        if slot is None:
            logger.error(f"Tool T{new_tool_number} not found in magazine")
            return False
        
        # Perform tool change
        old_tool = self.tool_in_spindle
        self.tool_in_spindle = new_tool_number
        self.next_tool = None
        
        # Apply tool offsets
        self.length_comp_offset = tool.length_offset
        
        logger.info(f"Tool change: T{old_tool} -> T{new_tool_number} ({tool.name})")
        return True
    
    def select_next_tool(self, tool_number: int) -> bool:
        """Pre-select next tool for quick change"""
        if tool_number not in self.tools:
            logger.error(f"Tool T{tool_number} not found in tool table")
            return False
        
        self.next_tool = tool_number
        logger.info(f"Next tool selected: T{tool_number}")
        return True
    
    def set_tool_length_compensation(self, tool_number: int, mode: str = "G43") -> bool:
        """Set tool length compensation (G43, G44, G49)"""
        if mode == "G49":
            # Cancel compensation
            self.length_comp_active = False
            self.length_comp_offset = 0.0
            logger.info("Tool length compensation cancelled (G49)")
            return True
        
        if tool_number not in self.tools:
            logger.error(f"Tool T{tool_number} not found")
            return False
        
        tool = self.tools[tool_number]
        
        if mode == "G43":
            # Positive compensation
            self.length_comp_offset = tool.length_offset
            self.length_comp_active = True
            logger.info(f"Tool length compensation +{tool.length_offset}mm (G43)")
        elif mode == "G44":
            # Negative compensation
            self.length_comp_offset = -tool.length_offset
            self.length_comp_active = True
            logger.info(f"Tool length compensation -{tool.length_offset}mm (G44)")
        else:
            logger.error(f"Invalid compensation mode: {mode}")
            return False
        
        return True
    
    def set_tool_radius_compensation(self, mode: str, direction: Optional[str] = None) -> bool:
        """Set tool radius compensation (G40, G41, G42)"""
        if mode == "G40":
            # Cancel compensation
            self.radius_comp_mode = self.COMP_OFF
            self.radius_comp_active = False
            logger.info("Tool radius compensation cancelled (G40)")
            return True
        
        if self.tool_in_spindle is None:
            logger.error("No tool in spindle for radius compensation")
            return False
        
        tool = self.tools.get(self.tool_in_spindle)
        if tool is None:
            logger.error(f"Tool T{self.tool_in_spindle} not found")
            return False
        
        if mode == "G41":
            # Left compensation
            self.radius_comp_mode = self.COMP_LEFT
            self.radius_comp_active = True
            logger.info(f"Tool radius compensation left (G41), radius={tool.diameter/2}mm")
        elif mode == "G42":
            # Right compensation
            self.radius_comp_mode = self.COMP_RIGHT
            self.radius_comp_active = True
            logger.info(f"Tool radius compensation right (G42), radius={tool.diameter/2}mm")
        else:
            logger.error(f"Invalid compensation mode: {mode}")
            return False
        
        return True
    
    def measure_tool(self, tool_number: int) -> Dict[str, float]:
        """Measure tool length and diameter"""
        if tool_number not in self.tools:
            logger.error(f"Tool T{tool_number} not found")
            return {}
        
        tool = self.tools[tool_number]
        
        # Simulate measurement (in real system, would use probe)
        measured_length = tool.length + (tool.wear_percentage * 0.001)  # Length doesn't change much
        measured_diameter = tool.diameter * (1 - tool.wear_percentage / 100)  # Diameter reduces with wear
        
        # Update tool data
        tool.last_measured = datetime.now().isoformat()
        
        logger.info(f"Tool T{tool_number} measured: L={measured_length:.3f}mm, D={measured_diameter:.3f}mm")
        
        return {
            "length": measured_length,
            "diameter": measured_diameter,
            "wear": tool.wear_percentage
        }
    
    def update_tool_wear(self, tool_number: int, cutting_time: float):
        """Update tool wear based on cutting time"""
        if tool_number not in self.tools:
            return
        
        tool = self.tools[tool_number]
        tool.cutting_time += cutting_time
        tool.wear_percentage = min(100.0, (tool.cutting_time / tool.expected_life) * 100)
        
        # Check if tool should be replaced
        if tool.wear_percentage >= 90:
            logger.warning(f"Tool T{tool_number} wear: {tool.wear_percentage:.1f}% - replacement recommended")
        
        if tool.wear_percentage >= 100:
            tool.is_available = False
            logger.error(f"Tool T{tool_number} exceeded life expectancy - marked as unavailable")
    
    def detect_tool_breakage(self, tool_number: int):
        """Mark tool as broken"""
        if tool_number in self.tools:
            tool = self.tools[tool_number]
            tool.is_broken = True
            tool.is_available = False
            logger.critical(f"Tool T{tool_number} BREAKAGE DETECTED!")
    
    def get_tool_list(self) -> List[Dict]:
        """Get list of all tools"""
        return [
            {
                "number": tool.number,
                "name": tool.name,
                "type": tool.type,
                "diameter": tool.diameter,
                "length": tool.length,
                "flutes": tool.flutes,
                "material": tool.material,
                "coating": tool.coating,
                "wear": tool.wear_percentage,
                "life_remaining": max(0, tool.expected_life - tool.cutting_time),
                "available": tool.is_available,
                "broken": tool.is_broken,
                "in_magazine": self.find_tool_in_magazine(tool.number)
            }
            for tool in self.tools.values()
        ]
    
    def get_magazine_status(self) -> Dict:
        """Get magazine status"""
        return {
            "capacity": self.magazine_capacity,
            "occupied_slots": sum(1 for t in self.magazine_slots.values() if t is not None),
            "slots": {
                slot: {
                    "tool_number": t_num,
                    "tool_name": self.tools[t_num].name if t_num and t_num in self.tools else None
                }
                for slot, t_num in self.magazine_slots.items()
            }
        }
