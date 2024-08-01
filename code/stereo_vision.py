import cv2  # Import OpenCV for image processing
import numpy as np  # Import NumPy for mathematical operations and image processing
from multiprocessing import Process, Queue, Event  # Import modules for process management
from calibration_camera import StereoCalibration  # Import the class for stereo calibration
from exception import file_create  # Import the function for file creation
from camera_control import DualCameraCapture  # Import the class for camera control
from depth_traitement import DepthMapProcessor  # Import the class for depth map processing

# Import the function show_image
from exception import show_image


class StereoVision:
    def __init__(self, cam_capture, baseline=0.06, focal_length=1300, block_size=15, P1=10 * 15, P2=64, min_disp=-16,
                 max_disp=128, uniqueRatio=4, speckleWindowSize=200, speckleRange=4, disp12MaxDiff=0):
        """
        Initialize parameters for stereo vision.

        :param cam_capture: Instance of DualCameraCapture for capturing images
        :param baseline: Distance between cameras (in meters)
        :param focal_length: Camera focal length
        :param block_size: Block size for stereo matching
        :param P1: Weight for cost regularization
        :param P2: Weight for cost regularization
        :param min_disp: Minimum disparity to consider
        :param max_disp: Maximum disparity to consider
        :param uniqueRatio: Uniqueness ratio for stereo matching
        :param speckleWindowSize: Window size for speckle filtering
        :param speckleRange: Range of values for speckle filtering
        :param disp12MaxDiff: Maximum difference between left and right disparities
        """
        self.cam_capture = cam_capture  # Instance of the camera capture class

        # Load stereo calibration data
        self.calibration = StereoCalibration()
        self.calibration.load_data('data')
        self.focal_length = focal_length  # Focal length calculated during calibration
        self.baseline = baseline  # Distance between cameras

        # Dictionary to store images
        self.images = {"left": None, "right": None, "left_rectify": None, "right_rectify": None}

        self.disparity = None
        self.disparity_normalized = None
        self.depth = None

        # Parameters for depth camera filters
        self.block_size = block_size
        self.min_disp = min_disp
        self.max_disp = max_disp
        self.num_disp = max_disp - min_disp
        self.P1 = P1
        self.P2 = P2
        self.uniquenessRatio = uniqueRatio
        self.speckleWindowSize = speckleWindowSize
        self.speckleRange = speckleRange
        self.disp12MaxDiff = disp12MaxDiff

        # Event to stop processes
        self.stop_event = Event()

        self.n = 0  # Counter for the number of saved images

    def stereo_taking(self):
        """
        Capture and rectify stereo images.
        """
        # Capture images from left and right cameras
        self.cam_capture.capture_and_save_image(self.cam_capture.left_cam_id, 'left.png')
        self.cam_capture.capture_and_save_image(self.cam_capture.right_cam_id, 'right.png')

        # Read captured images in grayscale
        for side in ("left", "right"):
            self.images[side] = cv2.imread(side + '.png', 0)

        # Rectify images using calibration data
        rectify_pair = self.calibration.rectify((self.images["left"], self.images["right"]))
        for i, side in enumerate(("left_rectify", "right_rectify")):
            self.images[side] = rectify_pair[i]

    def save_images(self):
        """
        Save images and the normalized disparity map.
        """
        for side in ("left", "right", "left_rectify", "right_rectify"):
            file_create(self.images[side], side + str(self.n), 'png')
        if self.disparity_normalized is not None:
            file_create(self.disparity_normalized, "depthmap" + str(self.n), 'png')
            self.n += 1

    def depth_map_calcul(self):
        """
        Calculate the disparity map from the rectified images.
        """
        # Create StereoSGBM object for disparity map calculation
        stereo = cv2.StereoSGBM_create(
            minDisparity=self.min_disp,
            numDisparities=self.num_disp,
            blockSize=self.block_size,
            P1=self.P1,
            P2=self.P2,
            uniquenessRatio=self.uniquenessRatio,
            speckleWindowSize=self.speckleWindowSize,
            speckleRange=self.speckleRange,
            disp12MaxDiff=self.disp12MaxDiff)

        # Calculate disparity
        self.disparity = stereo.compute(self.images["left_rectify"], self.images["right_rectify"])
        self.disparity = self.disparity.astype(np.float32) / 16.0  # Normalize for calculation
        self.disparity[self.disparity < 0] = 0  # Filter negative values
        # Normalize for display
        self.disparity_normalized = cv2.normalize(self.disparity, None, alpha=255, beta=0, norm_type=cv2.NORM_MINMAX,
                                                  dtype=cv2.CV_8U)

    def depth_calcul(self):
        """
        Calculate the depth for each pixel from the disparity map.
        """
        # Initialize depth
        self.depth = np.zeros_like(self.disparity)
        valid_disparity_mask = (self.disparity > 0)
        # Calculate depth
        self.depth[valid_disparity_mask] = self.focal_length * self.baseline / self.disparity[valid_disparity_mask]

    def process_stereo(self):
        """
        Process the depth map using DepthMapProcessor.
        """
        processor_stereo = DepthMapProcessor(
            depth_map=self.depth,
            disparity=self.disparity_normalized,
            pixel_min=20000,
            thresholds=[50, 100, 200, 255],
            kernel_size=5,
            dilate_iterations=1,
            erode_iterations=2
        )
        processor_stereo.process_disparity_image()

    def capture_and_compute(self, queue):
        """
        Capture images, calculate the disparity and depth maps, then place the results in a queue.

        :param queue: Queue to transmit results between processes
        """
        while not self.stop_event.is_set():
            # Capture and process stereo images
            self.stereo_taking()
            self.depth_map_calcul()
            self.depth_calcul()
            # Place results in the queue
            queue.put((self.disparity_normalized, self.depth))

        # Ensure the queue is empty before exiting
        queue.put((None, None))  # Send end-of-processing signal to the display process

        print("Image capture and processing stopped.")

    def depth_map_display(self, queue):
        """
        Display the disparity and depth maps from the results in the queue.

        :param queue: Queue to get the computed results
        """
        while not self.stop_event.is_set() or not queue.empty():
            if not queue.empty():
                self.disparity_normalized, self.depth = queue.get()
                # Apply color map for better visualization
                disparity_normalized_color = cv2.applyColorMap(self.disparity_normalized, cv2.COLORMAP_JET)
                cv2.imshow("disparity", disparity_normalized_color)
                key = cv2.waitKey(1)  # Wait for a short period for window events
                if key == ord('q'):  # Quit if 'q' key is pressed
                    self.stop_event.set()  # Signal the other process to stop
                elif key == ord('s'):  # Save images and depth map if 's' key is pressed
                    self.save_images()
                elif key == ord('t'):  # Process stereo images if 't' key is pressed
                    self.process_stereo()
        cv2.destroyAllWindows()

    def process_and_display(self):
        """
        Create processes for capturing and computing images, and for displaying the results.
        """
        queue = Queue()

        # Create processes
        capture_process = Process(target=self.capture_and_compute, args=(queue,))
        display_process = Process(target=self.depth_map_display, args=(queue,))

        try:
            # Start processes
            capture_process.start()
            display_process.start()

            # Wait for processes to finish
            capture_process.join()
            display_process.join()

        except KeyboardInterrupt:
            print("Interrupt detected. Stopping processes...")
            self.stop_event.set()  # Signal processes to stop

        finally:
            # Ensure processes are properly terminated
            if capture_process.is_alive():
                capture_process.terminate()
                capture_process.join()

            if display_process.is_alive():
                display_process.terminate()
                display_process.join()

            # Cleanup OpenCV windows
            cv2.destroyAllWindows()
