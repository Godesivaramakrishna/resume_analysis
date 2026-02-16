from flask import Flask, request, render_template
import joblib
import os
from PyPDF2 import PdfReader
from docx import Document

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Load model
model = joblib.load("job_role_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text
    return text

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    file = request.files["resume"]

    if file.filename == "":
        return "No file selected"

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    try:
        # Extract text
        if file.filename.endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
        elif file.filename.endswith(".docx"):
            text = extract_text_from_docx(file_path)
        else:
            return "Unsupported file format"

        # Transform text
        input_vector = vectorizer.transform([text])

        # Get decision scores
        decision_scores = model.decision_function(input_vector)

        # Get top 3 predictions
        top_indices = decision_scores[0].argsort()[-3:][::-1]
        top_roles = model.classes_[top_indices]

    finally:
        # Always delete the uploaded file after processing
        # This ensures files are removed even if an error occurs
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Deleted uploaded file: {file.filename}")

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Results - Resume Analyzer</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }}

        body::before,
        body::after {{
            content: '';
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
            animation: float 20s infinite ease-in-out;
        }}

        body::before {{
            width: 400px;
            height: 400px;
            top: -100px;
            left: -100px;
        }}

        body::after {{
            width: 300px;
            height: 300px;
            bottom: -50px;
            right: -50px;
            animation-delay: 5s;
        }}

        @keyframes float {{
            0%, 100% {{ transform: translate(0, 0) scale(1); }}
            50% {{ transform: translate(50px, 50px) scale(1.1); }}
        }}

        .container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 30px;
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.3);
            padding: 60px;
            max-width: 700px;
            width: 100%;
            position: relative;
            z-index: 1;
            animation: slideUp 0.8s ease-out;
        }}

        @keyframes slideUp {{
            from {{
                opacity: 0;
                transform: translateY(50px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .header {{
            text-align: center;
            margin-bottom: 50px;
        }}

        .success-icon {{
            font-size: 5rem;
            margin-bottom: 20px;
            animation: bounce 1s ease-in-out;
        }}

        @keyframes bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-20px); }}
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 15px;
        }}

        .subtitle {{
            color: #64748b;
            font-size: 1.1rem;
            font-weight: 500;
        }}

        .results-section {{
            margin: 40px 0;
        }}

        .role-card {{
            background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            animation: fadeIn 0.6s ease-out;
            animation-fill-mode: both;
        }}

        .role-card:nth-child(1) {{
            animation-delay: 0.1s;
            border-left: 6px solid #10b981;
        }}

        .role-card:nth-child(2) {{
            animation-delay: 0.2s;
            border-left: 6px solid #3b82f6;
        }}

        .role-card:nth-child(3) {{
            animation-delay: 0.3s;
            border-left: 6px solid #8b5cf6;
        }}

        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateX(-30px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}

        .role-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
        }}

        .role-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
            opacity: 0;
            transition: opacity 0.4s ease;
        }}

        .role-card:hover::before {{
            opacity: 1;
        }}

        .rank-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            font-size: 1.5rem;
            font-weight: 800;
            margin-bottom: 15px;
            position: relative;
            z-index: 1;
        }}

        .role-card:nth-child(1) .rank-badge {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            box-shadow: 0 5px 15px rgba(16, 185, 129, 0.4);
        }}

        .role-card:nth-child(2) .rank-badge {{
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4);
        }}

        .role-card:nth-child(3) .rank-badge {{
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            color: white;
            box-shadow: 0 5px 15px rgba(139, 92, 246, 0.4);
        }}

        .role-title {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 10px;
            position: relative;
            z-index: 1;
        }}

        .role-label {{
            color: #64748b;
            font-size: 0.9rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            z-index: 1;
        }}

        .back-btn {{
            width: 100%;
            padding: 20px;
            margin-top: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 1.2rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            text-decoration: none;
            display: block;
            text-align: center;
        }}

        .back-btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
        }}

        .divider {{
            height: 2px;
            background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
            margin: 30px 0;
        }}

        @media (max-width: 640px) {{
            .container {{
                padding: 40px 25px;
            }}

            h1 {{
                font-size: 2rem;
            }}

            .role-title {{
                font-size: 1.4rem;
            }}

            .role-card {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="success-icon">✨</div>
            <h1>Analysis Complete!</h1>
            <p class="subtitle">Here are your top 3 matching job roles</p>
        </div>

        <div class="results-section">
            <div class="role-card">
                <div class="rank-badge">1</div>
                <div class="role-label">Best Match</div>
                <div class="role-title">{top_roles[0]}</div>
            </div>

            <div class="role-card">
                <div class="rank-badge">2</div>
                <div class="role-label">Second Best</div>
                <div class="role-title">{top_roles[1]}</div>
            </div>

            <div class="role-card">
                <div class="rank-badge">3</div>
                <div class="role-label">Third Best</div>
                <div class="role-title">{top_roles[2]}</div>
            </div>
        </div>

        <div class="divider"></div>

        <a href="/" class="back-btn">🔄 Analyze Another Resume</a>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)
