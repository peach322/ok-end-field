import re
from src.data.delivery_area_service import extract_delivery_location, get_delivery_locations, get_ocr_priority_locations
from src.tasks.BaseEfTask import BaseEfTask


class MapMixin(BaseEfTask):
    def _try_recover_delivery_location_on_map(self):
        """地图已打开时，尝试通过右上角地点文字回填送货地点缓存。"""
        if not hasattr(self, "_accepted_delivery_location"):
            return
        if getattr(self, "_accepted_delivery_location", None):
            return
        area_name = getattr(self, "delivery_area", None)
        if not area_name:
            return
        try:
            ocr_locations = get_ocr_priority_locations(area_name) or get_delivery_locations(area_name)
        except Exception:
            return
        if not ocr_locations:
            return

        ocr_results = self.wait_ocr(
            match=ocr_locations,
            box=self.box.top_right,
            time_out=3,
            raise_if_not_found=False,
            log=True,
        )
        if not ocr_results:
            return

        recovered_location = None
        for location_name in ocr_locations:
            if any(location_name in item.name for item in ocr_results):
                recovered_location = location_name
                break
        if recovered_location is None:
            for item in ocr_results:
                recovered_location = extract_delivery_location(item.name, area_name)
                if recovered_location:
                    break

        if recovered_location:
            setattr(self, "_accepted_delivery_location", recovered_location)
            self.log_info(f"已从地图右上角地点文字回填委托地点: {recovered_location}")

    def task_to_transfer_point(self, test_target_box=None):
        """
        传送到运输委托对应的出发传送点。

        流程：
        1. 确保当前在主界面。
        2. 按 J 打开任务界面。
        3. 点击“任务定位到地图”的按钮。
        4. 等待地图稳定。
        5. 在地图上寻找附近传送点并执行传送。

        Args:
            test_target_box (Box, optional):
                查找传送点的屏幕区域。
                如果为 None，则默认使用 self.box.top 区域。

        Returns:
            bool:
                True  - 成功执行传送
                False - 任一步骤失败
        """

        # 如果没有指定搜索区域，则默认使用屏幕上半区域
        if test_target_box is None:
            test_target_box = self.box.top

        # 确保当前处于主界面
        self.ensure_main()

        # 打开任务界面
        self.press_key("j", after_sleep=2)

        # 查找“任务定位到地图”按钮
        result = self.find_feature(
            feature_name="one_task_to_map",
            threshold=0.8,
            box=self.box.bottom_right
        )

        # 如果没有找到按钮，则流程失败
        if not result:
            return False

        # 点击按钮跳转到地图
        self.click(result, after_sleep=2)

        # 等待 UI 稳定（地图加载完成）
        self.wait_ui_stable(refresh_interval=1)

        self._try_recover_delivery_location_on_map()
        if hasattr(self, "_get_transfer_search_box_by_location"):
            location_name = getattr(self, "_accepted_delivery_location", None)
            if location_name:
                resolved_box = self._get_transfer_search_box_by_location(location_name)
                if resolved_box:
                    test_target_box = resolved_box

        # 执行附近传送点传送
        return self.to_near_transfer_point(test_target_box)
    def clear_icon_in_map(self, need_reserve_icon_name=None):
        # 打开“标记显示管理”
        if not self.wait_click_ocr(
            match="标记显示管理", box=self.box.bottom_left, time_out=10, log=True, after_sleep=2
        ):
            return False

        # 点击“清空选中”，避免地图筛选导致传送点不显示
        if not self.wait_click_ocr(match="清空选中", box=self.box.bottom_left, time_out=10, log=True, after_sleep=0.5):
            return False
        for _ in range(2):
            # 如果需要保留特定图标，则点击保留图标
            if need_reserve_icon_name:
                if not self.wait_click_ocr(match=re.compile(need_reserve_icon_name), box=self.box.bottom_left, time_out=2, log=True, after_sleep=2):
                    self.scroll_relative(0.1, 0.5, -1)
                else:
                    break
        # 退出标记管理界面
        self.back(after_sleep=2)
    def to_near_transfer_point(self, test_target_box):
        """
        在地图上寻找最近的传送点并执行传送。

        流程：
        1. 打开“标记显示管理”。
        2. 清空当前地图选中标记。
        3. 关闭设置界面。
        4. 在地图上搜索传送点图标。
        5. 若未找到，则滚动地图继续查找。
        6. 找到传送点后点击。
        7. 点击“传送”按钮完成传送。

        Args:
            test_target_box (Box):
                搜索传送点的地图区域。

        Returns:
            bool:
                True  - 成功执行传送
                False - 未找到传送点或传送失败
        """
        self.clear_icon_in_map()
        result = None

        # 最多尝试 8 次寻找传送点
        for _ in range(16):

            # 查找传送点图标
            result = self.find_feature(
                feature_name="transfer_point",
                box=test_target_box,
                threshold=0.8
            )

            # 找到则跳出循环
            if result:
                break

            # 刷新一帧（防止识别缓存）
            self.next_frame()

            # 向下滚动地图继续查找
            self.scroll_relative(0.5, 0.5, -2)
            self.sleep(0.5)

        # 如果最终仍然没有找到传送点
        if not result:
            return False

        # 点击传送点
        self.click(result, after_sleep=2)

        # 查找“传送”按钮
        result = self.wait_ocr(
            match="传送",
            box=self.box.bottom_right,
            time_out=10,
            log=True
        )

        # 如果未找到传送按钮
        if not result:
            return False

        # 点击传送按钮
        self.click(result, after_sleep=2)

        return True
