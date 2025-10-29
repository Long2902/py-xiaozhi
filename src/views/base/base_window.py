# -*- coding: utf-8 -*-
"""
Lớp cửa sổ cơ sở - lớp cha của mọi cửa sổ PyQt
Hỗ trợ thao tác bất đồng bộ và tích hợp qasync.
"""

import asyncio
from typing import Optional

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QWidget

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class BaseWindow(QMainWindow):
    """
    Lớp cơ sở cho mọi cửa sổ, cung cấp hỗ trợ bất đồng bộ.
    """

    # Định nghĩa tín hiệu
    window_closed = pyqtSignal()
    status_updated = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = get_logger(self.__class__.__name__)

        # Quản lý tác vụ bất đồng bộ
        self._tasks = set()
        self._shutdown_event = asyncio.Event()

        # Bộ hẹn giờ dùng để cập nhật giao diện định kỳ (kết hợp với tác vụ bất đồng bộ)
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._on_timer_update)

        # Khởi tạo giao diện
        self._setup_ui()
        self._setup_connections()
        self._setup_styles()

        self.logger.debug(f"{self.__class__.__name__} đã khởi tạo xong")

    def _setup_ui(self):
        """Thiết lập giao diện - ghi đè ở lớp con"""

    def _setup_connections(self):
        """Thiết lập kết nối tín hiệu - ghi đè ở lớp con"""

    def _setup_styles(self):
        """Thiết lập kiểu dáng - ghi đè ở lớp con"""

    def _on_timer_update(self):
        """Hàm gọi lại của bộ hẹn giờ - ghi đè ở lớp con"""

    def start_update_timer(self, interval_ms: int = 1000):
        """
        Bắt đầu cập nhật định kỳ.
        """
        self._update_timer.start(interval_ms)
        self.logger.debug(f"Bắt đầu cập nhật định kỳ, chu kỳ: {interval_ms}ms")

    def stop_update_timer(self):
        """
        Dừng cập nhật định kỳ.
        """
        self._update_timer.stop()
        self.logger.debug("Dừng cập nhật định kỳ")

    def create_task(self, coro, name: str = None):
        """
        Tạo và quản lý tác vụ bất đồng bộ.
        """
        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)

        def done_callback(t):
            self._tasks.discard(t)
            if not t.cancelled() and t.exception():
                self.logger.error(f"Tác vụ bất đồng bộ gặp lỗi: {t.exception()}", exc_info=True)

        task.add_done_callback(done_callback)
        return task

    async def shutdown_async(self):
        """
        Đóng cửa sổ theo cách bất đồng bộ.
        """
        self.logger.info("Bắt đầu đóng cửa sổ bất đồng bộ")

        # Đặt cờ yêu cầu đóng
        self._shutdown_event.set()

        # Dừng bộ hẹn giờ
        self.stop_update_timer()

        # Hủy tất cả tác vụ
        for task in self._tasks.copy():
            if not task.done():
                task.cancel()

        # Chờ các tác vụ hoàn tất
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self.logger.info("Đã đóng cửa sổ bất đồng bộ xong")

    def closeEvent(self, event):
        """
        Sự kiện đóng cửa sổ.
        """
        self.logger.info("Sự kiện đóng cửa sổ được kích hoạt")

        # Đặt cờ yêu cầu đóng
        self._shutdown_event.set()

        # Nếu là cửa sổ kích hoạt, hủy quy trình kích hoạt
        if hasattr(self, "device_activator") and self.device_activator:
            self.device_activator.cancel_activation()
            self.logger.info("Đã gửi tín hiệu hủy kích hoạt")

        # Phát tín hiệu đóng
        self.window_closed.emit()

        # Dừng bộ hẹn giờ
        self.stop_update_timer()

        # Hủy mọi tác vụ (cách đồng bộ)
        for task in self._tasks.copy():
            if not task.done():
                task.cancel()

        # Chấp nhận sự kiện đóng
        event.accept()

        self.logger.info("Hoàn tất xử lý đóng cửa sổ")

    def update_status(self, message: str):
        """
        Cập nhật thông báo trạng thái.
        """
        self.status_updated.emit(message)
        self.logger.debug(f"Cập nhật trạng thái: {message}")

    def is_shutdown_requested(self) -> bool:
        """
        Kiểm tra đã yêu cầu đóng hay chưa.
        """
        return self._shutdown_event.is_set()
