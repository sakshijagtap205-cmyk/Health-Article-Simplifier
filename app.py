
import os
import re
import html
import time
import streamlit as st
from dotenv import load_dotenv

# ---------------- CONFIGURATION ----------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(
    page_title="Health Article Simplifier",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- DESIGN ----------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #f3f7fb;
    color: #193449;
}

[data-testid="stSidebar"] {
    background: #102e42;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.hero {
    background: linear-gradient(120deg, #075985, #0891a2);
    padding: 38px;
    border-radius: 20px;
    color: white;
    margin-bottom: 25px;
}

.hero h1 {
    color: white;
    font-size: 36px;
    font-weight: 800;
}

.hero p {
    color: #e0f7fa;
    font-size: 16px;
}

.section-title {
    color: #123b55;
    font-weight: 800;
    font-size: 25px;
}

.feature-card {
    background: white;
    padding: 23px;
    border-radius: 15px;
    min-height: 155px;
    border: 1px solid #e1ebf0;
    box-shadow: 0 4px 15px rgba(20,60,80,0.05);
    margin-bottom: 12px;
}

.feature-card h3 {
    color: #087f8c;
    font-size: 19px;
}

.feature-card p {
    color: #536b7a;
    font-size: 14px;
}

.result-card {
    background: white;
    padding: 25px;
    border-radius: 15px;
    border: 1px solid #dce8ef;
    margin-top: 15px;
}

.stat-card {
    background: white;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #e1ebf0;
    text-align: center;
}

div.stButton > button {
    background: #087f8c;
    color: white;
    border: none;
    border-radius: 9px;
    font-weight: 700;
    min-height: 43px;
}

div.stButton > button:hover {
    background: #075985;
    color: white;
}

div[data-testid="stDownloadButton"] button {
    background: #087f8c;
    color: white;
    border-radius: 9px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------

defaults = {
    "result": "",
    "summary": "",
    "key_points": "",
    "original_article": "",
    "source": "",
    "navigation": "Home"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------- MEDICAL GLOSSARY ----------------

GLOSSARY = {
    "Anemia": "A condition in which the body does not have enough healthy red blood cells.",
    "Blood Pressure": "The force of blood pushing against the walls of blood vessels.",
    "Diabetes": "A condition that causes high blood sugar levels.",
    "Diagnosis": "The process of identifying a disease or health condition.",
    "Hypertension": "Another name for high blood pressure.",
    "Immunity": "The body's ability to fight infections.",
    "Inflammation": "The body's response to injury or infection, often causing swelling.",
    "Infection": "A condition caused by harmful microorganisms entering the body.",
    "Metabolism": "The process by which the body converts food into energy.",
    "Symptoms": "Signs that indicate a possible health problem.",
    "Chronic Disease": "A disease that lasts for a long period.",
    "Cardiovascular": "Related to the heart and blood vessels.",
    "Respiratory": "Related to breathing and the lungs.",
    "Dehydration": "A condition caused by losing more water than the body takes in.",
    "Vaccine": "A substance that helps the immune system protect against disease."
}


# ---------------- AI ENGINE ----------------


def generate_ai_response(article, task, language="English",
                         level="Simple"):

    if not API_KEY:
        return None, "API key missing"

    from google import genai

    client = genai.Client(api_key=API_KEY)

    prompt = f"""
You are an expert medical education assistant.

TASK: {task}
TARGET LANGUAGE: {language}
READING LEVEL: {level}

Instructions:
1. Use simple and understandable language.
2. Preserve all medical facts.
3. Never invent medical information.
4. Do not change medicine names or dosages.
5. Explain difficult medical terms.
6. Use headings and bullet points.
7. Do not diagnose or prescribe treatment.
8. Do not guess unclear information.

ARTICLE:
{article}
"""

    # Automatic model fallback
    models = [
        "gemini-3.8-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite"
    ]

    errors = []

    for model in models:

        for attempt in range(2):

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                if response.text:
                    return response.text, "success"

            except Exception as e:

                error = str(e)
                errors.append(f"{model}: {error}")

                if "503" in error or "UNAVAILABLE" in error:
                    if attempt == 0:
                        time.sleep(3)
                    continue

                if "429" in error or "RESOURCE_EXHAUSTED" in error:
                    if attempt == 0:
                        time.sleep(5)
                    continue

                # Other errors: try the next model
                break

    return None, "All Gemini models are currently unavailable. " + " | ".join(errors)


# ---------------- BASIC OFFLINE ENGINE ----------------

def offline_simplify(article):

    replacements = {
        "hypertension": "high blood pressure",
        "cardiovascular": "related to the heart",
        "inflammation": "swelling or irritation",
        "diagnosis": "identifying a disease",
        "medication": "medicine",
        "approximately": "about",
        "individuals": "people",
        "utilize": "use",
        "commence": "start",
        "terminate": "stop",
        "sufficient": "enough",
        "symptoms": "signs of illness",
        "respiratory": "related to breathing",
        "obtain": "get",
        "administer": "give"
    }

    result = article

    for old, new in replacements.items():
        result = re.sub(
            r"\b" + re.escape(old) + r"\b",
            new,
            result,
            flags=re.IGNORECASE
        )

    return result


# ---------------- SIDEBAR ----------------

st.sidebar.markdown("# 🩺 HealthCare AI")
st.sidebar.caption("Smart Medical Information Assistant")

st.sidebar.markdown("---")

pages = [
    "Home",
    "Article Simplifier",
    "Medical Glossary",
    "About Project"
]

selected_page = st.sidebar.radio(
    "MAIN MENU",
    pages,
    key="navigation"
)

st.sidebar.markdown("---")

st.sidebar.markdown("### Project Information")
st.sidebar.write("AI-Based Health Article Simplification")

st.sidebar.markdown("---")
st.sidebar.caption("Making medical information simple for everyone.")


# ---------------- HOME PAGE ----------------

if selected_page == "Home":

    st.markdown("""
    <div class="hero">
        <h1>🩺 Health Article Simplifier</h1>
        <p>Understand complex medical information with the power of AI.</p>
        <p>Simple language. Better understanding. Smarter healthcare.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Welcome to Your Health Assistant</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Medical articles contain complex terminology that can be difficult "
        "to understand. Our AI-powered platform helps convert medical "
        "information into clear and simple language."
    )

    st.markdown("### Explore Our Features")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📄 Article Simplification</h3>
            <p>Convert complex medical articles into easy language.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🌐 Multiple Languages</h3>
            <p>Read simplified health information in English, Marathi and Hindi.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📚 Medical Glossary</h3>
            <p>Understand difficult medical words with simple explanations.</p>
        </div>
        """, unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown("""
        <div class="feature-card">
            <h3>📝 Smart Summary</h3>
            <p>Get a short summary of lengthy medical articles.</p>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown("""
        <div class="feature-card">
            <h3>💡 Key Points</h3>
            <p>Identify the important information from articles.</p>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown("""
        <div class="feature-card">
            <h3>⬇️ Download</h3>
            <p>Download simplified content for future reference.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### How It Works")

    st.write("""
    1. Select Article Simplifier from the menu.
    2. Paste your medical article.
    3. Select your preferred language.
    4. Choose your reading level.
    5. Click Simplify Article.
    6. Read and download your result.
    """)

    st.info("Get started by selecting Article Simplifier from the sidebar.")


# ---------------- ARTICLE SIMPLIFIER ----------------

elif selected_page == "Article Simplifier":

    st.markdown("""
    <div class="hero">
        <h1>📄 AI Article Simplifier</h1>
        <p>Transform complex medical information into simple explanations.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Enter Your Medical Article")

    article = st.text_area(
        "Paste your article below",
        height=230,
        placeholder="Paste your medical article here..."
    )

    col1, col2 = st.columns(2)

    with col1:
        language = st.selectbox(
            "🌐 Select Language",
            ["English", "Marathi", "Hindi"]
        )

    with col2:
        level = st.selectbox(
            "📖 Reading Level",
            ["Simple", "Very Simple"]
        )

    st.markdown("---")

    if st.button(
        "✨ Simplify My Article",
        use_container_width=True
    ):

        if not article.strip():
            st.warning("Please enter a medical article.")

        elif len(article.strip()) < 30:
            st.warning("Please enter a longer article.")

        else:

            with st.spinner("AI is simplifying your article..."):

                result, status = generate_ai_response(
                    article,
                    "Simplify the medical article.",
                    language,
                    level
                )

                if status == "success":

                    st.session_state.result = result
                    st.session_state.original_article = article
                    st.session_state.source = "Gemini AI"

                else:
                    st.error(f"Gemini API Error: {status}")
                    if language == "English":

                        st.session_state.result = offline_simplify(article)
                        st.session_state.original_article = article
                        st.session_state.source = "Offline basic simplifier"

                        st.warning(
                            "Gemini AI is unavailable. Basic English "
                            "word replacement is being used."
                        )

                    else:

                        st.error(
                            "AI is unavailable. Please configure your "
                            "Gemini API key for Marathi and Hindi output."
                        )

    if st.session_state.result:

        st.markdown("---")
        st.markdown("## ✅ Simplified Article")

        st.caption("Generated using: " + st.session_state.source)

        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown(st.session_state.result)
        st.markdown('</div>', unsafe_allow_html=True)

        st.download_button(
            "⬇️ Download Simplified Article",
            data=st.session_state.result,
            file_name="health_simplified_article.txt",
            mime="text/plain",
            use_container_width=True
        )

        st.markdown("---")

        st.markdown("### 📝 Generate Article Summary")

        if st.button("Generate Summary", use_container_width=True):

            with st.spinner("Creating summary..."):

                summary, status = generate_ai_response(
                    st.session_state.original_article,
                    "Create a concise summary of the article.",
                    language,
                    level
                )

                if status == "success":
                    st.session_state.summary = summary
                else:
                    st.error("Summary generation failed. Check your API key.")

        if st.session_state.summary:

            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown(st.session_state.summary)
            st.markdown('</div>', unsafe_allow_html=True)

            st.download_button(
                "⬇️ Download Summary",
                data=st.session_state.summary,
                file_name="health_article_summary.txt",
                mime="text/plain"
            )

        st.markdown("---")

        st.markdown("### 💡 Extract Important Key Points")

        if st.button("Generate Key Points", use_container_width=True):

            with st.spinner("Extracting key points..."):

                points, status = generate_ai_response(
                    st.session_state.original_article,
                    "Extract 5 to 8 important key points from this article.",
                    language,
                    level
                )

                if status == "success":
                    st.session_state.key_points = points
                else:
                    st.error("Key point generation failed. Check your API key.")

        if st.session_state.key_points:

            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown(st.session_state.key_points)
            st.markdown('</div>', unsafe_allow_html=True)

            st.download_button(
                "⬇️ Download Key Points",
                data=st.session_state.key_points,
                file_name="health_key_points.txt",
                mime="text/plain"
            )

        if st.button("🗑️ Clear All Results"):

            for key in ["result", "summary", "key_points",
                        "original_article", "source"]:
                st.session_state[key] = ""

            st.rerun()


# ---------------- MEDICAL GLOSSARY ----------------

elif selected_page == "Medical Glossary":

    st.markdown("""
    <div class="hero">
        <h1>📚 Medical Glossary</h1>
        <p>Learn medical terminology in simple words.</p>
    </div>
    """, unsafe_allow_html=True)

    search = st.text_input(
        "🔍 Search Medical Terms",
        placeholder="Search diabetes, anemia, immunity..."
    )

    matches = 0

    for term, meaning in GLOSSARY.items():

        if (
            search.lower() in term.lower()
            or search.lower() in meaning.lower()
        ):

            matches += 1

            st.markdown(
                f"""
                <div class="feature-card">
                    <h3>{html.escape(term)}</h3>
                    <p>{html.escape(meaning)}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    if matches == 0:
        st.warning("No matching medical term found.")


# ---------------- ABOUT PROJECT ----------------

elif selected_page == "About Project":

    st.markdown("""
    <div class="hero">
        <h1>ℹ️ About Our Project</h1>
        <p>AI-Based Health Article Simplifier</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## Project Overview")

    st.write("""
    Health Article Simplifier is an AI-powered educational application
    developed using Python and Streamlit.

    The main purpose of this project is to make complex medical
    information understandable for ordinary users.

    Users can paste medical articles and convert them into simple
    explanations using AI technology.
    """)

    st.markdown("## Technologies Used")

    technologies = [
        "Python",
        "Streamlit",
        "Google Gemini AI",
        "Natural Language Processing",
        "Regular Expressions",
        "Python Dotenv"
    ]

    for tech in technologies:
        st.markdown(f"- {tech}")

    st.markdown("## Project Objectives")

    st.write("""
    - Simplify complex medical information.
    - Improve health information accessibility.
    - Support multiple languages.
    - Explain medical terminology.
    - Generate summaries and key points.
    """)

    st.markdown("## Disclaimer")

    st.warning("""
    This application is developed for educational purposes.
    It does not replace doctors, professional medical advice,
    diagnosis or treatment. Always consult a qualified healthcare
    professional for medical decisions.
    """)


# ---------------- FOOTER ----------------

st.markdown("---")

st.markdown(
    """
    <div style="text-align:center; color:#607d8b; padding:15px;">
        <b>🩺 Health Article Simplifier</b><br>
        AI-Powered Healthcare Education Platform<br>
        <small>Mini Project | Built with Python and Streamlit</small>
    </div>
    """,
    unsafe_allow_html=True
)
