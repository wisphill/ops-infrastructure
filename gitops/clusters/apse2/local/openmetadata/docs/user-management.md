# OpenMetadata: Flow đăng ký và quản lý user

Bối cảnh hiện tại của instance https://openmetadata.opswork.io.vn:

- Đăng nhập bằng **Basic Auth** (email + mật khẩu), không dùng SSO.
- **Self signup đã tắt**: người dùng không tự tạo tài khoản được từ trang login
  (cách tắt xem [../READme.md](../READme.md)).
- **Chưa cấu hình SMTP**: OpenMetadata không gửi được email (không có email mời, không có
  "Quên mật khẩu", không xác minh email).

Vì vậy mọi tài khoản đều do admin tạo, và mật khẩu do admin giao cho người dùng.

## 1. Người dùng mới xin quyền truy cập

```text
Người dùng ──(yêu cầu qua chat/ticket)──▶ Admin OpenMetadata
                                             │
                                             ▼
                       Settings > Team & User Management > Users > Add User
                                             │
                                             ▼
                     Admin gửi email + mật khẩu tạm qua kênh riêng (không gửi
                     chung nhóm chat)
                                             │
                                             ▼
             Người dùng đăng nhập tại https://openmetadata.opswork.io.vn
                         và đổi mật khẩu ngay lần đầu
```

## 2. Admin tạo user

1. Đăng nhập bằng tài khoản admin.
2. Vào `Settings > Team & User Management > Users`, bấm **Add User**.
3. Điền thông tin:
   - **Email**: email thật của người dùng (dùng làm tên đăng nhập).
   - **Display Name**, **Description**: tùy chọn.
   - **Teams**: chọn team, user sẽ thừa hưởng role của team đó. Chỉ team loại `Group` mới
     nhận thành viên trực tiếp.
   - **Roles**: gán thêm role nếu cần (ví dụ `DataConsumer` để chỉ xem, `DataSteward` để
     chỉnh sửa metadata).
   - **Admin**: chỉ bật khi người đó cần toàn quyền cài đặt.
   - **Mật khẩu**: vì không có SMTP, chọn tự đặt hoặc tự sinh mật khẩu ngay trên form rồi
     copy lại để giao cho người dùng.
4. Bấm **Create**.

## 3. Người dùng đăng nhập lần đầu

1. Mở https://openmetadata.opswork.io.vn (có thể phải qua bước kiểm tra của Cloudflare).
2. Đăng nhập bằng email và mật khẩu tạm admin đã gửi.
3. Đổi mật khẩu ngay: bấm avatar góc phải, vào trang profile, chọn **Change Password**.

## 4. Quên mật khẩu

Không có SMTP nên nút "Forgot password" không gửi được email. Người dùng báo admin. Admin vào
`Settings > Team & User Management > Users`, mở user đó, đặt lại mật khẩu mới rồi giao lại như
lúc tạo user.

## 5. Đổi quyền, chuyển team

Admin mở user trong `Settings > Team & User Management > Users`, sửa **Teams** / **Roles**, hoặc
thêm/bỏ user khỏi danh sách `Settings > Team & User Management > Admins`.

Ưu tiên gán quyền qua team thay vì gán role lẻ cho từng người, để khi người dùng chuyển team chỉ
cần đổi team.

## 6. Khóa / xóa user (nghỉ việc, hết nhu cầu)

1. Vào `Settings > Team & User Management > Users`, chọn user, bấm **Delete**.
2. Chọn **Soft delete** nếu muốn giữ lịch sử (owner, hoạt động) và có thể khôi phục sau.
   Chọn **Permanently delete** nếu muốn xóa hẳn.

Rà lại định kỳ danh sách user để xóa tài khoản không còn dùng, nhất là các tài khoản từng tự
đăng ký trước khi tắt self signup.

## 7. Tài khoản admin mặc định

Lúc cài đặt, OpenMetadata tạo sẵn admin `admin@open-metadata.org` với mật khẩu `admin`. Sau khi đã
tạo ít nhất một admin thật:

1. Đăng nhập bằng admin thật, kiểm tra vào được `Settings`.
2. Đổi mật khẩu hoặc xóa tài khoản `admin@open-metadata.org`
   ([khuyến nghị của OpenMetadata](https://docs.open-metadata.org/v2.0.x/deployment/security/basic-auth)).

## Khi nào flow này thay đổi

- **Cấu hình SMTP**: admin chỉ cần nhập email, OpenMetadata tự gửi email mời và người dùng tự đặt
  mật khẩu; "Quên mật khẩu" cũng sẽ hoạt động.
- **Chuyển sang SSO** (ví dụ Google): người dùng đăng nhập bằng tài khoản Google, không còn mật
  khẩu riêng; việc cho phép tự tạo tài khoản khi đó bật/tắt ở `Settings > SSO` cho từng provider.
