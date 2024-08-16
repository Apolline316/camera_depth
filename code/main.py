import multiprocessing
from time import sleep
import cv2
import psutil
import sys
import os
import shutil
import signal

from tof_sensor import TofCamera
from stereo_vision import StereoVision, DualCameraCapture
from calibration_camera import Calibrator
from exception import folder_create


def calibrate_cameras(cam_capture):
    print("Starting camera calibration...")

    # Calibration parameters
    img_width = 840
    img_height = 820
    image_size = (img_width, img_height)

    # Capture the necessary photos for calibration
    nbr_photos = int(input("Enter the number of images to capture for calibration: "))
    rows = int(input("Enter the number of rows on the checkerboard: "))
    columns = int(input("Enter the number of columns on the checkerboard: "))
    square_size = 2.4  # Checkerboard square size

    cam_capture.capture_images(nbr_photos=nbr_photos, image_folder="image")

    calibrator = Calibrator(rows, columns, square_size, image_size)
    calibration = calibrator.calibration_process(nbr_photos, 'image')

    # Save calibration data
    calibration.save('data')

    print("Calibration completed.")


def run_tof_camera(camera_queue):
    tof_camera = TofCamera(max_distance=4)
    tof_camera.continuous_display()
    while True:
        depth_buf = tof_camera.get_depth_buf()
        depth_normalized = tof_camera.get_depth_normalized()
        if depth_buf is not None and depth_normalized is not None:
            camera_queue.put((depth_buf, depth_normalized))
        sleep(1)


def run_stereo_vision():
    img_width = 840
    img_height = 820
    image_size = (img_width, img_height)
    cam_capture = DualCameraCapture(left_cam_id=2, right_cam_id=1, preview_size=image_size)
    stereo_vision = StereoVision(cam_capture)
    stereo_vision.process_and_display()

    disparity_normalized = stereo_vision.disparity_normalized
    depth = stereo_vision.depth
    return disparity_normalized, depth


def terminate_processes(processes):
    """Terminates the given processes."""
    for proc in processes:
        if proc.is_alive():
            proc.terminate()
            proc.join()


def kill_zombie_processes():
    """Kills zombie processes."""
    for proc in psutil.process_iter(['pid', 'status']):
        try:
            if proc.info['status'] == psutil.STATUS_ZOMBIE:
                print(f"Zombie process detected: PID {proc.info['pid']}")
                os.kill(proc.info['pid'], signal.SIGKILL)
                print(f"Zombie process {proc.info['pid']} killed.")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"Error handling process {proc.info['pid']}: {e}")


def clean_temp_dirs(directories):
    """Cleans the specified temporary directories."""
    for directory in directories:
        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error cleaning {file_path}: {e}")
        except Exception as e:
            print(f"Error cleaning {directory}: {e}")


def cleanup():
    """Performs cleanup operations."""
    kill_zombie_processes()
    clean_temp_dirs(['/tmp', '/var/tmp'])
    print("Memory freed.")
    print("System cleanup completed.")


if __name__ == "__main__":
    folder_create('data')
    folder_create('image')
    folder_create('corner')

    calib_choice = input("Do you want to calibrate the cameras (y/n)? ").strip().lower()

    if calib_choice == "y":
        cam_capture = DualCameraCapture(left_cam_id=2, right_cam_id=1, preview_size=(840, 820))
        calibrate_cameras(cam_capture)
    elif calib_choice == "n":
        print("Cameras will not be calibrated.")
    else:
        print("Invalid choice. Please enter 'y' or 'n'.")
        exit(1)

    # Initialize queues for inter-process communication
    camera_queue = multiprocessing.Queue()

    # Create processes
    tof_process = multiprocessing.Process(target=run_tof_camera, args=(camera_queue,))
    stereo_process = multiprocessing.Process(target=run_stereo_vision)

    # Start processes
    tof_process.start()
    stereo_process.start()

    processes = [tof_process, stereo_process]

    # Wait for processes to finish
    try:
        # Keep processes alive
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("Interrupt detected. Stopping processes...")
    finally:
        # Stop processes
        terminate_processes(processes)
        print("All processes have been stopped.")
        cleanup()
        sys.exit(0)
