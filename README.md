# Trà Journey — Du lịch Thái Nguyên

Website tiếng Việt, HTML/CSS/JavaScript thuần. Chạy với Node.js:

```sh
npm start
```

Mở http://127.0.0.1:4173. Kiểm tra: `node check.cjs` và `npm run check`.

## Chức năng

- Banner, 10 tour kết hợp phủ 13 điểm đến; lọc theo điểm đến, 1–5 ngày, giá khởi điểm và nhiều tag; sắp xếp giá.
- Chi tiết tour theo ngày/giờ, đối tượng, thể lực, mùa, di chuyển, ăn nghỉ, dịch vụ, phương án thời tiết, nguồn tham khảo; tải lịch trình Markdown.
- Yêu thích, phiếu dự toán mẫu và tải phiếu. Tour mới không có đánh giá giả.
- Thiết kế tour theo ngân sách mỗi người, số khách, thời gian, phong cách và điểm đến; dự toán chi phí, cảnh báo vượt ngân sách.
- Bản đồ Leaflet/OpenStreetMap, đánh số điểm, đường nối minh họa, liên kết chỉ đường Google Maps. Có sơ đồ dự phòng nếu Leaflet không tải.
- Lưu và tải lịch trình, viết đánh giá, tin tức/cẩm nang.
- Giao diện thích ứng màn hình nhỏ, hộp thoại bàn phím, thông báo trạng thái.

## Giới hạn phiên bản

Đây là bản frontend tương tác với dữ liệu minh họa, chưa phải hệ thống kinh doanh vận hành. Không có backend, tài khoản, thanh toán, giữ chỗ, email hoặc quản trị nội dung. Phiếu đặt tour, bài đánh giá, yêu thích và lịch trình chỉ lưu trong localStorage của trình duyệt. Giá, đánh giá mẫu và lễ hội mẫu đều được đánh dấu trong giao diện.

Thuật toán cá nhân hóa vẫn dùng bộ 5 điểm thử nghiệm ban đầu; bộ danh mục 10 tour chi tiết mới được quản lý riêng. Nếu chưa chọn địa điểm trong bộ thiết kế, ưu tiên phong cách và chi phí; nếu đã chọn địa điểm, giữ lựa chọn. Dự toán gồm trải nghiệm, ăn uống, lưu trú, xe nội vùng chia theo nhóm. Không phải báo giá nhà cung cấp. Tọa độ khu vực gần đúng, đường nối không phải tuyến đường bộ; kiểm tra tuyến thực tế qua Google Maps.

Bản đồ nền và phông chữ cần kết nối mạng. Ảnh bìa của cả 10 tour và bộ ảnh trong chi tiết tour dùng 8 ảnh do chủ website cung cấp từ thư mục `../images`, được sao chép nguyên bản vào `dist/assets/tours/`. Địa danh ghép theo tên tệp của chủ website, không phải kết quả xác minh địa điểm bằng hình ảnh. Ảnh nhà sàn chưa rõ địa điểm chỉ minh họa không gian lưu trú của TJ04, không đại diện cơ sở đã đặt. Không dùng ảnh có tên Juknokwon (Hàn Quốc) cho Yến Dương. Các tour có nhiều ảnh hiển thị thêm bộ ảnh bấm mở lớn; các điểm chưa có ảnh không được gán nhầm ảnh từ nơi khác. Nguồn tham khảo điểm đến được gắn vào từng tour; chỉ dùng nguồn để đối chiếu cảnh quan và vị trí, không coi là xác nhận giá/giờ/dịch vụ hiện tại.

## Dữ liệu biên tập ngày 14/10/2026

- Nguồn duy nhất: `dist/tours-data.js`; chứa 13 điểm đến, 10 tour, điều kiện chung và nguồn dẫn.
- Chạy `node export-catalogue.cjs` sau khi sửa để cập nhật `dist/data/tours.json` và `dist/data/tour-catalogue.md`.
- `dist/tour-details.js` hiển thị chi tiết và xuất Markdown từng tour; `dist/tour-details.css` định dạng lịch trình.
- Mã TJ01–TJ10; trạng thái `draft_itinerary`; `rating: null`, `reviewCount: 0`.
- Giá là khoảng dự kiến cho đoàn 10 người lớn, ngày thường; chưa có nhà cung cấp hoặc lịch khởi hành được xác nhận. Phiếu dự toán nhân giá khởi điểm, không phải báo giá cho mọi quy mô đoàn.
- Yên Dương được chuẩn hóa thành Yến Dương (Phiêng Phàng/Pù Lầu), vẫn giữ alias để nhận diện. Chùa Hang được hiểu là Kim Sơn Tự gần trung tâm; cần đổi dữ liệu nếu chủ dự án muốn Chùa Hang ở Định Hóa.
- Địa danh theo khu vực quen thuộc, không cung cấp địa chỉ hành chính đầy đủ chưa xác minh. Tuyến Cửa Tử và Thẳm Phầy cần đơn vị chuyên môn xác nhận quyền khai thác, điều kiện nước, hướng dẫn, trang bị, bảo hiểm và phương án ứng phó trước khi nhận khách.

## Kiểm thử

`check.cjs` kiểm tra logic lọc, sắp xếp, tính ngân sách, tổng nhóm, gợi ý theo phong cách, mã hóa văn bản, độ phủ 13 điểm, 10 tour, số ngày/đêm, thứ tự thời gian, render chi tiết và tính đồng nhất JSON. Kiểm tra trực quan bằng trình duyệt chưa hoàn tất do công cụ trình duyệt lỗi khởi động sandbox Windows.
