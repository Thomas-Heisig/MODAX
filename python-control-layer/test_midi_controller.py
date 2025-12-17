"""Unit tests for MIDI Controller"""
import unittest
from midi_controller import MidiStub, MidiNote, create_midi_controller


class TestMidiNote(unittest.TestCase):
    """Test MIDI note enum"""

    def test_midi_note_values(self):
        """Test MIDI note enum values"""
        self.assertEqual(MidiNote.MACHINE_START, 48)
        self.assertEqual(MidiNote.TOOL_CHANGE, 60)
        self.assertEqual(MidiNote.PROGRAM_START, 72)
        self.assertEqual(MidiNote.ERROR, 84)


class TestMidiStub(unittest.TestCase):
    """Test MIDI stub implementation (no hardware required)"""

    def test_stub_machine_events(self):
        """Test stub machine events"""
        stub = MidiStub()

        self.assertFalse(stub.machine_start())
        self.assertFalse(stub.machine_stop())
        self.assertFalse(stub.machine_pause())

    def test_stub_tool_events(self):
        """Test stub tool events"""
        stub = MidiStub()

        self.assertFalse(stub.tool_change())

    def test_stub_program_events(self):
        """Test stub program events"""
        stub = MidiStub()

        self.assertFalse(stub.program_start())
        self.assertFalse(stub.program_end())

    def test_stub_alert_events(self):
        """Test stub alert events"""
        stub = MidiStub()

        self.assertFalse(stub.error_alert())
        self.assertFalse(stub.warning_alert())
        self.assertFalse(stub.emergency_stop())

    def test_stub_statistics(self):
        """Test stub statistics"""
        stub = MidiStub()
        stats = stub.get_statistics()

        self.assertFalse(stats['enabled'])
        self.assertTrue(stats['stub'])

    def test_stub_context_manager(self):
        """Test stub context manager"""
        with MidiStub() as stub:
            stub.machine_start()
        # Should not raise any exceptions


if __name__ == '__main__':
    unittest.main()
