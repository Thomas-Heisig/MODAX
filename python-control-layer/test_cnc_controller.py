"""Unit tests for CNC Controller"""
import unittest
from cnc_controller import CNCController, CNCMode, CNCState, SpindleState, CoolantState


class TestCNCController(unittest.TestCase):
    """Test CNC Controller"""

    def setUp(self):
        """Set up test controller"""
        self.controller = CNCController()

    def test_initialization(self):
        """Test controller initialization"""
        self.assertEqual(self.controller.state, CNCState.IDLE)
        self.assertEqual(self.controller.mode, CNCMode.MANUAL)
        self.assertFalse(self.controller.emergency_stop)
        self.assertEqual(self.controller.spindle_state, SpindleState.STOPPED)
        self.assertEqual(self.controller.spindle_speed, 0)

    def test_set_mode(self):
        """Test setting operation mode"""
        self.assertTrue(self.controller.set_mode(CNCMode.AUTO))
        self.assertEqual(self.controller.mode, CNCMode.AUTO)

        self.assertTrue(self.controller.set_mode(CNCMode.MDI))
        self.assertEqual(self.controller.mode, CNCMode.MDI)

    def test_emergency_stop(self):
        """Test emergency stop"""
        self.controller.set_emergency_stop(True)
        self.assertTrue(self.controller.emergency_stop_active())
        self.assertEqual(self.controller.state, CNCState.EMERGENCY)

        self.controller.set_emergency_stop(False)
        self.assertFalse(self.controller.emergency_stop_active())
        self.assertEqual(self.controller.state, CNCState.IDLE)

    def test_spindle_control(self):
        """Test spindle control"""
        # Start spindle CW
        self.assertTrue(self.controller.set_spindle(SpindleState.CW, 1000))
        self.assertEqual(self.controller.spindle_state, SpindleState.CW)
        self.assertEqual(self.controller.spindle_speed, 1000)

        # Stop spindle
        self.assertTrue(self.controller.set_spindle(SpindleState.STOPPED))
        self.assertEqual(self.controller.spindle_state, SpindleState.STOPPED)

        # Cannot start spindle in emergency
        self.controller.set_emergency_stop(True)
        self.assertFalse(self.controller.set_spindle(SpindleState.CW, 2000))

    def test_feed_rate(self):
        """Test feed rate setting"""
        self.assertTrue(self.controller.set_feed_rate(500.0))
        self.assertEqual(self.controller.feed_rate, 500.0)

        # Test maximum limit
        self.assertTrue(self.controller.set_feed_rate(20000.0))
        self.assertEqual(self.controller.feed_rate, 15000.0)  # Clamped to max

        # Test negative
        self.assertFalse(self.controller.set_feed_rate(-100.0))

    def test_coolant_control(self):
        """Test coolant control"""
        self.assertTrue(self.controller.set_coolant(CoolantState.FLOOD))
        self.assertEqual(self.controller.coolant_state, CoolantState.FLOOD)

        self.assertTrue(self.controller.set_coolant(CoolantState.OFF))
        self.assertEqual(self.controller.coolant_state, CoolantState.OFF)

    def test_overrides(self):
        """Test override settings"""
        # Feed override
        self.assertTrue(self.controller.set_feed_override(120))
        self.assertEqual(self.controller.feed_override, 120)

        # Test limits
        self.controller.set_feed_override(200)
        self.assertEqual(self.controller.feed_override, 150)  # Max 150%

        # Spindle override
        self.assertTrue(self.controller.set_spindle_override(80))
        self.assertEqual(self.controller.spindle_override, 80)

        # Rapid override
        self.assertTrue(self.controller.set_rapid_override(75))
        self.assertEqual(self.controller.rapid_override, 75)

    def test_position_limits(self):
        """Test position limit checking"""
        # Valid position
        valid, msg = self.controller.check_position_limits({"X": 100.0, "Y": 0.0, "Z": -50.0})
        self.assertTrue(valid)

        # Out of bounds X
        valid, msg = self.controller.check_position_limits({"X": 600.0})
        self.assertFalse(valid)
        self.assertIn("above maximum", msg)

        # Out of bounds Z
        valid, msg = self.controller.check_position_limits({"Z": -400.0})
        self.assertFalse(valid)
        self.assertIn("below minimum", msg)

    def test_program_control(self):
        """Test program execution control"""
        program = ["G90 G54", "G00 X10 Y20", "G01 Z-5 F500"]

        # Start program
        self.assertTrue(self.controller.start_program(program, "Test Program"))
        self.assertEqual(self.controller.state, CNCState.RUNNING)
        self.assertEqual(len(self.controller.program_lines), 3)

        # Pause
        self.assertTrue(self.controller.pause_program())
        self.assertEqual(self.controller.state, CNCState.PAUSED)

        # Resume
        self.assertTrue(self.controller.resume_program())
        self.assertEqual(self.controller.state, CNCState.RUNNING)

        # Stop
        self.assertTrue(self.controller.stop_program())
        self.assertEqual(self.controller.state, CNCState.STOPPED)

    def test_error_tracking(self):
        """Test error and warning tracking"""
        self.controller.add_error("E001", "Test error")
        self.assertEqual(len(self.controller.errors), 1)
        self.assertEqual(self.controller.errors[0]["code"], "E001")

        self.controller.add_warning("W001", "Test warning")
        self.assertEqual(len(self.controller.warnings), 1)
        self.assertEqual(self.controller.warnings[0]["code"], "W001")

    def test_get_status(self):
        """Test status retrieval"""
        status = self.controller.get_status()

        self.assertIn("state", status)
        self.assertIn("mode", status)
        self.assertIn("position", status)
        self.assertIn("spindle", status)
        self.assertIn("feed", status)
        self.assertIn("tool", status)
        self.assertIn("active_codes", status)


if __name__ == '__main__':
    unittest.main()
