import os
import cv2
import numpy as np
from exception import file_create


class StereoCalibration:
    def __str__(self):
        """Returns a string representation of the class attributes."""
        output = ""
        for key, item in self.__dict__.items():
            output += key + ":\n"
            output += str(item) + "\n"
        return output

    def __init__(self):
        """Initializes the StereoCalibration class with default parameters."""
        #: Camera matrices (intrinsic parameters)
        self.cam_mats = {"left": None, "right": None}
        #: Distortion coefficients (D)
        self.dist_coefs = {"left": None, "right": None}
        #: Rotation matrix (R)
        self.rot_mat = None
        #: Translation vector (T)
        self.trans_vec = None
        #: Essential matrix (E)
        self.e_mat = None
        #: Fundamental matrix (F)
        self.f_mat = None
        #: Rectification transforms (3x3 rectification matrices R1 / R2)
        self.rect_trans = {"left": None, "right": None}
        #: Projection matrices (3x4 projection matrices P1 / P2)
        self.proj_mats = {"left": None, "right": None}
        #: Disparity-to-depth mapping matrix (4x4 matrix, Q)
        self.disp_to_depth_mat = None
        #: Bounding boxes for valid pixels
        self.valid_boxes = {"left": None, "right": None}
        #: Undistortion maps for remapping
        self.undistortion_map = {"left": None, "right": None}
        #: Rectification maps for remapping
        self.rectification_map = {"left": None, "right": None}

    def save_data(self):
        """Saves calibration data to .npy and .csv files."""
        try:
            for key, item in self.__dict__.items():
                if isinstance(item, dict):
                    # Save data for each side (left, right) if it is a dictionary
                    for side in ("left", "right"):
                        filename = f"{key}_{side}"
                        file_create(self.__dict__[key][side], filename, 'npy', 'data')
                        file_create(self.__dict__[key][side], filename, 'csv', 'data')
                else:
                    # Save data for non-dictionary attributes
                    file_create(self.__dict__[key], key, 'npy', 'data')
                    file_create(self.__dict__[key], key, 'csv', 'data')

        except Exception as e:
            print(f"Error saving data to 'data': {e}")

    def rectify(self, frames):
        """Rectifies stereo images using the undistortion and rectification maps."""
        new_frames = []
        for i, side in enumerate(("left", "right")):
            # Apply remapping to correct distortion and rectify images
            new_frames.append(cv2.remap(frames[i],
                                        self.undistortion_map[side],
                                        self.rectification_map[side],
                                        cv2.INTER_NEAREST))
        return new_frames

    def load_data(self, directory):
        """Loads calibration parameters from .npy files in the specified directory."""
        try:
            for key in self.__dict__.keys():
                if isinstance(self.__dict__[key], dict):
                    for side in ("left", "right"):
                        filename = f"{directory}/{key}_{side}.npy"
                        if os.path.exists(filename):
                            # Load data for each side (left, right) from .npy files
                            self.__dict__[key][side] = np.load(filename)
                        else:
                            print(f"File {filename} not found.")
                else:
                    filename = f"{directory}/{key}.npy"
                    if os.path.exists(filename):
                        # Load data for non-dictionary attributes from .npy files
                        self.__dict__[key] = np.load(filename)
                    else:
                        print(f"File {filename} not found.")
            print("Data loading completed successfully.")
        except Exception as e:
            print(f"Error loading data: {e}")


class Calibrator:
    def __init__(self, row, column, square_size, image_size):
        """Initializes the Calibrator class with chessboard and image parameters."""
        #: Number of calibration images
        self.image_count = 0
        #: Number of inside corners in the chessboard's rows
        self.row = row
        #: Number of inside corners in the chessboard's columns
        self.column = column
        #: Size of chessboard squares in centimeters
        self.square_size = square_size
        #: Size of calibration images in pixels
        self.image_size = image_size
        #: 3D coordinates of chessboard corners
        pattern_size = (self.row, self.column)
        corner_coordinates = np.zeros((np.prod(pattern_size), 3), np.float32)
        corner_coordinates[:, :2] = np.indices(pattern_size).T.reshape(-1, 2)
        corner_coordinates *= self.square_size
        #: Real world corner coordinates found in each image
        self.corner_coordinates = corner_coordinates
        #: List of real world corner coordinates to match the corners found
        self.object_points = []
        #: List of found corner coordinates from calibration images for left and right cameras
        self.image_points = {"left": [], "right": []}

    def corner_detect(self, image_pair):
        """Detects and refines chessboard corners in a pair of images."""
        side = "left"
        self.object_points.append(self.corner_coordinates)

        for image in image_pair:
            img = np.copy(image)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, (self.row, self.column))
            if ret:
                # Draw the detected corners on the image
                cv2.drawChessboardCorners(img, (self.column, self.row), corners, ret)
                cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                 (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 30, 0.01))
                # Save the image with detected corners
                name = "corner/" + side + str(self.image_count + 1).zfill(2) + "corn"
                file_create(img, name, 'png')

            # Append detected corners to the list of image points
            self.image_points[side].append(corners.reshape(-1, 2))
            side = "right"
        self.image_count += 1

    def calibrate_camera(self):
        """Calibrates the stereo cameras and computes the calibration matrices."""
        criteria = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS,
                    100, 1e-5)
        flags = (cv2.CALIB_FIX_ASPECT_RATIO + cv2.CALIB_ZERO_TANGENT_DIST +
                 cv2.CALIB_SAME_FOCAL_LENGTH)
        calib = StereoCalibration()

        # Perform stereo calibration
        (calib.cam_mats["left"], calib.dist_coefs["left"],
         calib.cam_mats["right"], calib.dist_coefs["right"],
         calib.rot_mat, calib.trans_vec, calib.e_mat, calib.f_mat) = cv2.stereoCalibrate(self.object_points,
                                                                                         self.image_points["left"],
                                                                                         self.image_points["right"],
                                                                                         calib.cam_mats["left"],
                                                                                         calib.dist_coefs["left"],
                                                                                         calib.cam_mats["right"],
                                                                                         calib.dist_coefs["right"],
                                                                                         self.image_size,
                                                                                         calib.rot_mat,
                                                                                         calib.trans_vec,
                                                                                         calib.e_mat,
                                                                                         calib.f_mat,
                                                                                         criteria=criteria,
                                                                                         flags=flags)[1:]
        print("Step 1 complete")
        # Compute rectification transforms for the images
        (calib.rect_trans["left"], calib.rect_trans["right"],
         calib.proj_mats["left"], calib.proj_mats["right"],
         calib.disp_to_depth_mat, calib.valid_boxes["left"],
         calib.valid_boxes["right"]) = cv2.stereoRectify(calib.cam_mats["left"],
                                                         calib.dist_coefs["left"],
                                                         calib.cam_mats["right"],
                                                         calib.dist_coefs["right"],
                                                         self.image_size,
                                                         calib.rot_mat,
                                                         calib.trans_vec,
                                                         flags=0)
        print("Step 2 complete")
        # Compute remapping elements for rectification
        for side in ("left", "right"):
            (calib.undistortion_map[side],
             calib.rectification_map[side]) = cv2.initUndistortRectifyMap(
                calib.cam_mats[side],
                calib.dist_coefs[side],
                calib.rect_trans[side],
                calib.proj_mats[side],
                self.image_size,
                cv2.CV_32FC1)
        print("Step 3 complete")
        return calib

    def calibration_process(self, nbr_photo, image_folder):
        """Carries out the calibration process using a specified number of photos in the given folder."""
        photo_counter = 0
        print('Start Calibration')
        print('Start reading images')

        while photo_counter != nbr_photo:
            photo_counter += 1
            print('Importing pair No ' + str(photo_counter))
            left_name = image_folder + '/left' + str(photo_counter).zfill(2) + '.jpg'
            right_name = image_folder + '/right' + str(photo_counter).zfill(2) + '.jpg'

            if os.path.isfile(left_name) and os.path.isfile(right_name):
                img_left = cv2.imread(left_name, 1)
                img_right = cv2.imread(right_name, 1)
                self.corner_detect((img_left, img_right))

        print('End of cycle')
        print('Starting calibration... This may take several minutes!')
        calib = self.calibrate_camera()
        print('Calibration complete!')

        print('Saving data')
        calib.save_data()
        print('Data saving completed')

        return calib
