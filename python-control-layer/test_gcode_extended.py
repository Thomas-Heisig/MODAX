"""Unit tests for extended G-code Parser features"""
import unittest
from gcode_parser import GCodeParser


class TestExtendedGCodeParser(unittest.TestCase):
    """Test extended G-code Parser features"""

    def setUp(self):
        """Set up test parser"""
        self.parser = GCodeParser()

    def test_parse_advanced_interpolation_codes(self):
        """Test parsing advanced interpolation codes"""
        # G05 - High-speed machining
        cmd = self.parser.parse_line("G05 X100 Y50", 1)
        self.assertIn("G05", cmd.g_codes)

        # G05.1 - AI Contour Control
        cmd = self.parser.parse_line("G05.1 Q1", 1)
        self.assertIn("G05.1", cmd.g_codes)

        # G07.1 - Cylindrical interpolation
        cmd = self.parser.parse_line("G07.1 X50 C45", 1)
        self.assertIn("G07.1", cmd.g_codes)

        # G12.1 - Polar interpolation on
        cmd = self.parser.parse_line("G12.1", 1)
        self.assertIn("G12.1", cmd.g_codes)

        # G13.1 - Polar interpolation off
        cmd = self.parser.parse_line("G13.1", 1)
        self.assertIn("G13.1", cmd.g_codes)

    def test_parse_threading_codes(self):
        """Test parsing threading codes"""
        # G33 - Thread cutting
        cmd = self.parser.parse_line("G33 Z-50 K1.5", 1)
        self.assertIn("G33", cmd.g_codes)

        # G76 - Threading cycle
        cmd = self.parser.parse_line("G76 P021060 Q100 R0.05", 1)
        self.assertIn("G76", cmd.g_codes)

        # G84.2 - Right-hand tapping
        cmd = self.parser.parse_line("G84.2 X50 Y50 Z-30 R5 F1000", 1)
        self.assertIn("G84.2", cmd.g_codes)

        # G84.3 - Left-hand tapping
        cmd = self.parser.parse_line("G84.3 X50 Y50 Z-30 R5 F1000", 1)
        self.assertIn("G84.3", cmd.g_codes)

    def test_parse_workspace_codes(self):
        """Test parsing workspace and probing codes"""
        # G22/G23 - Work area limit
        cmd = self.parser.parse_line("G22", 1)
        self.assertIn("G22", cmd.g_codes)

        cmd = self.parser.parse_line("G23", 1)
        self.assertIn("G23", cmd.g_codes)

        # G31 - Skip/Probe
        cmd = self.parser.parse_line("G31 Z-50 F100", 1)
        self.assertIn("G31", cmd.g_codes)

        # G36 - Auto tool offset
        cmd = self.parser.parse_line("G36", 1)
        self.assertIn("G36", cmd.g_codes)

    def test_parse_extended_mcodes(self):
        """Test parsing extended M-codes"""
        # M21/M22 - Spindle gear shift
        cmd = self.parser.parse_line("M21", 1)
        self.assertIn("M21", cmd.m_codes)

        cmd = self.parser.parse_line("M22", 1)
        self.assertIn("M22", cmd.m_codes)

        # M29 - Rigid tapping
        cmd = self.parser.parse_line("M29 S1000", 1)
        self.assertIn("M29", cmd.m_codes)

        # M88/M89 - Through-coolant
        cmd = self.parser.parse_line("M88", 1)
        self.assertIn("M88", cmd.m_codes)

        # User macros
        cmd = self.parser.parse_line("M100", 1)
        self.assertIn("M100", cmd.m_codes)

        # Pallet control
        cmd = self.parser.parse_line("M200", 1)
        self.assertIn("M200", cmd.m_codes)

    def test_parse_goto(self):
        """Test parsing GOTO statements"""
        cmd = self.parser.parse_line("GOTO START", 1)
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.goto_target, "START")
        self.assertTrue(cmd.is_control_flow())

    def test_parse_gosub(self):
        """Test parsing GOSUB statements"""
        cmd = self.parser.parse_line("GOSUB SUB100", 1)
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.gosub_target, "SUB100")
        self.assertTrue(cmd.is_control_flow())

    def test_parse_label(self):
        """Test parsing labels"""
        # Label with colon
        cmd = self.parser.parse_line(":START", 1)
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.label, "START")
        self.assertTrue(cmd.is_label())

        # Label without colon
        cmd = self.parser.parse_line("END_PROGRAM", 1)
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.label, "END_PROGRAM")

    def test_parse_ocode_macro(self):
        """Test parsing O-code macro calls"""
        cmd = self.parser.parse_line("O1234", 1)
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.macro_call, "O1234")
        self.assertTrue(cmd.is_macro_call())

    def test_parse_g65_macro_call(self):
        """Test parsing G65 macro call with parameters"""
        cmd = self.parser.parse_line("G65 P1000 A10 B20 C5", 1)
        self.assertIsNotNone(cmd)
        self.assertIn("G65", cmd.g_codes)
        self.assertEqual(cmd.macro_call, "O1000")
        self.assertEqual(cmd.macro_params['A'], 10.0)
        self.assertEqual(cmd.macro_params['B'], 20.0)
        self.assertEqual(cmd.macro_params['C'], 5.0)

    def test_parse_g54_extended(self):
        """Test parsing extended work coordinate system G54.1"""
        cmd = self.parser.parse_line("G54.1 P10", 1)
        self.assertIsNotNone(cmd)
        self.assertIn("G54.1", cmd.g_codes)
        self.assertEqual(cmd.parameters['P'], 10.0)

    def test_spindle_and_feed(self):
        """Test spindle speed and feed rate parsing"""
        cmd = self.parser.parse_line("G01 X100 F500 S1200", 1)
        self.assertTrue(cmd.has_spindle_speed())
        self.assertTrue(cmd.has_feed_rate())
        self.assertEqual(cmd.get_spindle_speed(), 1200.0)
        self.assertEqual(cmd.get_feed_rate(), 500.0)

    def test_comment_styles(self):
        """Test both comment styles"""
        # Parentheses style
        cmd = self.parser.parse_line("G00 X10 (rapid move)", 1)
        self.assertEqual(cmd.comment, "rapid move")

        # Semicolon style
        cmd = self.parser.parse_line("G01 Y20 ; linear feed", 1)
        self.assertEqual(cmd.comment, "linear feed")

    def test_manufacturer_specific_codes(self):
        """Test manufacturer-specific code detection"""
        # Siemens
        is_specific, mfr = self.parser.is_manufacturer_specific("G05")
        self.assertTrue(is_specific)
        self.assertIn("Siemens", mfr)

        # Fanuc Macro B
        is_specific, mfr = self.parser.is_manufacturer_specific("G65")
        self.assertTrue(is_specific)
        self.assertIn("Fanuc", mfr)

        # Standard code
        is_specific, mfr = self.parser.is_manufacturer_specific("G01")
        self.assertFalse(is_specific)

    def test_user_mcode_description(self):
        """Test user-defined M-code descriptions"""
        desc = self.parser.get_m_code_description("M100")
        self.assertIn("User macro", desc)

        desc = self.parser.get_m_code_description("M250")
        self.assertIn("Macro call", desc)

    def test_foreign_machine_support(self):
        """Test foreign machine code support information"""
        supported = self.parser.supports_foreign_machine_codes()
        self.assertIsInstance(supported, list)
        self.assertGreater(len(supported), 0)
        self.assertTrue(any("Siemens" in s for s in supported))
        self.assertTrue(any("Fanuc" in s for s in supported))
        self.assertTrue(any("Heidenhain" in s for s in supported))

    def test_parse_high_speed_peck_drilling(self):
        """Test G73 high-speed peck drilling"""
        cmd = self.parser.parse_line("G73 X50 Y50 Z-30 R5 Q5 F200", 1)
        self.assertIn("G73", cmd.g_codes)
        self.assertEqual(cmd.parameters['Q'], 5.0)  # Peck increment

    def test_parse_g98_g99_return_modes(self):
        """Test G98/G99 canned cycle return modes"""
        cmd = self.parser.parse_line("G98", 1)
        self.assertIn("G98", cmd.g_codes)

        cmd = self.parser.parse_line("G99", 1)
        self.assertIn("G99", cmd.g_codes)

    def test_complex_program_with_control_flow(self):
        """Test parsing a program with control flow"""
        program = """
        O1000
        N10 G00 X0 Y0
        N20 GOSUB SUB1
        N30 G00 X100
        N40 GOTO N10

        :SUB1
        N100 G01 X50 F500
        N110 M99
        """

        commands = self.parser.parse_program(program)

        # Check that we have commands
        self.assertGreater(len(commands), 0)

        # Check for O-code
        o_cmds = [c for c in commands if c.is_macro_call()]
        self.assertEqual(len(o_cmds), 1)

        # Check for GOSUB
        gosub_cmds = [c for c in commands if c.gosub_target]
        self.assertEqual(len(gosub_cmds), 1)
        self.assertEqual(gosub_cmds[0].gosub_target, "SUB1")

        # Check for GOTO
        goto_cmds = [c for c in commands if c.goto_target]
        self.assertEqual(len(goto_cmds), 1)
        self.assertEqual(goto_cmds[0].goto_target, "N10")

        # Check for labels
        label_cmds = [c for c in commands if c.is_label()]
        self.assertGreater(len(label_cmds), 0)

        # Check for M99
        m99_cmds = [c for c in commands if 'M99' in c.m_codes]
        self.assertEqual(len(m99_cmds), 1)


if __name__ == '__main__':
    unittest.main()
