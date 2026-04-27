# Anti-pattern fixture A-05: Backend does not hold self._driver
# Violates: Common Mistake from creating-capabilities.md (the integration pattern)
# Expected pattern_id when skill runs: P-05
# Expected principle: P6 — Driver is the wire, backend is the protocol
#                     (backend reaches the driver via self._driver, not via
#                      module-level state, hidden globals, or re-construction)
#
# What's planted: ACMEFanBackend does not store a driver reference. To send
# commands it constructs a fresh ACMEDriver inside each method, which (a)
# reopens the connection per call, (b) bypasses the Device's wired driver,
# (c) breaks lifecycle expectations (the freshly-constructed driver was never
# subjected to setup() / stop() through the Device).

from pylabrobot.capabilities.fan_control import FanBackend
from pylabrobot.device import Device, Driver


class ACMEDriver(Driver):
    def __init__(self, port: str):
        self.port = port

    async def setup(self):
        pass

    async def stop(self):
        pass

    async def send(self, command: bytes):
        pass


class ACMEFanBackend(FanBackend):
    # ANTI-PATTERN: __init__ does not accept a driver and does not store
    # self._driver. The backend cannot share the Device's wired driver.
    def __init__(self, port: str):
        self._port = port

    async def turn_on(self, intensity: int) -> None:
        # ANTI-PATTERN: re-creating the driver per call. Connection lifecycle
        # is broken; the Device's setup()/stop() never see this driver.
        driver = ACMEDriver(port=self._port)
        await driver.setup()
        await driver.send(b"\x01" + bytes([intensity]))
        await driver.stop()

    async def turn_off(self) -> None:
        driver = ACMEDriver(port=self._port)
        await driver.setup()
        await driver.send(b"\x00")
        await driver.stop()
