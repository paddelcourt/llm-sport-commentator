# frontend.py

from flask import Flask, request, render_template, send_from_directory, make_response
import os
import threading
import logging
from werkzeug.utils import secure_filename
from app import analysis_thread, video_thread
from video import frame_lock  # Import the frame_lock from video.py

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
FRAMES_FOLDER = 'frames'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

# Thread synchronization lock
lock = threading.Lock()

# Initialize a list to store previous commentaries
previous_commentary_list = []

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def main_processing(filepath):
    # Start video processing thread
    vt = threading.Thread(target=video_thread, args=(filepath,))
    vt.start()

    # Start analysis thread
    at = threading.Thread(target=analysis_thread)
    at.daemon = True  # Daemonize thread to exit when main program exits
    at.start()

    logging.info("Started video and analysis threads.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        logging.error("No video part in the request.")
        return 'No video part', 400
    file = request.files['video']
    if file.filename == '':
        logging.error("No selected file.")
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logging.info(f"Video saved to {filepath}. Starting processing...")

        # Start main processing in a separate thread to prevent blocking
        thread = threading.Thread(target=main_processing, args=(filepath,))
        thread.start()

        commentary = "Processing your video..."  # Initial message
        return render_template('result.html', commentary=commentary)
    else:
        logging.error("Invalid file type uploaded.")
        return 'Invalid file type', 400

@app.route('/latest_frame')
def latest_frame():
    frame_path = os.path.join(FRAMES_FOLDER, 'frame.jpg')
    if os.path.exists(frame_path):
        logging.debug(f"Serving latest frame: {frame_path}")
        with frame_lock:
            response = make_response(send_from_directory(FRAMES_FOLDER, 'frame.jpg'))
            # Set headers to prevent caching
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            return response
    else:
        logging.warning(f"Frame not found: {frame_path}")
        return '', 204  # No Content

if __name__ == '__main__':
    # Ensure necessary directories exist
    for folder in [UPLOAD_FOLDER, FRAMES_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logging.info(f"Created missing directory: {folder}")

    app.run(debug=True)