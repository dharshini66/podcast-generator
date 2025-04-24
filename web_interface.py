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

# Create static directory for CSS and JS
static_dir = os.path.join(os.getcwd(), 'static')
css_dir = os.path.join(static_dir, 'css')
js_dir = os.path.join(static_dir, 'js')
os.makedirs(css_dir, exist_ok=True)
os.makedirs(js_dir, exist_ok=True)

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
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
</head>
<body>
    <header>
        <h1><i class="fas fa-podcast"></i> AI Podcast Generator</h1>
        <p>Transform meeting recordings into professional podcast snippets</p>
    </header>

    <div class="container">
        {% if message %}
        <div class="alert {% if success %}alert-success{% else %}alert-danger{% endif %}">
            {% if success %}
            <i class="fas fa-check-circle"></i>
            {% else %}
            <i class="fas fa-exclamation-circle"></i>
            {% endif %}
            {{ message }}
        </div>
        {% endif %}

        <div class="card">
            <h2><i class="fas fa-microphone-alt"></i> Create New Podcast</h2>
            <form action="{{ url_for('upload_file') }}" method="post" enctype="multipart/form-data" id="podcast-form">
                <div class="form-group">
                    <label for="file">Audio File (MP3 or WAV):</label>
                    <div class="file-input-wrapper">
                        <div class="file-input-button">
                            <i class="fas fa-cloud-upload-alt"></i> Choose an audio file or drag it here
                        </div>
                        <input type="file" id="file" name="file" accept=".mp3,.wav" required>
                    </div>
                    <div class="file-name" id="file-name"></div>
                </div>
                
                <div class="form-group">
                    <label for="title">Podcast Title:</label>
                    <input type="text" id="title" name="title" placeholder="Enter a title for your podcast">
                </div>
                
                <div class="options-grid">
                    <div class="form-group">
                        <label for="voice">AI Voice:</label>
                        <select id="voice" name="voice">
                            <option value="default">Default Voice</option>
                            <option value="male">Male Voice</option>
                            <option value="female">Female Voice</option>
                            <option value="british">British Accent</option>
                            <option value="american">American Accent</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="segments">Key Segments:</label>
                        <select id="segments" name="segments">
                            <option value="3">3 Segments</option>
                            <option value="5" selected>5 Segments</option>
                            <option value="7">7 Segments</option>
                            <option value="10">10 Segments</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="style">Podcast Style:</label>
                        <select id="style" name="style">
                            <option value="professional">Professional</option>
                            <option value="casual">Casual</option>
                            <option value="energetic">Energetic</option>
                            <option value="calm">Calm</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="add_music" value="yes"> 
                        Add background music
                    </label>
                </div>
                
                <button type="submit" id="generate-button">
                    <i class="fas fa-magic"></i> Generate Podcast
                </button>
            </form>
            
            <div class="loading" id="loading">
                <div class="loading-spinner"></div>
                <div class="loading-text">Generating your podcast...</div>
                <div class="visualization">
                    <div class="visualization-bars">
                        <div class="visualization-bar"></div>
                        <div class="visualization-bar"></div>
                        <div class="visualization-bar"></div>
                        <div class="visualization-bar"></div>
                        <div class="visualization-bar"></div>
                        <div class="visualization-bar"></div>
                        <div class="visualization-bar"></div>
                        <div class="visualization-bar"></div>
                        <div class="visualization-bar"></div>
                        <div class="visualization-bar"></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2><i class="fas fa-headphones"></i> Your Podcasts</h2>
            {% if podcasts %}
            <ul class="podcast-list">
                {% for podcast in podcasts %}
                <li class="podcast-item">
                    <h3>{{ podcast.title }}</h3>
                    <div class="podcast-meta">
                        <span class="date">{{ podcast.date }}</span>
                    </div>
                    <div class="podcast-actions">
                        <a href="{{ url_for('view_podcast', filename=podcast.info_file) }}" class="view">
                            <i class="fas fa-file-alt"></i> View Details
                        </a>
                        {% if podcast.audio_file %}
                        <a href="{{ url_for('download_podcast', filename=podcast.audio_file) }}" class="download">
                            <i class="fas fa-download"></i> Download
                        </a>
                        {% endif %}
                    </div>
                    {% if podcast.audio_file %}
                    <audio controls class="audio-player">
                        <source src="{{ url_for('download_podcast', filename=podcast.audio_file) }}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                    {% endif %}
                </li>
                {% endfor %}
            </ul>
            {% else %}
            <p class="no-podcasts"><i class="fas fa-info-circle"></i> No podcasts generated yet. Create your first one!</p>
            {% endif %}
        </div>
    </div>

    <footer>
        <p>&copy; 2025 AI Podcast Generator | Powered by AssemblyAI & ElevenLabs</p>
    </footer>
    
    <div class="theme-toggle" id="theme-toggle">
        <span class="theme-toggle-icon">
            <i class="fas fa-moon"></i>
        </span>
    </div>

    <script>
        // File input handling
        const fileInput = document.getElementById('file');
        const fileName = document.getElementById('file-name');
        
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                fileName.textContent = this.files[0].name;
            } else {
                fileName.textContent = '';
            }
        });
        
        // Form submission and loading animation
        const form = document.getElementById('podcast-form');
        const loading = document.getElementById('loading');
        const generateButton = document.getElementById('generate-button');
        
        form.addEventListener('submit', function() {
            if (fileInput.files && fileInput.files[0]) {
                loading.style.display = 'block';
                generateButton.disabled = true;
            }
        });
        
        // Theme toggle functionality
        const themeToggle = document.getElementById('theme-toggle');
        const themeIcon = themeToggle.querySelector('i');
        let lightMode = false;
        
        themeToggle.addEventListener('click', function() {
            if (lightMode) {
                document.documentElement.style.setProperty('--dark-bg', '#121212');
                document.documentElement.style.setProperty('--dark-card', '#1e1e1e');
                document.documentElement.style.setProperty('--dark-text', '#e0e0e0');
                themeIcon.className = 'fas fa-moon';
            } else {
                document.documentElement.style.setProperty('--dark-bg', '#f8f9fa');
                document.documentElement.style.setProperty('--dark-card', '#ffffff');
                document.documentElement.style.setProperty('--dark-text', '#333333');
                themeIcon.className = 'fas fa-sun';
            }
            lightMode = !lightMode;
        });
    </script>
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
    <title>{{ podcast.title }} - Podcast Details</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
</head>
<body>
    <header>
        <h1><i class="fas fa-podcast"></i> AI Podcast Generator</h1>
        <p>Podcast Details</p>
    </header>

    <div class="container">
        <div class="card">
            <h2><i class="fas fa-info-circle"></i> {{ podcast.title }}</h2>
            
            <div class="podcast-meta">
                <span class="date">{{ podcast.date }}</span>
            </div>
            
            {% if podcast.audio_file %}
            <div class="audio-section">
                <h3><i class="fas fa-headphones"></i> Listen</h3>
                <audio controls class="audio-player">
                    <source src="{{ url_for('download_podcast', filename=podcast.audio_file) }}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
                <div class="podcast-actions">
                    <a href="{{ url_for('download_podcast', filename=podcast.audio_file) }}" class="download">
                        <i class="fas fa-download"></i> Download Audio
                    </a>
                </div>
            </div>
            {% endif %}
            
            <div class="podcast-content">
                <h3><i class="fas fa-align-left"></i> Content</h3>
                
                {% if podcast.intro %}
                <div class="content-section">
                    <h4>Introduction</h4>
                    <p>{{ podcast.intro }}</p>
                </div>
                {% endif %}
                
                {% if podcast.key_points %}
                <div class="content-section">
                    <h4>Key Points</h4>
                    <ol>
                        {% for point in podcast.key_points %}
                        <li>{{ point }}</li>
                        {% endfor %}
                    </ol>
                </div>
                {% endif %}
                
                {% if podcast.outro %}
                <div class="content-section">
                    <h4>Conclusion</h4>
                    <p>{{ podcast.outro }}</p>
                </div>
                {% endif %}
            </div>
        </div>
        
        <div class="back-link">
            <a href="{{ url_for('index') }}"><i class="fas fa-arrow-left"></i> Back to Podcasts</a>
        </div>
    </div>

    <footer>
        <p>&copy; 2025 AI Podcast Generator | Powered by AssemblyAI & ElevenLabs</p>
    </footer>
    
    <div class="theme-toggle" id="theme-toggle">
        <span class="theme-toggle-icon">
            <i class="fas fa-moon"></i>
        </span>
    </div>

    <script>
        // Theme toggle functionality
        const themeToggle = document.getElementById('theme-toggle');
        const themeIcon = themeToggle.querySelector('i');
        let lightMode = false;
        
        themeToggle.addEventListener('click', function() {
            if (lightMode) {
                document.documentElement.style.setProperty('--dark-bg', '#121212');
                document.documentElement.style.setProperty('--dark-card', '#1e1e1e');
                document.documentElement.style.setProperty('--dark-text', '#e0e0e0');
                themeIcon.className = 'fas fa-moon';
            } else {
                document.documentElement.style.setProperty('--dark-bg', '#f8f9fa');
                document.documentElement.style.setProperty('--dark-card', '#ffffff');
                document.documentElement.style.setProperty('--dark-text', '#333333');
                themeIcon.className = 'fas fa-sun';
            }
            lightMode = !lightMode;
        });
    </script>
</body>
</html>
""")

# Create JavaScript file for additional functionality
with open(os.path.join(js_dir, 'main.js'), 'w') as f:
    f.write("""
// File input handling
const fileInput = document.getElementById('file');
const fileName = document.getElementById('file-name');

fileInput.addEventListener('change', function() {
    if (this.files && this.files[0]) {
        fileName.textContent = this.files[0].name;
    } else {
        fileName.textContent = '';
    }
});

// Form submission and loading animation
const form = document.getElementById('podcast-form');
const loading = document.getElementById('loading');
const generateButton = document.getElementById('generate-button');

form.addEventListener('submit', function() {
    if (fileInput.files && fileInput.files[0]) {
        loading.style.display = 'block';
        generateButton.disabled = true;
    }
});

// Theme toggle functionality
const themeToggle = document.getElementById('theme-toggle');
const themeIcon = themeToggle.querySelector('i');
let lightMode = false;

themeToggle.addEventListener('click', function() {
    if (lightMode) {
        document.documentElement.style.setProperty('--dark-bg', '#121212');
        document.documentElement.style.setProperty('--dark-card', '#1e1e1e');
        document.documentElement.style.setProperty('--dark-text', '#e0e0e0');
        themeIcon.className = 'fas fa-moon';
    } else {
        document.documentElement.style.setProperty('--dark-bg', '#f8f9fa');
        document.documentElement.style.setProperty('--dark-card', '#ffffff');
        document.documentElement.style.setProperty('--dark-text', '#333333');
        themeIcon.className = 'fas fa-sun';
    }
    lightMode = !lightMode;
});
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
            
            # Get the form parameters
            title = request.form.get('title', '').strip()
            if not title:
                title = os.path.splitext(filename)[0]
            
            voice = request.form.get('voice', 'default')
            segments = int(request.form.get('segments', 5))
            style = request.form.get('style', 'professional')
            add_music = request.form.get('add_music') == 'yes'
            
            # Generate the podcast with the selected options
            generator = PodcastGenerator()
            result = generator.generate_podcast(
                file_path, 
                title,
                max_points=segments,
                voice_style=voice,
                podcast_style=style,
                add_background_music=add_music
            )
            
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
