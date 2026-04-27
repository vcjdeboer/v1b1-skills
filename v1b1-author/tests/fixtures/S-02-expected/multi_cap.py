"""ACME MultiCap device class."""

from __future__ import annotations

from typing import Optional

from pylabrobot.capabilities.shaking import Shaker
from pylabrobot.capabilities.temperature_controlling import TemperatureController
from pylabrobot.device import Device

from .chatterbox_driver import ACMEMultiCapChatterboxDriver
from .door_backend import ACMEDoorBackend
from .driver import ACMEMultiCapDriver
from .shaker_backend import ACMEMultiCapShakerBackend
from .temperature_backend import ACMEMultiCapTemperatureControllerBackend


# CAUTION (FOR THE PROTOCOL-IMPLEMENTATION PHASE):
#
# Three wrong defaults the protocol-implementation phase tends to drift into. Each one is
# documented in the v1b1 review-skill run-doc trail; cite-chase before re-introducing.
#
# (a) Capability-named methods on the Driver (P-01 — driver-mirrors-capability)
#     The Driver stays generic transport — its public surface is send_command(command_object).
#     Adding shake/set_temperature/lock to the Driver creates same-named-method collisions
#     with the Backends.
#     Documented in: PR #1009 (Micronic) Finding 1; Echo branch Finding 1 (8-method collision).
#
# (b) Workflow on the Capability frontend (P-20 — workflow-on-Backend)
#     Multi-step orchestration belongs on the Backend, NEVER on the Capability frontend.
#     The Capability frontend stays a thin @need_capability_ready forward.
#     Documented in: PR #1009 Finding 2; Echo branch Finding 3.
#
# (c) Capability bypass via Device convenience methods (P-02 / P-06)
#     Convenience methods that map to a Capability operation MUST go through
#     self.<capability>.<method>, NEVER through self.driver.<method>.
#     - Genuinely device-level (e.g., serial-number query): self.driver — OK
#     - Capability-shaped (e.g., shake / set_temperature): self.<capability>.<method> — REQUIRED
#     Documented in: Echo branch Finding 5.

class ACMEMultiCap(Device):
  """ACME MultiCap device frontend."""

  def __init__(
    self,
    host: Optional[str] = None,
    port: int = 80,
    chatterbox: bool = False,
  ):
    if chatterbox:
      driver: ACMEMultiCapDriver = ACMEMultiCapChatterboxDriver()
    else:
      if not host:
        raise ValueError("host must be provided when chatterbox is False.")
      driver = ACMEMultiCapDriver(host=host, port=port)
    Device.__init__(self, driver=driver)
    self.driver: ACMEMultiCapDriver = driver

    self.shaker = Shaker(backend=ACMEMultiCapShakerBackend(driver=self.driver))
    self.temperature = TemperatureController(
      backend=ACMEMultiCapTemperatureControllerBackend(driver=self.driver)
    )
    self.door = ACMEDoorBackend(driver=self.driver)

    self._capabilities = [self.shaker, self.temperature]
    self._subsystems = [self.door]
