# 5-method subset of the upstream xArm-Python-SDK XArmAPI class stub.
#
# Source: https://github.com/xArm-Developer/xArm-Python-SDK
# Pinned package version: xArm-Python-SDK 1.13.30
# Pinned commit hash: 0c6a8b21f3e1a4a5b9d2f7c8e6d4f3a2b1c0d9e8 (synthetic — represents a stable release tag)
# Pinned at: 2026-04-25
#
# Methods covered: motion_enable, set_gripper_position, set_mode, set_servo_angle, set_state.
# Trimmed from the full XArmAPI surface (~120 methods) to a representative 5-method subset
# spanning motion control (set_servo_angle), end-effector control (set_gripper_position),
# and lifecycle control (motion_enable / set_mode / set_state).
#
# This is a Python stub file (.pyi). Type annotations are authoritative; bodies are `...`.

from typing import List, Optional, Union


class XArmAPI:
    """Top-level vendor SDK class for the UFactory xArm series (xArm5/6/7, Lite6, UFactory 850)."""

    def motion_enable(
        self,
        enable: bool = True,
        servo_id: Optional[int] = None,
    ) -> int:
        """Enable or disable motion on one or all joints.

        Required before any motion command. Pairs with `set_mode` (sets control mode) and `set_state` (transitions ready state). Returns 0 on success; non-zero is a vendor SDK error code.
        """
        ...

    def set_gripper_position(
        self,
        pos: float,
        wait: bool = False,
        speed: Optional[float] = None,
        auto_enable: bool = False,
        timeout: Optional[float] = None,
    ) -> int:
        """Command the standard xArm gripper to a target opening position.

        Position units are millimeters; range depends on the attached gripper. When `wait=True`, blocks until the gripper reaches `pos` or `timeout` elapses. Returns 0 on success.
        """
        ...

    def set_mode(self, mode: int = 0) -> int:
        """Set the arm's control mode.

        0 = position mode (servo angle / Cartesian motion), 1 = servo mode (real-time joint streaming), 2 = joint teaching, 3 = Cartesian teaching, 4 = simulation, 5 = velocity. Must be issued before `set_state(0)`. Returns 0 on success.
        """
        ...

    def set_servo_angle(
        self,
        servo_id: Optional[int] = None,
        angle: Union[float, List[float], None] = None,
        speed: Optional[float] = None,
        mvacc: Optional[float] = None,
        relative: bool = False,
        is_radian: Optional[bool] = None,
        wait: bool = False,
        timeout: Optional[float] = None,
    ) -> int:
        """Move one or more joints to the target angle.

        When `servo_id` is None, `angle` is interpreted as a per-joint list. When `wait=True`, blocks until motion completes or `timeout` elapses; otherwise returns as soon as the motion is queued. Returns 0 on success; non-zero is a vendor SDK error code.
        """
        ...

    def set_state(self, state: int = 0) -> int:
        """Transition the arm's ready state.

        0 = ready (motion permitted), 3 = paused, 4 = stopped. Always issue after `set_mode` to arm the controller. Returns 0 on success.
        """
        ...
