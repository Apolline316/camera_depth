import sys  # Import for exception handling and system operations
import cv2  # Import OpenCV for image processing
import numpy as np  # Import NumPy for mathematical operations
import ArducamDepthCamera as ac  # Import library for the Arducam ToF camera
from depth_traitement import DepthMapProcessor  # Import class for depth map processing


class TofCamera:
    def __init__(self, max_distance=4):
        """
        Initialize the ToF camera with maximum distance parameters.

        :param max_distance: Maximum measurable distance by the camera in meters
        """
        self.cam = ac.ArducamCamera()  # Create an instance of the Arducam camera
        self.max_distance = max_distance  # Maximum distance to normalize the depth
        self.frame = None  # Current frame captured by the camera
        self.amplitude_buf = None  # Buffer for amplitude data
        self.depth_buf = None  # Buffer for depth data
        self.depth_normalized = None  # Normalized depth map for display
        self.result_image = None  # Resulting image after processing
        self.n = 0  # Counter for saved image names

    # Have to be implemented
    def water_equation(self):
        self.depth_water = self.depth_buf * 0.75  # distance = d_air * (c_water/c_air)

    def process_frame(self) -> np.ndarray:
        """
        Process the captured frame to produce a resulting image by combining depth and amplitude data.

        :return: Resulting image after processing
        """
        if self.depth_buf is None or self.amplitude_buf is None:
            raise ValueError("Depth buffer and amplitude buffer must not be None.")

        # Convert NaN values to zero for the depth buffer
        self.depth_buf = np.nan_to_num(self.depth_buf)
        # Threshold amplitude data
        self.amplitude_buf = np.where(self.amplitude_buf <= 7, 0, 255)

        # Normalize depth data
        normalized_depth = (1 - (self.depth_buf / self.max_distance)) * 255
        normalized_depth = np.clip(normalized_depth, 0, 255).astype(np.uint8)
        self.depth_normalized = normalized_depth
        # Combine normalized depth and amplitude data
        result_frame = normalized_depth & self.amplitude_buf.astype(np.uint8)
        return result_frame

    def capture_image(self):
        """
        Save the resulting image as tof{n}.png.
        """
        if self.result_image is not None:
            cv2.imwrite(f"tof{self.n}.png", self.result_image)
            print(f"Image saved as tof{self.n}.png")
            self.n += 1
        else:
            print("No image to save")

    def process_tof(self):
        """
        Process the depth map using DepthMapProcessor to analyze and extract contours.
        """
        # Replace for a under water usage
        processor = DepthMapProcessor(
                depth_map=self.depth_buf, # self.depth_water
                disparity=self.depth_normalized,
                pixel_min=18000,
                min_contour_area=20,
                thresholds=[50, 100, 200, 255],
                kernel_size=5,
                dilate_iterations=1,
                erode_iterations=3
            )
        processor.process_disparity_image()

    def apply_median_filter(self, image: np.darray, ksize: int = 5) -> np.ndarray:
        """ Apply a median filter at the image
        :param image : input image
        :param ksize : Kernel size of the median filter
        :return: Filtered image
        """
        return cv2.medianBlur(image, ksize)

    def continuous_display(self):
        """
        Continuously capture and display images from the ToF camera, with options to save and process images.
        """
        # Open the connection to the ToF camera and start the depth data stream
        if self.cam.open(ac.TOFConnect.CSI, 0) != 0 or self.cam.start(ac.TOFOutput.DEPTH) != 0:
            print("Failed to initialize or start the camera")
            sys.exit(1)

        # Set the maximum distance of the camera
        self.cam.setControl(ac.TOFControl.RANG, self.max_distance)

        try:
            while True:
                # Capture a frame from the camera
                self.frame = self.cam.requestFrame(200)
                if self.frame is not None:
                    # Get depth and amplitude data
                    self.depth_buf = self.frame.getDepthData()
                    self.amplitude_buf = self.frame.getAmplitudeData()
                    self.cam.releaseFrame(self.frame)  # Release the frame after processing

                    # Normalize and process amplitude data
                    self.amplitude_buf = np.clip(self.amplitude_buf * (255 / 1024), 0, 255)

                    # Process the frame to get the resulting image
                    self.result_image = self.process_frame()
                    # Use for water application
                    # self.water_equation()

                    #Apply a median filter
                    self.result_image = self.apply_median_filter(self.result_image)

                    # Apply a color map for better display
                    self.result_image = cv2.applyColorMap(self.result_image, cv2.COLORMAP_JET)

                    # Display the resulting image
                    cv2.imshow("ToF Camera", self.result_image)

                    # Handle keyboard input
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):  # Quit if 'q' key is pressed
                        break
                    elif key == ord('s'):  # Save the image if 's' key is pressed
                        self.capture_image()
                    elif key == ord('t'):  # Process depth data if 't' key is pressed
                        self.process_tof()
                else:
                    print("Failed to capture frame")

        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()  # Clean up resources at the end of execution

    def cleanup(self):
        """
        Stop and close the camera, and destroy all OpenCV windows.
        """
        self.cam.stop()
        self.cam.close()
        cv2.destroyAllWindows()

    def get_depth_buf(self):
        """
        Return the current depth buffer.

        :return: Depth buffer
        """
        return self.depth_buf

    def get_depth_normalized(self):
        """
        Return the normalized depth map.

        :return: Normalized depth map
        """
        return self.depth_normalized
