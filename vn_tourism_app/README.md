# Coming Back · Streamlit app (M9 + M10)

## Chạy
```
pip install -r requirements.txt
streamlit run app.py
```
Deploy miễn phí: đẩy cả thư mục lên GitHub → https://share.streamlit.io → chọn `app.py`.
(Hosting miễn phí có thể xoá file trong `logs/` khi khởi động lại — tải log về sau mỗi buổi thử.)

## Cấu trúc
- `app.py` – giao diện + 5 trang (Câu chuyện, Explorer & Hỏi nhanh, Đua phục hồi, Mùa vụ & thời tiết, Phân khúc)
- `m10.py` – trang M10: kế hoạch test, ghi kết quả, phân tích, improvement log
- `data_layer.py` – xử lý dữ liệu (tái lập đặc trưng M6; test độc lập: `python data_layer.py`)
- `ui.py` – CSS, màu house style, định dạng số kiểu Việt Nam
- `house_style.py` – của nhóm (không sửa)
- `data/` – 5 file CSV lấy từ folder Drive
- `logs/` – log kiểm thử (user_tests, five_second, peer_review, improvement_log, ai_use_log)

## Nhóm cần tự làm (không thể thay bằng code)
1. Chụp ảnh storyboard vẽ tay 5–8 khung (app đã có sẵn 5 chương làm khung gợi ý).
2. Thử với ≥ 5 người ngoài nhóm, nhập kết quả THẬT ở tab "Ghi kết quả".
3. Ghi ≥ 8 cải tiến thật vào Improvement log; điền cột "Phần đã sửa/từ chối" trong `ai_use_log.csv`.
