"""Unit tests for G-code Parser"""
import unittest
from gcode_parser import GCodeParser


class TestGCodeParser(unittest.TestCase):
    """Test G-code Parser"""

    def setUp(self):
        """Set up test parser"""
        self.parser = GCodeParser()

    def test_parse_simple_line(self):
        """Test parsing simple G-code line"""
        cmd = self.parser.parse_line("G00 X10 Y20 Z5", 1)

        self.assertIsNotNone(cmd)
        self.assertIn("G00", cmd.g_codes)
        self.assertEqual(cmd.parameters["X"], 10.0)
        self.assertEqual(cmd.parameters["Y"], 20.0)
        self.assertEqual(cmd.parameters["Z"], 5.0)

    def test_parse_with_comments(self):
        """Test parsing with comments"""
        cmd = self.parser.parse_line("G01 X10 (move to X10)", 1)

        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.comment, "move to X10")
        self.assertIn("G01", cmd.g_codes)
        self.assertEqual(cmd.parameters["X"], 10.0)

    def test_parse_multiple_gcodes(self):
        """Test parsing multiple G-codes on one line"""
        cmd = self.parser.parse_line("G90 G54 G17", 1)

        self.assertIsNotNone(cmd)
        self.assertEqual(len(cmd.g_codes), 3)
        self.assertIn("G90", cmd.g_codes)
        self.assertIn("G54", cmd.g_codes)
        self.assertIn("G17", cmd.g_codes)

    def test_parse_mcodes(self):
        """Test parsing M-codes"""
        cmd = self.parser.parse_line("M03 S1000", 1)

        self.assertIsNotNone(cmd)
        self.assertIn("M03", cmd.m_codes)
        self.assertEqual(cmd.parameters["S"], 1000.0)

    def test_parse_circular_interpolation(self):
        """Test parsing circular interpolation"""
        cmd = self.parser.parse_line("G02 X20 Y10 I5 J0 F500", 1)

        self.assertIsNotNone(cmd)
        self.assertIn("G02", cmd.g_codes)
        self.assertEqual(cmd.parameters["I"], 5.0)
        self.assertEqual(cmd.parameters["J"], 0.0)
        self.assertEqual(cmd.parameters["F"], 500.0)

    def test_parse_tool_change(self):
        """Test parsing tool change"""
        cmd = self.parser.parse_line("T05 M06", 1)

        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.tool_number, 5)
        self.assertIn("M06", cmd.m_codes)

    def test_parse_line_number(self):
        """Test parsing line number"""
        cmd = self.parser.parse_line("N100 G00 X10", 1)

        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.n_number, 100)
        self.assertIn("G00", cmd.g_codes)

    def test_parse_negative_values(self):
        """Test parsing negative values"""
        cmd = self.parser.parse_line("G01 X-10.5 Y-20.3 Z-5", 1)

        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.parameters["X"], -10.5)
        self.assertEqual(cmd.parameters["Y"], -20.3)
        self.assertEqual(cmd.parameters["Z"], -5.0)

    def test_parse_program(self):
        """Test parsing complete program"""
        program = """
        G90 G54
        G00 X10 Y20
        G01 Z-5 F500
        M03 S1000
        """

        commands = self.parser.parse_program(program)

        self.assertEqual(len(commands), 4)
        self.assertIn("G90", commands[0].g_codes)
        self.assertIn("G00", commands[1].g_codes)
        self.assertIn("G01", commands[2].g_codes)
        self.assertIn("M03", commands[3].m_codes)

    def test_validate_command(self):
        """Test command validation"""
        # Valid command
        cmd = self.parser.parse_line("G00 X10 Y20", 1)
        valid, errors = self.parser.validate_command(cmd)
        self.assertTrue(valid)

        # Circular without I/J/K or R
        cmd = self.parser.parse_line("G02 X10 Y20", 1)
        valid, errors = self.parser.validate_command(cmd)
        self.assertFalse(valid)
        self.assertTrue(any("I/J/K or R" in err for err in errors))

    def test_get_target_position(self):
        """Test getting target position from command"""
        cmd = self.parser.parse_line("G01 X10 Y20 Z-5", 1)
        pos = cmd.get_target_position()

        self.assertEqual(pos["X"], 10.0)
        self.assertEqual(pos["Y"], 20.0)
        self.assertEqual(pos["Z"], -5.0)

    def test_has_motion(self):
        """Test motion detection"""
        cmd = self.parser.parse_line("G00 X10", 1)
        self.assertTrue(cmd.has_motion())

        cmd = self.parser.parse_line("G54", 1)
        self.assertFalse(cmd.has_motion())

    def test_has_coordinates(self):
        """Test coordinate detection"""
        cmd = self.parser.parse_line("G00 X10 Y20", 1)
        self.assertTrue(cmd.has_coordinates())

        cmd = self.parser.parse_line("M03 S1000", 1)
        self.assertFalse(cmd.has_coordinates())

    def test_gcode_descriptions(self):
        """Test G-code descriptions"""
        desc = self.parser.get_g_code_description("G00")
        self.assertIn("Rapid", desc)

        desc = self.parser.get_g_code_description("G01")
        self.assertIn("Linear", desc)

        desc = self.parser.get_m_code_description("M03")
        self.assertIn("Spindle", desc)


if __name__ == '__main__':
    unittest.main()
