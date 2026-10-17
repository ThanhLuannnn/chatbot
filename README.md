# NEURAL AGENT — AI Agent nâng cao

Starter project cho AI Agent giao diện xanh neon, dùng FastAPI và OpenAI Responses API.

## Tính năng

- Chat tiếng Việt với mô hình AI qua API.
- Tìm kiếm web bằng công cụ tích hợp `web_search`.
- Function calling với công cụ tính toán an toàn và lưu ghi chú cục bộ.
- Lịch sử hội thoại trong phiên trình duyệt.
- Giao diện responsive, phong cách dark/neon.
- API key chỉ nằm ở backend trong file `.env`.

## Yêu cầu

- Python 3.10 trở lên.
- Một API key có quyền sử dụng API và hạn mức phù hợp.
- Kết nối Internet.

Lưu ý: ChatGPT và API platform có hệ thống thanh toán/hạn mức riêng. Có thể phát sinh chi phí API.

## Chạy trên Windows + VS Code

1. Giải nén thư mục dự án và mở thư mục `neural_agent` bằng VS Code.
2. Mở Terminal → New Terminal.
3. Tạo môi trường ảo:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   Nếu dùng Command Prompt thay vì PowerShell:

   ```bat
   .venv\Scripts\activate.bat
   ```

4. Cài thư viện:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Tạo file `.env` bằng cách sao chép `.env.example`. Điền API key vào `OPENAI_API_KEY` và lưu file.
6. Chạy ứng dụng:

   ```powershell
   uvicorn app:app --reload
   ```

7. Mở trình duyệt tại `http://127.0.0.1:8000`.

## Dùng API an toàn

- Không gửi khóa API trong chat, ảnh chụp màn hình hoặc mã nguồn công khai.
- Không commit file `.env` lên Git.
- Nếu nghi ngờ khóa bị lộ, hãy thu hồi và tạo khóa mới trong trang quản lý API.
- Endpoint hiện chưa có đăng nhập, giới hạn tốc độ hoặc triển khai production. Chỉ chạy cục bộ để thử nghiệm; cần bổ sung xác thực và bảo vệ dữ liệu trước khi đưa lên Internet.
- Các ghi chú được lưu ở `data/notes.json`; thư mục này được loại khỏi Git.

## Mở rộng tiếp theo

- Thêm đăng nhập người dùng và cơ sở dữ liệu.
- Bổ sung xác nhận trước các hành động có tác động bên ngoài.
- Tạo trang quản lý ghi chú và lịch sử tác vụ.
- Thêm kiểm thử, logging, giới hạn tốc độ và triển khai bảo mật.
