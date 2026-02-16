# 🐳 Docker Deployment Guide

## Quick Start

### Build and Run with Docker

```bash
# Build the Docker image
docker build -t resume-analyzer .

# Run the container
docker run -p 5000:5000 resume-analyzer
```

Access the application at: **http://localhost:5000**

### Using Docker Compose (Recommended)

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## 📦 What's Included

- **Python 3.11** slim base image
- **All dependencies** installed automatically
- **Model files** (job_role_model.pkl, vectorizer.pkl)
- **Automatic file cleanup** after analysis
- **Port 5000** exposed for web access

## 🚀 Cloud Deployment

### Deploy to AWS (EC2)

```bash
# 1. SSH into your EC2 instance
ssh -i your-key.pem ec2-user@your-instance-ip

# 2. Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start

# 3. Copy your project files
scp -r resume_analyser ec2-user@your-instance-ip:~/

# 4. Build and run
cd resume_analyser
sudo docker build -t resume-analyzer .
sudo docker run -d -p 80:5000 resume-analyzer
```

### Deploy to Google Cloud Run

```bash
# 1. Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/resume-analyzer

# 2. Deploy to Cloud Run
gcloud run deploy resume-analyzer \
  --image gcr.io/YOUR_PROJECT_ID/resume-analyzer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Deploy to Azure Container Instances

```bash
# 1. Create Azure Container Registry
az acr create --resource-group myResourceGroup \
  --name myregistry --sku Basic

# 2. Build and push image
az acr build --registry myregistry \
  --image resume-analyzer:v1 .

# 3. Deploy container
az container create --resource-group myResourceGroup \
  --name resume-analyzer \
  --image myregistry.azurecr.io/resume-analyzer:v1 \
  --dns-name-label resume-analyzer \
  --ports 5000
```

### Deploy to Heroku

```bash
# 1. Login to Heroku
heroku login

# 2. Create app
heroku create your-app-name

# 3. Set stack to container
heroku stack:set container

# 4. Deploy
git push heroku main
```

## 🔧 Environment Variables

You can customize the application with environment variables:

```bash
docker run -p 5000:5000 \
  -e FLASK_ENV=production \
  -e MAX_CONTENT_LENGTH=16777216 \
  resume-analyzer
```

## 📊 Image Size Optimization

Current image uses `python:3.11-slim` for smaller size (~150MB vs 1GB for full Python image)

To further optimize:
```dockerfile
# Use alpine for even smaller size
FROM python:3.11-alpine
```

## 🔒 Security Best Practices

1. **Don't expose port 5000 directly in production** - Use a reverse proxy (nginx)
2. **Use HTTPS** - Set up SSL certificates
3. **Set file size limits** - Already configured (16MB max)
4. **Files are auto-deleted** - Privacy and security built-in

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs
docker logs resume-analyzer

# Check if port is already in use
netstat -ano | findstr :5000  # Windows
lsof -i :5000                 # Linux/Mac
```

### Model files missing
Make sure `job_role_model.pkl` and `vectorizer.pkl` are in the project directory before building.

### Permission errors
```bash
# Run with sudo (Linux)
sudo docker run -p 5000:5000 resume-analyzer
```

## 📝 Notes

- The application runs on port **5000** inside the container
- Files uploaded are **automatically deleted** after analysis
- The container uses **unbuffered Python output** for better logging
- **Restart policy** is set to `unless-stopped` in docker-compose
