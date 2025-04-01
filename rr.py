import base64
import playsound
import tempfile

p = ''.join([chr(i) for i in [112, 108, 97, 121, 115, 111, 117, 110, 100]])  # 'playsound' as before
m = ''.join([chr(i) for i in [112, 108, 97, 121, 115, 111, 117, 110, 100]])  # 'playsound' for the method
__import__(p).playsound = getattr(__import__(p), m)

# Step 1: Read the base64 string from your text file
with open('lsrf.txt', 'r') as file:
    base64_string = file.read().strip()  # Assuming the file contains only the base64 string

# Step 2: Decode the base64 string into binary data
audio_data = base64.b64decode(base64_string)

# Step 3: Save the decoded data to a temporary MP3 file
with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
    temp_file.write(audio_data)
    temp_file_path = temp_file.name

# Step 4: Play the MP3 file
playsound.playsound(temp_file_path)
