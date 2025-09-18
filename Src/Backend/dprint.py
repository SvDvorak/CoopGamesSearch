from datetime import datetime

def dprint(text):
    timestamp = datetime.now().strftime("%y:%m:%d_%H:%M:%S")
    print(f"{timestamp} {text}")