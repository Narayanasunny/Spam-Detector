import streamlit as st
import pandas as pd
import re
import speech_recognition as sr
from deep_translator import GoogleTranslator
from fpdf import FPDF

# ----------------- CONFIGURATION -----------------
st.set_page_config(page_title="Email Spam Detector", layout="wide")

HISTORY_FILE = "spam_history.csv"

# ----------------- CUSTOM HEADER & FOOTER -----------------
header_footer_css = """
<style>
/* Header - Minimalist GitHub Icon */
.header {
    position: absolute;
    top: 10px;
    right: 15px;
}
.header img {
    width: 30px;
    transition: transform 0.3s;
}
.header img:hover {
    transform: scale(1.2);
}

/* Footer - LinkedIn Name */
.footer {
    position: fixed;
    bottom: 10px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 14px;
    color: white;
    background: rgba(0, 0, 0, 0.7);
    padding: 8px 15px;
    border-radius: 5px;
}
.footer a {
    color: cyan;
    text-decoration: none;
}
.footer a:hover {
    text-decoration: underline;
}
</style>

<div class="header">
    View on GitHub 🔗<a href="https://github.com/Narayanasunny" target="_blank">
        <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" alt="GitHub Logo" width="30">
    </a>
</div>

<div class="footer">
    Created by 🤖 <a href="https://www.linkedin.com/in/narayanasunny/" target="_blank">Narayana Kumar</a>
</div>
"""
st.markdown(header_footer_css, unsafe_allow_html=True)

# ----------------- SPAM DETECTION FUNCTION -----------------
spam_words = ["win", "free", "money", "offer", "lottery", "prize", "congratulations", "urgent",
              "click", "subscribe", "discount", "deal", "gift", "limited", "now", "claim"]

safe_replacements = {
    "win": "achieve", "free": "complimentary", "money": "funds",
    "offer": "proposal", "lottery": "contest", "prize": "reward",
    "urgent": "important", "click": "visit", "discount": "price drop",
}

def is_spam(message):
    return any(word in message.lower() for word in spam_words)

def correct_spam_message(message):
    words = message.split()
    return " ".join([safe_replacements.get(word.lower(), word) for word in words])

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Speak Now...")
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            st.error("Could not understand your voice.")
        except sr.RequestError:
            st.error("Check your internet connection.")
    return None

def detect_spam_multilang(message, language):
    translated_text = GoogleTranslator(source=language, target="en").translate(message)
    return is_spam(translated_text)

def save_message(message, classification):
    df = pd.DataFrame([[message, classification]], columns=["Message", "Classification"])
    df.to_csv(HISTORY_FILE, mode="a", header=not pd.io.common.file_exists(HISTORY_FILE), index=False)

def generate_pdf():
    if not pd.io.common.file_exists(HISTORY_FILE):
        return None
    df = pd.read_csv(HISTORY_FILE)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Spam Detection Report", ln=True, align='C')
    
    for index, row in df.iterrows():
        pdf.cell(200, 10, txt=f"{row['Message']} - {row['Classification']}", ln=True)
    
    pdf_output = "spam_report.pdf"
    pdf.output(pdf_output)
    return pdf_output

# ----------------- STREAMLIT UI -----------------
st.title("📧 Spam Detector")
st.subheader("Check if a message is spam or safe")

message = st.text_area("Enter your message:")
language_options = {
    "English": "en", "French": "fr", "Spanish": "es", "Hindi": "hi",
    "German": "de", "Chinese": "zh-CN"
}
language = st.selectbox("Select Language", list(language_options.keys()))
detect_btn = st.button("🔍 Check Spam")

if detect_btn:
    if language != "English":
        spam_status = detect_spam_multilang(message, language_options[language])
    else:
        spam_status = is_spam(message)

    if spam_status:
        st.error("⚠️ This message is likely SPAM!")
        corrected_message = correct_spam_message(message)
        st.info(f"Suggested Safe Message: {corrected_message}")
        save_message(message, "Spam")
    else:
        st.success("✅ This message is SAFE!")
        save_message(message, "Safe")

# Voice Input
st.subheader("🎙️ Voice Input")
if st.button("🎤 Speak Now"):
    spoken_message = recognize_speech()
    if spoken_message:
        st.success(f"You said: {spoken_message}")
        if is_spam(spoken_message):
            st.error("⚠️ This message is likely SPAM!")
        else:
            st.success("✅ This message is SAFE!")

# Spam History
st.subheader("📜 Spam History")
if st.button("🔄 Load History"):
    if pd.io.common.file_exists(HISTORY_FILE):
        history = pd.read_csv(HISTORY_FILE)
        st.dataframe(history)
    else:
        st.warning("No history available.")

# Export Report
st.subheader("📄 Export Report")
if pd.io.common.file_exists(HISTORY_FILE):
    csv_data = pd.read_csv(HISTORY_FILE).to_csv(index=False).encode("utf-8")
    st.download_button(label="📥 Download CSV", data=csv_data, file_name="spam_report.csv", mime="text/csv")

    pdf_file = generate_pdf()
    if pdf_file:
        with open(pdf_file, "rb") as f:
            st.download_button(label="📥 Download PDF", data=f, file_name="spam_report.pdf", mime="application/pdf")
else:
    st.warning("No report available. Run some spam checks first.")
