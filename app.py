import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import re

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_repsonse(input):
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(input)
    return response.text

def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text
 
input_prompt = """
ROLE:
You are an expert with year of experience in writing resume and finding shortfalls in a resume. You are also
very also an expert in ATS (Application Tracking System) with a deep understanding of business analysis, process improvement, business transformation, data science ,data analysis
and Artificial intelligence.
TASK:
- Your task is to evaluate the resume based on the given job description.
- Assign a percentage match score based on the job description.
- Identify missing or weak keywords from the job description.
- Provide a profile summary.
- Suggest clear, actionable recommendations on how the resume can be improved to score more than 90%.
- Rewrite the resume to improve ATS score based on the job description and suggestions.
- Provide the rewritten resume in a professional format.
resume: {text}
description: {job_description}
 
INPUT:
You will be given a resume and a job description. Use the following format to provide your response
```json
{{
  "Job Description Match": "percentage",
  "MissingKeywords": ["keyword1", "keyword2"],
  "Profile Summary": "summary text",
  "ImprovementSuggestions": [
    "suggestion 1",
    "suggestion 2",
    "suggestion 3"
  ]
}}
```
Output:
Return the response in the following JSON format:
```json
{{
  "Job Description Match": "percentage",
  "MissingKeywords": ["keyword1", "keyword2"],
  "Profile Summary": "summary text",
  "ImprovementSuggestions": [
    "suggestion 1",
    "suggestion 2",
    "suggestion 3"
  ]
}}
```

"""

resume_imp_prompt = """
ROLE:
You are an expert with year of experience in writing resume and finding shortfalls in a resume. You are also
very also an expert in ATS (Application Tracking System) with a deep understanding of business analysis, process improvement, business transformation, data science ,data analysis
and Artificial intelligence.
TASK:
- Your task is to improve the candidate's resume based on the following:
    1. The original resume.
    2. The job description.
    3. The improvement suggestions.
- Analyze the job description and identify key skills, qualifications, and keywords that are essential for the role.
- Identify gaps in the original resume based on the job description and improvement suggestions.
- Rewrite the resume to ensure it is highly relevant to the job description, includes all suggested keywords and improves clarity, impact, and formatting.
- Ensure the rewritten resume is professional, structured, and ATS-friendly.
**Original Resume:**
{text}
**Job Description:**
{job_description}
**Improvement Suggestions:**
{suggestions}
 
Provide the improved resume as a properly formatted plain text resume (not JSON or markdown).
"""

## streamlit app
st.title("## 🚀 Smart Application Tracking System and Resume Optimizer")
st.markdown("#### 🎯 Developed by モヒット")
st.markdown("""
This application uses your resume and the job description you are interested to apply to analyze and provide insights on how well your resume matches against the role.
It also provides suggestions on how to improve your resume to increase your chances of passing the ATS (Applicant Tracking System) used by many companies.
Based on the information provided, the application will generate a score indicating how well your resume matches the job description and also rebuild your resume to align with the job description.
""")
st.markdown("### Instructions")
st.markdown("""
1. **Paste the job description** in the text area below.
2. **Upload your Resume** in PDF format.
3. Click **Submit** to get your ATS score and recommendations.
""")

job_description = st.text_area("📌 Paste the Job Description", height=300)
resume_input_mode = st.radio(
    "How would you like to input your resume?",
    ("Paste Resume Text", "Upload Resume PDF")
)

resume_text = ""
uploaded_file = None

if resume_input_mode == "Paste Resume Text":
    resume_text = st.text_area("📋Paste your resume here", height=300)
elif resume_input_mode == "Upload Resume PDF":
    uploaded_file = st.file_uploader("📄 Upload Your Resume (PDF)", type="pdf")

submit = st.button("🚀 Submit and Analyze")

if submit:
    if not job_description.strip():
        st.warning("Please paste the job description.")
        st.stop()
    
    # Get resume text based on input mode
    if resume_input_mode == "Paste Resume Text":
        if not resume_text.strip():
            st.warning("Please paste your resume text.")
            st.stop()
        text = resume_text
    elif resume_input_mode == "Upload Resume PDF":
        if uploaded_file is None:
            st.warning("Please upload your resume PDF.")
            st.stop()
        text = input_pdf_text(uploaded_file)
    
    # Format prompt
    filled_prompt = input_prompt.format(text=text, job_description=job_description)
    
    # Get LLM response
    with st.spinner("🤖 Analyzing your resume..."):
        response = get_gemini_repsonse(filled_prompt)
    
    # Parse JSON from model response
    try:
        json_str = re.search(r"\{.*\}", response, re.DOTALL).group()
        result = json.loads(json_str)
    except Exception as e:
        st.error(f"Couldn't parse LLM response: {str(e)}")
        st.code(response)
        st.stop()
    
    # Show results
    jd_match = result.get("Job Description Match", "N/A")
    st.markdown(f"### ✅ Resume Match to Job Description is **{jd_match}**")
    
    st.subheader("🧩 Missing Keywords")
    keywords = result.get("MissingKeywords", [])
    if keywords:
        col1, col2 = st.columns(2)
        half = (len(keywords) + 1) // 2
        with col1:
            for kw in keywords[:half]:
                st.markdown(f"- {kw}")
        with col2:
            for kw in keywords[half:]:
                st.markdown(f"- {kw}")
    else:
        st.write("No missing keywords identified.")
    
    st.subheader("👤 Profile Summary")
    st.write(result.get("Profile Summary", "Not available"))
    
    # Improvement suggestions + rewrite resume
    try:
        jd_score = int(result.get("Job Description Match", "0").replace("%", "").strip())
    except ValueError:
        jd_score = 0
    
    if jd_score < 90:
        st.warning("Your Job Description Match is below 90%.")
        st.subheader("Recommendations to improve your resume:")
        suggestions = result.get("ImprovementSuggestions", [])
        for s in suggestions:
            st.markdown(f"- {s}")
        
        # Rewrite prompt
        suggestions_text = "\n".join(suggestions)
        rewrite_filled_prompt = resume_imp_prompt.format(
            text=text,
            job_description=job_description,
            suggestions=suggestions_text
        )
        
        with st.spinner("✍️ Generating optimized resume..."):
            rewritten_resume = get_gemini_repsonse(rewrite_filled_prompt)
        
        rewritten_resume = rewritten_resume.replace("**", "")
        rewritten_resume = re.sub(r"(?i)^okay.*?resume.*?\n+", "", rewritten_resume).strip()

        st.subheader("📄 Optimized Resume Inline With The Job Description")
        st.markdown(rewritten_resume)
        
    else:
        st.warning("Please upload a resume and paste the job description.")   
  

     