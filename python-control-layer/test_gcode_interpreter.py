"""Unit tests for G-code Interpreter"""
import unittest
from gcode_interpreter import GCodeInterpreter, InterpreterState


class TestGCodeInterpreter(unittest.TestCase):
    """Test G-code Interpreter"""

    def setUp(self):
        """Set up test interpreter"""
        self.interpreter = GCodeInterpreter()

    def test_load_simple_program(self):
        """Test loading a simple program"""
        program = """
        G90 G54
        G00 X10 Y20
        G01 Z-5 F500
        M30
        """

        result = self.interpreter.load_program(program)
        self.assertTrue(result)
        self.assertGreater(len(self.interpreter.program), 0)

    def test_build_label_table(self):
        """Test building label table"""
        program = """
        :START
        N100 G00 X10
        :END
        N200 M30
        """

        self.interpreter.load_program(program)

        # Check labels
        self.assertIn("START", self.interpreter.state.labels)
        self.assertIn("END", self.interpreter.state.labels)
        self.assertIn("N100", self.interpreter.state.labels)
        self.assertIn("N200", self.interpreter.state.labels)

    def test_goto_execution(self):
        """Test GOTO execution"""
        program = """
        N10 G00 X0
        N20 GOTO N40
        N30 G00 X10 (should be skipped)
        N40 G00 X20
        M30
        """

        self.interpreter.load_program(program)
        executed = self.interpreter.execute_program()

        # Should execute N10, N20 (GOTO), N40, M30
        # N30 should be skipped
        self.assertEqual(len(executed), 4)

        # Check that we didn't execute N30
        x10_cmds = [c for c in executed if c.parameters.get('X') == 10.0]
        self.assertEqual(len(x10_cmds), 0)

    def test_gosub_return(self):
        """Test GOSUB and RETURN execution"""
        program = """
        N10 G00 X0
        N20 GOSUB SUB1
        N30 G00 X30
        M30

        :SUB1
        N100 G00 X100
        N110 G00 Y100
        M99
        """

        self.interpreter.load_program(program)
        executed = self.interpreter.execute_program()

        # Should execute in order: N10, N20 (GOSUB), N100, N110, M99 (RETURN), N30, M30
        self.assertGreaterEqual(len(executed), 6)

        # Verify subroutine was executed
        y100_cmds = [c for c in executed if c.parameters.get('Y') == 100.0]
        self.assertEqual(len(y100_cmds), 1)

        # Verify we returned and executed N30
        x30_cmds = [c for c in executed if c.parameters.get('X') == 30.0]
        self.assertEqual(len(x30_cmds), 1)

    def test_nested_gosub(self):
        """Test nested GOSUB calls"""
        program = """
        N10 GOSUB SUB1
        M30

        :SUB1
        N100 G00 X100
        N110 GOSUB SUB2
        M99

        :SUB2
        N200 G00 Y200
        M99
        """

        self.interpreter.load_program(program)
        executed = self.interpreter.execute_program()

        # Should handle nested calls correctly
        self.assertGreater(len(executed), 0)

        # Check call stack is empty after execution
        self.assertEqual(len(self.interpreter.state.call_stack), 0)

    def test_macro_variable_handling(self):
        """Test macro variable handling"""
        program = """
        G65 P1000 A10.5 B20.3
        """

        self.interpreter.load_program(program)
        cmd, _ = self.interpreter.execute_next_command()

        # Check variables were set
        self.assertEqual(self.interpreter.get_variable("#A"), 10.5)
        self.assertEqual(self.interpreter.get_variable("#B"), 20.3)

    def test_set_get_variable(self):
        """Test setting and getting variables"""
        self.interpreter.set_variable("#100", 42.5)
        self.assertEqual(self.interpreter.get_variable("#100"), 42.5)

        self.interpreter.set_variable("#200", -10.0)
        self.assertEqual(self.interpreter.get_variable("#200"), -10.0)

    def test_program_end_m02(self):
        """Test program end with M02"""
        program = """
        G00 X10
        M02
        G00 X20 (should not execute)
        """

        self.interpreter.load_program(program)
        executed = self.interpreter.execute_program()

        # Should execute only until M02
        self.assertEqual(len(executed), 2)

        # X20 should not be executed
        x20_cmds = [c for c in executed if c.parameters.get('X') == 20.0]
        self.assertEqual(len(x20_cmds), 0)

    def test_program_end_m30(self):
        """Test program end with M30"""
        program = """
        G00 X10
        M30
        G00 X30 (should not execute)
        """

        self.interpreter.load_program(program)
        executed = self.interpreter.execute_program()

        # Should stop at M30
        self.assertEqual(len(executed), 2)

    def test_execution_log(self):
        """Test execution logging"""
        program = """
        N10 G00 X10
        N20 G01 Y20 F500
        M30
        """

        self.interpreter.load_program(program)
        self.interpreter.execute_program()

        log = self.interpreter.get_execution_log()
        self.assertGreater(len(log), 0)

        # Check log contains line information
        self.assertTrue(any("Line" in entry for entry in log))

    def test_infinite_loop_prevention(self):
        """Test infinite loop prevention"""
        program = """
        :LOOP
        G00 X10
        GOTO LOOP
        """

        self.interpreter.load_program(program)

        # Should stop after max execution count
        executed = self.interpreter.execute_program(max_commands=100)

        # Should have stopped before executing too many commands
        self.assertLess(len(executed), 200)

    def test_invalid_goto_target(self):
        """Test handling of invalid GOTO target"""
        program = """
        G00 X10
        GOTO NONEXISTENT
        G00 X20
        """

        self.interpreter.load_program(program)
        executed = self.interpreter.execute_program()

        # Should stop when encountering invalid GOTO, executing only X10
        self.assertEqual(len(executed), 1)  # Only X10, GOTO fails and stops execution

    def test_return_without_gosub(self):
        """Test RETURN without GOSUB"""
        program = """
        G00 X10
        M99
        G00 X20
        """

        self.interpreter.load_program(program)
        executed = self.interpreter.execute_program()

        # Should handle gracefully and stop
        self.assertGreater(len(executed), 0)

    def test_reset(self):
        """Test interpreter reset"""
        program = """
        G00 X10
        M30
        """

        self.interpreter.load_program(program)
        self.interpreter.execute_program()

        # Set some state
        self.interpreter.set_variable("#100", 42)

        # Reset
        self.interpreter.reset()

        # State should be cleared
        self.assertEqual(self.interpreter.state.current_line, 0)
        self.assertEqual(len(self.interpreter.state.call_stack), 0)
        self.assertEqual(len(self.interpreter.state.variables), 0)
        self.assertEqual(len(self.interpreter.execution_log), 0)

    def test_complex_program_with_loops(self):
        """Test complex program with loops and subroutines"""
        program = """
        O1000
        N10 G00 X0 Y0
        N20 #1=0 (counter)

        :LOOP_START
        N30 #1=#1+1
        N40 GOSUB DRILL_SUB
        N50 G00 X[#1*10]
        N60 IF [#1 LT 5] GOTO LOOP_START
        N70 M30

        :DRILL_SUB
        N100 G81 Z-10 R2 F100
        N110 M99
        """

        self.interpreter.load_program(program)

        # Should load successfully
        self.assertGreater(len(self.interpreter.program), 0)

        # Should have identified labels
        self.assertIn("LOOP_START", self.interpreter.state.labels)
        self.assertIn("DRILL_SUB", self.interpreter.state.labels)


class TestInterpreterState(unittest.TestCase):
    """Test InterpreterState class"""

    def test_initial_state(self):
        """Test initial state"""
        state = InterpreterState()
        self.assertEqual(state.current_line, 0)
        self.assertEqual(len(state.call_stack), 0)
        self.assertEqual(len(state.variables), 0)
        self.assertEqual(len(state.labels), 0)

    def test_reset(self):
        """Test state reset"""
        state = InterpreterState()

        # Modify state
        state.current_line = 10
        state.call_stack.append(5)
        state.variables['#100'] = 42
        state.labels['START'] = 0
        state.execution_count = 100

        # Reset
        state.reset()

        # Should be back to initial state
        self.assertEqual(state.current_line, 0)
        self.assertEqual(len(state.call_stack), 0)
        self.assertEqual(len(state.variables), 0)
        self.assertEqual(len(state.labels), 0)
        self.assertEqual(state.execution_count, 0)


if __name__ == '__main__':
    unittest.main()
