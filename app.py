import streamlit as st
from PIL import Image
from rembg import remove, new_session
import io
import gc  # Thư viện giải phóng bộ nhớ RAM thừa

# Cấu hình giao diện Web gọn gàng
st.set_page_config(page_title="Tạo Ảnh Thẻ Học Viên", layout="centered")
st.title("📸 Web App Tạo Ảnh Thẻ Học Viên")
st.write("Phiên bản tối ưu hóa máy chủ - Tách nền ổn định, không lo gián đoạn.")

# Menu lựa chọn màu nền ảnh thẻ
bg_color = st.selectbox("Chọn màu nền ảnh thẻ:", ["Xanh dương (Chuẩn)", "Trắng tinh"])

# Upload ảnh học viên
uploaded_file = st.file_uploader("Tải ảnh chân dung lên:", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    input_image = Image.open(uploaded_file)
    st.image(input_image, caption="Ảnh gốc", use_container_width=True)
    
    if st.button("✨ Tiến hành tạo ảnh thẻ"):
        with st.spinner("Hệ thống AI đang xử lý tách nền nhanh..."):
            try:
                # 1. Chuyển đổi ảnh sang dạng bytes để tiết kiệm RAM
                img_byte_arr = io.BytesIO()
                input_image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                
                # 2. Khởi tạo session với mô hình u2net nhẹ (~170MB), an toàn cho Streamlit Cloud
                session = new_session("u2net")
                
                # 3. Thực hiện tách nền
                output_bytes = remove(img_bytes, session=session)
                fg_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
                
                # 4. Tạo nền màu ảnh thẻ chuẩn
                color_rgb = (0, 119, 255, 255) if "Xanh" in bg_color else (255, 255, 255, 255)
                bg_image = Image.new("RGBA", fg_image.size, color_rgb)
                
                # 5. Hợp nhất ảnh người và nền màu
                final_image = Image.alpha_composite(bg_image, fg_image).convert("RGB")
                
                st.success("Đã hoàn thành ảnh thẻ!")
                st.image(final_image, caption="Kết quả ảnh thẻ", use_container_width=True)
                
                # Nút tải ảnh chất lượng cao về máy
                buffered = io.BytesIO()
                final_image.save(buffered, format="JPEG", quality=100)
                st.download_button(
                    label="📥 Tải ảnh thẻ về máy",
                    data=buffered.getvalue(),
                    file_name="anh_the_hoc_vien.jpg",
                    mime="image/jpeg"
                )
                
                # 6. Ép hệ thống giải phóng bộ nhớ RAM ngay lập tức sau khi xử lý xong
                del img_bytes, output_bytes, fg_image, bg_image
                gc.collect()
                
            except Exception as e:
                st.error(f"Lỗi xử lý: {e}")
