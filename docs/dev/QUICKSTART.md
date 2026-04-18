# ok-ef 开发者快速开始

> 目标读者：希望为 ok-ef 贡献代码的开发者。

---

## 1. 从源码运行项目

### 1.1 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows |
| Python | **3.12**（仅支持此版本） |
| 运行权限 | **管理员权限**（必须；需以管理员身份启动 CMD / PyCharm / VSCode） |
| 安装路径 | 纯英文路径（例如 `D:\dev\ok-end-field`），不要含中文或空格 |

### 1.2 克隆仓库

```bash
git clone --recurse-submodules https://github.com/AliceJump/ok-end-field.git
cd ok-end-field
```

> 项目包含子模块，务必加上 `--recurse-submodules`。

### 1.3 安装依赖

```bash
pip install -r requirements.txt --upgrade
```

### 1.4 启动程序

```bash
# Release 模式
python main.py

# Debug 模式（截图/日志更详细，推荐开发时使用）
python main_debug.py
```

程序启动后会打开 GUI 窗口，左侧列出所有可用任务。

---

## 2. 新建一个触发式任务

触发式任务（`TriggerTask`）在后台持续运行，满足条件时自动激活。以下示例新增一个最小化的触发式任务。

### 2.1 创建任务文件

在 `src/tasks/` 下新建文件，例如 `MyTriggerTask.py`：

```python
from ok import TriggerTask
from src.tasks.BaseEfTask import BaseEfTask

class MyTriggerTask(BaseEfTask, TriggerTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "我的触发任务"
        self.description = "在此描述任务功能"

    def run(self):
        # 在此编写触发后执行的逻辑
        self.log_info("触发任务已执行")
```

> **提示**：若任务需要战斗能力，可额外继承 `BattleMixin`；需要地图导航则继承 `MapMixin`。
> 日志建议统一使用 `self.log_info/self.log_debug/self.log_error`，避免在运行时代码中使用 `print`。

### 2.2 注册任务

打开 `src/config.py`，将新任务加入 `trigger_tasks` 列表：

```python
config = {
    ...
    "trigger_tasks": [
        ...,
        ["src.tasks.MyTriggerTask", "MyTriggerTask"],  # 新增
    ],
    ...
}
```

### 2.3 运行与验证

重新启动程序（`python main_debug.py`），在 GUI 右侧的触发任务列表中即可看到并启用新任务。

---

## 3. 新建一次性任务（可选）

一次性任务（`BaseTask` 子类）由用户点击触发，执行完毕后自动停止。流程与触发式任务相同，区别在于：

- 继承 `BaseTask`（而非 `TriggerTask`）
- 注册到 `config["onetime_tasks"]` 列表

---

## 4. 最小 OCR 示例

游戏界面中绝大多数交互都通过"识别屏幕文字 → 点击"来完成。框架提供了四个核心函数：

| 函数 | 作用 |
|------|------|
| `ocr(match, box)` | **单次**扫描指定区域，立即返回匹配结果列表（不等待） |
| `wait_ocr(match, box, time_out)` | **持续扫描**直到找到匹配文字或超时，返回结果列表或 `None` |
| `click(target, after_sleep)` | 点击一个坐标或 OCR/Feature 返回的 `Box` 对象 |
| `wait_click_ocr(match, box, time_out, alt)` | 等待 OCR 找到匹配后**自动点击**，是 `wait_ocr` + `click` 的组合 |

### 4.1 `ocr` — 单次扫描

```python
import re

# 字符串精确匹配：在屏幕左侧区域查找"舰桥"文字
result = self.ocr(match="舰桥", box=self.box.left)
if result:
    self.log_info("找到舰桥提示")

# 正则匹配：扫描全屏查找武器补给文字
boxes = self.ocr(match=re.compile("武器补给"), box=self.box.top_right)
if len(boxes) > 0:
    self.log_info("发现武器补给")
```

> `ocr` 不等待，适合在循环中轮询或判断当前画面状态。

### 4.2 `wait_ocr` — 等待出现后返回

```python
# 等待"信赖"弹窗最多 5 秒
if self.wait_ocr(match=re.compile("信赖"), box=self.box.left, time_out=5):
    self.log_info("信赖弹窗已出现")

# 读取数字：等待区域内出现纯数字文本，并解析为整数
num_str = self.wait_ocr(
    match=re.compile(r"\d+"),
    box=self.box_of_screen(1224/1920, 235/1080, 1551/1920, 356/1080),
    time_out=5,
)
num = int(num_str[0].name) if num_str else 0
```

> `wait_ocr` 返回 `List[Box]`（每个 `Box.name` 为识别到的文字），超时返回 `None`。

### 4.3 `click` — 点击坐标或 Box

```python
# 点击 OCR 返回的第一个结果，操作后等待 1 秒
result = self.wait_ocr(match="确认", box=self.box.bottom, time_out=5)
if result:
    self.click(result[0], after_sleep=1)

# 点击相对坐标（0.0~1.0 为屏幕比例），操作后等待 2 秒
self.click(3530/3840, 80/2160, after_sleep=2)

# 点击后把鼠标移回原位（适合后台运行时不干扰用户鼠标）
self.click(result[0], move_back=True, after_sleep=0.5)
```

### 4.4 `wait_click_ocr` — 等待并自动点击

```python
# 最简用法：等待"确认"按钮出现后点击
self.wait_click_ocr(match="确认", box=self.box.bottom, time_out=5)

# 正则匹配 + 操作后等 2 秒
self.wait_click_ocr(match=re.compile("信用交易所"), box=self.box.top, time_out=5, after_sleep=2)

# 多关键词（任意匹配其一即点击）
result = self.wait_click_ocr(
    match=[re.compile("收取信用"), re.compile("无待领取信用")],
    box=self.box.bottom_left,
    time_out=7,
    recheck_time=1,  # 找到后再等 1 秒二次确认，避免误点动画帧
)
if result and "收取信用" in result[0].name:
    self.wait_pop_up()
```

### 4.5 `alt=True` — 为什么要按住 Alt 再点击

游戏中部分按钮（例如副本的**激发**、**领取奖励**、**放弃**）在被鼠标悬停时会触发 tooltip，  
直接发送点击消息时游戏有时会把 tooltip 状态的按钮识别为不可交互。  
`alt=True` 会让框架在点击前先按住 `Alt` 键、点击后再松开，  
模拟人工操作习惯，绕过 tooltip 拦截，使点击被游戏正确响应。

```python
# 等待"放弃"按钮后以 Alt+点击 方式触发
self.wait_click_ocr(
    match=re.compile("放弃"),
    box=self.box.bottom_right,
    time_out=5,
    recheck_time=1,
    alt=True,
)

# 等待"激发"并 Alt+点击，失败则记录日志
if not self.wait_click_ocr(
    match=re.compile("激发"),
    box=self.box.bottom_right,
    time_out=5,
    recheck_time=1,
    alt=True,
):
    self.log_info("没有找到『激发』按钮")
    return False
```

> **经验法则**：按钮被遮挡、带有动画或悬停 tooltip 时优先尝试 `alt=True`；普通 UI 按钮无需加。

---

## 后续阅读

| 文档 | 说明 |
|------|------|
| [DEVELOPMENT.md](DEVELOPMENT.md) | 完整架构、目录结构、CI/CD |
| [API.md](API.md) | BaseEfTask、Mixin、ScreenPosition 等详细 API |
