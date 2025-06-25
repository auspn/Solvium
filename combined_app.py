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

    # Clear the canvas by resetting session state
    if st.button("🧹 Clear Drawing"):
        st.session_state["canvas"] = None

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
        base_image = Image.open(uploaded_img).convert("RGBA")
        st.image(base_image, caption="Base Image", use_container_width=True)

        # Clear button
        if st.button("🧹 Clear Drawing"):
            st.session_state["draw_over_image"] = None
            st.rerun()

        # Single canvas to draw over uploaded image
        canvas_result = st_canvas(
            background_image=base_image,
            stroke_width=5,
            stroke_color="#FF0000",
            height=base_image.height,
            width=base_image.width,
            drawing_mode="freedraw",
            key="draw_over_image",
            update_streamlit=True
        )

        # Merge drawing with uploaded image
        if canvas_result.image_data is not None:
            drawing_layer = Image.fromarray(canvas_result.image_data.astype("uint8")).convert("RGBA")
            image = Image.alpha_composite(base_image, drawing_layer)
        else:
            image = base_image


        
# 7. GEMINI PROCESSING
if image:
    st.image(image, caption="Your Input", use_container_width=True)

    if st.button("🤖 Ask Solvium"):
        with st.spinner("🧠 Solvium is thinking..."):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.005)
                progress_bar.progress(i + 1)

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
                st.markdown(" ")  # Optional space instead of a line
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.stop()


# 8. OUTPUT
if "last_response" in st.session_state:
    st.subheader("🧠 Solvium Says:")
    st.markdown(st.session_state.last_response)

    # Download
    st.download_button("💾 Download Response", st.session_state.last_response, file_name="solvium_response.txt")

from gtts import gTTS
import base64

# Read aloud using gTTS with download option
if st.button("🔊 Read Aloud"):
    try:
        # Convert response text to speech
        tts = gTTS(st.session_state.last_response)
        tts.save("response.mp3")

        # Read the file as bytes
        with open("response.mp3", "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")

            # Create a download button
            b64 = base64.b64encode(audio_bytes).decode()
            href = f'<a href="data:audio/mp3;base64,{b64}" download="solvium_response.mp3">📥 Download MP3</a>'
            st.markdown(href, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Text-to-speech failed: {e}")


# 9. RESPONSE HISTORY
if "history" in st.session_state:
    with st.expander("📜 View History"):
        for i, (prompt, resp) in enumerate(st.session_state.history):
            st.markdown(f"**{i+1}. Prompt:** *{prompt}*")
            st.markdown(resp)
            st.markdown("<hr style='border-top: 1px solid #eee;'>", unsafe_allow_html=True)

#Footer
st.markdown("""
    <footer style="text-align: center; padding: 20px; font-size: 0.8em;">
        Made By Shubh Narayan Dubey
    </footer>
""", unsafe_allow_html=True)
