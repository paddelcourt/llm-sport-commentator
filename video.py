import cv2
import time
from PIL import Image
import numpy as np
import os


def process_video(video_path):
    # Folder
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

    frame_interval = int(fps * 2) #number of frames skip

    frame_count = 0

    while True:
        # Set the position of the next frame to capture
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)

        ret, frame = cap.read()
        if ret:
            # Convert the frame to a PIL image
            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # Resize the image
            max_size = 765
            ratio = max_size / max(pil_img.size)
            new_size = tuple([int(x*ratio) for x in pil_img.size])
            resized_img = pil_img.resize(new_size, Image.LANCZOS)

            # Convert the PIL image back to an OpenCV image
            frame = cv2.cvtColor(np.array(resized_img), cv2.COLOR_RGB2BGR)

            # Save the frame as an image file
            print("📸 Say cheese! Saving frame.")
            path = f"{folder}/frame.jpg"
            cv2.imwrite(path, frame)

            # Move to the next frame interval
            frame_count += frame_interval

            time.sleep(1) # Sleep for half a second
        else:
            break



