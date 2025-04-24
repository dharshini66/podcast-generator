import os
import time
import json
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from production_podcast_generator import PodcastGenerator

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'temp_audio')
app.config['OUTPUT_FOLDER'] = os.path.join(os.getcwd(), 'output_podcasts')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload size

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Create templates directory and files
templates_dir = os.path.join(os.getcwd(), 'templates')
os.makedirs(templates_dir, exist_ok=True)

# Create static directory for CSS
static_dir = os.path.join(os.getcwd(), 'static')
css_dir = os.path.join(static_dir, 'css')
os.makedirs(css_dir, exist_ok=True)

# Write CSS file
with open(os.path.join(css_dir, 'style.css'), 'w') as f:
    f.write("""
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    background-color: #f8f9fa;
    color: #333;
}

.container {
    width: 80%;
    margin: 0 auto;
    padding: 20px;
}

header {
    background-color: #343a40;
    color: white;
    padding: 1rem;
    text-align: center;
}

h1 {
    margin: 0;
}

.card {
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    padding: 20px;
    margin-bottom: 20px;
}

.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

input[type="text"],
input[type="file"] {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background-color: #0069d9;
}

.alert {
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 15px;
}

.alert-success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.alert-danger {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.podcast-list {
    list-style: none;
    padding: 0;
}

.podcast-item {
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    padding: 15px;
    margin-bottom: 10px;
}

.podcast-item a {
    color: #007bff;
    text-decoration: none;
}

.podcast-item a:hover {
    text-decoration: underline;
}

.audio-player {
    width: 100%;
    margin-top: 10px;
}

footer {
    text-align: center;
    padding: 20px;
    margin-top: 20px;
    background-color: #343a40;
    color: white;
}
""")

# Write index.html template
with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
    f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Podcast Generator</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <header>
        <h1>AI Podcast Generator</h1>
        <p>Upload meeting recordings and generate podcast snippets</p>
    </header>

    <div class="container">
        {% if message %}
        <div class="alert {% if success %}alert-success{% else %}alert-danger{% endif %}">
            {{ message }}
        </div>
        {% endif %}

        <div class="card">
            <h2>Upload Audio</h2>
            <form action="{{ url_for('upload_file') }}" method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="file">Audio File (MP3 or WAV):</label>
                    <input type="file" id="file" name="file" accept=".mp3,.wav" required>
                </div>
                <div class="form-group">
                    <label for="title">Podcast Title (optional):</label>
                    <input type="text" id="title" name="title" placeholder="Enter a title for your podcast">
                </div>
                <button type="submit">Generate Podcast</button>
            </form>
        </div>

        <div class="card">
            <h2>Generated Podcasts</h2>
            {% if podcasts %}
            <ul class="podcast-list">
                {% for podcast in podcasts %}
                <li class="podcast-item">
                    <h3>{{ podcast.title }}</h3>
                    <p>Generated: {{ podcast.date }}</p>
                    <p>
                        <a href="{{ url_for('view_podcast', filename=podcast.info_file) }}">View Podcast Info</a>
                        {% if podcast.audio_file %}
                        | <a href="{{ url_for('download_podcast', filename=podcast.audio_file) }}">Download Audio</a>
                        <audio controls class="audio-player">
                            <source src="{{ url_for('download_podcast', filename=podcast.audio_file) }}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                        {% endif %}
                    </p>
                </li>
                {% endfor %}
            </ul>
            {% else %}
            <p>No podcasts generated yet.</p>
            {% endif %}
        </div>
    </div>

    <footer>
        <p>&copy; 2025 AI Podcast Generator</p>
    </footer>
</body>
</html>
""")

# Write podcast_info.html template
with open(os.path.join(templates_dir, 'podcast_info.html'), 'w') as f:
    f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ podcast.title }} - AI Podcast Generator</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <header>
        <h1>AI Podcast Generator</h1>
        <p>Podcast Information</p>
    </header>

    <div class="container">
        <div class="card">
            <h2>{{ podcast.title }}</h2>
            <p>Generated: {{ podcast.date }}</p>
            
            {% if podcast.audio_file %}
            <div>
                <h3>Podcast Audio</h3>
                <audio controls class="audio-player">
                    <source src="{{ url_for('download_podcast', filename=podcast.audio_file) }}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
                <p><a href="{{ url_for('download_podcast', filename=podcast.audio_file) }}">Download Audio</a></p>
            </div>
            {% endif %}
            
            <div>
                <h3>Intro</h3>
                <p>{{ podcast.intro }}</p>
            </div>
            
            <div>
                <h3>Key Points</h3>
                <ol>
                    {% for point in podcast.key_points %}
                    <li>
                        <strong>{{ point.title }}</strong>
                        <p>{{ point.text }}</p>
                    </li>
                    {% endfor %}
                </ol>
            </div>
            
            <div>
                <h3>Outro</h3>
                <p>{{ podcast.outro }}</p>
            </div>
        </div>
        
        <p><a href="{{ url_for('index') }}">&larr; Back to Home</a></p>
    </div>

    <footer>
        <p>&copy; 2025 AI Podcast Generator</p>
    </footer>
</body>
</html>
""")

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp3', 'wav'}

def get_podcasts():
    """Get list of generated podcasts"""
    podcasts = []
    try:
        for filename in os.listdir(app.config['OUTPUT_FOLDER']):
            if filename.startswith('podcast_') and filename.endswith('.txt'):
                info_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
                with open(info_path, 'r') as f:
                    content = f.read()
                
                # Extract basic info
                title = "Untitled Podcast"
                date = "Unknown Date"
                
                for line in content.split('\n'):
                    if line.startswith('PODCAST:'):
                        title = line.replace('PODCAST:', '').strip()
                    elif line.startswith('Generated:'):
                        date = line.replace('Generated:', '').strip()
                
                # Check if there's a corresponding audio file
                audio_file = filename.replace('.txt', '.mp3')
                if not os.path.exists(os.path.join(app.config['OUTPUT_FOLDER'], audio_file)):
                    audio_file = None
                
                podcasts.append({
                    'title': title,
                    'date': date,
                    'info_file': filename,
                    'audio_file': audio_file
                })
        
        # Sort by filename (which includes timestamp) in descending order
        podcasts.sort(key=lambda x: x['info_file'], reverse=True)
    except Exception as e:
        print(f"Error getting podcasts: {str(e)}")
    
    return podcasts

def parse_podcast_info(filename):
    """Parse podcast info file into structured data"""
    info_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    
    podcast = {
        'title': 'Untitled Podcast',
        'date': 'Unknown Date',
        'intro': '',
        'outro': '',
        'key_points': [],
        'audio_file': None
    }
    
    try:
        with open(info_path, 'r') as f:
            content = f.read()
        
        # Extract sections
        lines = content.split('\n')
        current_section = None
        current_point = None
        
        for line in lines:
            if line.startswith('PODCAST:'):
                podcast['title'] = line.replace('PODCAST:', '').strip()
            elif line.startswith('Generated:'):
                podcast['date'] = line.replace('Generated:', '').strip()
            elif line.startswith('INTRO:'):
                podcast['intro'] = line.replace('INTRO:', '').strip()
                current_section = 'intro'
            elif line.startswith('OUTRO:'):
                podcast['outro'] = line.replace('OUTRO:', '').strip()
                current_section = 'outro'
            elif line.startswith('KEY POINTS:'):
                current_section = 'key_points'
            elif line.startswith('FULL PODCAST AUDIO:'):
                podcast['audio_file'] = line.replace('FULL PODCAST AUDIO:', '').strip()
            elif current_section == 'key_points' and line.strip() and line[0].isdigit():
                # This is a key point title
                parts = line.split('.', 1)
                if len(parts) > 1:
                    current_point = {
                        'title': parts[1].strip(),
                        'text': ''
                    }
                    podcast['key_points'].append(current_point)
            elif current_point is not None and line.strip():
                # This is key point content
                current_point['text'] += line.strip() + ' '
        
        # Check if there's a corresponding audio file
        if not podcast['audio_file']:
            audio_file = filename.replace('.txt', '.mp3')
            if os.path.exists(os.path.join(app.config['OUTPUT_FOLDER'], audio_file)):
                podcast['audio_file'] = audio_file
    
    except Exception as e:
        print(f"Error parsing podcast info: {str(e)}")
    
    return podcast

@app.route('/')
def index():
    """Home page"""
    podcasts = get_podcasts()
    return render_template('index.html', podcasts=podcasts)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and podcast generation"""
    if 'file' not in request.files:
        return render_template('index.html', message='No file part', success=False, podcasts=get_podcasts())
    
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', message='No file selected', success=False, podcasts=get_podcasts())
    
    if file and allowed_file(file.filename):
        try:
            # Save the uploaded file
            filename = secure_filename(file.filename)
            timestamp = int(time.time())
            temp_filename = f"upload_{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            file.save(file_path)
            
            # Get the title (if provided)
            title = request.form.get('title', '').strip()
            if not title:
                title = os.path.splitext(filename)[0]
            
            # Generate the podcast
            generator = PodcastGenerator()
            result = generator.generate_podcast(file_path, title)
            
            if result and result.get('info'):
                return render_template('index.html', 
                                      message='Podcast generated successfully!', 
                                      success=True, 
                                      podcasts=get_podcasts())
            else:
                return render_template('index.html', 
                                      message='Failed to generate podcast. Check the logs for details.', 
                                      success=False, 
                                      podcasts=get_podcasts())
        
        except Exception as e:
            return render_template('index.html', 
                                  message=f'Error: {str(e)}', 
                                  success=False, 
                                  podcasts=get_podcasts())
    
    return render_template('index.html', 
                          message='Invalid file type. Please upload an MP3 or WAV file.', 
                          success=False, 
                          podcasts=get_podcasts())

@app.route('/podcast/<filename>')
def view_podcast(filename):
    """View podcast information"""
    podcast = parse_podcast_info(filename)
    return render_template('podcast_info.html', podcast=podcast)

@app.route('/download/<filename>')
def download_podcast(filename):
    """Download podcast audio file"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
