import os
import cv2
import numpy as np
import csv


def create_folder(folder):
    """
    This function checks if the folder exists, if not, it creates it.

    :param folder: The path of the folder to check/create
    """
    if not os.path.exists(folder):
        # If the folder does not exist, try to create it
        try:
            # Create the folder with permissions 777 (read, write, execute for everyone)
            os.makedirs(folder, mode=0o777, exist_ok=False)
            print(f"Folder '{folder}' has been created.")
        except Exception as e:
            # If an error occurs while creating the folder, print an error message
            print(f"An error occurred while creating the folder '{folder}': {e}")
    else:
        # If the folder already exists, inform the user
        print(f"Folder '{folder}' already exists.")


def create_file(data, file_name, file_type, folder_name=None):
    """
    This function creates a file of the specified type in the given folder (optional).

    :param data: Data to save in the file
    :param file_name: Name of the file to create (without extension)
    :param file_type: Type of file to create ('csv', 'image', 'npy', etc.)
    :param folder_name: Folder in which to create the file (optional)
    """
    # Build the full file path
    if folder_name:
        name = folder_name + '/' + file_name + '.' + file_type
    else:
        name = file_name + '.' + file_type

    try:
        # Check the file type and call the appropriate write function
        if file_type in ['jpg', 'png']:
            # For images (jpg, png formats), use OpenCV to save the image
            cv2.imwrite(name, data)

        elif file_type == 'npy':
            # For NumPy files (.npy), use NumPy to save the data
            np.save(name, data)

        elif file_type == 'csv':
            # For CSV files, use the csv module to write the data
            with open(name, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                for row in data:
                    processed_row = []
                    for item in row:
                        if isinstance(item, (int, float)):
                            # If the item is a number, convert it to a string and replace the dot with a comma
                            processed_row.append(str(item).replace('.', ','))
                        else:
                            processed_row.append(item)
                    writer.writerow(processed_row)

    except Exception as e:
        # In case of an error while creating the file, print an error message
        print(f"An error occurred while creating the file '{name}': {e}")


def show_image(title, image, cmap='gray'):
    """
    Displays an image with the specified colormap.

    :param title: Title of the image window
    :param image: Image to display
    :param cmap: Colormap to apply to the image (default is 'gray')
    """
    # List of different OpenCV colormaps to apply colors
    colormaps = {
        "autumn": cv2.COLORMAP_AUTUMN,
        "bone": cv2.COLORMAP_BONE,
        "jet": cv2.COLORMAP_JET,
        "winter": cv2.COLORMAP_WINTER,
        "rainbow": cv2.COLORMAP_RAINBOW,
        "ocean": cv2.COLORMAP_OCEAN,
        "summer": cv2.COLORMAP_SUMMER,
        "spring": cv2.COLORMAP_SPRING,
        "cool": cv2.COLORMAP_COOL,
        "hsv": cv2.COLORMAP_HSV,
        "pink": cv2.COLORMAP_PINK,
        "hot": cv2.COLORMAP_HOT,
        "parula": cv2.COLORMAP_PARULA,
        "magma": cv2.COLORMAP_MAGMA,
        "inferno": cv2.COLORMAP_INFERNO,
        "plasma": cv2.COLORMAP_PLASMA,
        "viridis": cv2.COLORMAP_VIRIDIS,
        "cividis": cv2.COLORMAP_CIVIDIS,
        "twilight": cv2.COLORMAP_TWILIGHT,
        "twilight_shifted": cv2.COLORMAP_TWILIGHT_SHIFTED,
        "turbo": cv2.COLORMAP_TURBO,
        "deepgreen": cv2.COLORMAP_DEEPGREEN
    }
    if cmap in colormaps:
        image = cv2.applyColorMap(image, colormaps[cmap])
    elif cmap != 'gray':
        print("The selected color is not available. Default color applied")
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
