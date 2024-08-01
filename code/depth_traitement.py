import cv2
import numpy as np
import matplotlib.pyplot as plt
from exception import show_image


class DepthMapProcessor:
    def __init__(self, depth_map, disparity, pixel_min=15000, min_contour_area=10, thresholds=[], kernel_size=5, dilate_iterations=1, erode_iterations=2):
        """
        Initializes the DepthMapProcessor class with the given parameters.

        :param depth_map: Original depth map
        :param disparity: Normalized disparity map
        :param pixel_min: Minimum number of non-zero pixels to consider a segment (default is 15000)
        :param min_contour_area: Minimum area for contours to consider (default is 10)
        :param thresholds: List of thresholds for disparity segmentation
        :param kernel_size: Size of the kernel for morphological operations (default is 5)
        :param dilate_iterations: Number of iterations for dilation (default is 1)
        :param erode_iterations: Number of iterations for erosion (default is 2)
        """
        self.depth_map_original = depth_map
        self.depth_map_normalized = disparity
        self.pixel_min = pixel_min
        self.min_contour_area = min_contour_area
        self.thresholds = thresholds
        self.kernel_size = kernel_size
        self.dilate_iterations = dilate_iterations
        self.erode_iterations = erode_iterations
        self.segmented_image = None
        self.contours = []
        self.mean_amplitudes = {}

    def apply_morphological_operations(self, image):
        """
        Applies morphological operations (dilation and erosion) to the specified image.

        :param image: Image to process
        :return: Image after applying morphological operations
        """
        # Create the kernel for morphological operations
        kernel = np.ones((self.kernel_size, self.kernel_size), np.uint8)
        # Apply dilation
        dilated_image = cv2.dilate(image, kernel, iterations=self.dilate_iterations)
        # Apply erosion on the dilated image
        eroded_image = cv2.erode(dilated_image, kernel, iterations=self.erode_iterations)
        # Apply dilation again on the eroded image
        dilated_image2 = cv2.dilate(eroded_image, kernel, iterations=self.dilate_iterations)
        return dilated_image2

    def calculate_mean_amplitude(self, contours):
        """
        Calculates the mean amplitude for each specified contour.

        :param contours: List of contours found in the image
        :return: Dictionary of mean amplitudes for each contour
        """
        self.mean_amplitudes = {}
        for i, contour in enumerate(contours):
            if cv2.contourArea(contour) >= self.min_contour_area:
                # Create a mask for the current contour
                mask = np.zeros(self.depth_map_original.shape, dtype=np.uint8)
                cv2.drawContours(mask, [contour], -1, 255, -1)
                # Calculate the mean amplitude in the mask area
                mean_amplitude = cv2.mean(self.depth_map_original, mask=mask)[0]
                self.mean_amplitudes[i] = mean_amplitude
        return self.mean_amplitudes

    def find_and_draw_contours(self, processed_image):
        """
        Finds and draws contours in the processed image.

        :param processed_image: Image after morphological operations
        :return: Image with contours drawn
        """
        # Edge detection using Canny algorithm
        edges = cv2.Canny(processed_image, 50, 150)
        # Find contours in the edge image
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Convert processed image to color image for drawing contours
        image_with_contours = cv2.cvtColor(processed_image, cv2.COLOR_GRAY2BGR)

        for i, contour in enumerate(contours):
            if cv2.contourArea(contour) >= self.min_contour_area:
                # Generate a random color for each contour
                color = tuple(np.random.randint(0, 256, size=3).tolist())
                # Draw the contour on the image
                cv2.drawContours(image_with_contours, [contour], -1, color, 2)
                mean_amplitude = self.mean_amplitudes.get(i, 0)
                if mean_amplitude > 0:
                    # Draw the mean amplitude near the contour
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.putText(image_with_contours, f"{mean_amplitude:.2f}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        self.contours = contours
        return image_with_contours

    def process_contour(self):
        """
        Processes contours by applying morphological operations, finding and drawing contours,
        and calculating mean amplitudes for the found contours.
        """
        processed_image = self.apply_morphological_operations(self.segmented_image)
        # Display normalized depth map (commented out)
        # show_image('Normalized Depth Map', processed_image)
        processed_image_with_contours = self.find_and_draw_contours(processed_image)

        self.mean_amplitudes = self.calculate_mean_amplitude(self.contours)
        for idx, mean_amplitude in self.mean_amplitudes.items():
            print(f'Contour {idx} : Mean Amplitude = {mean_amplitude:.2f}')
        # Display image with contours and mean amplitudes (commented out)
        processed_image_with_contours = self.find_and_draw_contours(processed_image)
        show_image('Image with Contours and Means', processed_image_with_contours)
        cv2.imwrite('contour.png', processed_image_with_contours)

    def process_disparity_image(self):
        """
        Processes the disparity image by segmenting it according to the defined thresholds,
        and then applying contour processing on each segment.
        """
        # Display normalized disparity map (commented out)
        # show_image('Normalized Disparity Map', self.depth_map_normalized)

        for i in range(len(self.thresholds) - 1):
            lower_thresh = self.thresholds[i]
            upper_thresh = self.thresholds[i + 1]
            # Create a mask for the current threshold
            mask = cv2.inRange(self.depth_map_normalized, lower_thresh, upper_thresh)
            # Apply the mask to extract the region of interest
            self.segmented_image = cv2.bitwise_and(self.depth_map_normalized, self.depth_map_normalized, mask=mask)

            hist = calculate_histogram(self.segmented_image)
            non_zero_count = count_non_zero_pixels_from_histogram(hist)

            if non_zero_count >= self.pixel_min:
                # Display the segment (commented out)
                # show_image(f'Segment {i + 1}: {lower_thresh} - {upper_thresh}', self.segmented_image)
                print(f'Number of non-zero pixels for segment {i + 1} ({lower_thresh} - {upper_thresh}): {non_zero_count}')
                self.process_contour()
            else:
                print(f'Segment {i + 1} ({lower_thresh} - {upper_thresh}) rejected: too few non-zero pixels ({non_zero_count})')


def calculate_histogram(image):
    """
    Calculates the histogram of pixel values of the image.

    :param image: Image to analyze
    :return: Histogram of pixel values
    """
    hist = cv2.calcHist([image], [0], None, [256], [0, 256])
    return hist.flatten()


def count_non_zero_pixels_from_histogram(hist):
    """
    Counts the number of non-zero pixels from the pixel value histogram.

    :param hist: Histogram of pixel values
    :return: Total number of non-zero pixels
    """
    return int(np.sum(hist[1:]))


def plot_histogram(title, hist):
    """
    Plots and displays the histogram of pixel values.

    :param title: Title of the graph
    :param hist: Histogram of pixel values
    """
    plt.figure(figsize=(8, 6))
    plt.title(title)
    plt.plot(hist, color='blue')
    plt.xlabel('Disparity Value')
    plt.ylabel('Number of Pixels')
    plt.show()
