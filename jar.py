import os
import json
import pyttsx3
import pyautogui
import webbrowser
import requests
import speech_recognition as sr
import shutil
import time
import cv2
import pyperclip
import speedtest
import pywhatkit
import screen_brightness_control as sbc
from datetime import datetime
from dotenv import load_dotenv
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import google.generativeai as genai
import re

load_dotenv()
GEMINI_API_KEY = os.getenv("AIzaSyCxyValqZoY0P6oaPj0OLrhdrB4Vgjf2Cc")
genai.configure(api_key=GEMINI_API_KEY)

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
engine.setProperty('rate', 170)
engine.setProperty('volume', 1.0)

MEMORY_FILE = "jarvis_memory.json"

def speak(text):
    print(f"Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as file:
            return json.load(file)
    return {"reminders": [], "notes": [], "history": []}

def save_memory(data):
    with open(MEMORY_FILE, "w") as file:
        json.dump(data, file, indent=4)

def add_reminder(task, time):
    memory = load_memory()
    memory["reminders"].append({"task": task, "time": time})
    save_memory(memory)

def add_note(note):
    memory = load_memory()
    memory["notes"].append(note)
    save_memory(memory)

def add_to_history(entry):
    memory = load_memory()
    memory["history"].append({"entry": entry, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
    save_memory(memory)

def check_reminders():
    memory = load_memory()
    now = datetime.now().strftime("%H:%M")
    new_reminders = []
    for reminder in memory["reminders"]:
        if reminder["time"] == now:
            speak(f"Reminder: {reminder['task']}")
        else:
            new_reminders.append(reminder)
    memory["reminders"] = new_reminders
    save_memory(memory)

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio)
            print(f"You: {command}")
            add_to_history(command)
            return command.lower()
        except:
            return ""

def get_ai_response(command):
    try:
        model = genai.GenerativeModel(model_name="models/gemini-pro")
        response = model.generate_content(command)
        return response.text if hasattr(response, "text") else str(response)
    except Exception as e:
        print("Gemini Error:", e)
        return "Sorry boss, I couldn't get an answer from Gemini."

def clean_junk():
    temp = os.getenv('TEMP')
    try:
        for f in os.listdir(temp):
            f_path = os.path.join(temp, f)
            if os.path.isfile(f_path) or os.path.islink(f_path):
                os.unlink(f_path)
            elif os.path.isdir(f_path):
                shutil.rmtree(f_path)
        speak("Junk files cleaned.")
    except Exception as e:
        speak(f"Error cleaning junk files: {e}")

def check_internet_speed():
    st = speedtest.Speedtest()
    download = st.download() / 1_000_000
    upload = st.upload() / 1_000_000
    speak(f"Download: {download:.2f} Mbps, Upload: {upload:.2f} Mbps")

def describe_image():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    if ret:
        cv2.imwrite("capture.jpg", frame)
        speak("Image captured. Description coming soon.")
    cam.release()
    cv2.destroyAllWindows()

def execute_code(code):
    try:
        exec(code)
        speak("Code executed successfully.")
    except Exception as e:
        speak(f"Error: {e}")

def read_clipboard():
    text = pyperclip.paste()
    if text:
        speak("Clipboard contains: " + text)
    else:
        speak("Clipboard is empty.")

def read_document(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
            speak("Reading document:")
            print(content)
    except Exception as e:
        speak(f"Unable to read the document: {e}")

def change_volume(action):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    current = volume.GetMasterVolumeLevelScalar()
    new_volume = min(current + 0.1, 1.0) if action == "up" else max(current - 0.1, 0.0)
    volume.SetMasterVolumeLevelScalar(new_volume, None)
    speak(f"Volume {'increased' if action == 'up' else 'decreased'}.")

def change_brightness(action):
    try:
        current = sbc.get_brightness()[0]
        new = min(current + 10, 100) if action == "up" else max(current - 10, 0)
        sbc.set_brightness(new)
        speak(f"Brightness {'increased' if action == 'up' else 'decreased'}.")
    except Exception as e:
        speak(f"Failed to change brightness: {e}")

def open_anything(command):
    try:
        name = command.replace("open", "").strip()
        app_map = {
            "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "notepad": "notepad",
            "whatsapp": "C:\\Users\\Rahul\\AppData\\Local\\WhatsApp\\WhatsApp.exe",
            "vscode": "C:\\Users\\Rahul\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"
        }
        if "youtube" in command and "search" in command:
            search_term = command.split("search")[-1].strip()
            url = f"https://www.youtube.com/results?search_query={search_term.replace(' ', '+')}"
            webbrowser.open(url)
            speak(f"Searching {search_term} on YouTube.")
        elif "search" in command:
            search_term = command.split("search")[-1].strip()
            url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
            webbrowser.open(url)
            speak(f"Searching for {search_term} on Google.")
        elif "chrome" in command:
            os.startfile(app_map["chrome"])
            speak("Opening Chrome.")
        elif name in app_map:
            os.startfile(app_map[name])
            speak(f"Opening {name}.")
        else:
            speak(f"I couldn't find {name} on your system.")
    except Exception as e:
        speak(f"Something went wrong: {e}")

def close_app(app_name):
    try:
        os.system(f"taskkill /f /im {app_name}.exe")
        speak(f"{app_name} closed.")
    except Exception as e:
        speak(f"Couldn't close the app: {e}")

def handle_command(command):
    if "remind me" in command:
        match = re.search(r"remind me at (\d{1,2})(?::(\d{2}))?\s*(am|pm)? to (.+)", command)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            am_pm = match.group(3)
            task = match.group(4)
            if am_pm:
                if am_pm.lower() == "pm" and hour != 12:
                    hour += 12
                elif am_pm.lower() == "am" and hour == 12:
                    hour = 0
            reminder_time = f"{hour:02d}:{minute:02d}"
            add_reminder(task, reminder_time)
            speak(f"Reminder set for {reminder_time} to {task}.")
        else:
            speak("Couldn't understand the reminder format.")
    elif "play" in command and "youtube" in command:
        search_term = command.replace("play", "").replace("on youtube", "").strip()
        speak(f"Playing {search_term} on YouTube.")
        pywhatkit.playonyt(search_term)
    elif "note" in command:
        note = command.replace("note", "").strip()
        add_note(note)
        speak("Note added.")
    elif "read notes" in command:
        for note in load_memory()["notes"]:
            speak(note)
    elif "read reminders" in command:
        for reminder in load_memory()["reminders"]:
            speak(f"{reminder['time']} - {reminder['task']}")
    elif "clean junk" in command:
        clean_junk()
    elif "check speed" in command:
        check_internet_speed()
    elif "describe image" in command:
        describe_image()
    elif "read clipboard" in command:
        read_clipboard()
    elif "run code" in command:
        speak("Please type the Python code:")
        code = input("Enter code: ")
        execute_code(code)
    elif "read file" in command:
        path = command.replace("read file", "").strip()
        read_document(path)
    elif "show history" in command:
        for h in load_memory()["history"][-10:]:
            speak(f"At {h['time']}, you said: {h['entry']}")
    elif command.startswith("open"):
        open_anything(command)
    elif command.startswith("close"):
        for app in ["chrome", "notepad", "vlc", "whatsapp", "vscode"]:
            if app in command:
                close_app(app)
                return
        speak("I don't recognize that application.")
    elif "increase volume" in command:
        change_volume("up")
    elif "decrease volume" in command:
        change_volume("down")
    elif "increase brightness" in command:
        change_brightness("up")
    elif "decrease brightness" in command:
        change_brightness("down")
    elif "jarvis" in command:
        speak("Yes Boss")
    else:
        ai_response = get_ai_response(command)
        speak(ai_response)

def main():
    speak("Hello Boss, I am JARVIS.")
    try:
        while True:
            check_reminders()
            command = recognize_speech()
            if command:
                if "exit" in command or "quit" in command or "stop" in command:
                    speak("Goodbye Boss.")
                    break
                handle_command(command)
            time.sleep(5)
    except KeyboardInterrupt:
        speak("Goodbye Boss.")


if __name__ == '__main__':
    main()
