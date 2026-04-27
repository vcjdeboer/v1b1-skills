# Anti-pattern fixture A-06: Backend implements optional mixin methods without inheriting the mixin
# Violates: P-14 (backend-mixin pattern — Has.../Can... ABCs)
# Expected pattern_id when skill runs: P-14
# Expected principle: P4 — Keep the ABC small, grow through mixins
#
# What's planted: ACMEShakerBackend defines start_shaking and stop_shaking methods
# (the canonical HasContinuousShaking interface) but does not inherit HasContinuousShaking.
# The Capability frontend cannot use isinstance(backend, HasContinuousShaking) to detect
# support; the methods are present but invisible to the framework. The opt-in declaration
# is missing.

from typing import Optional, Union

from pylabrobot.capabilities.capability import BackendParams
from pylabrobot.capabilities.shaking import ShakerBackend

# NOTE: HasContinuousShaking is the available mixin ABC for start/stop continuous shaking.
# from pylabrobot.capabilities.shaking.backend import HasContinuousShaking


class ACMEDriver:
    async def setup(self):
        pass

    async def stop(self):
        pass

    async def send_command(self, cmd: str):
        pass


# ANTI-PATTERN: this backend supports continuous shaking (it has start_shaking and
# stop_shaking matching the HasContinuousShaking interface) but does NOT inherit
# HasContinuousShaking. The Capability frontend's isinstance check will fail; the
# optional capability is present but not declared.
class ACMEShakerBackend(ShakerBackend):
    def __init__(self, driver: ACMEDriver):
        self._driver = driver

    async def shake(self, speed: float, duration: float, backend_params=None):
        await self.start_shaking(speed)
        # ... duration handling

    # ANTI-PATTERN: present but undeclared via mixin.
    async def start_shaking(self, speed: float, acceleration: Union[int, float] = 0):
        await self._driver.send_command(f"setShakeTargetSpeed{int(speed)}")
        await self._driver.send_command("shakeOn")

    # ANTI-PATTERN: same — not opted in via mixin inheritance.
    async def stop_shaking(self, deceleration: Union[int, float] = 0):
        await self._driver.send_command("shakeOff")


# CORRECT form, for reference (not part of the anti-pattern fixture):
#
# from pylabrobot.capabilities.shaking.backend import HasContinuousShaking
#
# class ACMEShakerBackend(ShakerBackend, HasContinuousShaking):
#     ...  # same methods, but now framework-visible via isinstance
