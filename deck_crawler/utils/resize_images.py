import argparse
import os

from PIL import Image
from tqdm import tqdm

IMAGE_OUTPUT_SIZE = (600, 838)


def is_tuple_of_two_ints(input):
    # Check if the input is a tuple
    if not isinstance(input, tuple):
        return False

    # Check if the tuple has exactly 2 elements
    if len(input) != 2:
        return False

    # Check if both elements are integers
    if not isinstance(input[0], int) or not isinstance(input[1], int):
        return False

    return True


def resize_images(input_folder, output_folder, shape=None):
    """
    Resize all images in the input folder to the size
    specified by the IMAGE_OUTPUT_SIZE
    constant and save the resized images to the output folder.

    Parameters:
    input_folder (str):
    path to the folder containing the images to be resized

    output_folder (str):
    path to the folder where the resized images will be saved

    Returns:
    None
    """
    if not is_tuple_of_two_ints(shape):
        shape = IMAGE_OUTPUT_SIZE

    # create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # loop through all imgs in the input folder
    pbar = tqdm(os.listdir(input_folder))
    for img in pbar:
        pbar.set_description(f"Resizing: {img}")

        # check if the img is an image
        if img.endswith(".jpg") or img.endswith(".png"):
            # open the image
            image = Image.open(os.path.join(input_folder, img))
            # resize the image
            image = image.resize(shape)
            # save the resized image to the output folder
            image.save(os.path.join(output_folder, img))


def main():
    # parse the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input_folder",
        required=True,
        help="path to the folder containing the images to be resized",
    )
    parser.add_argument(
        "-o",
        "--output_folder",
        required=True,
        help="path to the folder where the resized images will be saved",
    )
    args = parser.parse_args()

    # resize the images
    resize_images(args.input_folder, args.output_folder)


if __name__ == "__main__":
    main()
