from PIL import Image
import glob 
import os

def convert_to_individual():
    images = glob.glob("./Panoramas/*.png")
    for image in images:
        split_cube_map(image)

def split_cube_map(image_path):
    cube_map = Image.open(image_path)
    width, height = cube_map.size
    if width % 6 != 0:
        raise ValueError("Image width must be divisible by 6")
    face_width = width // 6

    faces = {
        "pX": (0, 0, face_width, height),
        "nX": (face_width, 0, 2 * face_width, height),
        "pY": (2 * face_width, 0, 3 * face_width, height),
        "nY": (3 * face_width, 0, 4 * face_width, height),
        "pZ": (4 * face_width, 0, 5 * face_width, height),
        "nZ": (5 * face_width, 0, 6 * face_width, height),
    }

    for coord, (left, top, right, bottom) in faces.items():
        face = cube_map.crop((left, top, right, bottom))
        face.save(f"./Panoramas/individual/{os.path.basename(image_path)}_{coord}.png")

convert_to_individual()