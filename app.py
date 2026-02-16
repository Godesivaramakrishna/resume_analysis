from flask import Flask, request, render_template, jsonify
import joblib
import os
import tempfile
from PyPDF2 import PdfReader
from docx import Document
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Environment-agnostic configuration
# Use environment variables with fallback defaults
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16MB default
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Upload folder configuration - works in any environment
# Use temp directory if uploads folder can't be created (some cloud platforms have read-only filesystems)
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    logger.info(f"Upload folder set to: {UPLOAD_FOLDER}")
except (PermissionError, OSError) as e:
    # Fallback to system temp directory for read-only filesystems
    app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()
    logger.warning(f"Could not create upload folder, using temp directory: {app.config['UPLOAD_FOLDER']}")

# Load model files with error handling
try:
    MODEL_PATH = os.environ.get("MODEL_PATH", "job_role_model.pkl")
    VECTORIZER_PATH = os.environ.get("VECTORIZER_PATH", "vectorizer.pkl")
    
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    logger.info("Model and vectorizer loaded successfully")
except Exception as e:
    logger.error(f"Error loading model files: {e}")
    raise

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

# Function to validate if document is a resume
def is_resume(text):
    """
    Validates if the extracted text appears to be from a resume.
    Checks for common resume keywords and sections.
    """
    text_lower = text.lower()
    
    # Common resume keywords and sections
    resume_keywords = [
        'experience', 'education', 'skills', 'work experience',
        'employment', 'qualification', 'professional', 'career',
        'objective', 'summary', 'projects', 'certifications',
        'achievements', 'responsibilities', 'duties', 'resume',
        'cv', 'curriculum vitae', 'profile', 'expertise',
        'accomplishments', 'training', 'languages', 'references'
    ]
    
    # Count how many resume keywords are found
    keyword_count = sum(1 for keyword in resume_keywords if keyword in text_lower)
    
    # Check minimum text length (resumes should have substantial content)
    min_length = 100
    
    # Validation criteria:
    # 1. Text should be at least 100 characters
    # 2. Should contain at least 3 resume-related keywords
    if len(text) < min_length:
        return False, "Document is too short to be a resume. Please upload a complete resume."
    
    if keyword_count < 3:
        return False, "This document doesn't appear to be a resume. Please upload a valid resume containing sections like Experience, Education, Skills, etc."
    
    return True, "Valid resume detected"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health_check():
    """Health check endpoint for cloud platforms and load balancers"""
    return jsonify({
        "status": "healthy",
        "service": "resume-analyzer",
        "model_loaded": model is not None,
        "vectorizer_loaded": vectorizer is not None
    }), 200

@app.route("/predict", methods=["POST"])
def predict():
    file_path = None
    try:
        # Validate file upload
        if "resume" not in request.files:
            logger.warning("No file part in request")
            return "No file uploaded", 400
        
        file = request.files["resume"]
        
        if file.filename == "":
            logger.warning("Empty filename received")
            return "No file selected", 400
        
        # Validate file extension
        allowed_extensions = {".pdf", ".docx"}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            logger.warning(f"Unsupported file format: {file_ext}")
            return f"Unsupported file format. Please upload PDF or DOCX files.", 400
        
        # Create secure filename and save
        import uuid
        safe_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_filename)
        file.save(file_path)
        logger.info(f"File saved: {safe_filename}")
        
        # Extract text based on file type
        if file_ext == ".pdf":
            text = extract_text_from_pdf(file_path)
        elif file_ext == ".docx":
            text = extract_text_from_docx(file_path)
        
        # Validate extracted text
        if not text or len(text.strip()) < 10:
            logger.warning("Insufficient text extracted from file")
            return "Could not extract enough text from the resume. Please ensure the file is not empty or corrupted.", 400
        
        logger.info(f"Extracted {len(text)} characters from document")
        
        # Validate if document is actually a resume
        is_valid_resume, validation_message = is_resume(text)
        if not is_valid_resume:
            logger.warning(f"Non-resume document detected: {validation_message}")
            return f"⚠️ {validation_message}", 400
        
        logger.info("Resume validation passed")
        
        # Transform text and predict
        input_vector = vectorizer.transform([text])
        decision_scores = model.decision_function(input_vector)
        
        # Get top 3 predictions
        top_indices = decision_scores[0].argsort()[-3:][::-1]
        top_roles = model.classes_[top_indices]
        
        logger.info(f"Prediction successful: {top_roles[0]}")
        
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        return f"An error occurred while processing your resume. Please try again.", 500
    
    finally:
        # Always delete the uploaded file after processing
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"✅ Deleted uploaded file: {safe_filename}")
            except Exception as e:
                logger.error(f"Error deleting file: {e}")

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
    # Get configuration from environment variables with sensible defaults
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")  # Default to 0.0.0.0 for cloud compatibility
    
    # Detect environment - check multiple cloud platform indicators
    is_production = (
        # Generic production indicators
        os.environ.get("FLASK_ENV") == "production" or
        os.environ.get("ENV") == "production" or
        os.environ.get("ENVIRONMENT") == "production" or
        os.environ.get("PRODUCTION") == "true" or
        
        # Cloud platform specific indicators
        os.environ.get("RENDER") or  # Render
        os.environ.get("RAILWAY_ENVIRONMENT") or  # Railway
        os.environ.get("HEROKU") or  # Heroku
        os.environ.get("DYNO") or  # Heroku dyno
        
        # AWS indicators
        os.environ.get("AWS_EXECUTION_ENV") or  # AWS Lambda/ECS
        os.environ.get("AWS_REGION") or  # AWS general
        os.environ.get("EC2_INSTANCE_ID") or  # AWS EC2
        
        # Google Cloud indicators
        os.environ.get("GAE_ENV") or  # Google App Engine
        os.environ.get("GOOGLE_CLOUD_PROJECT") or  # GCP general
        os.environ.get("K_SERVICE") or  # Google Cloud Run
        
        # Azure indicators
        os.environ.get("WEBSITE_INSTANCE_ID") or  # Azure App Service
        os.environ.get("AZURE_FUNCTIONS_ENVIRONMENT") or  # Azure Functions
        
        # Container/Kubernetes indicators
        os.environ.get("KUBERNETES_SERVICE_HOST") or  # Kubernetes
        os.environ.get("CONTAINER_NAME")  # Generic container
    )
    
    # Determine debug mode
    debug_mode = os.environ.get("DEBUG", "False").lower() == "true" and not is_production
    
    # Log startup information
    logger.info(f"="*50)
    logger.info(f"Starting Resume Analyzer Application")
    logger.info(f"Environment: {'Production' if is_production else 'Development'}")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Debug Mode: {debug_mode}")
    logger.info(f"Upload Folder: {app.config['UPLOAD_FOLDER']}")
    logger.info(f"="*50)
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        threaded=True  # Enable threading for better performance
    )
