
import streamlit as st
import pdfplumber
import os
import pandas as pd
import re
import altair as alt

# Define scoring weights (adjusted for experience)
WEIGHTS = {
    "experience": 2,
    "adtech": 2,
    "java": 2,
    "rtb": 1,
    "leadership": 1.5,
    "ci_cd": 0.5,
    "nosql": 1,
    "scalable": 1,
    "olap": 0.5,
    "cloud": 0.5,
    "bonus": 0.5,
}

# Define keywords for evaluation
KEYWORDS = {
    "adtech": ["dsp", "ssp", "ad exchange", "adtech"],
    "java": ["java"],
    "rtb": ["real-time bidding", "openrtb", "rtb"],
    "leadership": ["led team", "team lead", "engineering manager", "tech lead", "led backend"],
    "ci_cd": ["ci/cd", "jenkins", "github actions", "pipeline"],
    "nosql": ["mongodb", "dynamodb", "cassandra", "aerospike"],
    "scalable": ["scalable", "distributed", "horizontal scalability", "microservices"],
    "olap": ["clickhouse", "aerospike"],
    "cloud": ["aws", "ec2", "s3", "gcp", "azure"],
    "bonus": ["node.js", "docker", "kubernetes", "etl", "parquet"],
}

# Extract text from PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.lower()

# Estimate years of experience
def extract_years_of_experience(text):
    matches = re.findall(r'(\d{1,2})\+?\s+years? of experience', text)
    if matches:
        years = max(int(m) for m in matches)
        return years
    return 0

# Scoring function
def score_cv(text):
    results = {}
    missing = []

    # Experience check
    years_exp = extract_years_of_experience(text)
    results["experience"] = WEIGHTS["experience"] if years_exp >= 7 else 0
    if years_exp < 7:
        missing.append("experience")

    for key, keywords in KEYWORDS.items():
        found = any(k in text for k in keywords)
        score = WEIGHTS[key] if found else 0
        results[key] = score if key != "bonus" else (0.5 if found else 0)
        if not found and key != "bonus":
            missing.append(key)

    total_score = round(sum(results.values()), 2)

    # Tagging logic
    if total_score >= 8:
        tag = "✅ Interview"
    elif total_score >= 6:
        tag = "🤔 Maybe"
    else:
        tag = "❌ Reject"

    return total_score, results, missing, tag, years_exp

# Streamlit App
st.title("🧠 CV Screening AI Agent")
st.markdown("Upload candidate CVs in PDF format and get scored based on your Lead Backend Engineer criteria.")

uploaded_files = st.file_uploader("Upload PDF CVs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    data = []
    for file in uploaded_files:
        text = extract_text_from_pdf(file)
        score, breakdown, missing, tag, years_exp = score_cv(text)
        data.append({
            "Candidate": file.name,
            "Score (out of 10)": score,
            "Tag": tag,
            "Years of Experience": years_exp,
            "Missing Must-Haves": ", ".join(missing) if missing else "None",
            **breakdown
        })

    df = pd.DataFrame(data)
    st.success("Scoring Complete!")
    st.dataframe(df)

    # Bar chart summary
    chart_data = df[["Candidate", "Score (out of 10)"]]
    bar_chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("Score (out of 10):Q", scale=alt.Scale(domain=[0, 10])),
        y=alt.Y("Candidate:N", sort='-x'),
        color=alt.value("#4CAF50")
    ).properties(height=400, title="Candidate Score Overview")
    st.altair_chart(bar_chart, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Results as CSV", data=csv, file_name="cv_scores.csv", mime="text/csv")
