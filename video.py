import cv2
import time
from PIL import Image
import numpy as np
import os
import threading

# Initialize a lock for thread-safe operations
frame_lock = threading.Lock()

def process_video(video_path):
    # Folder to save frames
    folder = "frames"

    # Create the frames folder if it doesn't exist
    frames_dir = os.path.join(os.getcwd(), folder)
    os.makedirs(frames_dir, exist_ok=True)

    # Initialize the video capture
    cap = cv2.VideoCapture(video_path)

    # Check if the video is opened correctly
    if not cap.isOpened():
        raise IOError("Cannot open video file")

    # Get the frames per second (fps) of the video
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 24  # Default to 24 fps if unable to get fps from video

    frame_rate = 24  # Desired frame rate for processing/display
    frame_interval = int(cap.get(cv2.CAP_PROP_FPS) / frame_rate)
    if frame_interval == 0:
        frame_interval = 1

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if ret:
            # Convert the frame to a PIL image
            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # Resize the image
            max_size = 765
            ratio = max_size / max(pil_img.size)
            new_size = tuple([int(x * ratio) for x in pil_img.size])
            resized_img = pil_img.resize(new_size, Image.LANCZOS)

            # Convert the PIL image back to an OpenCV image
            frame = cv2.cvtColor(np.array(resized_img), cv2.COLOR_RGB2BGR)

            # Define paths for temporary and final frame
            temp_frame_path = os.path.join(folder, 'frame_temp.jpg')
            final_frame_path = os.path.join(folder, 'frame.jpg')

            # Write to temporary file first
            with frame_lock:
                cv2.imwrite(temp_frame_path, frame)
                print(f"📸 Saved frame_{frame_count}.jpg as frame_temp.jpg")

                # Atomically replace frame.jpg with frame_temp.jpg
                os.replace(temp_frame_path, final_frame_path)
                print(f"✅ Renamed frame_temp.jpg to frame.jpg")

            frame_count += 1

            # Wait to match the desired frame rate
            time.sleep(1 / frame_rate)
        else:
            break

    cap.release()
    print("🎞️ Video processing completed.")