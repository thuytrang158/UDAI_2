# Trà Journey — Du lịch Thái Nguyên

Website tiếng Việt, HTML/CSS/JavaScript thuần. Chạy với Node.js:

```sh
npm start
```

Mở http://127.0.0.1:4173. Kiểm tra: `node check.cjs` và `npm run check`.

## Chức năng

- Banner, 6 tour mẫu; lọc theo điểm đến, số ngày, giá và phong cách; sắp xếp giá.
- Chi tiết tour, yêu thích, phiếu đặt tour mẫu và tải phiếu.
- Thiết kế tour theo ngân sách mỗi người, số khách, thời gian, phong cách và điểm đến; dự toán chi phí, cảnh báo vượt ngân sách.
- Bản đồ Leaflet/OpenStreetMap, đánh số điểm, đường nối minh họa, liên kết chỉ đường Google Maps. Có sơ đồ dự phòng nếu Leaflet không tải.
- Lưu và tải lịch trình, viết đánh giá, tin tức/cẩm nang.
- Giao diện thích ứng màn hình nhỏ, hộp thoại bàn phím, thông báo trạng thái.

## Giới hạn phiên bản

Đây là bản frontend tương tác với dữ liệu minh họa, chưa phải hệ thống kinh doanh vận hành. Không có backend, tài khoản, thanh toán, giữ chỗ, email hoặc quản trị nội dung. Phiếu đặt tour, bài đánh giá, yêu thích và lịch trình chỉ lưu trong localStorage của trình duyệt. Giá, đánh giá mẫu và lễ hội mẫu đều được đánh dấu trong giao diện.

Thuật toán cá nhân hóa dùng quy tắc: nếu chưa chọn địa điểm, ưu tiên phong cách và chi phí; nếu đã chọn địa điểm, giữ lựa chọn. Dự toán gồm trải nghiệm, ăn uống, lưu trú, xe nội vùng chia theo nhóm. Không phải báo giá nhà cung cấp. Tọa độ khu vực gần đúng, đường nối không phải tuyến đường bộ; kiểm tra tuyến thực tế qua Google Maps.

Bản đồ nền và phông chữ cần kết nối mạng. Nội dung điểm đến tham khảo và ảnh từ https://mythainguyen.vn/vi/tancuong11 và https://mythainguyen.vn/vi/honuicoc. Ảnh Tân Cương minh họa cho một số tour khác; cần thay bằng bộ ảnh có quyền sử dụng phù hợp trước khi kinh doanh công khai.

## Kiểm thử

`check.cjs` kiểm tra logic lọc, sắp xếp, tính ngân sách, tổng nhóm, gợi ý theo phong cách, mã hóa văn bản và tài nguyên. Máy chủ đã trả HTTP 200. Kiểm tra trực quan bằng trình duyệt chưa hoàn tất do công cụ trình duyệt lỗi khởi động sandbox Windows.
