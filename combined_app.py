import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import google.generativeai as genai
import numpy as np
import time
import pyttsx3
import io

# 1. SETUP
st.set_page_config(layout="wide")
st.title("🧠 Solvium: Solve from Drawing or Photo")

# 2. DARK MODE TOGGLE
dark_mode = st.toggle("🌙 Dark Mode")
bg_color = "#1e1e1e" if dark_mode else "#ffffff"
text_color = "#ffffff" if dark_mode else "#000000"
st.markdown(f"""
    <style>
        body {{ background-color: {bg_color}; color: {text_color}; }}
        .stTextInput > div > div > input {{
            background-color: {bg_color}; color: {text_color};
        }}
    </style>
""", unsafe_allow_html=True)

# 3. SOLVIUM API CONFIG
genai.configure(api_key="AIzaSyCxkJFiy3T4PXe_YFUgn3RKgknl-yuVKqo")
model = genai.GenerativeModel("gemini-2.0-flash")

# 4. SELECT PROMPT AND INPUT METHOD
prompt_option = st.selectbox("What should Solvium do?", ["Solve this", "Explain this", "Grade this"])
input_mode = st.radio("Choose Input Method", ["🖌️ Draw Here", "📸 Use Camera or Upload"])

image = None

# 5. DRAWING MODE
if input_mode == "🖌️ Draw Here":
    st.subheader("Draw with your finger (touchscreen) or mouse")
    if st.button("🧹 Clear Drawing"):
        st.experimental_rerun()
    canvas_result = st_canvas(
        stroke_width=10,
        stroke_color="#000000",
        background_color="#FFFFFF",
        width=400,
        height=400,
        drawing_mode="freedraw",
        key="canvas",
    )
    if canvas_result.image_data is not None:
        image = Image.fromarray(canvas_result.image_data.astype("uint8"))

# 6. CAMERA OR UPLOAD MODE
elif input_mode == "📸 Use Camera or Upload":
    st.subheader("Snap or upload an image")
    uploaded_img = st.camera_input("📸 Take a photo") or st.file_uploader("📁 Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_img:
        base_image = Image.open(uploaded_img)
        st.image(base_image, caption="Base Image", use_column_width=True)

        # Draw over the uploaded image
        canvas_result = st_canvas(
            background_image=base_image,
            stroke_width=5,
            stroke_color="#FF0000",
            height=base_image.height,
            width=base_image.width,
            drawing_mode="freedraw",
            key="canvas_with_upload",
        )
        if canvas_result.image_data is not None:
            image = Image.fromarray(canvas_result.image_data.astype("uint8"))
        else:
            image = base_image

# 7. GEMINI PROCESSING
if image:
    st.image(image, caption="Your Input", use_column_width=True)

    if st.button("🤖 Ask Solvium"):
        with st.spinner("🧠 Solvium is thinking..."):
            for i in range(100):
                time.sleep(0.005)
                st.progress(i + 1)
            prompt_map = {
                "Solve this": "Solve this handwritten or drawn math problem:",
                "Explain this": "Explain this drawing or problem:",
                "Grade this": "Grade this and give feedback:",
            }
            try:
                response = model.generate_content([prompt_map[prompt_option], image])
                st.session_state.last_response = response.text
                st.session_state.history = st.session_state.get("history", []) + [(prompt_option, response.text)]
                st.success("✅ Solvium responded!")
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.stop()

# 8. OUTPUT
if "last_response" in st.session_state:
    st.subheader("🧠 Solvium Says:")
    st.markdown(st.session_state.last_response)

    # Download
    st.download_button("💾 Download Response", st.session_state.last_response, file_name="solvium_response.txt")

    # Read aloud
    if st.button("🔊 Read Aloud"):
        engine = pyttsx3.init()
        engine.say(st.session_state.last_response)
        engine.runAndWait()

# 9. RESPONSE HISTORY
if "history" in st.session_state:
    with st.expander("📜 View History"):
        for i, (prompt, resp) in enumerate(st.session_state.history):
            st.markdown(f"**{i+1}. Prompt:** *{prompt}*")
            st.markdown(resp)
            st.markdown("---")
