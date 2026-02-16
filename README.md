# 🎯 AI Resume Analyzer

An intelligent resume analysis tool powered by Machine Learning that predicts the top 3 most suitable job roles based on resume content.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- 🤖 **AI-Powered Analysis** - Uses scikit-learn ML model for accurate predictions
- 📊 **Top 3 Job Roles** - Shows best matching positions with confidence scores
- 📄 **Multiple Formats** - Supports PDF and DOCX resume uploads
- 🎨 **Modern UI/UX** - Beautiful gradient design with smooth animations
- 🗑️ **Auto Cleanup** - Automatically deletes uploaded files for privacy
- 🐳 **Docker Ready** - Easy deployment with Docker/Docker Compose
- ☁️ **Cloud Ready** - Deploy to AWS, GCP, Azure, or Heroku

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/Godesivaramakrishna/resume_analysis.git
cd resume_analysis

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Visit: **http://localhost:5000**

### Docker Deployment

```bash
# Using Docker
docker build -t resume-analyzer .
docker run -p 5000:5000 resume-analyzer

# Using Docker Compose (Recommended)
docker-compose up -d
```

## 📁 Project Structure

```
resume_analyser/
├── app.py                    # Flask application
├── job_role_model.pkl        # Trained ML model
├── vectorizer.pkl            # TF-IDF vectorizer
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── .dockerignore           # Docker ignore rules
├── templates/
│   └── index.html          # Frontend UI
└── uploads/                # Temporary file storage
```

## 🎨 Screenshots

### Upload Page
Modern gradient UI with drag-and-drop file upload

### Results Page
Beautiful cards showing top 3 job role predictions with color-coded rankings

## 🛠️ Technologies Used

- **Backend**: Flask (Python)
- **ML Model**: scikit-learn (SVM with TF-IDF)
- **Frontend**: HTML, CSS, JavaScript
- **File Processing**: PyPDF2, python-docx
- **Deployment**: Docker, Docker Compose

## 📊 Supported Job Roles

The model can predict various tech roles including:
- Data Scientist
- Data Engineer
- Software Engineer
- Web Developer
- DevOps Engineer
- Cloud Engineer
- SEO Specialist
- And more...

## 🔒 Security Features

- ✅ File type validation (PDF, DOCX only)
- ✅ File size limit (16MB max)
- ✅ Automatic file deletion after analysis
- ✅ No data persistence
- ✅ Privacy-first design

## 🌐 Cloud Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guides for:
- AWS EC2
- Google Cloud Run
- Azure Container Instances
- Heroku

## 📝 API Endpoints

### `GET /`
Returns the upload page

### `POST /predict`
Analyzes resume and returns predictions

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: `resume` (file)

**Response:**
HTML page with top 3 job role predictions

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 👤 Author

**Gode Sivaramakrishna**
- GitHub: [@Godesivaramakrishna](https://github.com/Godesivaramakrishna)

## 🙏 Acknowledgments

- Built with Flask and scikit-learn
- UI inspired by modern web design trends
- Docker support for easy deployment

---

⭐ If you find this project useful, please consider giving it a star!
