# banana_leaf_ai_app.py
# Streamlit prototype: "BananaLeafAI - Smart Assistant"
# Prototype dùng công thức ước lượng + phân tích màu ảnh.

import streamlit as st
from PIL import Image
import numpy as np
import math

st.set_page_config(page_title="BananaLeafAI", layout="wide", page_icon="🌿")

# -------------------------------------------------
# 1) HÀM ƯỚC LƯỢNG HIỆU SUẤT CHIẾT POLYPHENOL
# -------------------------------------------------
def estimate_yield(leaf_mass_g, ethanol_pct, time_h, temp_c, cut_size_mm):
    base = 0.04  
    ethanol_opt = 70
    ethanol_effect = 1 - 0.003 * abs(ethanol_pct - ethanol_opt)
    ethanol_effect = max(0.6, ethanol_effect)

    time_effect = 1 - math.exp(-time_h / 18)
    temp_opt = 65
    temp_effect = 1 - 0.005 * abs(temp_c - temp_opt)
    temp_effect = max(0.7, temp_effect)

    cut_effect = 1 + 0.02 * max(0, (5 - cut_size_mm))

    yield_per_g = base * ethanol_effect * (0.5 + time_effect) * temp_effect * cut_effect * 1000
    yield_per_g = max(0.5, yield_per_g)
    total_yield_mg = yield_per_g * leaf_mass_g

    return round(total_yield_mg, 1), round(yield_per_g, 3)


# -------------------------------------------------
# 2) GỢI Ý QUY TRÌNH TỪ INPUT NGƯỜI DÙNG
# -------------------------------------------------
def recommend_process(leaf_mass_g, product_choice, yield_mg_total, mg_per_g):
    checklist = []

    checklist.append("Rửa sạch lá chuối, để ráo.")
    checklist.append("Cắt lá thành miếng 0.5–1 cm.")
    checklist.append("Sấy 50–60°C hoặc phơi bóng râm 1–2 giờ.")
    checklist.append(f"Chuẩn bị ethanol {st.session_state['ethanol_pct']}%.")
    checklist.append(f"Ngâm ở {st.session_state['temp_c']}°C trong {st.session_state['time_h']} giờ.")
    checklist.append("Lọc dung dịch, cô đặc nếu cần.")

    if product_choice == "Viên hút mùi":
        per_unit = 20  
        num_units = int(yield_mg_total // per_unit)

        checklist.append(f"Mỗi viên cần ~{per_unit} mg polyphenol → ước tính làm được {num_units} viên.")
        checklist.append("Trộn than hoạt tính + polyphenol + hồ tinh bột, nén khuôn, sấy 12–24h.")

    elif product_choice == "Gạch sinh học":
        bã = leaf_mass_g * 0.25
        per_brick = 50
        num_bricks = int(bã // per_brick)

        checklist.append(f"Bã sau chiết ~{int(bã)} g → ~{num_bricks} viên gạch mini.")
        checklist.append("Trộn bã + đất sét + trấu/mùn cưa, nén khuôn và phơi — sau đó sấy.")

    else:
        per_unit = 20
        num_units = int(yield_mg_total // per_unit)
        bã = leaf_mass_g * 0.25
        per_brick = 50
        num_bricks = int(bã // per_brick)

        checklist.append(f"Ước tính: {num_units} viên hút mùi + {num_bricks} viên gạch mini.")

    checklist.append("Lưu ý an toàn: đeo găng tay, tránh lửa khi dùng ethanol.")

    return checklist


# -------------------------------------------------
# 3) PHÂN TÍCH MÀU DỊCH CHIẾT
# -------------------------------------------------
def analyze_image_strength(img):
    img = img.convert('RGB').resize((200,200))
    arr = np.array(img).astype(float) / 255.0

    r,g,b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    maxc = np.maximum(np.maximum(r,g), b)
    minc = np.minimum(np.minimum(r,g), b)

    v = maxc
    s = (maxc - minc) / (maxc + 1e-9)

    sat = float(np.nanmean(s))
    val = float(np.nanmean(v))

    score = sat * 0.7 + (1 - val) * 0.3

    if score > 0.35:
        return "Mạnh (đậm)", score
    elif score > 0.20:
        return "Trung bình", score
    else:
        return "Nhạt (yếu)", score


# -------------------------------------------------
# 4) GIAO DIỆN CHÍNH
# -------------------------------------------------
st.title("🌿 BanaLe - Hỗ trợ công thức phù hợp với lá chuối")
st.write("Nhập lượng lá chuối → AI sẽ tính hiệu suất, gợi ý quy trình, sản lượng & phân tích ảnh dịch chiết.")

# ---- INPUT FORM ----
col1, col2 = st.columns(2)

with col1:
    st.subheader("Thông số đầu vào")

    leaf_mass = st.number_input("Khối lượng lá chuối (g)", min_value=10.0, value=2000.0)
    st.session_state['ethanol_pct'] = st.slider("Nồng độ ethanol (%)", 30, 90, 70)
    st.session_state['time_h'] = st.slider("Thời gian chiết (giờ)", 1, 72, 24)
    st.session_state['temp_c'] = st.slider("Nhiệt độ chiết (°C)", 20, 90, 65)
    cut_size = st.slider("Kích thước cắt lá (mm)", 1, 20, 5)

    product_choice = st.selectbox("Sản phẩm mong muốn", ["Viên hút mùi", "Gạch sinh học", "Cả hai"])

    if st.button("Tính & gợi ý"):
        total_mg, mg_per_g = estimate_yield(
            leaf_mass, 
            st.session_state['ethanol_pct'],
            st.session_state['time_h'],
            st.session_state['temp_c'],
            cut_size
        )
        st.session_state['calc'] = (total_mg, mg_per_g)

with col2:
    st.subheader("Phân tích màu dịch chiết")
    upl = st.file_uploader("Tải ảnh (jpg/png):", type=['jpg','jpeg','png'])
    if upl:
        img = Image.open(upl)
        st.image(img, caption="Ảnh mẫu", use_column_width=True)
        strength, score = analyze_image_strength(img)
        st.metric("Độ đậm polyphenol (ước lượng)", strength, f"score={score:.2f}")

st.markdown("---")

# ---- OUTPUT RESULT ----
if 'calc' in st.session_state:
    total_mg, mg_per_g = st.session_state['calc']

    st.header("📌 KẾT QUẢ AI")
    st.write(f"**Tổng polyphenol ước tính:** {total_mg} mg GAE")
    st.write(f"**Hiệu suất (mg/g):** {mg_per_g} mg GAE/g lá")

    st.subheader("📋 Checklist quy trình")
    plan = recommend_process(leaf_mass, product_choice, total_mg, mg_per_g)
    for i, step in enumerate(plan, 1):
        st.write(f"**{i}.** {step}")

    st.markdown("---")
    st.subheader("📦 Sản lượng dự kiến")

    if product_choice == "Viên hút mùi":
        per_unit = 20
        st.write(f"≈ {int(total_mg // per_unit)} viên hút mùi")

    elif product_choice == "Gạch sinh học":
        bã = leaf_mass * 0.25
        per_brick = 50
        st.write(f"≈ {int(bã // per_brick)} viên gạch mini")

    else:
        per_unit = 20
        bã = leaf_mass * 0.25
        per_brick = 50
        st.write(f"- Hút mùi: {int(total_mg // per_unit)} viên")
        st.write(f"- Gạch: {int(bã // per_brick)} viên")

st.markdown("---")

st.caption("Trang web được phụ trách bởi nhóm nghiên cứu khoa học: Trần Nguyễn Thanh Vy - Trịnh Công Minh Anh.")

