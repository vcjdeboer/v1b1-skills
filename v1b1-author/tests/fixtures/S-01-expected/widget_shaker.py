"""ACME WidgetShaker device — single-file scaffold."""

from __future__ import annotations

from typing import Optional

from pylabrobot.capabilities.capability import BackendParams
from pylabrobot.capabilities.shaking import Shaker
from pylabrobot.capabilities.shaking.backend import HasContinuousShaking, ShakerBackend
from pylabrobot.device import Device, Driver


class ACMEWidgetShakerDriver(Driver):
  """Driver for the ACME WidgetShaker.

  Generic transport only — never adds Capability-named methods.
  Per-Capability protocol encoding lives in the Backend(s) below.
  """

  def __init__(self, port: str):
    super().__init__()
    self.port = port
    # TODO: connection state (e.g., serial port handle)

  async def setup(self, backend_params: Optional[BackendParams] = None) -> None:
    # TODO: open the connection. Capability-specific init lives in Backend._on_setup.
    pass

  async def stop(self) -> None:
    # TODO: close the connection.
    pass

  async def send_command(self, cmd: str) -> str:
    """Generic transport — sends a wire-format string and returns the raw response.

    Per-Capability operations build their wire payload in the Backend method body
    and call this transport. Do NOT add domain-named methods (set_temperature,
    start_shaking, etc.) here — that's P-01 anti-pattern.
    """
    # TODO: write cmd to the serial port; read and return the response string.
    raise NotImplementedError


class ACMEWidgetShakerShakerBackend(ShakerBackend, HasContinuousShaking):
  """Shaker backend backed by the ACME WidgetShaker serial protocol.

  Explicit P-14 mixin opt-in: HasContinuousShaking declares this backend supports
  start_shaking / stop_shaking independently (matching the device's natural shape).
  """

  def __init__(self, driver: ACMEWidgetShakerDriver):
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
    # TODO: return True if the WidgetShaker model supports plate locking.
    return False

  async def shake(
    self,
    speed: float,
    duration: float,
    backend_params: Optional[BackendParams] = None,
  ):
    # TODO: build wire payload here (e.g., f"SHAKE {int(speed)} {int(duration)}")
    # and call self.driver.send_command(...).
    raise NotImplementedError

  async def lock_plate(self):
    # TODO: build wire payload here for plate-lock; call self.driver.send_command(...).
    raise NotImplementedError

  async def unlock_plate(self):
    # TODO: build wire payload here for plate-unlock; call self.driver.send_command(...).
    raise NotImplementedError

  async def start_shaking(self, speed: float):
    # TODO: build wire payload here (e.g., f"SHAKE_START {int(speed)}")
    # and call self.driver.send_command(...).
    raise NotImplementedError

  async def stop_shaking(self):
    # TODO: build wire payload here (e.g., "SHAKE_STOP")
    # and call self.driver.send_command(...).
    raise NotImplementedError


class ACMEWidgetShaker(Device):
  """ACME WidgetShaker device frontend."""

  def __init__(self, port: str):
    driver = ACMEWidgetShakerDriver(port=port)
    super().__init__(driver=driver)
    self.driver: ACMEWidgetShakerDriver = driver
    # CAUTION: Convenience methods on this Device that map to a Capability operation
    # MUST go through self.<capability>.<method>, NEVER through self.driver.<method>.
    # Wrong default: capability bypass.
    self.shaker = Shaker(backend=ACMEWidgetShakerShakerBackend(driver))
    self._capabilities = [self.shaker]
