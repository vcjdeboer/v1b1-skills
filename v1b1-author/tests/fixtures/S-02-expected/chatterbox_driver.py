"""ACME MultiCap chatterbox driver — device-free testing for a discovery-using device.

Documented P-04 exception: this driver class extends ACMEMultiCapDriver itself rather than
a CapabilityBackend, because the standard chatterbox form cannot fake the runtime discovery
that ACMEMultiCapDriver.setup() performs. Substitutes pre-built defaults for the discovery
output so backends can be wired without a real device.

For drivers that do NOT do discovery, use the standard chatterbox form (chatterbox.py).
"""

from __future__ import annotations

from typing import Optional

from pylabrobot.capabilities.capability import BackendParams

from .driver import ACMEMultiCapCommand, ACMEMultiCapDriver


class ACMEMultiCapChatterboxDriver(ACMEMultiCapDriver):
  """Chatterbox-mode driver for the ACME MultiCap.

  Substitutes pre-built defaults for the module discovery output that the real driver's
  setup() would normally probe over HTTP. The Device class wires this driver instead of
  the real one when the contributor passes ``chatterbox=True`` at construction time.
  """

  def __init__(self, host: str = "chatterbox", port: int = 0):
    super().__init__(host=host, port=port)

  async def setup(self, backend_params: Optional[BackendParams] = None) -> None:
    # TODO: substitute pre-built defaults for the discovery output.
    # Pre-built defaults (instead of GET /info):
    #   self._modules = {"shaker": {"present": True}, "temperature": {"present": True}, "door": {"present": True}}
    # Do NOT call the real discovery routines from ACMEMultiCapDriver.setup();
    # the whole point of the chatterbox is to skip them.
    pass

  async def stop(self) -> None:
    pass

  async def send_command(self, command: ACMEMultiCapCommand):
    # TODO: log the command instead of sending it; return canned data appropriate to command.path.
    raise NotImplementedError
