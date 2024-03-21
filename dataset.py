import os
from PIL import Image
import torch
from torch.utils.data import Dataset
from torchvision.transforms import functional as F


class CustomDataset(Dataset):
    def __init__(self, image_dir, label_dir, transform=None):
        self.image_dir = image_dir
        self.label_dir = label_dir
        self.transform = transform
        self.image_names = os.listdir(image_dir)

    def __len__(self):
        return len(self.image_names)

    def __getitem__(self, idx):
        img_name = os.path.join(self.image_dir, self.image_names[idx])
        label_name = os.path.join(self.label_dir, os.path.splitext(self.image_names[idx])[0] + ".txt")

        image = Image.open(img_name).convert("RGB")
        image = self.auto_orient_image(image)  # Auto-orient image

        # Resize image to 640x640
        image = F.resize(image, (640, 640))

        labels = self.parse_label(label_name)

        if self.transform:
            image = self.transform(image)

        return image, labels

    def read_polygon_vertices(file_path):
        with open(file_path, 'r') as file:
            vertices = []
            for line in file:
                values = line.strip().split()
                for value in values:
                    try:
                        vertices.append(float(value))
                    except ValueError:
                        print(f"Ignoring non-numeric value: {value}")
                        continue
        return vertices

    file_path = "polygon_vertices.txt"
    polygon_vertices = read_polygon_vertices(file_path)
    print("Polygon vertices:", polygon_vertices)

    def auto_orient_image(self, image):
        exif = image.getexif()
        if exif is not None:
            orientation = exif.get(0x0112)
            if orientation is not None:
                if orientation == 3:
                    image = F.rotate(image, 180)
                elif orientation == 6:
                    image = F.rotate(image, -90, expand=True)
                elif orientation == 8:
                    image = F.rotate(image, 90, expand=True)
        return image
