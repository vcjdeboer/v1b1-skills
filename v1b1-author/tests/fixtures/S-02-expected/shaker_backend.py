"""ACME MultiCap backend for the Shaker capability."""

from __future__ import annotations

from typing import Optional

from pylabrobot.capabilities.capability import BackendParams
from pylabrobot.capabilities.shaking.backend import HasContinuousShaking, ShakerBackend

from .driver import ACMEMultiCapCommand, ACMEMultiCapDriver


class _ShakeCommand(ACMEMultiCapCommand):
  verb = "POST"
  path = "/shake"

  def __init__(self, speed: float, duration: float):
    self.speed = speed
    self.duration = duration

  def body(self):
    return {"speed": self.speed, "duration": self.duration}


class _StartShakingCommand(ACMEMultiCapCommand):
  verb = "POST"
  path = "/shake/start"

  def __init__(self, speed: float):
    self.speed = speed

  def body(self):
    return {"speed": self.speed}


class _StopShakingCommand(ACMEMultiCapCommand):
  verb = "POST"
  path = "/shake/stop"


class _LockPlateCommand(ACMEMultiCapCommand):
  verb = "POST"
  path = "/shake/lock"


class _UnlockPlateCommand(ACMEMultiCapCommand):
  verb = "POST"
  path = "/shake/unlock"


class ACMEMultiCapShakerBackend(ShakerBackend, HasContinuousShaking):
  """Shaker backend backed by the ACME MultiCap HTTP protocol.

  Explicit P-14 mixin opt-in: HasContinuousShaking declares this backend supports
  start_shaking / stop_shaking independently (matching the device's natural shape).
  """

  def __init__(self, driver: ACMEMultiCapDriver):
    super().__init__()
    self.driver = driver

  async def _on_setup(self, backend_params: Optional[BackendParams] = None) -> None:
    # TODO: capability-specific post-connection init (e.g., calibration probe).
    pass

  async def _on_stop(self) -> None:
    # TODO: capability-specific safety shutdown (e.g., ensure shaking has stopped).
    pass

  @property
  def supports_locking(self) -> bool:
    # TODO: return True if this MultiCap unit's shaker supports plate locking.
    return False

  async def shake(
    self,
    speed: float,
    duration: float,
    backend_params: Optional[BackendParams] = None,
  ):
    # TODO: build wire payload here; call self.driver.send_command(_ShakeCommand(...)).
    raise NotImplementedError

  async def lock_plate(self):
    # TODO: build wire payload here; call self.driver.send_command(_LockPlateCommand()).
    raise NotImplementedError

  async def unlock_plate(self):
    # TODO: build wire payload here; call self.driver.send_command(_UnlockPlateCommand()).
    raise NotImplementedError

  async def start_shaking(self, speed: float):
    # TODO: build wire payload here; call self.driver.send_command(_StartShakingCommand(speed)).
    raise NotImplementedError

  async def stop_shaking(self):
    # TODO: build wire payload here; call self.driver.send_command(_StopShakingCommand()).
    raise NotImplementedError
