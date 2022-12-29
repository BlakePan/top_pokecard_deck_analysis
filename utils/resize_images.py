import os
import argparse
from tqdm import tqdm
from PIL import Image

IMAGE_OUTPUT_SIZE = (600, 838)


def resize_images(input_folder, output_folder):
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
    # create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # get the total number of images in the input folder
    num_images = len(
        [
            file
            for file in os.listdir(input_folder)
            if file.endswith(".jpg") or file.endswith(".png")
        ]
    )

    # loop through all files in the input folder
    for file in tqdm(os.listdir(input_folder), total=num_images):
        # check if the file is an image
        if file.endswith(".jpg") or file.endswith(".png"):
            # open the image
            image = Image.open(os.path.join(input_folder, file))
            # resize the image
            image = image.resize(IMAGE_OUTPUT_SIZE)
            # save the resized image to the output folder
            image.save(os.path.join(output_folder, file))


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
