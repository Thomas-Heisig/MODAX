"""
Pendant Control Device Driver

This module provides support for pendant/handheld control devices used for
manual CNC machine control. Pendants provide:
- Manual jog control (X, Y, Z axes)
- Feed rate override
- Spindle speed override
- Emergency stop
- Cycle start/stop
- Tool selection
- Program selection

Supports:
- USB HID pendants (MPG/handwheel)
- Wireless pendants (Bluetooth, WiFi)
- Serial pendants (RS232, RS485)
- Custom pendant protocols

Compatible Devices:
- Generic USB MPG/handwheel pendants
- XHC WHB series wireless pendants
- MACH3/LinuxCNC compatible pendants
- Custom Arduino/ESP32 based pendants
"""

import logging
from typing import Optional, Dict, Any, Callable, List
from enum import IntEnum
from dataclasses import dataclass
import threading
import time

try:
    import hid
    HID_AVAILABLE = True
except ImportError:
    HID_AVAILABLE = False
    logging.warning("HID support not available. Install with: pip install hidapi")

logger = logging.getLogger(__name__)


class PendantButton(IntEnum):
    """Pendant button definitions"""
    EMERGENCY_STOP = 0
    CYCLE_START = 1
    CYCLE_STOP = 2
    FEED_HOLD = 3
    RESET = 4
    SPINDLE_START = 5
    SPINDLE_STOP = 6
    PROBE_START = 7
    MACRO_1 = 8
    MACRO_2 = 9
    MACRO_3 = 10
    MACRO_4 = 11


class PendantAxis(IntEnum):
    """Pendant axis selection"""
    X = 0
    Y = 1
    Z = 2
    A = 3
    B = 4
    C = 5
    SPINDLE = 6
    FEED = 7


class JogMode(IntEnum):
    """Jog mode selection"""
    CONTINUOUS = 0
    STEP = 1
    MPG = 2  # Manual Pulse Generator


@dataclass
class PendantState:
    """Current pendant state"""
    axis: PendantAxis = PendantAxis.X
    jog_mode: JogMode = JogMode.STEP
    jog_step: float = 0.1  # mm
    feed_override: int = 100  # percent
    spindle_override: int = 100  # percent
    mpg_position: int = 0
    buttons_pressed: List[int] = None
    
    def __post_init__(self):
        if self.buttons_pressed is None:
            self.buttons_pressed = []


class PendantEvent:
    """Pendant event data"""
    
    def __init__(
        self,
        event_type: str,
        data: Any = None,
        timestamp: Optional[float] = None
    ):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or time.time()


class PendantDevice:
    """
    Pendant control device driver
    
    Provides interface for pendant/handwheel devices.
    Supports USB HID and custom protocols.
    """
    
    def __init__(
        self,
        vendor_id: Optional[int] = None,
        product_id: Optional[int] = None,
        device_path: Optional[str] = None
    ):
        """
        Initialize pendant device
        
        Args:
            vendor_id: USB vendor ID (for HID devices)
            product_id: USB product ID (for HID devices)
            device_path: Direct device path
        """
        if not HID_AVAILABLE:
            logger.warning("HID not available - running in stub mode")
            self._enabled = False
            return
            
        self._enabled = True
        self._vendor_id = vendor_id
        self._product_id = product_id
        self._device_path = device_path
        self._device: Optional[hid.device] = None
        self._connected = False
        
        # State
        self._state = PendantState()
        self._lock = threading.Lock()
        self._running = False
        self._read_thread: Optional[threading.Thread] = None
        
        # Event handlers
        self._button_handlers: Dict[int, Callable] = {}
        self._axis_handler: Optional[Callable] = None
        self._mpg_handler: Optional[Callable] = None
        
        # Statistics
        self._stats = {
            'events_processed': 0,
            'buttons_pressed': 0,
            'mpg_pulses': 0,
            'last_event': None
        }
        
        # Connect to device
        self._connect()
        
    def _connect(self) -> bool:
        """Connect to pendant device"""
        try:
            self._device = hid.device()
            
            if self._device_path:
                # Connect using device path
                self._device.open_path(self._device_path.encode())
            elif self._vendor_id and self._product_id:
                # Connect using VID/PID
                self._device.open(self._vendor_id, self._product_id)
            else:
                # Try to find any pendant device
                devices = hid.enumerate()
                pendant_devices = [
                    d for d in devices
                    if 'pendant' in d['product_string'].lower() or
                    'mpg' in d['product_string'].lower() or
                    'handwheel' in d['product_string'].lower()
                ]
                
                if not pendant_devices:
                    logger.warning("No pendant devices found")
                    return False
                    
                # Use first found pendant
                device_info = pendant_devices[0]
                self._device.open(device_info['vendor_id'], device_info['product_id'])
                logger.info(f"Auto-detected pendant: {device_info['product_string']}")
                
            # Set non-blocking mode
            self._device.set_nonblocking(1)
            
            self._connected = True
            logger.info("Pendant device connected")
            
            # Start read thread
            self._start_read_thread()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to pendant device: {e}")
            self._connected = False
            return False
            
    def _start_read_thread(self) -> None:
        """Start background thread to read pendant data"""
        if self._read_thread and self._read_thread.is_alive():
            return
            
        self._running = True
        self._read_thread = threading.Thread(
            target=self._read_loop,
            daemon=True
        )
        self._read_thread.start()
        
    def _read_loop(self) -> None:
        """Background loop to read pendant events"""
        logger.info("Pendant read thread started")
        
        while self._running and self._connected:
            try:
                # Read data from device
                data = self._device.read(64, timeout_ms=100)
                
                if data:
                    self._process_data(data)
                    
            except Exception as e:
                logger.error(f"Error reading pendant data: {e}")
                time.sleep(0.1)
                
        logger.info("Pendant read thread stopped")
        
    def _process_data(self, data: List[int]) -> None:
        """Process data from pendant"""
        if not data:
            return
            
        try:
            # Parse data based on protocol
            # This is a generic parser - customize for your pendant
            
            report_id = data[0]
            
            if report_id == 0x01:  # Button report
                self._process_buttons(data[1:])
            elif report_id == 0x02:  # Axis/MPG report
                self._process_mpg(data[1:])
            elif report_id == 0x03:  # Override report
                self._process_overrides(data[1:])
                
            self._stats['events_processed'] += 1
            self._stats['last_event'] = time.time()
            
        except Exception as e:
            logger.error(f"Error processing pendant data: {e}")
            
    def _process_buttons(self, data: List[int]) -> None:
        """Process button presses"""
        # Parse button state from data
        # This is protocol-specific
        button_state = data[0]
        
        for button_id in range(16):
            if button_state & (1 << button_id):
                # Button pressed
                with self._lock:
                    if button_id not in self._state.buttons_pressed:
                        self._state.buttons_pressed.append(button_id)
                        self._stats['buttons_pressed'] += 1
                        
                # Call handler if registered
                if button_id in self._button_handlers:
                    event = PendantEvent('button_press', button_id)
                    self._button_handlers[button_id](event)
            else:
                # Button released
                with self._lock:
                    if button_id in self._state.buttons_pressed:
                        self._state.buttons_pressed.remove(button_id)
                        
    def _process_mpg(self, data: List[int]) -> None:
        """Process MPG (handwheel) movement"""
        # Parse MPG data
        axis = data[0]
        delta = int.from_bytes(data[1:3], byteorder='little', signed=True)
        
        if delta != 0:
            with self._lock:
                self._state.mpg_position += delta
                self._stats['mpg_pulses'] += abs(delta)
                
            # Call handler if registered
            if self._mpg_handler:
                event = PendantEvent('mpg_move', {
                    'axis': axis,
                    'delta': delta,
                    'position': self._state.mpg_position
                })
                self._mpg_handler(event)
                
    def _process_overrides(self, data: List[int]) -> None:
        """Process feed/spindle override"""
        feed_override = data[0]
        spindle_override = data[1]
        
        with self._lock:
            self._state.feed_override = feed_override
            self._state.spindle_override = spindle_override
            
    def register_button_handler(
        self,
        button: PendantButton,
        handler: Callable[[PendantEvent], None]
    ) -> None:
        """
        Register handler for button press
        
        Args:
            button: Button to monitor
            handler: Callback function
        """
        self._button_handlers[int(button)] = handler
        logger.debug(f"Registered handler for button {button.name}")
        
    def register_mpg_handler(
        self,
        handler: Callable[[PendantEvent], None]
    ) -> None:
        """
        Register handler for MPG movement
        
        Args:
            handler: Callback function
        """
        self._mpg_handler = handler
        logger.debug("Registered MPG handler")
        
    def get_state(self) -> PendantState:
        """Get current pendant state"""
        with self._lock:
            return PendantState(
                axis=self._state.axis,
                jog_mode=self._state.jog_mode,
                jog_step=self._state.jog_step,
                feed_override=self._state.feed_override,
                spindle_override=self._state.spindle_override,
                mpg_position=self._state.mpg_position,
                buttons_pressed=self._state.buttons_pressed.copy()
            )
            
    def set_axis(self, axis: PendantAxis) -> None:
        """Set active axis"""
        with self._lock:
            self._state.axis = axis
            logger.debug(f"Pendant axis set to {axis.name}")
            
    def set_jog_mode(self, mode: JogMode, step: Optional[float] = None) -> None:
        """
        Set jog mode
        
        Args:
            mode: Jog mode
            step: Step size for STEP mode (mm)
        """
        with self._lock:
            self._state.jog_mode = mode
            if step is not None:
                self._state.jog_step = step
            logger.debug(f"Pendant jog mode set to {mode.name}")
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get pendant statistics"""
        return {
            'connected': self._connected,
            'vendor_id': self._vendor_id,
            'product_id': self._product_id,
            **self._stats
        }
        
    def close(self) -> None:
        """Close pendant device"""
        self._running = False
        
        # Wait for read thread to stop
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=1.0)
            
        if self._device:
            try:
                self._device.close()
                logger.info("Pendant device closed")
            except Exception as e:
                logger.error(f"Error closing pendant device: {e}")
            finally:
                self._device = None
                self._connected = False
                
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class PendantStub:
    """Stub implementation when HID is not available"""
    
    def __init__(self, *args, **kwargs):
        logger.info("Using Pendant stub (HID not available)")
        
    def register_button_handler(self, button, handler) -> None:
        pass
        
    def register_mpg_handler(self, handler) -> None:
        pass
        
    def get_state(self) -> PendantState:
        return PendantState()
        
    def set_axis(self, axis: PendantAxis) -> None:
        pass
        
    def set_jog_mode(self, mode: JogMode, step: Optional[float] = None) -> None:
        pass
        
    def get_statistics(self) -> Dict[str, Any]:
        return {'connected': False, 'stub': True}
        
    def close(self) -> None:
        pass
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Factory function
def create_pendant_device(**kwargs) -> Any:
    """
    Create pendant device instance
    
    Returns PendantDevice if HID is available, otherwise PendantStub
    """
    if HID_AVAILABLE:
        return PendantDevice(**kwargs)
    else:
        return PendantStub(**kwargs)
