"""G-code Interpreter - Executes G-code programs with control flow support"""
import logging
from typing import Dict, List, Optional, Tuple
from gcode_parser import GCodeParser, GCodeCommand

logger = logging.getLogger(__name__)


class InterpreterState:
    """Maintains interpreter execution state"""

    def __init__(self):
        """
        Initialize interpreter state
        
        Sets up execution state including current line, call stack, variables,
        labels, and execution counter for loop prevention.
        """
        self.current_line: int = 0
        self.call_stack: List[int] = []  # For GOSUB/RETURN
        self.variables: Dict[str, float] = {}  # Macro variables
        self.labels: Dict[str, int] = {}  # Label name -> line number
        self.execution_count: int = 0
        self.max_execution_count: int = 100000  # Prevent infinite loops

    def reset(self):
        """Reset interpreter state"""
        self.current_line = 0
        self.call_stack.clear()
        self.variables.clear()
        self.labels.clear()
        self.execution_count = 0


class GCodeInterpreter:
    """Interprets and executes G-code programs with control flow"""

    def __init__(self):
        """
        Initialize G-code interpreter
        
        Creates parser, interpreter state, program storage, and execution log.
        """
        self.parser = GCodeParser()
        self.state = InterpreterState()
        self.program: List[GCodeCommand] = []
        self.execution_log: List[str] = []

        logger.info("G-code Interpreter initialized")

    def load_program(self, program_text: str) -> bool:
        """Load and preprocess a G-code program

        Args:
            program_text: Complete G-code program as string

        Returns:
            True if program loaded successfully
        """
        try:
            self.program = self.parser.parse_program(program_text)
            self.state.reset()

            # Build label table
            self._build_label_table()

            logger.info(f"Program loaded: {len(self.program)} commands, "
                       f"{len(self.state.labels)} labels")
            return True

        except Exception as e:
            logger.error(f"Failed to load program: {e}")
            return False

    def _build_label_table(self):
        """Build a table of all labels in the program"""
        self.state.labels.clear()

        for idx, cmd in enumerate(self.program):
            if cmd.is_label():
                self.state.labels[cmd.label] = idx
                logger.debug(f"Label '{cmd.label}' at line {idx}")

            # Also recognize N-numbers as labels
            if cmd.n_number is not None:
                label_name = f"N{cmd.n_number}"
                self.state.labels[label_name] = idx
                logger.debug(f"N-number '{label_name}' at line {idx}")

    def execute_next_command(self) -> Tuple[Optional[GCodeCommand], bool]:
        """Execute the next command in the program

        Returns:
            Tuple of (command, continue_execution)
            - command: The executed command (or None if no command)
            - continue_execution: False if program should stop
        """
        # Check execution limit
        self.state.execution_count += 1
        if self.state.execution_count > self.state.max_execution_count:
            logger.error("Maximum execution count exceeded - possible infinite loop")
            return None, False

        # Check if we're at the end
        if self.state.current_line >= len(self.program):
            logger.info("Program execution complete")
            return None, False

        # Get current command
        cmd = self.program[self.state.current_line]

        # Log execution
        log_msg = f"Line {self.state.current_line}: {cmd.raw_line}"
        self.execution_log.append(log_msg)
        logger.debug(log_msg)

        # Handle control flow
        if cmd.is_control_flow():
            return self._handle_control_flow(cmd)

        # Handle macro calls
        if cmd.is_macro_call():
            return self._handle_macro_call(cmd)

        # Handle labels (just skip them during execution)
        if cmd.is_label():
            self.state.current_line += 1
            return cmd, True

        # Normal command execution
        self.state.current_line += 1
        return cmd, True

    def _handle_control_flow(self, cmd: GCodeCommand) -> Tuple[GCodeCommand, bool]:
        """Handle GOTO, GOSUB, RETURN commands"""

        # GOTO - Jump to label
        if cmd.goto_target:
            target = cmd.goto_target
            if target not in self.state.labels:
                logger.error(f"GOTO target '{target}' not found")
                return cmd, False

            self.state.current_line = self.state.labels[target]
            logger.debug(f"GOTO {target} -> line {self.state.current_line}")
            return cmd, True

        # GOSUB - Call subroutine
        if cmd.gosub_target:
            target = cmd.gosub_target
            if target not in self.state.labels:
                logger.error(f"GOSUB target '{target}' not found")
                return cmd, False

            # Push return address onto call stack
            self.state.call_stack.append(self.state.current_line + 1)
            self.state.current_line = self.state.labels[target]
            logger.debug(f"GOSUB {target} -> line {self.state.current_line}, "
                        f"return to {self.state.call_stack[-1]}")
            return cmd, True

        return cmd, True

    def _handle_macro_call(self, cmd: GCodeCommand) -> Tuple[GCodeCommand, bool]:
        """Handle macro calls (G65, O-codes)"""
        logger.debug(f"Macro call: {cmd.macro_call} with params {cmd.macro_params}")

        # Store macro parameters in variables
        for param, value in cmd.macro_params.items():
            var_name = f"#{param}"
            self.state.variables[var_name] = value
            logger.debug(f"Set variable {var_name} = {value}")

        # In a real implementation, this would execute the macro program
        # For now, just continue to next line
        self.state.current_line += 1
        return cmd, True

    def handle_return(self) -> bool:
        """Handle RETURN from subroutine (M99)

        Returns:
            True if return was successful
        """
        if not self.state.call_stack:
            logger.warning("RETURN without GOSUB - ending program")
            return False

        return_line = self.state.call_stack.pop()
        self.state.current_line = return_line
        logger.debug(f"RETURN to line {return_line}")
        return True

    def execute_program(self, max_commands: int = 10000) -> List[GCodeCommand]:
        """Execute the entire program

        Args:
            max_commands: Maximum number of commands to execute

        Returns:
            List of executed commands
        """
        executed_commands = []

        while len(executed_commands) < max_commands:
            cmd, should_continue = self.execute_next_command()

            if cmd is None or not should_continue:
                break

            # Check for M99 (return from subroutine)
            if 'M99' in cmd.m_codes:
                if not self.handle_return():
                    break

            # Check for program end (M02, M30)
            if any(m in cmd.m_codes for m in ['M02', 'M30']):
                logger.info(f"Program end: {cmd.m_codes}")
                executed_commands.append(cmd)
                break

            executed_commands.append(cmd)

        logger.info(f"Executed {len(executed_commands)} commands")
        return executed_commands

    def get_variable(self, var_name: str) -> Optional[float]:
        """Get value of a variable"""
        return self.state.variables.get(var_name)

    def set_variable(self, var_name: str, value: float):
        """Set value of a variable"""
        self.state.variables[var_name] = value
        logger.debug(f"Variable {var_name} = {value}")

    def get_execution_log(self) -> List[str]:
        """Get the execution log"""
        return self.execution_log.copy()

    def reset(self):
        """Reset interpreter state"""
        self.state.reset()
        self.execution_log.clear()
        logger.info("Interpreter reset")
