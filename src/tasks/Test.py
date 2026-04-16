import re

from src.tasks.mixin.login_mixin import LoginMixin
import pyautogui


class Test(LoginMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.refresh_count = 0
        self.refresh_cost_list = [80, 120, 160, 200]
        self.credit_good_search_box = None

    def run(self):
        self.wait_click_ocr(match=re.compile("立即刷新"), time_out=5, box=self.box.bottom_right, log=True)

    def _type_text(self, text: str):
        """
        通用输入（支持中文）
        """
        import pyperclip

        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
