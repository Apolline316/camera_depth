import time
from picamera2 import Picamera2, Preview
import os
import cv2  # OpenCV for displaying images

# Import the show_image function
from exception import show_image


class DualCameraCapture:
    def __init__(self, left_cam_id=0, right_cam_id=1, preview_size=(840, 820),
                 preview_type=Preview.QTGL, capture_delay=0, interval=5):
        """
        Initializes the DualCameraCapture class with camera parameters.

        :param left_cam_id: ID of the left camera (default 0)
        :param right_cam_id: ID of the right camera (default 1)
        :param preview_size: Size of the preview (default (840, 820))
        :param preview_type: Type of preview (default Preview.QTGL)
        :param capture_delay: Delay before capturing the image (default 0)
        :param interval: Interval between image captures (default 5)
        """
        self.left_cam_id = left_cam_id
        self.right_cam_id = right_cam_id
        self.preview_size = preview_size
        self.preview_type = preview_type
        self.capture_delay = capture_delay
        self.interval = interval

    def capture_and_save_image(self, picam_id, filename):
        """
        Captures and saves an image from the specified camera.

        :param picam_id: ID of the camera to use
        :param filename: Name of the file to save the image
        """
        # Create an instance of Picamera2 with the specified ID
        picam = Picamera2(picam_id)
        # Create preview configuration with the specified size
        preview_config = picam.create_preview_configuration(main={"size": self.preview_size})
        picam.configure(preview_config)
        # Start the camera preview with the specified preview type
        picam.start_preview(self.preview_type)
        # Start capturing
        picam.start()
        # Delay to allow the camera to stabilize before capturing
        time.sleep(self.capture_delay)
        # Capture the image and save it to the specified file
        metadata = picam.capture_file(filename)
        print(f"Image captured {filename}: {metadata}")
        # Close the camera after capturing
        picam.close()

    def display_images(self, left_filename, right_filename):
        """
        Displays the captured images from the specified files.

        :param left_filename: Name of the left image file
        :param right_filename: Name of the right image file
        """
        # Read the images from the specified files
        left_image = cv2.imread(left_filename)
        right_image = cv2.imread(right_filename)

        # Display the images using the imported show_image function
        show_image("Left Image", left_image, cmap='gray')
        show_image("Right Image", right_image, cmap='gray')

    def validate_images(self):
        """
        Validates if the captured images are acceptable.

        :return: True if the images are acceptable, otherwise False
        """
        while True:
            # Ask the user to validate the images
            user_input = input("Are the images acceptable? (y/n): ").strip().lower()
            if user_input in ["y", "n"]:
                # Return True if the user accepts the images, otherwise False
                return user_input == "y"
            print("Invalid input. Please enter 'y' or 'n'.")

    def capture_images(self, nbr_photos, image_folder):
        """
        Captures a specified number of pairs of images and saves them to the specified folder.

        :param nbr_photos: Number of pairs of images to capture
        :param image_folder: Folder to save the images
        """
        photo_counter = 0
        while photo_counter < nbr_photos:
            # Wait before capturing the next pair of images
            time.sleep(self.interval)
            # Define filenames for left and right images
            left_filename = os.path.join(image_folder, f'left_{str(photo_counter + 1).zfill(2)}.png')
            right_filename = os.path.join(image_folder, f'right_{str(photo_counter + 1).zfill(2)}.png')

            # Capture and save images for the left and right cameras
            self.capture_and_save_image(self.left_cam_id, left_filename)
            self.capture_and_save_image(self.right_cam_id, right_filename)

            # Display the captured images for validation
            self.display_images(left_filename, right_filename)

            # Validate the images with the user
            if self.validate_images():
                photo_counter += 1
                print(f'Captured pair No {photo_counter}')
            else:
                print("Retrying images...")
