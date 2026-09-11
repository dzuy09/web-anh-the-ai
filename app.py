import streamlit as st
from PIL import Image
from rembg import remove, new_session
import io

# Cấu hình giao diện Web
st.set_page_config(page_title="Tạo Ảnh Thẻ Chất Lượng Cao", layout="centered")
st.title("📸 Web App Tạo Ảnh Thẻ Học Viên (Mô hình SOTA)")
st.write("Tách nền bằng mô hình BiRefNet chuyên dụng, sắc nét từng sợi tóc.")

# Menu lựa chọn màu nền ảnh thẻ
bg_color = st.selectbox("Chọn màu nền ảnh thẻ:", ["Xanh dương (Chuẩn)", "Trắng tinh"])

# Upload ảnh học viên
uploaded_file = st.file_uploader("Tải ảnh chân dung lên:", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    input_image = Image.open(uploaded_file)
    st.image(input_image, caption="Ảnh gốc", use_container_width=True)
    
    if st.button("✨ Tiến hành tạo ảnh thẻ"):
        with st.spinner("AI đang bóc tách viền tóc siêu nét..."):
            try:
                # Chuyển đổi ảnh sang dạng bytes
                img_byte_arr = io.BytesIO()
                input_image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                
                # Khởi tạo session với mô hình cao cấp chuyên cho ảnh chân dung người
                session = new_session("birefnet-portrait")
                
                # Thực hiện tách nền chất lượng cao
                output_bytes = remove(img_bytes, session=session)
                fg_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
                
                # Tạo nền màu ảnh thẻ chuẩn
                color_rgb = (0, 119, 255, 255) if "Xanh" in bg_color else (255, 255, 255, 255)
                bg_image = Image.new("RGBA", fg_image.size, color_rgb)
                
                # Hợp nhất ảnh người và nền
                final_image = Image.alpha_composite(bg_image, fg_image).convert("RGB")
                
                st.success("Đã hoàn thành ảnh thẻ chất lượng cao!")
                st.image(final_image, caption="Kết quả siêu nét", use_container_width=True)
                
                # Nút tải ảnh
                buffered = io.BytesIO()
                final_image.save(buffered, format="JPEG", quality=100)
                st.download_button(
                    label="📥 Tải ảnh thẻ về máy",
                    data=buffered.getvalue(),
                    file_name="anh_the_birefnet.jpg",
                    mime="image/jpeg"
                )
                
            except Exception as e:
                st.error(f"Lỗi xử lý: {e}")
