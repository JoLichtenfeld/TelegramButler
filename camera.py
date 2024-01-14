import subprocess
import os
from datetime import datetime

def capture_and_transfer_image(pi_user, pi_ip, remote_path, local_path) -> (int, str):
    # Generate timestamp
    timestamp = datetime.now().strftime("%H_%M_%S")
    date = datetime.now().strftime("%Y_%m_%d")

    # Remote path for storing the captured image
    global_path_remote = f"/home/{pi_user}/{remote_path}"
    img_path_remote = f"{global_path_remote}/{date}"

    # Local path to save the image on your laptop
    global_path_local = f"/home/{os.environ['USER']}/{local_path}"
    img_path_local = f"{global_path_local}/{date}"
    os.makedirs(img_path_local, exist_ok=True)

    # Define commands
    ssh_command = ["ssh", "-o", "ConnectTimeout=10", f"{pi_user}@{pi_ip}", f"mkdir -p {img_path_remote} && libcamera-still -n -q 99 -o {img_path_remote}/image_{timestamp}.jpg"]
    scp_command = ["scp", "-o", "ConnectTimeout=10", f"{pi_user}@{pi_ip}:{img_path_remote}/image_{timestamp}.jpg", f"{img_path_local}/image.jpg"]

    try:
        # Connect to Raspberry Pi, capture image
        print("Capturing image on Raspberry Pi...")
        subprocess.run(ssh_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error capturing image on Raspberry Pi: {e}")
        return 1, f"Error capturing image on Raspberry Pi: {e}"

    try:
        # Transfer image to local machine
        print("Transferring image to local machine (" + f"{img_path_local}/image.jpg" + ")...")
        subprocess.run(scp_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error transferring image to local machine: {e}")
        return 1, f"Error transferring image to local machine: {e}"

    print("...done!")
    return 0, f"{img_path_local}/image.jpg"

