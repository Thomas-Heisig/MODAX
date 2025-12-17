"""
MIDI Controller for CNC Machine Feedback

This module provides MIDI-based audio feedback for CNC operations:
- Machine status notifications (start, stop, pause)
- Tool change signals
- Error alerts
- Completion notifications
- Custom event sounds

MIDI provides:
- Low latency audio feedback
- Standard protocol support
- Easy integration with audio systems
- Configurable sound mapping
"""

import logging
from typing import Optional, Dict, Any
from enum import IntEnum
import threading

try:
    import mido
    from mido import Message, MidiFile, MidiTrack
    MIDI_AVAILABLE = True
except ImportError:
    MIDI_AVAILABLE = False
    logging.warning("MIDI support not available. Install with: pip install mido python-rtmidi")

logger = logging.getLogger(__name__)


class MidiNote(IntEnum):
    """MIDI note definitions for machine events"""
    # Status events (low notes)
    MACHINE_START = 48  # C3
    MACHINE_STOP = 50   # D3
    MACHINE_PAUSE = 52  # E3
    MACHINE_RESUME = 53 # F3
    
    # Tool events (mid notes)
    TOOL_CHANGE = 60    # C4
    TOOL_MEASURE = 62   # D4
    SPINDLE_START = 64  # E4
    SPINDLE_STOP = 65   # F4
    
    # Program events (high notes)
    PROGRAM_START = 72  # C5
    PROGRAM_END = 74    # D5
    PROGRAM_PAUSE = 76  # E5
    
    # Alert events (very high notes)
    ERROR = 84          # C6
    WARNING = 86        # D6
    LIMIT_SWITCH = 88   # E6
    EMERGENCY_STOP = 90 # F#6


class MidiController:
    """
    MIDI Controller for CNC machine audio feedback
    
    Provides audio notifications for CNC events using MIDI protocol.
    Can be connected to:
    - Hardware MIDI synthesizers
    - Software MIDI devices
    - Virtual MIDI ports
    - Audio workstations
    """
    
    def __init__(
        self,
        port_name: Optional[str] = None,
        channel: int = 0,
        velocity: int = 100,
        duration: float = 0.2
    ):
        """
        Initialize MIDI controller
        
        Args:
            port_name: MIDI output port name (None = auto-detect)
            channel: MIDI channel (0-15)
            channel: MIDI channel (0-15)
            velocity: Note velocity (0-127)
            duration: Note duration in seconds
        """
        if not MIDI_AVAILABLE:
            logger.warning("MIDI not available - running in stub mode")
            self._enabled = False
            return
            
        self._enabled = True
        self._port: Optional[Any] = None
        self._channel = channel
        self._velocity = velocity
        self._duration = duration
        self._lock = threading.Lock()
        
        # Event counters for statistics
        self._event_count: Dict[str, int] = {}
        
        # Initialize MIDI output
        self._init_port(port_name)
        
    def _init_port(self, port_name: Optional[str]) -> None:
        """Initialize MIDI output port"""
        try:
            # Get available output ports
            outputs = mido.get_output_names()
            
            if not outputs:
                logger.warning("No MIDI output ports available")
                self._enabled = False
                return
                
            # Select port
            if port_name and port_name in outputs:
                selected_port = port_name
            else:
                # Use first available port
                selected_port = outputs[0]
                logger.info(f"Auto-selected MIDI port: {selected_port}")
                
            # Open port
            self._port = mido.open_output(selected_port)
            logger.info(f"MIDI controller initialized on port: {selected_port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MIDI port: {e}")
            self._enabled = False
            
    def play_note(
        self,
        note: int,
        velocity: Optional[int] = None,
        duration: Optional[float] = None
    ) -> bool:
        """
        Play a MIDI note
        
        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (None = use default)
            duration: Note duration in seconds (None = use default)
            
        Returns:
            True if note was played successfully
        """
        if not self._enabled or not self._port:
            return False
            
        vel = velocity if velocity is not None else self._velocity
        dur = duration if duration is not None else self._duration
        
        try:
            with self._lock:
                # Note on
                msg = Message(
                    'note_on',
                    channel=self._channel,
                    note=note,
                    velocity=vel
                )
                self._port.send(msg)
                
                # Note off after duration (non-blocking)
                def note_off():
                    import time
                    time.sleep(dur)
                    with self._lock:
                        off_msg = Message(
                            'note_off',
                            channel=self._channel,
                            note=note,
                            velocity=0
                        )
                        self._port.send(off_msg)
                        
                threading.Thread(target=note_off, daemon=True).start()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to play MIDI note {note}: {e}")
            return False
            
    def machine_start(self) -> bool:
        """Play sound for machine start"""
        self._increment_event('machine_start')
        return self.play_note(MidiNote.MACHINE_START)
        
    def machine_stop(self) -> bool:
        """Play sound for machine stop"""
        self._increment_event('machine_stop')
        return self.play_note(MidiNote.MACHINE_STOP)
        
    def machine_pause(self) -> bool:
        """Play sound for machine pause"""
        self._increment_event('machine_pause')
        return self.play_note(MidiNote.MACHINE_PAUSE)
        
    def tool_change(self) -> bool:
        """Play sound for tool change"""
        self._increment_event('tool_change')
        return self.play_note(MidiNote.TOOL_CHANGE, velocity=110)
        
    def program_start(self) -> bool:
        """Play sound for program start"""
        self._increment_event('program_start')
        # Play ascending chord
        self.play_note(MidiNote.PROGRAM_START, duration=0.15)
        self.play_note(MidiNote.PROGRAM_START + 4, duration=0.15)
        return self.play_note(MidiNote.PROGRAM_START + 7, duration=0.3)
        
    def program_end(self) -> bool:
        """Play sound for program completion"""
        self._increment_event('program_end')
        # Play descending chord
        self.play_note(MidiNote.PROGRAM_END + 7, duration=0.15)
        self.play_note(MidiNote.PROGRAM_END + 4, duration=0.15)
        return self.play_note(MidiNote.PROGRAM_END, duration=0.3)
        
    def error_alert(self) -> bool:
        """Play sound for error"""
        self._increment_event('error')
        # Play rapid beeps
        for _ in range(3):
            self.play_note(MidiNote.ERROR, velocity=127, duration=0.1)
        return True
        
    def warning_alert(self) -> bool:
        """Play sound for warning"""
        self._increment_event('warning')
        return self.play_note(MidiNote.WARNING, velocity=100, duration=0.25)
        
    def emergency_stop(self) -> bool:
        """Play sound for emergency stop"""
        self._increment_event('emergency_stop')
        # Play loud, sustained alarm
        return self.play_note(MidiNote.EMERGENCY_STOP, velocity=127, duration=1.0)
        
    def _increment_event(self, event: str) -> None:
        """Increment event counter"""
        self._event_count[event] = self._event_count.get(event, 0) + 1
        
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get MIDI controller statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            'enabled': self._enabled,
            'port': str(self._port) if self._port else None,
            'channel': self._channel,
            'event_counts': self._event_count.copy(),
            'total_events': sum(self._event_count.values())
        }
        
    def close(self) -> None:
        """Close MIDI port"""
        if self._port:
            try:
                self._port.close()
                logger.info("MIDI controller closed")
            except Exception as e:
                logger.error(f"Error closing MIDI port: {e}")
            finally:
                self._port = None
                self._enabled = False
                
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class MidiStub:
    """Stub implementation when MIDI is not available"""
    
    def __init__(self, *args, **kwargs):
        logger.info("Using MIDI stub (MIDI not available)")
        
    def play_note(self, *args, **kwargs) -> bool:
        return False
        
    def machine_start(self) -> bool:
        logger.debug("MIDI stub: machine_start")
        return False
        
    def machine_stop(self) -> bool:
        logger.debug("MIDI stub: machine_stop")
        return False
        
    def machine_pause(self) -> bool:
        logger.debug("MIDI stub: machine_pause")
        return False
        
    def tool_change(self) -> bool:
        logger.debug("MIDI stub: tool_change")
        return False
        
    def program_start(self) -> bool:
        logger.debug("MIDI stub: program_start")
        return False
        
    def program_end(self) -> bool:
        logger.debug("MIDI stub: program_end")
        return False
        
    def error_alert(self) -> bool:
        logger.debug("MIDI stub: error_alert")
        return False
        
    def warning_alert(self) -> bool:
        logger.debug("MIDI stub: warning_alert")
        return False
        
    def emergency_stop(self) -> bool:
        logger.debug("MIDI stub: emergency_stop")
        return False
        
    def get_statistics(self) -> Dict[str, Any]:
        return {'enabled': False, 'stub': True}
        
    def close(self) -> None:
        pass
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Factory function
def create_midi_controller(**kwargs) -> Any:
    """
    Create MIDI controller instance
    
    Returns MidiController if MIDI is available, otherwise MidiStub
    """
    if MIDI_AVAILABLE:
        return MidiController(**kwargs)
    else:
        return MidiStub(**kwargs)
