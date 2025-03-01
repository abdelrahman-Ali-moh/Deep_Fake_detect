import os
import cv2
import numpy as np
from flask import Flask, render_template_string, request, redirect, Response, url_for, session
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from werkzeug.utils import secure_filename
import requests
import os

os.makedirs("models", exist_ok=True)
# MediaFire direct download link (replace with your actual link)
MEDIAFIRE_URL = "https://www.mediafire.com/file/boqwvnp8fgon05e/deepfake_model.h5/file"

# Folder to store the model
MODEL_PATH = "models/model.h5"

# Function to download the model if it doesn't exist
def download_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading model...")
        response = requests.get(MEDIAFIRE_URL, stream=True)
        if response.status_code == 200:
            with open(MODEL_PATH, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print("Model downloaded successfully.")
        else:
            print("Failed to download model.")
    else:
        print("Model already exists.")

# Call the function before loading the model
download_model()



# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load the model in Flask
from tensorflow.keras.models import load_model
model = load_model(MODEL_PATH)

# Configure upload settings
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "avif", "jpg", "jpeg", "mp4"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def predict_image(image_path):
    """Predict if image is real or fake"""
    img = cv2.imread(image_path)
    img = cv2.resize(img, (224, 224))
    img = img_to_array(img) / 255.0
    img = np.expand_dims(img, axis=0)

    prediction = model.predict(img)[0][0]
    return "Fake" if prediction > 0.5 else "Real"

def predict_video(video_path):
    """Analyze video frame by frame"""
    cap = cv2.VideoCapture(video_path)
    frame_count, fake_count = 0, 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        img = cv2.resize(frame, (224, 224))
        img = img_to_array(img) / 255.0
        img = np.expand_dims(img, axis=0)

        prediction = model.predict(img)[0][0]
        if prediction > 0.5:
            fake_count += 1

    cap.release()
    
    percentage_fake = (fake_count / frame_count) * 100
    return f"{percentage_fake:.2f}% of the video is fake"

def detect_live():
    """Live video stream detection"""
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        img = cv2.resize(frame, (224, 224))
        img = img_to_array(img) / 255.0
        img = np.expand_dims(img, axis=0)

        prediction = model.predict(img)[0][0]
        label = "Fake" if prediction > 0.5 else "Real"

        cv2.putText(frame, label, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        _, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

    cap.release()

# Login Page
@app.route("/", methods=["GET", "POST"])
def login():
    login_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Deepfake Detection - Login</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
            }
            .login-card {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                max-width: 400px;
                margin: auto;
            }
            .form-control:focus {
                border-color: #667eea;
                box-shadow: none;
            }
            .btn-primary {
                background: #667eea;
                border: none;
                width: 100%;
                padding: 12px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="login-card p-4">
                <h2 class="text-center mb-4"><i class="fas fa-shield-alt"></i> Deepfake Detection</h2>
                {% if error %}
                    <div class="alert alert-danger">{{ error }}</div>
                {% endif %}
                <form method="POST">
                    <div class="mb-3">
                        <input type="text" name="username" class="form-control form-control-lg" placeholder="Username" required>
                    </div>
                    <div class="mb-3">
                        <input type="password" name="password" class="form-control form-control-lg" placeholder="Password" required>
                    </div>
                    <button type="submit" class="btn btn-primary btn-lg">
                        <i class="fas fa-sign-in-alt"></i> Login
                    </button>
                </form>
            </div>
        </div>
    </body>
    </html>
    '''
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "admin":
            session['user'] = username
            return redirect(url_for("home"))
        else:
            return render_template_string(login_template, error="Invalid credentials")
    return render_template_string(login_template)

# Main Dashboard
@app.route("/home")
def home():
    if 'user' not in session:
        return redirect(url_for("login"))

    home_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Deepfake Detection System</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {
                background: #f8f9fa;
                min-height: 100vh;
            }
            .dashboard-card {
                background: white;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s;
                height: 100%;
            }
            .dashboard-card:hover {
                transform: translateY(-5px);
            }
            .card-icon {
                font-size: 2.5rem;
                color: #667eea;
                margin-bottom: 1rem;
            }
        </style>
    </head>
    <body>
        <div class="container py-5">
            <div class="text-center mb-5">
                <h1 class="display-4 mb-3"><i class="fas fa-robot"></i> Deepfake Detection</h1>
                <p class="lead">Analyze media files for potential deepfake content</p>
            </div>
            
            <div class="row g-4">
                <div class="col-md-4">
                    <div class="dashboard-card p-4 text-center">
                        <i class="fas fa-image card-icon"></i>
                        <h3>Image Analysis</h3>
                        <form action="/upload-image" method="post" enctype="multipart/form-data">
                            <input type="file" name="file" class="form-control mb-3" required>
                            <button type="submit" class="btn btn-outline-primary">
                                <i class="fas fa-search"></i> Analyze Image
                            </button>
                        </form>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="dashboard-card p-4 text-center">
                        <i class="fas fa-video card-icon"></i>
                        <h3>Video Analysis</h3>
                        <form action="/upload-video" method="post" enctype="multipart/form-data">
                            <input type="file" name="file" class="form-control mb-3" required>
                            <button type="submit" class="btn btn-outline-danger">
                                <i class="fas fa-film"></i> Analyze Video
                            </button>
                        </form>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="dashboard-card p-4 text-center">
                        <i class="fas fa-camera card-icon"></i>
                        <h3>Live Detection</h3>
                        <p class="text-muted mb-3">Real-time webcam analysis</p>
                        <a href="/live-video" class="btn btn-outline-success">
                            <i class="fas fa-play"></i> Start Camera
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="text-center mt-5">
                <a href="/logout" class="btn btn-secondary">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </a>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(home_template)

# Results Pages
# Results Pages - Updated Design
@app.route("/upload-image", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return redirect(url_for("home"))

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return redirect(url_for("home"))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    result = predict_image(filepath)
    icon = "fa-times-circle text-danger" if result == "Fake" else "fa-check-circle text-success"
    
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Analysis Result</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .result-card {{
                background: white;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
                max-width: 700px;
                margin: 2rem auto;
                padding: 2rem;
            }}
            .result-icon {{
                font-size: 4rem;
                margin-bottom: 1.5rem;
                animation: fadeIn 0.5s ease-in;
            }}
            .analysis-image {{
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                max-height: 500px;
                object-fit: contain;
                transition: transform 0.3s ease;
            }}
            .analysis-image:hover {{
                transform: scale(1.02);
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
        </style>
    </head>
    <body style="background: #f8f9fa;">
        <div class="result-card">
            <div class="text-center">
                <i class="fas {icon} result-icon"></i>
                <h2 class="mb-4">Image Analysis Result</h2>
                
                <div class="alert { 'alert-danger' if result == 'Fake' else 'alert-success' } 
                    rounded-pill p-3 mb-4" style="font-size: 1.25rem">
                    <strong>Classification:</strong> {result}
                </div>
                
                <div class="image-container mb-4">
                    <img src='/{filepath}' class="analysis-image img-fluid">
                </div>
                
                <div class="d-grid gap-2 d-md-block">
                    <a href="/home" class="btn btn-primary btn-lg px-5">
                        <i class="fas fa-redo"></i> Analyze Another
                    </a>
                    <a href="/home" class="btn btn-outline-secondary btn-lg px-5">
                        <i class="fas fa-home"></i> Back to Home
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route("/upload-video", methods=["POST"])
def upload_video():
    if "file" not in request.files:
        return redirect(url_for("home"))

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return redirect(url_for("home"))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    result = predict_video(filepath)
    percentage = float(result.split("%")[0])
    progress_color = "danger" if percentage > 50 else "warning" if percentage > 20 else "info"
    
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Video Analysis Result</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .progress-container {{
                background: rgba(0,0,0,0.05);
                border-radius: 50px;
                height: 40px;
                overflow: hidden;
                position: relative;
                margin: 2rem 0;
            }}
            .progress-bar {{
                transition: all 1s ease-in-out;
                height: 100%;
            }}
            .percentage-text {{
                position: absolute;
                left: 50%;
                top: 50%;
                transform: translate(-50%, -50%);
                font-weight: bold;
                color: white;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
            }}
            .result-card {{
                background: white;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                max-width: 700px;
                margin: 2rem auto;
                padding: 2rem;
            }}
        </style>
    </head>
    <body style="background: #f8f9fa;">
        <div class="result-card">
            <div class="text-center">
                <i class="fas fa-video result-icon mb-4 text-{progress_color}" style="font-size: 4rem;"></i>
                <h2 class="mb-4">Video Analysis Result</h2>
                
                <div class="progress-container">
                    <div class="progress-bar bg-{progress_color}" 
                         style="width: {percentage}%">
                        <span class="percentage-text">{result}</span>
                    </div>
                </div>
                
                <div class="alert alert-{progress_color}">
                    <h5 class="mb-0">This video contains <strong>{percentage}%</strong> potential fake content</h5>
                </div>
                
                <div class="row g-3 mt-4">
                    <div class="col-md-6">
                        <div class="card p-3 border-{progress_color}">
                            <i class="fas fa-file-video fa-2x mb-2 text-{progress_color}"></i>
                            <h5>Original File</h5>
                            <p class="mb-0 text-muted">{filename}</p>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card p-3">
                            <i class="fas fa-chart-bar fa-2x mb-2 text-primary"></i>
                            <h5>Analysis Summary</h5>
                            <p class="mb-0 text-muted">{percentage}% fake frames detected</p>
                        </div>
                    </div>
                </div>
                
                <div class="d-grid gap-2 d-md-block mt-4">
                    <a href="/home" class="btn btn-primary btn-lg px-5">
                        <i class="fas fa-redo"></i> Analyze Another
                    </a>
                    <a href="/home" class="btn btn-outline-secondary btn-lg px-5">
                        <i class="fas fa-home"></i> Back to Home
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route("/live-video")
def live_video():
    return Response(detect_live(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
