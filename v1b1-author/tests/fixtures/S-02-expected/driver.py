"""ACME MultiCap driver — wire transport + runtime discovery."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pylabrobot.capabilities.capability import BackendParams
from pylabrobot.device import Driver


class ACMEMultiCapCommand:
  """Base class for ACME MultiCap wire commands.

  Each subclass carries the wire-format payload for one vendor endpoint.
  Backends construct command instances and pass them to driver.send_command;
  the driver does NOT know what each command means.
  """

  verb: str = ""
  path: str = ""

  def body(self) -> Dict[str, Any]:
    return {}


class ACMEMultiCapDriver(Driver):
  """Driver for the ACME MultiCap.

  Owns HTTP transport and runtime discovery of attached modules. Per-Capability
  protocol encoding lives in ACMEMultiCap<Capability>Backend classes; door helper
  lives in ACMEDoorBackend. Same-named methods on driver and Capability are an
  anti-pattern (P-01).
  """

  def __init__(self, host: str, port: int = 80):
    super().__init__()
    self.host = host
    self.port = port
    # TODO: connection-state attributes (e.g., aiohttp.ClientSession or httpx.AsyncClient).
    self._session: Optional[Any] = None
    self._modules: Dict[str, Any] = {}

  async def setup(self, backend_params: Optional[BackendParams] = None) -> None:
    # TODO: open the HTTP session against http://<host>:<port>.
    # Discovery (P-18): query /info to learn which modules are installed so backends
    # can be wired with knowledge of which Capabilities the unit supports.
    # TODO: GET /info → populate self._modules
    pass

  async def stop(self) -> None:
    # TODO: close the HTTP session. Best-effort cleanup.
    pass

  async def send_command(self, command: ACMEMultiCapCommand) -> Dict[str, Any]:
    """Generic transport — sends a command object as an HTTP request and returns parsed JSON.

    Backends build ACMEMultiCapCommand subclasses with the wire payload; this method
    does not know about domain operations (P-01). One generic transport on the driver,
    per-operation encoding on the backend.
    """
    # TODO: send command.verb / command.path / command.body() via self._session
    # and return parsed JSON.
    raise NotImplementedError
