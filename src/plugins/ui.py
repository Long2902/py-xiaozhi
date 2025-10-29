from typing import Any, Optional

from src.constants.constants import AbortReason, DeviceState
from src.plugins.base import Plugin


class UIPlugin(Plugin):
    """Plugin UI - quản lý hiển thị CLI/GUI."""

    name = "ui"

    # Bản đồ văn bản cho trạng thái thiết bị
    STATE_TEXT_MAP = {
        DeviceState.IDLE: "Sẵn sàng",
        DeviceState.LISTENING: "Đang lắng nghe...",
        DeviceState.SPEAKING: "Đang nói...",
    }

    def __init__(self, mode: Optional[str] = None) -> None:
        super().__init__()
        self.app = None
        self.mode = (mode or "cli").lower()
        self.display = None
        self._is_gui = False
        self.is_first = True

    async def setup(self, app: Any) -> None:
        """Khởi tạo plugin UI."""
        self.app = app

        # Tạo thể hiện display tương ứng
        self.display = self._create_display()

        # Vô hiệu hóa nhập liệu trong bảng điều khiển nội bộ của ứng dụng
        if hasattr(app, "use_console_input"):
            app.use_console_input = False

    def _create_display(self):
        """Tạo thể hiện display theo chế độ."""
        if self.mode == "gui":
            from src.display.gui_display import GuiDisplay

            self._is_gui = True
            return GuiDisplay()
        else:
            from src.display.cli_display import CliDisplay

            self._is_gui = False
            return CliDisplay()

    async def start(self) -> None:
        """Khởi động hiển thị UI."""
        if not self.display:
            return

        # Gắn các hàm gọi lại
        await self._setup_callbacks()

        # Khởi động hiển thị
        self.app.spawn(self.display.start(), name=f"ui:{self.mode}:start")

    async def _setup_callbacks(self) -> None:
        """Thiết lập các hàm gọi lại cho display."""
        if self._is_gui:
            # GUI cần điều phối vào tác vụ bất đồng bộ
            callbacks = {
                "press_callback": self._wrap_callback(self._press),
                "release_callback": self._wrap_callback(self._release),
                "auto_callback": self._wrap_callback(self._auto_toggle),
                "abort_callback": self._wrap_callback(self._abort),
                "send_text_callback": self._send_text,
            }
        else:
            # CLI truyền trực tiếp coroutine
            callbacks = {
                "auto_callback": self._auto_toggle,
                "abort_callback": self._abort,
                "send_text_callback": self._send_text,
            }

        await self.display.set_callbacks(**callbacks)

    def _wrap_callback(self, coro_func):
        """Đóng gói coroutine thành lambda có thể được lập lịch."""
        return lambda: self.app.spawn(coro_func(), name="ui:callback")

    async def on_incoming_json(self, message: Any) -> None:
        """Xử lý thông điệp JSON đến."""
        if not self.display or not isinstance(message, dict):
            return

        msg_type = message.get("type")

        # Cả tts/stt đều cập nhật văn bản
        if msg_type in ("tts", "stt"):
            if text := message.get("text"):
                await self.display.update_text(text)

        # llm cập nhật biểu cảm
        elif msg_type == "llm":
            if emotion := message.get("emotion"):
                await self.display.update_emotion(emotion)

    async def on_device_state_changed(self, state: Any) -> None:
        """Xử lý thay đổi trạng thái thiết bị."""
        if not self.display:
            return

        # Bỏ qua lần gọi đầu tiên
        if self.is_first:
            self.is_first = False
            return

        # Cập nhật biểu cảm và trạng thái
        await self.display.update_emotion("neutral")
        if status_text := self.STATE_TEXT_MAP.get(state):
            await self.display.update_status(status_text, True)

    async def shutdown(self) -> None:
        """Dọn dẹp tài nguyên UI và đóng cửa sổ."""
        if self.display:
            await self.display.close()
            self.display = None

    # ===== Hàm gọi lại =====

    async def _send_text(self, text: str):
        """Gửi văn bản tới máy chủ."""
        if await self.app.connect_protocol():
            await self.app.protocol.send_wake_word_detected(text)

    async def _press(self):
        """Chế độ thủ công: nhấn để bắt đầu ghi âm."""
        await self.app.start_listening_manual()

    async def _release(self):
        """Chế độ thủ công: thả để dừng ghi âm."""
        await self.app.stop_listening_manual()

    async def _auto_toggle(self):
        """Chuyển đổi chế độ tự động."""
        await self.app.start_auto_conversation()

    async def _abort(self):
        """Ngắt đoạn hội thoại."""
        await self.app.abort_speaking(AbortReason.USER_INTERRUPTION)
