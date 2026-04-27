# Smoke fixture S-02: Hamilton Nimbus
# Source: pylabrobot v1b1 commit d3c6d0a5, pylabrobot/hamilton/liquid_handlers/nimbus/
# Vendored: 2026-04-25 (verbatim copy of all .py files in the package; no edits)
# Expected skill outcome: 0 findings — compliant with v1b1 patterns
# Patterns this fixture exercises:
#   P-06 four-layer architecture
#   P-12 complex multi-file split (driver / pip_backend / door / commands / chatterbox / nimbus)
#   P-16 device-specific helper subsystems (NimbusDoor — plain helper class with lifecycle)
#   P-18 runtime configuration discovery (NimbusDriver.setup introspects pipette/door addresses)
#   P-04 chatterbox-extends-Driver discovery exception (NimbusChatterboxDriver)
#   P-21 driver-internal protocol via command classes (commands.py)
#   P-25 lifecycle hook scope (driver opens connection; backend _on_setup runs SmartRoll init)

from .chatterbox import NimbusChatterboxDriver
from .door import NimbusDoor
from .driver import NimbusDriver
from .nimbus import Nimbus
from .pip_backend import NimbusPIPBackend
