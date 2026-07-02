import logging
from typing import Any, Optional

import tinytuya

logger = logging.getLogger(__name__)


class TuyaClient:
    def __init__(
        self,
        device_config: dict[str, Any],
        exit_on_command_error: bool = True,
        exit_on_status_error: bool = False,
    ):
        self.config = device_config
        self.device_id = device_config["id"]
        self.ip = device_config["ip"]
        self.local_key = device_config["local_key"]
        self.version = device_config.get("version", "3.3")
        self.name = device_config["name"]
        self.dev_type = device_config.get("dev_type", "default")
        self.connection_timeout = device_config.get("connection_timeout_seconds", 5)
        self.connection_retry_limit = device_config.get("connection_retry_limit", 3)
        self.connection_retry_delay = device_config.get("connection_retry_delay_seconds", 5)
        self.persist = device_config.get("persist", False)
        self.exit_on_command_error = exit_on_command_error
        self.exit_on_status_error = exit_on_status_error

        self.device = tinytuya.Device(
            self.device_id,
            self.ip,
            self.local_key,
            dev_type=self.dev_type,
            connection_timeout=self.connection_timeout,
            persist=self.persist,
            connection_retry_limit=self.connection_retry_limit,
            connection_retry_delay=self.connection_retry_delay,
        )
        self.device.set_version(float(self.version))
        self._is_online = False

    def status(self) -> Optional[dict[str, Any]]:
        """Get status from device."""
        try:
            data = self.device.status()
            if data and "dps" in data:
                self._is_online = True
                return data["dps"]
            elif data and "Error" in data:
                error_msg = (
                    f"Error getting status for {self.name} ({self.device_id}): {data['Error']}. "
                    f"Check version={self.version}, dev_type={self.dev_type}, "
                    f"persist={self.persist}, and local_key."
                )
                if self.exit_on_status_error:
                    logger.critical(f"{error_msg} - Exiting process as configured.")
                    import sys

                    sys.exit(1)
                logger.error(error_msg)
            else:
                logger.debug(f"Device {self.name} ({self.device_id}) returned no DPS data")
        except Exception as e:
            if self.exit_on_status_error and (
                "DecodeError" in str(type(e)) or "unexpected payload" in str(e).lower()
            ):
                logger.critical(
                    f"Fatal error getting status for {self.name}: {e} - Exiting process as configured."
                )
                import sys

                sys.exit(1)
            logger.error(f"Failed to get status for {self.name}: {e}")
        
        self._is_online = False
        return None

    def _cast_value(self, dps_id: str, value: Any) -> Any:
        """Cast value according to device schema."""
        mappings = self.config.get("mappings", {})

        dps_meta = next((meta for meta in mappings.values() if str(meta.get("dps")) == str(dps_id)), {})
        dps_type = dps_meta.get("type", "").lower()

        try:
            if dps_type == "integer":
                return int(float(value)) if isinstance(value, (str, float)) else int(value)
            elif dps_type == "boolean":
                if isinstance(value, str):
                    return value.upper() == "ON" or value.lower() == "true"
                return bool(value)
            # Enum, String, Bitmap types - return as is or convert to string if necessary
        except (ValueError, TypeError):
            logger.warning(f"Failed to cast {value} to {dps_type} for DPS {dps_id}")
        
        return value

    def set_dps(self, dps_id: str, value: Any) -> bool:
        """Set DPS value."""
        try:
            casted_value = self._cast_value(dps_id, value)
            logger.info(f"Setting DPS {dps_id} to {casted_value} (original: {value}) for {self.name}")
            # Ensure dps_id is string for key
            payload = {str(dps_id): casted_value}
            logger.info(f"Sending payload to device: {payload}")
            # Revert to standard set_status, but pass the dictionary payload correctly
            # set_status(payload) should send {dps: value} for v3.3
            data = self.device.set_multiple_values(payload)
            if data and "Error" not in data:
                return True
            error = data.get("Error", "Unknown error") if isinstance(data, dict) else "Unknown error"
            self._handle_command_error(f"Error setting DPS for {self.name}: {error}")
        except Exception as e:
            self._handle_command_error(f"Failed to set DPS for {self.name}: {e}")
        return False

    def _handle_command_error(self, message: str):
        if self.exit_on_command_error:
            logger.critical(f"{message} - Exiting process as configured.")
            import sys

            sys.exit(1)
        logger.error(message)

    def is_online(self) -> bool:
        return self._is_online
