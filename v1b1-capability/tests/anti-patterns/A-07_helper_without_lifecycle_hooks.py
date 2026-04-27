# Anti-pattern fixture A-07: Device-specific helper class without _on_setup / _on_stop
# Violates: P-16 (device-specific helper subsystems must have lifecycle hooks)
#           P-25 (lifecycle hook scope — backend / helper init lives in _on_setup)
# Expected pattern_id when skill runs: P-16 (primary)
# Expected principle: P3 — ABC extraction trigger (helpers are localities-without-an-ABC;
#                    they still need lifecycle to integrate with Device.setup/stop)
#
# What's planted: ACMECover is a plain helper class attached to ACMEDriver as
# driver.cover. It has methods that the user calls (lock, unlock), so it qualifies
# as a device-specific helper subsystem (the STARCover / NimbusDoor pattern, P-16).
# But it has NO _on_setup or _on_stop methods. When the driver tries to walk its
# subsystems for lifecycle, this helper has nothing to call. State is not initialized,
# safe shutdown does not run, and the inconsistency with other helpers in the same
# device package becomes a maintenance hazard.

from pylabrobot.device import Driver


class ACMEDriver(Driver):
    def __init__(self, port: str):
        super().__init__()
        self.port = port
        self.cover: "ACMECover" = ACMECover(driver=self)

    async def setup(self):
        # Connect, then walk subsystems. The cover's missing hooks mean its
        # initialization is silently skipped.
        for sub in self._subsystems:
            await sub._on_setup()

    async def stop(self):
        for sub in reversed(self._subsystems):
            await sub._on_stop()

    @property
    def _subsystems(self):
        return [self.cover]

    async def send_command(self, module: str, command: str):
        pass


# ANTI-PATTERN: this is a device-specific helper subsystem (P-16) attached to the
# driver, but it lacks _on_setup and _on_stop. The driver's _subsystems walk in
# setup() and stop() will fail with AttributeError, OR if the walk uses getattr
# defaults, lifecycle is silently skipped — neither is acceptable.
class ACMECover:
    """Plain helper class for ACME device cover."""

    def __init__(self, driver: ACMEDriver):
        self.driver = driver

    # ANTI-PATTERN: missing async def _on_setup(self): pass
    # ANTI-PATTERN: missing async def _on_stop(self): pass

    async def lock(self):
        await self.driver.send_command(module="C0", command="CO")

    async def unlock(self):
        await self.driver.send_command(module="C0", command="HO")


# CORRECT form (for reference):
#
# class ACMECover:
#     async def _on_setup(self):
#         pass
#
#     async def _on_stop(self):
#         pass
#
#     async def lock(self): ...
#     async def unlock(self): ...
