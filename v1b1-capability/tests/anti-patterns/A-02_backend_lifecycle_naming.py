# Anti-pattern fixture A-02: Backend uses setup/stop instead of _on_setup/_on_stop
# Violates: Common Mistake from creating-capabilities.md (Lifecycle section)
# Expected pattern_id when skill runs: P-02
# Expected principle: P6 — Driver is the wire, backend is the protocol
#                     (also signals that lifecycle hooks are misused — backend
#                     should override the leading-underscore hooks, not the
#                     public methods which only Device/Driver own)
#
# What's planted: ACMEFanBackend overrides setup() and stop() instead of
# _on_setup() and _on_stop(). The Capability lifecycle (Device.setup ->
# cap._on_setup -> backend._on_setup) bypasses this entirely; the backend's
# initialization will never be called.

from pylabrobot.capabilities.fan_control import FanBackend


class ACMEFanBackend(FanBackend):
    def __init__(self, driver):
        self._driver = driver
        self._configured = False

    # ANTI-PATTERN: backend should override _on_setup, not setup.
    # Capability._on_setup() -> backend._on_setup(). The backend's setup() here
    # is dead code — it is never called by the Device lifecycle.
    async def setup(self):
        await self._driver.send(b"\x10")  # configure fan
        self._configured = True

    # ANTI-PATTERN: same — should be _on_stop.
    async def stop(self):
        await self._driver.send(b"\x00")  # turn off

    async def turn_on(self, intensity: int) -> None:
        if not self._configured:
            raise RuntimeError("Fan not configured")
        await self._driver.send(b"\x01" + bytes([intensity]))

    async def turn_off(self) -> None:
        await self._driver.send(b"\x00")
