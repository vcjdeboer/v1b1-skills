# Anti-pattern fixture A-01: Driver method shares name with Capability method
# Violates: Common Mistake #1 from creating-capabilities.md
# Expected pattern_id when skill runs: P-01
# Expected principle: P6 — Driver is the wire, backend is the protocol
#
# What's planted: ACMEDriver has a set_temperature method that mirrors the
# capability operation. The driver should expose generic transport (e.g., send,
# send_command) only; protocol encoding belongs in the backend.

from pylabrobot.capabilities.temperature_controlling import (
    TemperatureController,
    TemperatureControllerBackend,
)
from pylabrobot.device import Device, Driver


class ACMEDriver(Driver):
    """ACME thermostat driver."""

    def __init__(self, port: str):
        self.port = port

    async def setup(self):
        pass

    async def stop(self):
        pass

    # ANTI-PATTERN: this method name (set_temperature) collides with
    # TemperatureControllerBackend.set_temperature. Driver should expose
    # generic transport (send / send_command), not capability-named methods.
    async def set_temperature(self, temperature: float):
        await self._write(f"SET {temperature}".encode())

    async def _write(self, command: bytes):
        # imagined transport
        pass


class ACMETemperatureBackend(TemperatureControllerBackend):
    def __init__(self, driver: ACMEDriver):
        self._driver = driver

    async def set_temperature(self, temperature: float):
        # Pointless delegation through driver.set_temperature — the encoding
        # f"SET {temperature}" lives in the wrong place.
        await self._driver.set_temperature(temperature)


class ACMEThermostat(Device):
    def __init__(self, port: str):
        driver = ACMEDriver(port=port)
        super().__init__(driver=driver)
        self._driver: ACMEDriver = driver
        self.temperature_controller = TemperatureController(
            backend=ACMETemperatureBackend(driver)
        )
        self._capabilities = [self.temperature_controller]
