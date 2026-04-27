# Anti-pattern fixture A-08: Workflow method on the driver (sequences multiple vendor calls)
# Violates: P-20 (workflow methods sequencing vendor calls belong on the backend)
# Expected pattern_id when skill runs: P-20
# Expected principle: P6 — Driver is the wire, backend is the protocol
#
# What's planted: ACMEFlexDriver.drop_tip_in_trash() sequences TWO vendor API calls
# (moveToAddressableArea + dropTipInPlace) plus a decision based on resource type
# (alternateDropLocation=True for trash). This is workflow sequencing carrying domain
# meaning — exactly the work that belongs in the backend's drop_tips method per P-20.
# The driver should expose 1:1 wrappers around individual vendor endpoints, not
# multi-step orchestrations.

from typing import Any, Dict, Optional

from pylabrobot.device import Driver


class ACMEFlexDriver(Driver):
    """Driver for the ACME Flex robot."""

    def __init__(self, host: str):
        super().__init__()
        self.host = host

    async def setup(self):
        pass

    async def stop(self):
        pass

    async def execute_command(self, command_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generic transport — send a command, get a response. Public surface, OK."""
        return {}

    # CORRECT private wire methods (1:1 with vendor endpoints): these are fine.
    async def _move_to_addressable_area(self, pipette_id: str, area_name: str) -> Dict[str, Any]:
        """Single endpoint wrapper. 1:1 with vendor API. OK on driver."""
        return await self.execute_command(
            "moveToAddressableAreaForDropTip",
            {"pipetteId": pipette_id, "addressableAreaName": area_name},
        )

    async def _drop_tip_in_place(
        self, pipette_id: str, alternate_drop_location: bool = False
    ) -> Dict[str, Any]:
        """Single endpoint wrapper. 1:1 with vendor API. OK on driver."""
        return await self.execute_command(
            "dropTipInPlace",
            {"pipetteId": pipette_id, "alternateDropLocation": alternate_drop_location},
        )

    # ANTI-PATTERN: multi-step workflow with domain decision (alternateDropLocation=True
    # is determined by the resource type — trash vs rack — which is domain knowledge).
    # This sequencing belongs on the backend (FlexHead8Backend.drop_tips), not the driver.
    async def drop_tip_in_trash(self, pipette_id: str, trash_area_name: str) -> Dict[str, Any]:
        """Drop tip in the trash chute.

        ANTI-PATTERN: this method sequences two vendor calls AND encodes the
        alternate_drop_location=True decision. Both belong on the backend.
        """
        await self._move_to_addressable_area(pipette_id, trash_area_name)
        return await self._drop_tip_in_place(pipette_id, alternate_drop_location=True)

    # ANTI-PATTERN: parses domain meaning out of the response. Tip-detection state
    # is a backend concern; the driver should return raw API data and let the
    # backend extract domain meaning.
    async def request_tip_presence(self, pipette_id: str) -> bool:
        """Returns whether a tip is on the pipette.

        ANTI-PATTERN: this method calls /instruments and parses state.tipDetected
        out of the response. Move to FlexHead8Backend.request_tip_presence
        (matches the PIPBackend ABC pattern).
        """
        instruments = await self.execute_command("GET /instruments", {})
        for inst in instruments.get("data", []):
            if inst.get("instrumentId") == pipette_id:
                return bool(inst.get("state", {}).get("tipDetected", False))
        return False


# CORRECT form: workflow + state parsing on the backend.
#
# class ACMEFlexHead8Backend(Head8Backend):
#     def __init__(self, driver: ACMEFlexDriver):
#         self._driver = driver
#
#     async def drop_tips8(self, ops: List[TipDrop], use_channels: List[int]):
#         # Backend decides whether the resource is a trash and sequences accordingly.
#         is_trash = any(isinstance(op.resource, Trash) for op in ops)
#         if is_trash:
#             trash_area = self._resolve_trash_area(ops[0].resource)
#             await self._driver._move_to_addressable_area(self._pipette_id, trash_area)
#             await self._driver._drop_tip_in_place(self._pipette_id, alternate_drop_location=True)
#         else:
#             # ... rack drop path
#             pass
