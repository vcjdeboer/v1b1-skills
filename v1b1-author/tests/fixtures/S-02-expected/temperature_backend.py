"""ACME MultiCap backend for the TemperatureController capability."""

from __future__ import annotations

from typing import Optional

from pylabrobot.capabilities.capability import BackendParams
from pylabrobot.capabilities.temperature_controlling.backend import (
  TemperatureControllerBackend,
)

from .driver import ACMEMultiCapCommand, ACMEMultiCapDriver


class _SetTemperatureCommand(ACMEMultiCapCommand):
  verb = "POST"
  path = "/temperature"

  def __init__(self, temperature: float):
    self.temperature = temperature

  def body(self):
    return {"temperature": self.temperature}


class _RequestTemperatureCommand(ACMEMultiCapCommand):
  verb = "GET"
  path = "/temperature"


class _DeactivateCommand(ACMEMultiCapCommand):
  verb = "POST"
  path = "/temperature/off"


class ACMEMultiCapTemperatureControllerBackend(TemperatureControllerBackend):
  """TemperatureController backend backed by the ACME MultiCap HTTP protocol."""

  def __init__(self, driver: ACMEMultiCapDriver):
    super().__init__()
    self.driver = driver

  async def _on_setup(self, backend_params: Optional[BackendParams] = None) -> None:
    # TODO: capability-specific post-connection init (e.g., sanity probe).
    pass

  async def _on_stop(self) -> None:
    # TODO: capability-specific safety shutdown (e.g., deactivate heater).
    pass

  @property
  def supports_active_cooling(self) -> bool:
    # TODO: return True if this MultiCap unit can actively cool below ambient.
    return False

  async def set_temperature(self, temperature: float):
    # TODO: build wire payload here; call self.driver.send_command(_SetTemperatureCommand(...)).
    raise NotImplementedError

  async def request_current_temperature(self) -> float:
    # TODO: call self.driver.send_command(_RequestTemperatureCommand()); parse and return.
    raise NotImplementedError

  async def deactivate(self):
    # TODO: build wire payload here; call self.driver.send_command(_DeactivateCommand()).
    raise NotImplementedError
