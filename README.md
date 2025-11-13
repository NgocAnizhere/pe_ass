Commit Message Guide (Conventional Commits)
Đây là bảng hướng dẫn các loại commit message theo chuẩn Conventional Commits

Cấu trúc commit cơ bản:
<type>: <short message>
feat: add LED control endpoint for ESP32 web server

# Commit types
| Loại commit (`type`) | Ý nghĩa                                                                 |
| -------------------- | ----------------------------------------------------------------------- |
| `feat`               | Thêm tính năng mới                                                      |
| `fix`                | Sửa lỗi                                                                 |
| `docs`               | Cập nhật tài liệu (README, hướng dẫn...)                                |
| `style`              | Thay đổi định dạng (formatting) – không làm thay đổi logic chương trình |
| `refactor`           | Cải tổ code – không thêm tính năng, không sửa lỗi                       |
| `test`               | Thêm hoặc sửa các bài kiểm thử (unit, integration tests)                |
| `chore`              | Công việc phụ trợ như config, CI/CD, build script...                    |