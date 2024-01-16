import subprocess
import os
from datetime import datetime

def capture_and_transfer_image(path: str) -> (int, str):
    # Generate timestamp
    timestamp = datetime.now().strftime("%H_%M_%S")
    date = datetime.now().strftime("%Y_%m_%d")

    path_with_date = f"{path}/{date}"

    # Local path to save the image on your laptop
    absolute_path = f"/home/{os.environ['USER']}/{path_with_date}"
    os.makedirs(absolute_path, exist_ok=True)

    libcamera_command = ["libcamera-still", "-n", "-o", f"{absolute_path}/image_{timestamp}.jpg"]

    try:
        # Connect to Raspberry Pi, capture image
        print("Capturing image on Raspberry Pi...")
        subprocess.run(libcamera_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error capturing image on Raspberry Pi: {e}")
        return 1, f"Error capturing image on Raspberry Pi: {e}"
    print("...done!")

    # Return success flag and path to image
    return 0, f"{absolute_path}/image_{timestamp}.jpg"

