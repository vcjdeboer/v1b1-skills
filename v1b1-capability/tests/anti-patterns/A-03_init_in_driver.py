# Anti-pattern fixture A-03: Hardware-specific init in driver.setup() instead
# of backend._on_setup()
# Violates: Common Mistake from creating-capabilities.md (Backend _on_setup section)
# Expected pattern_id when skill runs: P-03
# Expected principle: P6 — Driver is the wire, backend is the protocol
#
# What's planted: ACMEDriver.setup() configures objectives and filter cubes,
# which is microscopy capability initialization. Capability-specific hardware
# init (configure objectives, calibrate, query device card) belongs in
# backend._on_setup(), called after driver.setup() opens the connection.
# Driver.setup() should only open the connection.

from pylabrobot.capabilities.microscopy import MicroscopyBackend
from pylabrobot.device import Driver


class ACMEDriver(Driver):
    def __init__(self, port: str, objectives=None, filter_cubes=None):
        self.port = port
        self._objectives = objectives or {}
        self._filter_cubes = filter_cubes or {}

    async def setup(self):
        # Open connection (this part is correct)
        await self._open_connection()
        # ANTI-PATTERN: capability-specific initialization in driver.setup().
        # These belong in ACMEMicroscopyBackend._on_setup(), where the backend
        # configures the objectives and filter cubes after the driver
        # connection is open.
        for pos, obj in self._objectives.items():
            await self._send(f"OBJECTIVE {pos} {obj}".encode())
        for pos, mode in self._filter_cubes.items():
            await self._send(f"FILTER {pos} {mode}".encode())

    async def stop(self):
        await self._close_connection()

    async def _open_connection(self):
        pass

    async def _close_connection(self):
        pass

    async def _send(self, command: bytes):
        pass


class ACMEMicroscopyBackend(MicroscopyBackend):
    def __init__(self, driver: ACMEDriver):
        self._driver = driver

    # _on_setup is missing here — and even if it existed, the work is already
    # done by driver.setup(), which is the wrong place.
