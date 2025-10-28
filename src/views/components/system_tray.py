"""
Mô-đun thành phần khay hệ thống cung cấp biểu tượng khay, menu và chỉ báo trạng thái.
"""

from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import QAction, QMenu, QSystemTrayIcon, QWidget

from src.utils.logging_config import get_logger


class SystemTray(QObject):
    """
    Thành phần khay hệ thống.
    """

    # Định nghĩa tín hiệu
    show_window_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.logger = get_logger("SystemTray")
        self.parent_widget = parent

        # Thành phần liên quan tới khay
        self.tray_icon = None
        self.tray_menu = None

        # Thông tin trạng thái
        self.current_status = ""
        self.is_connected = True

        # Khởi tạo khay
        self._setup_tray()

    def _setup_tray(self):
        """
        Thiết lập biểu tượng khay hệ thống.
        """
        try:
            # Kiểm tra hệ thống có hỗ trợ khay hay không
            if not QSystemTrayIcon.isSystemTrayAvailable():
                self.logger.warning("Hệ thống không hỗ trợ khay hệ thống")
                return

            # Tạo menu khay
            self._create_tray_menu()

            # Tạo biểu tượng khay (không gắn QWidget làm cha để tránh vòng đời cửa sổ ảnh hưởng tới biểu tượng)
            self.tray_icon = QSystemTrayIcon()
            self.tray_icon.setContextMenu(self.tray_menu)

            # Đặt biểu tượng tạm trước khi hiển thị để tránh cảnh báo QSystemTrayIcon::setVisible: No Icon set
            try:
                # Dùng chấm tròn màu làm biểu tượng ban đầu
                pixmap = QPixmap(16, 16)
                pixmap.fill(QColor(0, 0, 0, 0))
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setBrush(QBrush(QColor(0, 180, 0)))
                painter.setPen(QColor(0, 0, 0, 0))
                painter.drawEllipse(2, 2, 12, 12)
                painter.end()
                self.tray_icon.setIcon(QIcon(pixmap))
            except Exception:
                pass

            # Kết nối sự kiện của biểu tượng khay
            self.tray_icon.activated.connect(self._on_tray_activated)

            # Đặt trạng thái ban đầu (trì hoãn để tránh lỗi kết xuất lần đầu trên một số nền tảng)
            try:
                from PyQt5.QtCore import QTimer

                QTimer.singleShot(0, lambda: self.update_status("Sẵn sàng", connected=True))
            except Exception:
                self.update_status("Sẵn sàng", connected=True)

            # Hiển thị biểu tượng khay
            self.tray_icon.show()
            self.logger.info("Đã khởi tạo biểu tượng khay hệ thống")

        except Exception as e:
            self.logger.error(f"Không thể khởi tạo biểu tượng khay hệ thống: {e}", exc_info=True)

    def _create_tray_menu(self):
        """
        Tạo menu chuột phải của khay.
        """
        self.tray_menu = QMenu()

        # Thêm mục hiển thị cửa sổ chính
        show_action = QAction("Hiện cửa sổ chính", self.parent_widget)
        show_action.triggered.connect(self._on_show_window)
        self.tray_menu.addAction(show_action)

        # Thêm đường phân tách
        self.tray_menu.addSeparator()

        # Thêm mục cấu hình
        settings_action = QAction("Cấu hình tham số", self.parent_widget)
        settings_action.triggered.connect(self._on_settings)
        self.tray_menu.addAction(settings_action)

        # Thêm đường phân tách
        self.tray_menu.addSeparator()

        # Thêm mục thoát
        quit_action = QAction("Thoát ứng dụng", self.parent_widget)
        quit_action.triggered.connect(self._on_quit)
        self.tray_menu.addAction(quit_action)

    def _on_tray_activated(self, reason):
        """
        Xử lý sự kiện nhấn vào biểu tượng khay.
        """
        if reason == QSystemTrayIcon.Trigger:  # Nhấp chuột
            self.show_window_requested.emit()

    def _on_show_window(self):
        """
        Xử lý khi chọn hiển thị cửa sổ chính.
        """
        self.show_window_requested.emit()

    def _on_settings(self):
        """
        Xử lý khi chọn mục cấu hình.
        """
        self.settings_requested.emit()

    def _on_quit(self):
        """
        Xử lý khi chọn thoát ứng dụng.
        """
        self.quit_requested.emit()

    def update_status(self, status: str, connected: bool = True):
        """Cập nhật trạng thái biểu tượng khay.

        Args:
            status: văn bản trạng thái
            connected: tình trạng kết nối
        """
        if not self.tray_icon:
            return

        self.current_status = status
        self.is_connected = connected

        try:
            icon_color = self._get_status_color(status, connected)

            # Tạo biểu tượng với màu tương ứng
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(0, 0, 0, 0))  # Nền trong suốt

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(icon_color))
            painter.setPen(QColor(0, 0, 0, 0))  # Viền trong suốt
            painter.drawEllipse(2, 2, 12, 12)
            painter.end()

            # Đặt biểu tượng
            self.tray_icon.setIcon(QIcon(pixmap))

            # Đặt văn bản gợi ý
            tooltip = f"Trợ lý XiaoZhi AI - {status}"
            self.tray_icon.setToolTip(tooltip)

        except Exception as e:
            self.logger.error(f"Không thể cập nhật biểu tượng khay hệ thống: {e}")

    def _get_status_color(self, status: str, connected: bool) -> QColor:
        """Trả về màu sắc tương ứng với trạng thái.

        Args:
            status: văn bản trạng thái
            connected: tình trạng kết nối

        Returns:
            QColor: Màu tương ứng
        """
        if not connected:
            return QColor(128, 128, 128)  # Xám - chưa kết nối

        if "Lỗi" in status:
            return QColor(255, 0, 0)  # Đỏ - trạng thái lỗi
        elif "lắng nghe" in status:
            return QColor(255, 200, 0)  # Vàng - đang lắng nghe
        elif "Đang nói" in status:
            return QColor(0, 120, 255)  # Xanh dương - đang nói
        else:
            return QColor(0, 180, 0)  # Xanh lá - sẵn sàng/đã khởi động

    def show_message(
        self,
        title: str,
        message: str,
        icon_type=QSystemTrayIcon.Information,
        duration: int = 2000,
    ):
        """Hiển thị thông báo từ khay.

        Args:
            title: tiêu đề thông báo
            message: nội dung thông báo
            icon_type: loại biểu tượng
            duration: thời gian hiển thị (ms)
        """
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, icon_type, duration)

    def hide(self):
        """
        Ẩn biểu tượng khay.
        """
        if self.tray_icon:
            self.tray_icon.hide()

    def is_visible(self) -> bool:
        """
        Kiểm tra biểu tượng khay có hiển thị hay không.
        """
        return self.tray_icon and self.tray_icon.isVisible()

    def is_available(self) -> bool:
        """
        Kiểm tra khay hệ thống có khả dụng hay không.
        """
        return QSystemTrayIcon.isSystemTrayAvailable()
