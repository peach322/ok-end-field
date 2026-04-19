import sys
import types
import unittest
from unittest.mock import patch

if "pyautogui" not in sys.modules:
    pyautogui_stub = types.ModuleType("pyautogui")
    pyautogui_stub.mouseDown = lambda: None
    pyautogui_stub.mouseUp = lambda: None
    sys.modules["pyautogui"] = pyautogui_stub

from src.tasks.AutoCombatLogic import AutoCombatLogic


class _DummyTask:
    def __init__(self, exit_on_check=True):
        self.config = {
            "技能释放": "123",
            "启动技能点数": 2,
            "进入战斗后的初始等待时间": 3,
            "后台结束战斗通知": False,
        }
        self.debug = False
        self._exit_on_check = exit_on_check
        self._last_no_combat_log_time = 0

    def in_combat(self, required_yellow=None):
        return True

    def log_info(self, *args, **kwargs):
        pass

    def sleep(self, *args, **kwargs):
        pass

    def _parse_skill_sequence(self, *_args, **_kwargs):
        return ["1", "2", "3"]

    def active_and_send_mouse_delta(self, *args, **kwargs):
        pass

    def click(self, *args, **kwargs):
        pass

    def _check_single_exit_condition(self):
        return self._exit_on_check

    def in_bg(self):
        return False


class TestAutoCombatLogic(unittest.TestCase):
    def test_no_battle_does_not_trigger_mouse_down(self):
        task = _DummyTask(exit_on_check=True)
        events = []
        with patch("src.tasks.AutoCombatLogic.pyautogui.mouseDown", side_effect=lambda: events.append("down")), \
                patch("src.tasks.AutoCombatLogic.pyautogui.mouseUp", side_effect=lambda: events.append("up")):
            AutoCombatLogic(task).run(no_battle=True)
        self.assertNotIn("down", events)

    def test_mouse_down_is_not_delayed_by_start_sleep(self):
        task = _DummyTask(exit_on_check=True)
        events = []

        def fake_sleep(seconds):
            events.append(f"sleep:{seconds}")

        with patch("src.tasks.AutoCombatLogic.pyautogui.mouseDown", side_effect=lambda: events.append("down")), \
                patch("src.tasks.AutoCombatLogic.pyautogui.mouseUp", side_effect=lambda: events.append("up")), \
                patch("src.tasks.AutoCombatLogic.time.sleep", side_effect=fake_sleep):
            AutoCombatLogic(task).run(start_sleep=5, no_battle=False)

        self.assertIn("down", events)
        self.assertIn("sleep:5", events)
        self.assertLess(events.index("down"), events.index("sleep:5"))


if __name__ == '__main__':
    unittest.main()
