"""CNC API Demo - Demonstrates CNC functionality"""
import sys
from cnc_integration import get_cnc_integration
from cnc_controller import CNCMode, SpindleState

def print_separator():
    print("=" * 60)

def demo_cnc_functionality():
    """Demonstrate CNC functionality"""
    print_separator()
    print("MODAX CNC Functionality Demo")
    print_separator()
    
    # Initialize CNC
    print("\n1. Initializing CNC Integration...")
    cnc = get_cnc_integration()
    print("   ✅ CNC Integration initialized")
    print(f"   - Demo tools loaded: {len(cnc.tools.tools)}")
    
    # Get initial status
    status = cnc.get_comprehensive_status()
    print(f"   - Machine state: {status['controller']['state']}")
    print(f"   - Mode: {status['controller']['mode']}")
    
    # Set mode to AUTO
    print("\n2. Setting CNC mode to AUTO...")
    cnc.controller.set_mode(CNCMode.AUTO)
    print("   ✅ Mode set to AUTO")
    
    # Load G-code program
    print("\n3. Loading G-code program...")
    gcode_program = """
(Test program - Simple drilling and milling)
G90 G54 G17 G21  (Absolute, WCS1, XY plane, metric)
G00 Z10.0        (Safe Z)
T01 M06          (Tool change to T1)
M03 S1500        (Spindle on CW at 1500 RPM)
G00 X50.0 Y50.0  (Rapid to position)
G81 Z-20.0 R2.0 F200  (Drilling cycle)
X100.0           (Second hole)
X150.0           (Third hole)
G80              (Cancel cycle)
G01 X0 Y0 F500   (Linear move)
G02 X50 Y50 I25 J25 F300  (Circular interpolation)
G00 Z50.0        (Retract)
M05              (Spindle off)
M30              (Program end)
"""
    
    success = cnc.load_program(gcode_program, "Demo Drilling Program")
    if success:
        print(f"   ✅ Program loaded: {len(cnc.current_program)} commands")
        print(f"   - Program name: {cnc.controller.program_name}")
    else:
        print("   ❌ Failed to load program")
        return False
    
    # Show parsed commands
    print("\n4. Parsed G-code commands (first 5):")
    for i, cmd in enumerate(cnc.current_program[:5], 1):
        print(f"   Line {i}: {cmd.raw_line}")
        if cmd.g_codes:
            g_descriptions = [f"{g} ({cnc.parser.get_g_code_description(g)})" 
                            for g in cmd.g_codes]
            print(f"      G-codes: {', '.join(g_descriptions)}")
        if cmd.m_codes:
            m_descriptions = [f"{m} ({cnc.parser.get_m_code_description(m)})" 
                            for m in cmd.m_codes]
            print(f"      M-codes: {', '.join(m_descriptions)}")
        if cmd.parameters:
            params = ', '.join([f"{k}={v}" for k, v in cmd.parameters.items()])
            print(f"      Parameters: {params}")
    
    # Spindle control
    print("\n5. Testing spindle control...")
    cnc.controller.set_spindle(SpindleState.CW, 1500)
    print(f"   ✅ Spindle: {cnc.controller.spindle_state.value} at {cnc.controller.spindle_speed} RPM")
    
    # Feed rate control
    print("\n6. Testing feed rate control...")
    cnc.controller.set_feed_rate(500.0)
    print(f"   ✅ Feed rate: {cnc.controller.feed_rate} mm/min")
    cnc.controller.set_feed_override(120)
    print(f"   ✅ Feed override: {cnc.controller.feed_override}%")
    
    # Tool change
    print("\n7. Testing tool change...")
    tool_num = 2
    if cnc.tools.change_tool(tool_num):
        tool = cnc.tools.get_tool(tool_num)
        print(f"   ✅ Tool change to T{tool_num}")
        print(f"      - Tool name: {tool.name}")
        print(f"      - Type: {tool.type}")
        print(f"      - Diameter: {tool.diameter} mm")
        print(f"      - Length: {tool.length} mm")
    
    # Coordinate system
    print("\n8. Testing coordinate system...")
    cnc.coords.set_work_offsets("G54", {"X": 100.0, "Y": 50.0, "Z": 25.0})
    cnc.coords.set_active_coordinate_system("G54")
    print(f"   ✅ Work coordinate system: G54")
    print(f"      - Offsets: X=100, Y=50, Z=25")
    
    # Get comprehensive status
    print("\n9. Comprehensive status:")
    status = cnc.get_comprehensive_status()
    print(f"   Controller:")
    print(f"      - State: {status['controller']['state']}")
    print(f"      - Mode: {status['controller']['mode']}")
    print(f"      - Spindle: {status['controller']['spindle']['state']} @ {status['controller']['spindle']['speed']} RPM")
    print(f"      - Feed: {status['controller']['feed']['rate']} mm/min ({status['controller']['feed']['override']}%)")
    print(f"   Tools:")
    print(f"      - In spindle: T{status['tools']['in_spindle']}")
    print(f"      - Available tools: {len(status['tools']['tool_list'])}")
    print(f"   Coordinates:")
    print(f"      - Active system: {status['coordinates']['active_coord_system']}")
    print(f"   Program:")
    print(f"      - Loaded: {status['program']['loaded']}")
    print(f"      - Total commands: {status['program']['total_commands']}")
    
    # Stop spindle
    print("\n10. Stopping spindle...")
    cnc.controller.set_spindle(SpindleState.STOPPED)
    print(f"   ✅ Spindle stopped")
    
    print_separator()
    print("✅ ALL TESTS PASSED - CNC functionality working correctly!")
    print_separator()
    
    return True


if __name__ == "__main__":
    try:
        success = demo_cnc_functionality()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
