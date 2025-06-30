import streamlit as st
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import AzureChatOpenAI

# ----------------- CONFIG -----------------
AZURE_API_KEY = "EsPiRoXPamifGbSbz2htceK2mFtKOC2RHQ2NMz6vIU5d2Jc5i02fJQQJ99BFACHYHv6XJ3w3AAAAACOG4fY9"
AZURE_DEPLOYMENT_NAME = "gpt-4o"
AZURE_ENDPOINT = "https://diyaj-mblu6wtj-eastus2.cognitiveservices.azure.com"
AZURE_API_VERSION = "2025-01-01-preview"
# -----------------------------------------

# --- Utility Functions ---
def extract_text_from_pdf(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    return "\n".join([p.page_content for p in pages])

def score_resume(llm, jd_text, resume_text):
    prompt = f"""
You are an AI recruiter. Score the following resume against the given job description.

Job Description:
\"\"\"
{jd_text}
\"\"\"

Resume:
\"\"\"
{resume_text}
\"\"\"

Only respond with a relevance score from 0 to 100.
"""
    response = llm.invoke(prompt)
    try:
        return int("".join(filter(str.isdigit, response.content)))
    except:
        return 0

# --- Streamlit UI ---
st.set_page_config(page_title="Resume Ranker", layout="centered")
st.title("📄 Resume Ranker with Azure OpenAI")
st.markdown("Upload a **Job Description** and up to **10 resumes**. The app will rank them based on relevance using an LLM.")

jd_file = st.file_uploader("📌 Upload Job Description PDF", type=["pdf"])
resume_files = st.file_uploader("👤 Upload Resume PDFs", type=["pdf"], accept_multiple_files=True)

if jd_file and resume_files:
    if jd_file.size == 0:
        st.error("❌ Uploaded Job Description file is empty. Please upload a valid PDF.")
        st.stop()

    # Load Job Description
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as jd_temp:
        jd_temp.write(jd_file.read())
        jd_temp.flush()
        jd_text = extract_text_from_pdf(jd_temp.name)

    # Load Resumes
    resumes = []
    for rfile in resume_files:
        if rfile.size == 0:
            st.warning(f"⚠️ Skipping empty file: {rfile.name}")
            continue
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as res_temp:
            res_temp.write(rfile.read())
            res_temp.flush()
            res_text = extract_text_from_pdf(res_temp.name)
            resumes.append((rfile.name, res_text))

    if not resumes:
        st.error("❌ All uploaded resumes were empty. Please upload valid resume PDFs.")
        st.stop()

    st.info("🔍 Scoring resumes. Please wait...")

    # Azure OpenAI setup
    llm = AzureChatOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        openai_api_key=AZURE_API_KEY,
        deployment_name=AZURE_DEPLOYMENT_NAME,
        openai_api_version=AZURE_API_VERSION
    )

    results = []
    for name, text in resumes:
        score = score_resume(llm, jd_text, text)
        results.append((name, score))

    ranked = sorted(results, key=lambda x: x[1], reverse=True)

    st.success("✅ Resumes ranked successfully!")
    st.subheader("🏆 Ranked Resumes")

    for i, (name, score) in enumerate(ranked, 1):
        st.markdown(f"**{i}. {name}** — Score: `{score}/100`")
