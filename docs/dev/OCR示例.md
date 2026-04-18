# OCR 操作示例

> 本文演示四个核心屏幕识别/点击函数的用法。
> 每个示例都是**可直接放入 `src/tasks/` 并注册运行**的完整任务文件，
> 风格与 `src/tasks/Test.py` 保持一致。

---

## 函数速览

| 函数 | 何时用 |
|------|--------|
| `ocr(match, box)` | 立即扫描一次，不等待；适合循环轮询或判断当前画面 |
| `wait_ocr(match, box, time_out)` | 持续扫描直到出现匹配或超时；返回 `List[Box]`，超时返回 `None` |
| `click(target, after_sleep)` | 点击坐标或 `Box` 对象 |
| `wait_click_ocr(match, box, time_out)` | `wait_ocr` + `click` 的一步组合 |

`Box.name` 属性保存 OCR 识别到的文字内容，可用于二次判断。

---

## 示例一：用 `wait_click_ocr` 点击简单按钮

> **场景**：打开信用交易所，等待"立即刷新"按钮出现后点击。

```python
# src/tasks/ExampleClickOcr.py
import re

from ok import BaseTask
from src.tasks.BaseEfTask import BaseEfTask


class ExampleClickOcr(BaseEfTask, BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "示例：wait_click_ocr"
        self.description = "等待指定文字出现后自动点击"

    def run(self):
        # 等待顶部区域出现"信用交易所"并点击，最多等 5 秒
        self.wait_click_ocr(
            match=re.compile("信用交易所"),
            box=self.box.top,
            time_out=5,
        )

        # 等待左下角出现"收取信用"或"无待领取信用"其中之一并点击
        # recheck_time=1：找到后再等 1 秒做二次确认，避免误点过渡动画帧
        result = self.wait_click_ocr(
            match=[re.compile("收取信用"), re.compile("无待领取信用")],
            box=self.box.bottom_left,
            time_out=7,
            recheck_time=1,
        )

        if not result:
            self.log_info("未找到收取信用或无待领取信用")
            return

        # result 是 List[Box]，Box.name 是识别到的文字
        if "收取信用" in result[0].name:
            self.log_info("已点击收取信用，等待弹窗关闭")
            self.wait_pop_up()
        else:
            self.log_info("本次无待领取信用，跳过")
```

---

## 示例二：用 `wait_ocr` + 手动 `click` 拆分识别与点击

> **场景**：需要在点击前先记录识别结果或做额外判断时，手动拆分两步。

```python
# src/tasks/ExampleWaitOcrClick.py
import re

from ok import BaseTask
from src.tasks.BaseEfTask import BaseEfTask


class ExampleWaitOcrClick(BaseEfTask, BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "示例：wait_ocr + click"
        self.description = "先等待识别，再手动点击"

    def run(self):
        # 等待右侧出现"好友"按钮（最多 7 秒）
        result = self.wait_ocr(
            match=re.compile("好友"),
            box=self.box.right,
            time_out=7,
        )
        if not result:
            self.log_info("超时未找到好友按钮，任务结束")
            return

        # result 是 List[Box]，取第一个匹配项点击
        # after_sleep=1：点击后等待 1 秒，让页面完成跳转
        self.click(result[0], after_sleep=1)
        self.log_info(f"已点击：{result[0].name}")

        # 等待确认弹窗出现并点击，点击后将鼠标移回原位
        confirm = self.wait_ocr(match="确认", box=self.box.bottom, time_out=5)
        if confirm:
            self.click(confirm[0], move_back=True, after_sleep=0.5)
```

---

## 示例三：用 `ocr` 循环轮询（不阻塞等待）

> **场景**：需要在某个文字**消失**之前持续等待，`wait_ocr` 等待的是"出现"，
> 而等待"消失"只能用 `ocr` 自行轮询。

```python
# src/tasks/ExampleOcrPolling.py
import re

from ok import BaseTask
from src.tasks.BaseEfTask import BaseEfTask


class ExampleOcrPolling(BaseEfTask, BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "示例：ocr 轮询"
        self.description = "等待某文字消失，或用 ocr 读取当前状态"

    def run(self):
        # 等待"舰桥"提示文字从左侧区域消失（最多 60 秒）
        for _ in range(120):
            if not self.ocr(match="舰桥", box=self.box.left):
                self.log_info("舰桥提示已消失，继续执行")
                break
            self.next_frame()
            self.sleep(0.5)
        else:
            self.log_info("等待舰桥消失超时，任务中断")
            return

        # 单次扫描右上角，判断当前有没有武器补给提示
        if self.ocr(match=re.compile("武器补给"), box=self.box.top_right):
            self.log_info("检测到武器补给，跳过本次任务")
            return

        self.log_info("画面正常，继续后续操作")
```

---

## 示例四：`wait_ocr` 读取屏幕上的数字

> **场景**：等待指定区域出现数字文本并解析为整数（例如读取剩余票数）。

```python
# src/tasks/ExampleOcrReadNumber.py
import re

from ok import BaseTask
from src.tasks.BaseEfTask import BaseEfTask


class ExampleOcrReadNumber(BaseEfTask, BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "示例：wait_ocr 读数字"
        self.description = "识别屏幕上的数字并解析为整数"

    def run(self):
        # box_of_screen(x1, y1, x2, y2) 的参数是 0.0~1.0 的相对比例
        ticket_box = self.box_of_screen(
            1224 / 1920, 235 / 1080,
            1551 / 1920, 356 / 1080,
        )

        num_str = self.wait_ocr(
            match=re.compile(r"\d+"),
            box=ticket_box,
            time_out=5,
        )

        if not num_str:
            self.log_info("未识别到数字")
            return

        try:
            count = int(num_str[0].name)
        except ValueError:
            self.log_info(f"识别内容无法转为数字：{num_str[0].name}")
            return

        self.log_info(f"当前剩余票数：{count}")
```

---

## 示例五：`alt=True` — 绕过悬停 Tooltip 的点击

> **为什么需要 `alt=True`？**
>
> 框架使用 `PostMessage` 向游戏窗口发送鼠标消息，游戏窗口不需要在前台。
> 但部分按钮（如副本的**激发**、**领取奖励**、**放弃**）在鼠标悬停时会弹出
> tooltip 覆盖层，此时直接发送点击消息，游戏会将点击视为命中 tooltip 而非
> 按钮本身，导致点击**静默失败**。
>
> `alt=True` 会让框架在点击前先按住 `Alt` 键（通过 `send_key_down`），
> 发送点击后再松开（`send_key_up`）。`Alt` 键会使游戏关闭当前 tooltip，
> 从而让后续点击命中真正的按钮。
>
> **经验法则**：按钮带有悬停动画或 tooltip 时加 `alt=True`；普通 UI 按钮不需要。

```python
# src/tasks/ExampleAltClick.py
import re

from ok import BaseTask
from src.tasks.BaseEfTask import BaseEfTask


class ExampleAltClick(BaseEfTask, BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "示例：alt=True 点击"
        self.description = "演示需要按住 Alt 才能正确触发的按钮"

    def run(self):
        # 如果画面存在"放弃"按钮（说明有未领取的旧奖励），先放弃再继续
        if self.wait_ocr(match=re.compile("放弃"), box=self.box.bottom_right, time_out=5):
            self.log_info("发现放弃按钮，先放弃旧奖励")
            # recheck_time=1：点击前再等 1 秒重新确认，防止按钮因动画偏移
            self.wait_click_ocr(
                match=re.compile("放弃"),
                box=self.box.bottom_right,
                time_out=5,
                recheck_time=1,
                alt=True,          # 按住 Alt 再点击，绕过 tooltip
            )
            self.wait_click_ocr(
                match=re.compile("确认"),
                box=self.box.bottom_right,
                time_out=5,
            )

        # 等待"激发"按钮（带有悬停 tooltip），用 alt=True 确保点击生效
        self.sleep(1)
        if not self.wait_click_ocr(
            match=re.compile("激发"),
            box=self.box.bottom_right,
            time_out=5,
            recheck_time=1,
            alt=True,
        ):
            self.log_info("没有找到『激发』按钮，任务结束")
            return

        self.log_info("激发成功，进入战斗")
```

---

## 注册与运行

将上述任意示例文件保存到 `src/tasks/` 后，在 `src/config.py` 中注册：

```python
config = {
    ...
    "onetime_tasks": [
        ...,
        ["src.tasks.ExampleClickOcr", "ExampleClickOcr"],
    ],
    ...
}
```

重启程序（`python main_debug.py`），在 GUI 任务列表中即可找到并运行。
