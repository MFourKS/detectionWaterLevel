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

# Check if GPU is available, else use CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Define paths to training and validation data
train_image_dir = "C:/Users/maksp/Downloads/miniproject-water-.v5i.yolov7pytorch/train/images"
train_label_dir = "C:/Users/maksp/Downloads/miniproject-water-.v5i.yolov7pytorch/train/labels"
valid_image_dir = "C:/Users/maksp/Downloads/miniproject-water-.v5i.yolov7pytorch/valid/images"
valid_label_dir = "C:/Users/maksp/Downloads/miniproject-water-.v5i.yolov7pytorch/valid/labels"

# Define transforms for preprocessing images
transform = transforms.Compose([
    transforms.Resize((640, 640)),
    transforms.ToTensor(),
])

# Create custom datasets for training and validation
train_dataset = CustomDataset(train_image_dir, train_label_dir, transform=transform)
valid_dataset = CustomDataset(valid_image_dir, valid_label_dir, transform=transform)

# Define batch size and number of epochs
batch_size = 8
epochs = 20

# Create data loaders
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
valid_loader = DataLoader(valid_dataset, batch_size=batch_size, shuffle=False)

# Initialize YOLOv7 model
model = YOLOv7(num_classes=1).to(device)

# Define optimizer and loss function
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
loss_fn = YOLOLoss()

# Training loop
for epoch in range(epochs):
    model.train()
    train_loss = 0.0

    for images, targets in train_loader:
        images, targets = images.to(device), targets.to(device)

        # Forward pass
        outputs = model(images)

        # Compute loss
        loss = loss_fn(outputs, targets)

        # Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        train_loss += loss.item()

    train_loss /= len(train_loader)

    # Validation
    model.eval()
    valid_loss = 0.0

    with torch.no_grad():
        for images, targets in valid_loader:
            images, targets = images.to(device), targets.to(device)

            # Forward pass
            outputs = model(images)

            # Compute loss
            loss = loss_fn(outputs, targets)
            valid_loss += loss.item()

        valid_loss /= len(valid_loader)

    print(f"Epoch [{epoch + 1}/{epochs}], Train Loss: {train_loss:.4f}, Valid Loss: {valid_loss:.4f}")

# Save trained model
torch.save(model.state_dict(), "yolov7_model.pth")
