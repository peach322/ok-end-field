# find_feature 操作示例

> 本文演示 `find_feature` 系列函数的用法。
> 每个示例都是**可直接放入 `src/tasks/` 并注册运行**的完整任务文件，
> 风格与 `src/tasks/Test.py` 保持一致。

---

## 函数速览

| 函数 | 何时用 |
|------|--------|
| `find_feature(feature_name, box, threshold)` | 对当前帧做一次模板匹配；找到时返回 `List[Box]`，未找到时返回空列表 |
| `find_one(feature_name, box, threshold)` | `find_feature` 的便捷封装，只返回第一个匹配结果（`Box` 或 `None`） |

`feature_name` 接受 `FeatureList` 枚举值、枚举值组成的列表，或直接使用字符串。
框架会根据当前分辨率自动选取 `_2k` / `_4k` 后缀变体（如有）。

---

## 示例一：检测单个图标并点击

> **场景**：等待关闭按钮（`×`）出现后点击。

```python
# src/tasks/ExampleFindFeature.py
from ok import BaseTask
from src.data.FeatureList import FeatureList as fL
from src.tasks.BaseEfTask import BaseEfTask


class ExampleFindFeature(BaseEfTask, BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "示例：find_feature 点击图标"
        self.description = "检测关闭按钮并点击"

    def run(self):
        # find_feature 返回 List[Box]，未找到时返回空列表
        result = self.find_feature(feature_name=fL.close)

        if not result:
            self.log_info("未找到关闭按钮")
            return

        # 取第一个匹配结果点击
        self.click(result[0], after_sleep=0.5)
        self.log_info("已点击关闭按钮")
```

---

## 示例二：限制搜索区域（`box` 参数）

> **场景**：只在右上角区域寻找 ESC 图标，避免在其他位置产生误匹配。

```python
# src/tasks/ExampleFindFeatureBox.py
from ok import BaseTask
from src.data.FeatureList import FeatureList as fL
from src.tasks.BaseEfTask import BaseEfTask


class ExampleFindFeatureBox(BaseEfTask, BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "示例：find_feature + box"
        self.description = "限制搜索区域的模板匹配"

    def run(self):
        # box_of_screen 的参数是 0.0~1.0 的相对比例
        # 这里只在右上角 20%×15% 的区域搜索
        top_right = self.box_of_screen(0.8, 0.0, 1.0, 0.15)

        result = self.find_feature(
            feature_name=fL.esc,
            box=top_right,
            threshold=0.8,   # 相似度阈值，越高越严格
        )

        if result:
            self.log_info(f"在右上角找到 ESC 图标，坐标：{result[0].x}, {result[0].y}")
            self.click(result[0])
        else:
            self.log_info("右上角未找到 ESC 图标")
```

---

## 示例三：检测多个候选图标之一

> **场景**：列表中可能出现两种不同图标（例如聊天图标的亮色/暗色版本），
> 任意找到一种即可点击。

```python
# src/tasks/ExampleFindFeatureMultiple.py
from ok import BaseTask
from src.data.FeatureList import FeatureList as fL
from src.tasks.BaseEfTask import BaseEfTask


class ExampleFindFeatureMultiple(BaseEfTask, BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "示例：find_feature 多候选图标"
        self.description = "在多个候选图标中找到任意一个并点击"

    def run(self):
        # 传入列表，框架会依次尝试每个 feature_name，返回所有命中结果
        result = self.find_feature(
            feature_name=[fL.chat_icon, fL.chat_icon_dark, fL.chat_icon_2],
            box=self.box.right,
            threshold=0.75,
        )

        if not result:
            self.log_info("未找到聊天图标")
            return

        # result 按相似度从高到低排列，取第一个（最佳匹配）点击
        self.log_info(f"找到图标：{result[0].name}，相似度：{result[0].confidence:.2f}")
        self.click(result[0], after_sleep=0.5)
```

---

## 示例四：轮询等待图标出现

> **场景**：某个图标需要等待数秒后才出现（如战斗结束后的奖励图标），
> `find_feature` 不会自动等待，需要用循环轮询。

```python
# src/tasks/ExampleFindFeatureWait.py
from ok import BaseTask
from src.data.FeatureList import FeatureList as fL
from src.tasks.BaseEfTask import BaseEfTask


class ExampleFindFeatureWait(BaseEfTask, BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "示例：find_feature 轮询等待"
        self.description = "等待图标出现后再执行操作"

    def run(self):
        # 最多等待 30 秒（60 次 × 0.5 秒）
        result = None
        for _ in range(60):
            result = self.find_feature(
                feature_name=fL.claim_gift,
                box=self.box.bottom_right,
                threshold=0.8,
            )
            if result:
                break
            self.next_frame()
            self.sleep(0.5)

        if not result:
            self.log_info("等待领取礼物图标超时，任务结束")
            return

        self.log_info("检测到领取礼物图标，执行点击")
        self.click(result[0], after_sleep=1)
```

---

## 注册与运行

将上述任意示例文件保存到 `src/tasks/` 后，在 `src/config.py` 中注册：

```python
config = {
    ...
    "onetime_tasks": [
        ...,
        ["src.tasks.ExampleFindFeature", "ExampleFindFeature"],
    ],
    ...
}
```

重启程序（`python main_debug.py`），在 GUI 任务列表中即可找到并运行。
