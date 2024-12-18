import base64
import time
from openai import OpenAI
import os
from pydub import AudioSegment
from pydub.playback import play
import errno
import numpy as np
from video import process_video
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)

previous_commentary_list = []
lock = threading.Lock()

def encode_image(image_path):
    while True:
        try:
            with open(image_path, "rb") as image_file:
                logging.debug(f"Encoding image: {image_path}")
                return base64.b64encode(image_file.read()).decode("utf-8")
        except IOError as e:
            if e.errno != errno.EACCES:
                logging.error(f"Error accessing {image_path}: {e}")
                raise
            logging.warning(f"Access denied to {image_path}, retrying in 0.1 seconds...")
            time.sleep(0.1)

def analyze_image(base64_image, previous_commentary):
    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                f"Previous commentary: {previous_commentary}\nThis is a frame from a video. You are a friendly and excited sports commentator who particularly enjoys Moneyball, Baseball and Shohei Ohtani. \
                Generate short compelling and accurate baseball commentary following the previous commentary and keep it below 15 words. Be analytical and don't over use adjectives. Make sure you understand if Shohei Ohtani is the pitcher or the batter, or catcher. Don't repeat yourself. If there was previous commentary, then continue on like natural commentary and build on it. Avoid starting off with words like here we go as I will be combining the commentary.",
                {"image": base64_image, "resize": 768},
            ],
        },
    ]

    logging.debug("Sending request to OpenAI for image analysis.")
    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=PROMPT_MESSAGES,
        max_tokens=200
    )

    text_content = result.choices[0].message.content
    logging.debug(f"Received analysis: {text_content}")
    return text_content

def process_audio(analysis):
    logging.debug("Sending request to OpenAI for audio processing.")
    completion = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "alloy", "format": "mp3"},
        messages=[
            {
                "role": "system",
                "content": "You are a sports commentator Speak in a British accent and speak enthusiastically and quickly. Read exactly as the text is written and keep the audio under 10 seconds.",
            },
            {
                "role": "user",
                "content": analysis,
            }
        ],
    )
    speech_file_path = "./sound/output.mp3"
    mp3_bytes = base64.b64decode(completion.choices[0].message.audio.data)

    with open(speech_file_path, "wb") as f:
        logging.debug(f"Writing audio to {speech_file_path}")
        f.write(mp3_bytes)

    sound = AudioSegment.from_mp3(speech_file_path)
    logging.debug("Playing audio.")
    play(sound)

def video_thread(filepath):
    logging.info(f"Starting video processing for {filepath}")
    process_video(filepath)
    logging.info(f"Finished video processing for {filepath}")

def analysis_thread():
    while True:
        with lock:
            frame_path = "./frames/frame.jpg"
            if os.path.exists(frame_path):
                logging.info(f"Found frame: {frame_path}. Starting analysis.")
                base64_image = encode_image(frame_path)
                previous_commentary = " ".join(previous_commentary_list)
                analysis = analyze_image(base64_image, previous_commentary)
                process_audio(analysis)
                previous_commentary_list.append(analysis)
            else:
                logging.debug(f"Frame not found: {frame_path}")
        time.sleep(3)

def main(filepath):
    vt = threading.Thread(target=video_thread, args=(filepath,))
    at = threading.Thread(target=analysis_thread)
    vt.start()
    at.start()
    # Removed vt.join() and at.join() to prevent blocking
    logging.info("Started video and analysis threads.")

if __name__ == "__main__":
    main("./video_test.mp4")