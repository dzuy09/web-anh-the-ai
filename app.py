import streamlit as st
from PIL import Image
from rembg import remove, new_session
import io
import gc
import zipfile

# 1. Thiết lập giao diện hiện đại & CSS Custom
st.set_page_config(page_title="Hệ Thống Làm Ảnh Thẻ Tự Động", layout="wide", page_icon="📸")

# Chèn CSS tùy biến để tối ưu giao diện theo phong cách mới thanh lịch hơn
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1 {color: #1e293b; font-weight: 800 !important; font-size: 2.5rem !important; margin-bottom: 5px;}
    .subtitle {color: #64748b; font-size: 1.1rem; margin-bottom: 30px;}
    .stButton>button {
        background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
        color: white; border: none; border-radius: 8px;
        padding: 10px 24px; font-weight: 600; width: 100%;
        transition: all 0.3s ease; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);}
    .upload-box {border: 2px dashed #cbd5e1; border-radius: 12px; padding: 20px; background: white;}
    .success-box {background-color: #f0fdf4; border-left: 5px solid #22c55e; padding: 15px; border-radius: 4px;}
    </style>
""", unsafe_allow_html=True)

# 2. Tiêu đề chính
st.markdown("<h1>📸 Hệ Thống Tạo Ảnh Thẻ Học Viên</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Công cụ AI hỗ trợ tách nền hàng loạt, chuẩn hóa màu sắc và giữ nguyên tên file gốc.</p>", unsafe_allow_html=True)

# 3. Tạo layout 2 cột rõ ràng: Cột cấu hình (Trái) & Cột xử lý (Phải)
col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.subheader("⚙️ Cấu hình ảnh thẻ")
    bg_color = st.radio(
        "Chọn màu phông nền:",
        ["Xanh dương (Chuẩn quốc tế)", "Trắng tinh khôi"],
        index=0,
        help="Chọn màu nền phù hợp với yêu cầu của thẻ học viên."
    )
    
    st.divider()
    st.info("💡 **Mẹo:** Bạn có thể kéo thả cùng lúc nhiều file ảnh vào ô bên cạnh để hệ thống tự động xử lý hàng loạt.")

with col_right:
    st.subheader("📥 Khu vực tải ảnh lên")
    
    # Cho phép chọn nhiều file cùng lúc qua tham số accept_multiple_files=True
    uploaded_files = st.file_uploader(
        "Kéo và thả các file ảnh chân dung tại đây:",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.write(f"📂 Đang chuẩn bị xử lý: **{len(uploaded_files)} ảnh**")
        
        # Nút kích hoạt lớn, trực quan
        if st.button("✨ Bắt đầu xử lý hàng loạt"):
            
            # Tạo file ZIP trong bộ nhớ tạm để chứa ảnh đầu ra
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                # Khởi tạo thanh tiến trình (Progress Bar)
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Khởi tạo mô hình AI u2net ổn định RAM
                session = new_session("u2net")
                
                # Biến lưu danh sách ảnh hiển thị preview kết quả lên giao diện web
                processed_previews = []
                
                for index, file in enumerate(uploaded_files):
                    status_text.text(f"⏳ Đang xử lý file ({index+1}/{len(uploaded_files)}): {file.name}")
                    
                    try:
                        # Đọc ảnh gốc
                        input_image = Image.open(file)
                        
                        # Chuyển đổi sang bytes
                        img_byte_arr = io.BytesIO()
                        input_image.save(img_byte_arr, format='PNG')
                        img_bytes = img_byte_arr.getvalue()
                        
                        # AI tách nền
                        output_bytes = remove(img_bytes, session=session)
                        fg_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
                        
                        # Đổi màu nền theo lựa chọn
                        color_rgb = (0, 119, 255, 255) if "Xanh" in bg_color else (255, 255, 255, 255)
                        bg_image = Image.new("RGBA", fg_image.size, color_rgb)
                        
                        # Ghép nền màu với người
                        final_image = Image.alpha_composite(bg_image, fg_image).convert("RGB")
                        
                        # Lưu ảnh đã xử lý vào bộ nhớ dạng JPG chất lượng cao nhất
                        out_img_buffer = io.BytesIO()
                        final_image.save(out_img_buffer, format="JPEG", quality=100)
                        
                        # Đưa vào file nén ZIP, GIỮ NGUYÊN TÊN FILE GỐC (chỉ đổi đuôi thành .jpg)
                        original_name_without_ext = file.name.rsplit('.', 1)[0]
                        new_filename = f"{original_name_without_ext}.jpg"
                        zip_file.writestr(new_filename, out_img_buffer.getvalue())
                        
                        # Lưu 3 ảnh đầu tiên để tạo preview trực quan cho người dùng xem trước
                        if len(processed_previews) < 3:
                            processed_previews.append((new_filename, final_image))
                            
                    except Exception as e:
                        st.error(f"❌ Lỗi khi xử lý file {file.name}: {e}")
                        
                    # Cập nhật thanh tiến trình thanh thoát
                    progress_bar.progress((index + 1) / len(uploaded_files))
                
                status_text.markdown("<div class='success-box'>🎉 Hoàn thành xử lý tất cả hình ảnh!</div>", unsafe_allow_html=True)
                
                # Giải phóng RAM thừa ngay
                del img_bytes, output_bytes
                gc.collect()

            # 4. Khu vực hiển thị kết quả và tải về
            st.divider()
            st.subheader("📸 Kết quả & Tải về")
            
            # Nút tải trọn gói toàn bộ thư mục ảnh đã đổi nền dưới dạng file ZIP
            st.download_button(
                label="📥 TẢI XUỐNG TẤT CẢ ẢNH (FILE .ZIP)",
                data=zip_buffer.getvalue(),
                file_name="anh_the_hoc_vien_hoan_thanh.zip",
                mime="application/zip"
            )
            
            # Hiển thị khu vực xem trước (Preview Grid) dạng lưới hiện đại
            st.write("🔍 *Xem trước một vài ảnh đã xử lý:*")
            grid_cols = st.columns(len(processed_previews))
            for g_col, (fname, img) in zip(grid_cols, processed_previews):
                with g_col:
                    st.image(img, caption=fname, use_container_width=True)
