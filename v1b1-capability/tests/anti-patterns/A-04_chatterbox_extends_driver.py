# Anti-pattern fixture A-04: Chatterbox backend inherits from Driver
# Violates: Common Mistake from creating-capabilities.md (Chatterbox backends section)
# Expected pattern_id when skill runs: P-04
# Expected principle: P6 — Driver is the wire, backend is the protocol
#                     (chatterbox is a backend-replacement, not a driver-replacement)
#
# What's planted: ACMEFanChatterboxBackend inherits from Driver, which conflates
# the chatterbox role (a no-op backend for testing without hardware) with the
# driver role (hardware connection lifecycle). Chatterbox backends inherit from
# CapabilityBackend (or the specific capability's backend ABC) only.

from pylabrobot.capabilities.fan_control import FanBackend
from pylabrobot.device import Driver


# ANTI-PATTERN: chatterbox should inherit from FanBackend (a CapabilityBackend
# subclass), not from Driver. Inheriting Driver gives the chatterbox a
# connection lifecycle it does not need and confuses the test setup.
class ACMEFanChatterboxBackend(FanBackend, Driver):
    """A chatterbox that pretends to be the fan and the driver."""

    async def setup(self):
        # Borrowed from Driver — irrelevant for a chatterbox
        pass

    async def stop(self):
        pass

    async def turn_on(self, intensity: int) -> None:
        pass

    async def turn_off(self) -> None:
        pass
