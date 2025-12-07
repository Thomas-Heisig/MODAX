# CNC Machine Features Documentation

## Overview

MODAX now includes comprehensive CNC machine functionality, supporting the full range of functions typical for professional CNC machines including milling machines, lathes, and machining centers.

**Version:** 0.2.0  
**Last Updated:** 2025-12-07

## Architecture

The CNC functionality is implemented as a modular system within the Control Layer:

```
python-control-layer/
├── cnc_controller.py        # Main CNC controller
├── gcode_parser.py          # G-code parser and interpreter
├── motion_controller.py     # Motion planning and interpolation
├── tool_manager.py          # Tool management and compensation
├── coordinate_system.py     # Coordinate transformations
├── cnc_cycles.py            # Fixed cycles (drilling, milling)
└── cnc_integration.py       # Integration with MODAX
```

## Core Components

### 1. CNC Controller (`cnc_controller.py`)

The main controller manages overall machine state and operations.

**Features:**
- Machine states: IDLE, RUNNING, PAUSED, STOPPED, ERROR, EMERGENCY, HOMING
- Operation modes: AUTO, MANUAL, MDI, REFERENCE, HANDWHEEL, SINGLE_STEP, DRY_RUN, SIMULATION
- Position tracking (machine, work, remaining distance)
- Spindle control (CW/CCW/STOPPED, speed, load, override)
- Feed rate control with override (0-150%)
- Coolant control (OFF, FLOOD, MIST, BOTH)
- Emergency stop functionality
- Software position limits
- Error and warning tracking
- Active G-code and M-code tracking

**Example Usage:**
```python
from cnc_controller import CNCController, CNCMode, SpindleState

controller = CNCController()
controller.set_mode(CNCMode.AUTO)
controller.set_spindle(SpindleState.CW, 1000)  # 1000 RPM
controller.set_feed_rate(500.0)  # 500 mm/min
```

### 2. G-code Parser (`gcode_parser.py`)

Parses and validates G-code programs according to ISO 6983 (DIN 66025) standard.

**Supported G-codes:**

#### Motion Commands
- **G00/G0:** Rapid positioning
- **G01/G1:** Linear interpolation
- **G02/G2:** Circular interpolation clockwise
- **G03/G3:** Circular interpolation counter-clockwise

#### Plane Selection
- **G17:** XY plane
- **G18:** ZX plane
- **G19:** YZ plane

#### Units
- **G20:** Inch units
- **G21:** Metric units (mm)

#### Distance Mode
- **G90:** Absolute positioning
- **G91:** Incremental positioning

#### Feed Rate Mode
- **G93:** Inverse time feed
- **G94:** Feed per minute (mm/min)
- **G95:** Feed per revolution (mm/rev)

#### Spindle Speed Mode
- **G96:** Constant surface speed (CSS)
- **G97:** RPM mode

#### Tool Radius Compensation
- **G40:** Tool radius compensation off
- **G41:** Tool radius compensation left
- **G42:** Tool radius compensation right

#### Tool Length Compensation
- **G43:** Tool length compensation positive
- **G44:** Tool length compensation negative
- **G49:** Tool length compensation cancel

#### Work Coordinate Systems
- **G52:** Local coordinate system
- **G53:** Machine coordinate system
- **G54-G59:** Work coordinate systems 1-6
- **G59.1-G59.3:** Extended work coordinate systems 7-9

#### Coordinate Transformations
- **G50:** Scaling cancel
- **G51:** Scaling
- **G68:** Coordinate rotation
- **G69:** Coordinate rotation cancel
- **G92:** Coordinate system offset

#### Drilling Cycles
- **G80:** Cancel canned cycle
- **G81:** Drilling cycle
- **G82:** Drilling cycle with dwell
- **G83:** Peck drilling cycle (deep hole)
- **G84:** Tapping cycle
- **G85:** Boring cycle
- **G86:** Boring cycle with spindle stop
- **G87:** Back boring cycle
- **G88:** Boring cycle with manual retract
- **G89:** Boring cycle with dwell

#### Milling Cycles
- **G12:** Circular pocket clockwise
- **G13:** Circular pocket counter-clockwise

#### Other Commands
- **G04:** Dwell
- **G09:** Exact stop
- **G10:** Programmable data input
- **G15:** Polar coordinate cancel
- **G16:** Polar coordinate
- **G28:** Return to home position
- **G30:** Return to 2nd home position
- **G31:** Probe function
- **G37:** Tool length measurement
- **G38:** Tool diameter measurement
- **G61:** Exact stop mode
- **G64:** Continuous path mode

**Supported M-codes:**
- **M00:** Program stop
- **M01:** Optional stop
- **M02:** Program end
- **M03:** Spindle on CW
- **M04:** Spindle on CCW
- **M05:** Spindle stop
- **M06:** Tool change
- **M07:** Coolant mist on
- **M08:** Coolant flood on
- **M09:** Coolant off
- **M19:** Spindle orientation
- **M30:** Program end and reset
- **M98:** Subprogram call
- **M99:** Subprogram return

**Example:**
```python
from gcode_parser import GCodeParser

parser = GCodeParser()
program = """
G90 G54 G17
G00 X10 Y20 Z5
G01 Z-5 F500
M03 S1000
"""
commands = parser.parse_program(program)
```

### 3. Motion Controller (`motion_controller.py`)

Handles motion interpolation and path planning.

**Features:**
- Linear interpolation (G01)
- Circular interpolation (G02/G03)
- Helical interpolation (spiral milling)
- Path optimization with look-ahead
- Velocity planning
- S-curve acceleration
- Corner rounding
- Configurable motion limits

**Parameters:**
- Max feed rate: 15,000 mm/min
- Max rapid rate: 30,000 mm/min
- Max acceleration: 5,000 mm/s²
- Max jerk: 50,000 mm/s³
- Look-ahead blocks: 100

**Example:**
```python
from motion_controller import MotionController

motion = MotionController()
motion.set_plane("G17")  # XY plane

# Linear move
target = {"X": 100.0, "Y": 50.0, "Z": -10.0}
move = motion.calculate_linear_move(target, feed_rate=500.0)

# Circular move
center_offset = {"I": 25.0, "J": 0.0}
move = motion.calculate_circular_move(target, center_offset, 500.0, clockwise=True)
```

### 4. Tool Manager (`tool_manager.py`)

Manages CNC tools, tool changes, and compensations.

**Features:**
- Tool table management (up to 999 tools)
- Tool magazine management (default 24 slots)
- Automatic tool change (M06)
- Tool pre-selection
- Tool length compensation (G43/G44/G49)
- Tool radius compensation (G40/G41/G42)
- 3D tool radius compensation
- Tool wear tracking
- Tool life management
- Tool breakage detection
- Automatic tool measurement

**Tool Properties:**
- Number, name, type
- Diameter, length, flutes
- Material, coating
- Length offset, radius offset
- Cutting time, expected life, wear percentage
- Status (available, broken)
- Manufacturer, part number

**Example:**
```python
from tool_manager import ToolManager, Tool

tools = ToolManager(magazine_capacity=24)

# Add tool
tool = Tool(
    number=1,
    name="End Mill 10mm",
    type="end_mill",
    diameter=10.0,
    length=75.0,
    flutes=4,
    material="carbide",
    coating="TiAlN",
    expected_life=120.0
)
tools.add_tool(tool)
tools.load_tool_to_magazine(1, 1)

# Tool change
tools.change_tool(1)

# Set compensation
tools.set_tool_length_compensation(1, "G43")
tools.set_tool_radius_compensation("G41")
```

### 5. Coordinate System Manager (`coordinate_system.py`)

Manages work coordinate systems and transformations.

**Features:**
- 9 work coordinate systems (G54-G59.3)
- Machine coordinate system (G53)
- Local coordinate system (G52)
- Coordinate system offset (G92)
- Coordinate rotation (G68/G69)
- Coordinate scaling (G50/G51)
- Coordinate mirroring
- Polar coordinates (G15/G16)
- Coordinate conversion (machine ↔ work)

**Example:**
```python
from coordinate_system import CoordinateSystemManager

coords = CoordinateSystemManager()

# Set work offset
coords.set_work_offsets("G54", {"X": 100.0, "Y": 50.0, "Z": 25.0})
coords.set_active_coordinate_system("G54")

# Coordinate rotation
coords.set_rotation(center_x=0.0, center_y=0.0, angle=45.0)

# Coordinate scaling
coords.set_scaling({"X": 0.0, "Y": 0.0, "Z": 0.0}, {"X": 1.5, "Y": 1.5, "Z": 1.0})

# Convert coordinates
machine_pos = {"X": 150.0, "Y": 75.0, "Z": 10.0}
work_pos = coords.machine_to_work(machine_pos)
```

### 6. CNC Cycles (`cnc_cycles.py`)

Implements fixed cycles for drilling, tapping, boring, and milling.

**Drilling Cycles:**
- **G81:** Simple drilling
- **G82:** Drilling with dwell
- **G83:** Peck drilling (for deep holes)
- **G84:** Tapping (synchronized with spindle)
- **G85:** Boring
- **G86:** Boring with spindle stop

**Milling Cycles:**
- **G12/G13:** Circular pocket milling
- **G26:** Rectangular pocket milling (vendor-specific)

**Example:**
```python
from cnc_cycles import CNCCycles

cycles = CNCCycles()

# Drilling cycle
cycles.set_cycle("G81", {
    "X": 50.0, "Y": 50.0,  # Hole position
    "Z": -20.0,  # Hole depth
    "R": 2.0,  # Retract plane
    "F": 200.0  # Feed rate
})

# Peck drilling
cycles.set_cycle("G83", {
    "X": 100.0, "Y": 100.0,
    "Z": -50.0,
    "R": 5.0,
    "Q": 5.0,  # Peck depth
    "F": 150.0
})

# Circular pocket
moves = cycles.execute_circular_pocket(
    x=75.0, y=75.0,
    diameter=40.0,
    depth=10.0,
    tool_diameter=10.0,
    stepover=0.6,
    stepdown=3.0,
    feed_rate=500.0
)
```

### 7. CNC Integration (`cnc_integration.py`)

Integrates all CNC components into a unified system and provides the main interface.

**Features:**
- G-code program loading and parsing
- Command execution
- Status monitoring
- Demo tool initialization

**Example:**
```python
from cnc_integration import get_cnc_integration

cnc = get_cnc_integration()

# Load program
gcode_program = """
G90 G54 G17
G00 X0 Y0 Z10
M03 S1000
G01 Z-5 F500
G01 X50 Y50
G00 Z10
M05
M30
"""

cnc.load_program(gcode_program, "Demo Program")

# Get status
status = cnc.get_comprehensive_status()
```

## REST API Endpoints

The CNC functionality is exposed through RESTful API endpoints in the Control Layer.

### Base URL
```
http://localhost:8000/api/v1/cnc
```

### Endpoints

#### 1. Get CNC Status
```
GET /api/v1/cnc/status
```

Returns comprehensive CNC machine status including controller state, position, tools, coordinate systems, and active cycles.

**Response:**
```json
{
  "controller": {
    "state": "idle",
    "mode": "manual",
    "position": {...},
    "spindle": {...},
    "feed": {...},
    "tool": {...}
  },
  "motion": {...},
  "tools": {...},
  "coordinates": {...},
  "cycles": {...}
}
```

#### 2. Load G-code Program
```
POST /api/v1/cnc/program/load
```

**Request Body:**
```json
{
  "gcode": "G90 G54\nG00 X10 Y20\n...",
  "name": "program_name"
}
```

#### 3. Set CNC Mode
```
POST /api/v1/cnc/mode/{mode}
```

**Modes:** `auto`, `manual`, `mdi`, `reference`, `handwheel`, `single_step`, `dry_run`, `simulation`

#### 4. Control Spindle
```
POST /api/v1/cnc/spindle
```

**Request Body:**
```json
{
  "state": "cw",  // "cw", "ccw", or "stopped"
  "speed": 1000   // RPM (optional)
}
```

#### 5. Change Tool
```
POST /api/v1/cnc/tool/change/{tool_number}
```

#### 6. Get Tool List
```
GET /api/v1/cnc/tools
```

#### 7. Get Magazine Status
```
GET /api/v1/cnc/magazine
```

#### 8. Set Coordinate System
```
POST /api/v1/cnc/coordinate-system/{system}
```

**Systems:** `G54`, `G55`, `G56`, `G57`, `G58`, `G59`, `G59.1`, `G59.2`, `G59.3`

#### 9. Set Feed Override
```
POST /api/v1/cnc/override/feed
```

**Request Body:**
```json
{
  "percentage": 100  // 0-150
}
```

#### 10. Set Spindle Override
```
POST /api/v1/cnc/override/spindle
```

**Request Body:**
```json
{
  "percentage": 100  // 50-150
}
```

#### 11. Emergency Stop
```
POST /api/v1/cnc/emergency-stop
```

**Request Body:**
```json
{
  "active": true  // true to activate, false to release
}
```

#### 12. Parse G-code
```
GET /api/v1/cnc/gcode/parse?gcode=G00 X10 Y20
```

Returns parsed G-code without executing it, useful for validation.

## Safety Features

### 1. Emergency Stop
- Hardware-based emergency stop on ESP32
- Software emergency stop in controller
- All motion and spindle operations halt immediately
- Must be manually released to resume operation

### 2. Software Limits
Configurable position limits for all axes:
- X: -500mm to +500mm
- Y: -500mm to +500mm
- Z: -300mm to 0mm
- A: -360° to +360°
- B: -120° to +120°
- C: -360° to +360°

### 3. Safety Checks
- Position limit checking before movements
- Tool availability checking before tool changes
- System safe state verification before commands
- Collision detection (future enhancement)
- Overload protection (integrated with existing system)

### 4. Error Handling
- Comprehensive error tracking with codes and timestamps
- Warning system for non-critical issues
- Error history (last 100 errors/warnings)
- Automatic state management on errors

## Performance

### Motion Planning
- **Look-ahead:** Up to 100 blocks for smooth path execution
- **Interpolation Rate:** 1kHz (1000 points/second)
- **Path Optimization:** Automatic corner rounding and velocity planning

### Limits
- **Max Feed Rate:** 15,000 mm/min (250 mm/s)
- **Max Rapid Rate:** 30,000 mm/min (500 mm/s)
- **Max Acceleration:** 5,000 mm/s²
- **Max Jerk:** 50,000 mm/s³

### Tool Change
- **Time:** ~6 seconds (typical)
- **Magazine Capacity:** 24 tools (configurable)

## Example Programs

### Example 1: Simple Drilling
```gcode
%
O1000
G90 G54 G17 G21  (Absolute, WCS1, XY plane, metric)
G00 Z10.0        (Rapid to safe Z)
M03 S1500        (Spindle on CW, 1500 RPM)
G00 X50.0 Y50.0  (Rapid to first hole)
G81 Z-20.0 R2.0 F200  (Drill cycle)
X100.0           (Second hole)
X150.0           (Third hole)
G80              (Cancel cycle)
G00 Z50.0        (Retract)
M05              (Spindle off)
M30              (Program end)
%
```

### Example 2: Rectangular Pocket
```gcode
%
O2000
G90 G54 G17 G21
T01 M06          (Tool change to end mill)
G00 X50.0 Y50.0 Z10.0
M03 S2000
(Rectangular pocket 80x60mm, depth 10mm)
G00 Z2.0
G01 Z0.0 F300
(Implementation depends on G26 or manual programming)
G00 Z10.0
M05
M30
%
```

### Example 3: Circular Interpolation
```gcode
%
O3000
G90 G54 G17 G21
G00 X0.0 Y0.0 Z10.0
M03 S1200
G00 Z2.0
G01 Z-5.0 F200  (Plunge)
G01 X25.0 F500  (Move to arc start)
G02 X25.0 Y0.0 I-25.0 J0.0  (Full circle, radius 25mm)
G00 Z10.0       (Retract)
M05
M30
%
```

## Integration with MODAX

The CNC functionality seamlessly integrates with existing MODAX features:

### 1. Sensor Data Integration
- Monitor spindle load, vibration, temperature during machining
- Automatic feed rate adjustment based on load
- Predictive maintenance for tools

### 2. AI Layer Integration
- Tool wear prediction based on cutting parameters
- Process optimization recommendations
- Anomaly detection during machining

### 3. Safety Integration
- Emergency stop connected to MODAX safety system
- Overload protection based on sensor data
- Automatic pause on safety violations

### 4. Data Export
- Export machining data (positions, feed rates, spindle speed)
- CSV/JSON export for analysis
- Integration with existing data persistence

## Testing

The CNC implementation includes comprehensive unit tests:

```bash
cd python-control-layer
python -m unittest test_cnc_controller.py -v
python -m unittest test_gcode_parser.py -v
```

**Test Coverage:**
- 25+ unit tests
- Controller state management
- G-code parsing and validation
- Motion calculations
- Tool management
- Coordinate transformations

## Future Enhancements

⭐ **See [ADVANCED_CNC_INDUSTRY_4_0.md](ADVANCED_CNC_INDUSTRY_4_0.md) for comprehensive Industry 4.0 features roadmap**

### Phase 2 (Planned)
- [ ] 5-axis simultaneous machining
- [ ] RTCP (Rotary Tool Center Point)
- [ ] Advanced cycles (threading, grooving)
- [ ] Macro programming (variables, loops)
- [ ] CAM integration (import toolpaths)
- [ ] Simulation with 3D visualization
- [ ] Collision detection with machine model

### Phase 3 (Future - See Advanced Documentation)
- [ ] Adaptive feed control based on AI
- [ ] Automatic program optimization
- [ ] Digital twin integration
- [ ] Cloud-based program library
- [ ] Remote monitoring and control
- [ ] AR/VR support for programming

### Industry 4.0 Advanced Features (Roadmap)
For detailed information on advanced CNC capabilities, see:
- **[ADVANCED_CNC_INDUSTRY_4_0.md](ADVANCED_CNC_INDUSTRY_4_0.md)** - Comprehensive guide covering:
  - Advanced Communication Protocols (EtherCAT, PROFINET, OPC UA, MQTT, MTConnect)
  - Adaptive Process Control (Feed optimization, vibration monitoring, energy management)
  - Intelligent Automation (Predictive maintenance, lights-out production, automated setup)
  - Future Integration (AI optimization, digital twin, peer-to-peer learning)
  - Next-Gen HMI (AR overlays, cloud-native interfaces, voice/gesture control)
  - Implementation roadmap and ROI analysis

## References

### Standards
- **ISO 6983:** Numerical control of machines - Program format
- **DIN 66025:** Programming of numerically controlled machines
- **FANUC:** G-code reference
- **Siemens:** SINUMERIK programming guide
- **Heidenhain:** TNC programming manual

### Related Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [API.md](API.md) - Complete API reference
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration options
- [SECURITY.md](SECURITY.md) - Security considerations

## Support

For issues or questions regarding CNC functionality:
- Check this documentation
- Review code examples
- Open an issue on GitHub
- Consult related documentation

---

**Note:** This CNC implementation is designed for integration with industrial control systems. Always ensure proper safety measures are in place when operating CNC machinery. The software should be thoroughly tested in simulation mode before use with real machines.
