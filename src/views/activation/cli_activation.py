# -*- coding: utf-8 -*-
"""
Quy trình kích hoạt thiết bị ở chế độ CLI cung cấp cùng chức năng với cửa sổ GUI nhưng hiển thị hoàn toàn trên dòng lệnh.
"""

from datetime import datetime
from typing import Optional

from src.core.system_initializer import SystemInitializer
from src.utils.device_activator import DeviceActivator
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CLIActivation:
    """
    Trình xử lý kích hoạt thiết bị ở chế độ CLI.
    """

    def __init__(self, system_initializer: Optional[SystemInitializer] = None):
        # Tham chiếu thành phần
        self.system_initializer = system_initializer
        self.device_activator: Optional[DeviceActivator] = None

        # Quản lý trạng thái
        self.current_stage = None
        self.activation_data = None
        self.is_activated = False

        self.logger = logger

    async def run_activation_process(self) -> bool:
        """Chạy toàn bộ quy trình kích hoạt CLI.

        Returns:
            bool: Kích hoạt có thành công hay không
        """
        try:
            self._print_header()

            # Nếu đã có sẵn SystemInitializer thì sử dụng trực tiếp
            if self.system_initializer:
                self._log_and_print("Sử dụng hệ thống đã được khởi tạo")
                self._update_device_info()
                return await self._start_activation_process()
            else:
                # Ngược lại tạo phiên bản mới và chạy khởi tạo
                self._log_and_print("Bắt đầu quy trình khởi tạo hệ thống")
                self.system_initializer = SystemInitializer()

                # Thực thi quy trình khởi tạo
                init_result = await self.system_initializer.run_initialization()

                if init_result.get("success", False):
                    self._update_device_info()

                    # Hiển thị thông báo trạng thái
                    status_message = init_result.get("status_message", "")
                    if status_message:
                        self._log_and_print(status_message)

                    # Kiểm tra có cần kích hoạt hay không
                    if init_result.get("need_activation_ui", True):
                        return await self._start_activation_process()
                    else:
                        # Không cần kích hoạt, kết thúc ngay
                        self.is_activated = True
                        self._log_and_print("Thiết bị đã được kích hoạt, không cần thao tác thêm")
                        return True
                else:
                    error_msg = init_result.get("error", "Khởi tạo thất bại")
                    self._log_and_print(f"Lỗi: {error_msg}")
                    return False

        except KeyboardInterrupt:
            self._log_and_print("\nNgười dùng đã hủy quy trình kích hoạt")
            return False
        except Exception as e:
            self.logger.error(f"Quy trình kích hoạt CLI gặp lỗi: {e}", exc_info=True)
            self._log_and_print(f"Lỗi kích hoạt: {e}")
            return False

    def _print_header(self):
        """
        In thông tin phần đầu của quy trình kích hoạt CLI.
        """
        print("\n" + "=" * 60)
        print("Khách hàng XiaoZhi AI - Quy trình kích hoạt thiết bị")
        print("=" * 60)
        print("Đang khởi tạo thiết bị, vui lòng chờ...")
        print()

    def _update_device_info(self):
        """
        Cập nhật hiển thị thông tin thiết bị.
        """
        if (
            not self.system_initializer
            or not self.system_initializer.device_fingerprint
        ):
            return

        device_fp = self.system_initializer.device_fingerprint

        # Lấy thông tin thiết bị
        serial_number = device_fp.get_serial_number()
        mac_address = device_fp.get_mac_address_from_efuse()

        # Lấy trạng thái kích hoạt
        activation_status = self.system_initializer.get_activation_status()
        local_activated = activation_status.get("local_activated", False)
        server_activated = activation_status.get("server_activated", False)
        status_consistent = activation_status.get("status_consistent", True)

        # Cập nhật trạng thái kích hoạt
        self.is_activated = local_activated

        # Hiển thị thông tin thiết bị
        print("📱 Thông tin thiết bị:")
        print(f"   Số sê-ri: {serial_number if serial_number else '--'}")
        print(f"   Địa chỉ MAC: {mac_address if mac_address else '--'}")

        # Hiển thị trạng thái kích hoạt
        if not status_consistent:
            if local_activated and not server_activated:
                status_text = "Trạng thái không khớp (cần kích hoạt lại)"
            else:
                status_text = "Trạng thái không khớp (đã tự sửa)"
        else:
            status_text = "Đã kích hoạt" if local_activated else "Chưa kích hoạt"

        print(f"   Trạng thái kích hoạt: {status_text}")

    async def _start_activation_process(self) -> bool:
        """
        Bắt đầu quy trình kích hoạt.
        """
        try:
            # Lấy dữ liệu kích hoạt
            activation_data = self.system_initializer.get_activation_data()

            if not activation_data:
                self._log_and_print("\nKhông nhận được dữ liệu kích hoạt")
                print("Lỗi: Không nhận được dữ liệu kích hoạt, vui lòng kiểm tra kết nối mạng")
                return False

            self.activation_data = activation_data

            # Hiển thị thông tin kích hoạt
            self._show_activation_info(activation_data)

            # Khởi tạo bộ kích hoạt thiết bị
            config_manager = self.system_initializer.get_config_manager()
            self.device_activator = DeviceActivator(config_manager)

            # Bắt đầu quy trình kích hoạt
            self._log_and_print("\nBắt đầu quy trình kích hoạt thiết bị...")
            print("Đang kết nối tới máy chủ kích hoạt, vui lòng giữ kết nối mạng...")

            activation_success = await self.device_activator.process_activation(
                activation_data
            )

            if activation_success:
                self._log_and_print("\nKích hoạt thiết bị thành công!")
                self._print_activation_success()
                return True
            else:
                self._log_and_print("\nKích hoạt thiết bị thất bại")
                self._print_activation_failure()
                return False

        except Exception as e:
            self.logger.error(f"Quy trình kích hoạt gặp lỗi: {e}", exc_info=True)
            self._log_and_print(f"\nLỗi kích hoạt: {e}")
            return False

    def _show_activation_info(self, activation_data: dict):
        """
        Hiển thị thông tin kích hoạt.
        """
        code = activation_data.get("code", "------")
        message = activation_data.get("message", "Hãy truy cập xiaozhi.me để nhập mã xác minh")

        print("\n" + "=" * 60)
        print("Thông tin kích hoạt thiết bị")
        print("=" * 60)
        print(f"Mã kích hoạt: {code}")
        print(f"Hướng dẫn kích hoạt: {message}")
        print("=" * 60)

        # Định dạng mã xác minh (thêm dấu cách giữa các ký tự)
        formatted_code = " ".join(code)
        print(f"\nMã xác minh (hãy nhập trên trang web): {formatted_code}")
        print("\nHãy làm theo các bước sau để hoàn tất kích hoạt:")
        print("1. Mở trình duyệt và truy cập xiaozhi.me")
        print("2. Đăng nhập vào tài khoản của bạn")
        print("3. Chọn thêm thiết bị")
        print(f"4. Nhập mã xác minh: {formatted_code}")
        print("5. Xác nhận thêm thiết bị")
        print("\nĐang chờ xác nhận kích hoạt, vui lòng hoàn tất trên trang web...")

        self._log_and_print(f"Mã kích hoạt: {code}")
        self._log_and_print(f"Hướng dẫn kích hoạt: {message}")

    def _print_activation_success(self):
        """
        In thông báo kích hoạt thành công.
        """
        print("\n" + "=" * 60)
        print("Kích hoạt thiết bị thành công!")
        print("=" * 60)
        print("Thiết bị đã được thêm vào tài khoản của bạn")
        print("Cấu hình đã được cập nhật tự động")
        print("Chuẩn bị khởi động ứng dụng XiaoZhi AI...")
        print("=" * 60)

    def _print_activation_failure(self):
        """
        In thông báo kích hoạt thất bại.
        """
        print("\n" + "=" * 60)
        print("Kích hoạt thiết bị thất bại")
        print("=" * 60)
        print("Nguyên nhân có thể:")
        print("• Kết nối mạng không ổn định")
        print("• Mã xác minh nhập sai hoặc đã hết hạn")
        print("• Máy chủ tạm thời không khả dụng")
        print("\nGiải pháp đề xuất:")
        print("• Kiểm tra kết nối mạng")
        print("• Chạy lại chương trình để lấy mã mới")
        print("• Đảm bảo nhập chính xác mã trên trang web")
        print("=" * 60)

    def _log_and_print(self, message: str):
        """
        Ghi log đồng thời in ra terminal.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.logger.info(message)

    def get_activation_result(self) -> dict:
        """
        Lấy kết quả kích hoạt.
        """
        device_fingerprint = None
        config_manager = None

        if self.system_initializer:
            device_fingerprint = self.system_initializer.device_fingerprint
            config_manager = self.system_initializer.config_manager

        return {
            "is_activated": self.is_activated,
            "device_fingerprint": device_fingerprint,
            "config_manager": config_manager,
        }
