"""ACMEDoorBackend — device-specific helper subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from .driver import ACMEMultiCapDriver

from .driver import ACMEMultiCapCommand


class _IsLockedCommand(ACMEMultiCapCommand):
  verb = "GET"
  path = "/door/locked"


class _LockDoorCommand(ACMEMultiCapCommand):
  verb = "POST"
  path = "/door/lock"


class _UnlockDoorCommand(ACMEMultiCapCommand):
  verb = "POST"
  path = "/door/unlock"


class ACMEDoorBackend:
  """ACMEDoorBackend — plain helper class (not a CapabilityBackend), following the STARCover pattern.

  Device-specific subsystem with no Backend ABC (P-16). When a second device upstream
  needs the same door-shaped operation, this can be promoted to a Capability ABC + concrete
  Backend. Until then, it stays attached to the driver as a plain helper with lifecycle hooks.
  """

  def __init__(self, driver: "ACMEMultiCapDriver"):
    self.driver = driver

  async def _on_setup(self) -> None:
    # TODO: helper-specific init (if any). Pass is acceptable.
    pass

  async def _on_stop(self) -> None:
    # TODO: helper-specific safety shutdown (if any). Pass is acceptable.
    pass

  async def is_locked(self) -> bool:
    # TODO: call self.driver.send_command(_IsLockedCommand()); parse and return.
    raise NotImplementedError

  async def lock(self) -> None:
    # TODO: call self.driver.send_command(_LockDoorCommand()).
    raise NotImplementedError

  async def unlock(self) -> None:
    # TODO: call self.driver.send_command(_UnlockDoorCommand()).
    raise NotImplementedError
