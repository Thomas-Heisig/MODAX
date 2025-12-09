"""
MODAX OPC UA Server Implementation

This module provides an OPC UA server for exposing MODAX device data
to external systems like SCADA, MES, or other industrial automation systems.
"""

import asyncio
import logging
import os
from asyncua import Server, ua
from asyncua.common.node import Node
from datetime import datetime, timezone
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class MODAXOpcUaServer:
    """OPC UA Server for MODAX System"""

    def __init__(
        self,
        endpoint: str = "opc.tcp://0.0.0.0:4840",
        name: str = "MODAX OPC UA Server",
        enable_security: bool = False
    ):
        """
        Initialize OPC UA server

        Args:
            endpoint: Server endpoint URL
            name: Server name
            enable_security: Enable certificate-based security
        """
        self.endpoint = endpoint
        self.name = name
        self.enable_security = enable_security
        self.server: Optional[Server] = None
        self.namespace_idx: Optional[int] = None
        self.device_nodes: Dict[str, Dict[str, Any]] = {}
        self.devices_folder: Optional[Node] = None
        self.system_folder: Optional[Node] = None
        self._running = False

    async def init(self):
        """Initialize OPC UA server"""
        self.server = Server()
        await self.server.init()

        # Set server properties
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name(self.name)

        # Set up security if enabled
        if self.enable_security:
            await self.setup_security()
        else:
            # Development mode: anonymous access
            self.server.set_security_IDs(["Anonymous"])

        # Set up namespace
        self.namespace_idx = await self.server.register_namespace("urn:modax:server")

        # Create root objects
        await self.setup_object_model()

        logger.info(f"OPC UA Server initialized at {self.endpoint}")

    async def setup_security(self):
        """Configure OPC UA security with certificates"""
        cert_dir = os.getenv("OPCUA_CERT_DIR", "certs")
        server_cert = os.path.join(cert_dir, "server_cert.der")
        server_key = os.path.join(cert_dir, "server_key.pem")

        if os.path.exists(server_cert) and os.path.exists(server_key):
            try:
                await self.server.load_certificate(server_cert)
                await self.server.load_private_key(server_key)

                # Set security policies
                self.server.set_security_policy([
                    ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
                    ua.SecurityPolicyType.Basic256Sha256_Sign,
                ])

                logger.info("OPC UA security enabled with certificates")
            except Exception as e:
                logger.warning(f"Failed to load certificates: {e}. Running without security.")
                self.server.set_security_IDs(["Anonymous"])
        else:
            logger.warning(
                f"Certificates not found at {cert_dir}. "
                "Running without security. Use generate_opcua_certs.sh to create them."
            )
            self.server.set_security_IDs(["Anonymous"])

    async def setup_object_model(self):
        """Create OPC UA object model"""
        objects = self.server.get_objects_node()

        # Create MODAX root folder
        modax_root = await objects.add_folder(self.namespace_idx, "MODAX")

        # Create Devices folder
        self.devices_folder = await modax_root.add_folder(self.namespace_idx, "Devices")

        # Create System folder
        self.system_folder = await modax_root.add_folder(self.namespace_idx, "System")

        # System status variables
        await self.system_folder.add_variable(self.namespace_idx, "Status", "Running")
        await self.system_folder.add_variable(self.namespace_idx, "ConnectedDevices", 0)
        await self.system_folder.add_variable(self.namespace_idx, "Timestamp", datetime.now(timezone.utc))

        logger.info("OPC UA object model created")

    async def add_device(self, device_id: str):
        """
        Add a device to OPC UA namespace

        Args:
            device_id: Unique device identifier
        """
        if device_id in self.device_nodes:
            logger.debug(f"Device {device_id} already exists in OPC UA namespace")
            return

        # Create device folder
        device_node = await self.devices_folder.add_folder(self.namespace_idx, device_id)

        # Create device variables
        variables = {
            "DeviceID": await device_node.add_variable(self.namespace_idx, "DeviceID", device_id),
            "Status": await device_node.add_variable(self.namespace_idx, "Status", "Unknown"),
            "Current_A": await device_node.add_variable(self.namespace_idx, "Current_A", 0.0),
            "Current_B": await device_node.add_variable(self.namespace_idx, "Current_B", 0.0),
            "Current_C": await device_node.add_variable(self.namespace_idx, "Current_C", 0.0),
            "Vibration": await device_node.add_variable(self.namespace_idx, "Vibration", 0.0),
            "Temperature": await device_node.add_variable(self.namespace_idx, "Temperature", 0.0),
            "RPM": await device_node.add_variable(self.namespace_idx, "RPM", 0),
            "PowerKW": await device_node.add_variable(self.namespace_idx, "PowerKW", 0.0),
            "IsSafe": await device_node.add_variable(self.namespace_idx, "IsSafe", True),
            "LastUpdate": await device_node.add_variable(self.namespace_idx, "LastUpdate", datetime.now(timezone.utc)),
        }

        # Make variables writable for server-side updates
        for var in variables.values():
            await var.set_writable()

        # AI Analysis folder
        ai_folder = await device_node.add_folder(self.namespace_idx, "AI_Analysis")
        ai_variables = {
            "IsAnomaly": await ai_folder.add_variable(self.namespace_idx, "IsAnomaly", False),
            "AnomalyScore": await ai_folder.add_variable(self.namespace_idx, "AnomalyScore", 0.0),
            "WearPercentage": await ai_folder.add_variable(self.namespace_idx, "WearPercentage", 0.0),
            "RemainingHours": await ai_folder.add_variable(self.namespace_idx, "RemainingHours", 0),
            "Confidence": await ai_folder.add_variable(self.namespace_idx, "Confidence", 0.0),
        }

        # Make AI variables writable
        for var in ai_variables.values():
            await var.set_writable()

        variables.update(ai_variables)

        self.device_nodes[device_id] = {
            "node": device_node,
            "variables": variables
        }

        logger.info(f"Added device {device_id} to OPC UA namespace")

    async def update_device_data(self, device_id: str, data: Dict):
        """
        Update device data in OPC UA namespace

        Args:
            device_id: Device identifier
            data: Dictionary with sensor data
        """
        if device_id not in self.device_nodes:
            await self.add_device(device_id)

        variables = self.device_nodes[device_id]["variables"]

        # Update sensor data
        try:
            if "current_a" in data:
                await variables["Current_A"].write_value(float(data["current_a"]))
            if "current_b" in data:
                await variables["Current_B"].write_value(float(data["current_b"]))
            if "current_c" in data:
                await variables["Current_C"].write_value(float(data["current_c"]))
            if "vibration" in data:
                await variables["Vibration"].write_value(float(data["vibration"]))
            if "temperature" in data:
                await variables["Temperature"].write_value(float(data["temperature"]))
            if "rpm" in data:
                await variables["RPM"].write_value(int(data["rpm"]))
            if "power_kw" in data:
                await variables["PowerKW"].write_value(float(data["power_kw"]))
            if "is_safe" in data:
                await variables["IsSafe"].write_value(bool(data["is_safe"]))
            if "status" in data:
                await variables["Status"].write_value(str(data["status"]))

            # Update timestamp
            await variables["LastUpdate"].write_value(datetime.now(timezone.utc))
        except Exception as e:
            logger.error(f"Error updating device {device_id} data: {e}")

    async def update_ai_analysis(self, device_id: str, analysis: Dict):
        """
        Update AI analysis data in OPC UA namespace

        Args:
            device_id: Device identifier
            analysis: Dictionary with AI analysis results
        """
        if device_id not in self.device_nodes:
            return

        variables = self.device_nodes[device_id]["variables"]

        try:
            if "is_anomaly" in analysis:
                await variables["IsAnomaly"].write_value(bool(analysis["is_anomaly"]))
            if "anomaly_score" in analysis:
                await variables["AnomalyScore"].write_value(float(analysis["anomaly_score"]))
            if "wear_percentage" in analysis:
                await variables["WearPercentage"].write_value(float(analysis["wear_percentage"]))
            if "remaining_hours" in analysis:
                await variables["RemainingHours"].write_value(int(analysis["remaining_hours"]))
            if "confidence" in analysis:
                await variables["Confidence"].write_value(float(analysis["confidence"]))
        except Exception as e:
            logger.error(f"Error updating AI analysis for device {device_id}: {e}")

    async def update_system_status(self, connected_devices: int):
        """
        Update system-level status

        Args:
            connected_devices: Number of connected devices
        """
        if self.system_folder is None:
            return

        try:
            # Get system status nodes with specific error handling
            try:
                status_node = await self.system_folder.get_child([f"{self.namespace_idx}:Status"])
                await status_node.write_value("Running")
            except Exception as e:
                logger.error(f"Error updating Status node: {e}")

            try:
                devices_node = await self.system_folder.get_child([f"{self.namespace_idx}:ConnectedDevices"])
                await devices_node.write_value(connected_devices)
            except Exception as e:
                logger.error(f"Error updating ConnectedDevices node: {e}")

            try:
                timestamp_node = await self.system_folder.get_child([f"{self.namespace_idx}:Timestamp"])
                await timestamp_node.write_value(datetime.now(timezone.utc))
            except Exception as e:
                logger.error(f"Error updating Timestamp node: {e}")
        except Exception as e:
            logger.error(f"Error updating system status (folder access): {e}")

    async def start(self):
        """Start OPC UA server"""
        if self._running:
            logger.warning("OPC UA server already running")
            return

        await self.server.start()
        self._running = True
        logger.info(f"OPC UA Server started at {self.endpoint}")

    async def stop(self):
        """Stop OPC UA server"""
        if not self._running:
            return

        await self.server.stop()
        self._running = False
        logger.info("OPC UA Server stopped")

    @property
    def is_running(self) -> bool:
        """Check if server is running"""
        return self._running


# Global OPC UA server instance
_opcua_server: Optional[MODAXOpcUaServer] = None


def get_opcua_server() -> Optional[MODAXOpcUaServer]:
    """Get the global OPC UA server instance"""
    return _opcua_server


async def init_opcua_server(
    enable: bool = True,
    endpoint: str = "opc.tcp://0.0.0.0:4840",
    enable_security: bool = False
) -> Optional[MODAXOpcUaServer]:
    """
    Initialize and start OPC UA server

    Args:
        enable: Enable OPC UA server
        endpoint: Server endpoint URL
        enable_security: Enable certificate-based security

    Returns:
        OPC UA server instance or None if disabled
    """
    global _opcua_server

    if not enable:
        logger.info("OPC UA server is disabled")
        return None

    _opcua_server = MODAXOpcUaServer(
        endpoint=endpoint,
        enable_security=enable_security
    )

    try:
        await _opcua_server.init()
        await _opcua_server.start()
        return _opcua_server
    except Exception as e:
        logger.error(f"Failed to start OPC UA server: {e}")
        _opcua_server = None
        return None


async def stop_opcua_server():
    """Stop OPC UA server"""
    global _opcua_server

    if _opcua_server is not None:
        await _opcua_server.stop()
        _opcua_server = None
