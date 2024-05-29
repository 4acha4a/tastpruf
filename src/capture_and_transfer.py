import subprocess
import paramiko
import os
import time
import cv2

def capture_image_ssh():
    time.sleep(5)
    # Define Orange Pi SSH connection details
    ORANGE_PI_IP = "192.168.18.30"
    ORANGE_PI_USER = "orangepi"
    IMAGE_NAME = "img_from_camera.jpg"  # Name of the captured image

    # Define local and remote file paths
    LOCAL_IMAGE_PATH = os.path.expanduser("img_from_camera.jpg")
    REMOTE_IMAGE_PATH = f"/home/{ORANGE_PI_USER}/{IMAGE_NAME}"
    ROTATED_REMOTE_IMAGE_PATH = f"/tmp/rotated_image.jpg"

    # Define `fswebcam` and `imagemagick` commands
    fswebcam_command = f"fswebcam -r 2592x1936 --palette YUV420P --jpeg 100 -D 1 {REMOTE_IMAGE_PATH}"
    rotate_command = f"convert {REMOTE_IMAGE_PATH} -rotate -90 {ROTATED_REMOTE_IMAGE_PATH}"

    # Run `fswebcam` command on Orange Pi
    subprocess.run(["ssh", f"{ORANGE_PI_USER}@{ORANGE_PI_IP}", fswebcam_command])

    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ORANGE_PI_IP, username=ORANGE_PI_USER)

    try:
        # Run image rotation command on Orange Pi
        _, stdout, stderr = ssh.exec_command(rotate_command)
        if stderr.read():
            raise RuntimeError("Error rotating image:", stderr.read().decode())

        # Transfer rotated image from Orange Pi to local machine
        with paramiko.SFTPClient.from_transport(ssh.get_transport()) as sftp:
            sftp.get(ROTATED_REMOTE_IMAGE_PATH, LOCAL_IMAGE_PATH)

        # print(f"Image captured, rotated, and transferred to MacBook as {LOCAL_IMAGE_PATH}")

    except Exception as e:
        print("An error occurred:", e)

    finally:
        # Close SSH connection
        ssh.close()

    # print(f"Image captured, rotated, and transferred to MacBook as {LOCAL_IMAGE_PATH}")

def capture_image_local():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Failed to create capture object.")
        quit(-1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,2592)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,1936)
    #cap.set(cv2.cv.CV_CAP_PROP_FORMAT, cv2.cv.IPL_DEPTH_32F)

    print("Ramping camera...")
    for i in range(0, 30):
        _, image = cap.read()
    #image = cv2.rotate(src, cv2.ROTATE_90_COUNTERCLOCKWISE)
    cv2.imwrite("img_from_camera.jpg", image)
    cap.release()

def capture_image(ssh=False):
    if     ssh == True:
        capture_image_ssh()
    else:
        capture_image_local()



if __name__ == "__main__":
    capture_image()

