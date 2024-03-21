# pip install torch
# pip install torchvision
# pip install utils

import os
import torch
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from dataset import CustomDataset
from model import YOLOv7, YOLOLoss
from utils import *


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


train_image_dir = "C:/Users/maksp/Downloads/miniproject-water-.v5i.yolov7pytorch/train/images"
train_label_dir = "C:/Users/maksp/Downloads/miniproject-water-.v5i.yolov7pytorch/train/labels"
valid_image_dir = "C:/Users/maksp/Downloads/miniproject-water-.v5i.yolov7pytorch/valid/images"
valid_label_dir = "C:/Users/maksp/Downloads/miniproject-water-.v5i.yolov7pytorch/valid/labels"


transform = transforms.Compose([
    transforms.Resize((640, 640)),
    transforms.ToTensor(),
])


train_dataset = CustomDataset(train_image_dir, train_label_dir, transform=transform)
valid_dataset = CustomDataset(valid_image_dir, valid_label_dir, transform=transform)


batch_size = 8
epochs = 20


train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
valid_loader = DataLoader(valid_dataset, batch_size=batch_size, shuffle=False)


model = YOLOv7(num_classes=1).to(device)


optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
loss_fn = YOLOLoss()


for epoch in range(epochs):
    model.train()
    train_loss = 0.0

    for images, targets in train_loader:
        images, targets = images.to(device), targets.to(device)


        outputs = model(images)


        loss = loss_fn(outputs, targets)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        train_loss += loss.item()

    train_loss /= len(train_loader)


    model.eval()
    valid_loss = 0.0

    with torch.no_grad():
        for images, targets in valid_loader:
            images, targets = images.to(device), targets.to(device)


            outputs = model(images)


            loss = loss_fn(outputs, targets)
            valid_loss += loss.item()

        valid_loss /= len(valid_loader)

    print(f"Epoch [{epoch + 1}/{epochs}], Train Loss: {train_loss:.4f}, Valid Loss: {valid_loss:.4f}")


torch.save(model.state_dict(), "yolov7_model.pth")
