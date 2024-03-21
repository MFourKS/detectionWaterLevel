import torch
import torch.nn as nn



class YOLOv7(nn.Module):
    def __init__(self, num_classes):
        super(YOLOv7, self).__init__()
        self.num_classes = num_classes


        self.conv1 = nn.Conv2d(in_channels=3, out_channels=32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=2, padding=1)
        self.conv3 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, stride=2, padding=1)
        self.conv4 = nn.Conv2d(in_channels=128, out_channels=256, kernel_size=3, stride=2, padding=1)
        self.conv5 = nn.Conv2d(in_channels=256, out_channels=512, kernel_size=3, stride=2, padding=1)
        self.conv6 = nn.Conv2d(in_channels=512, out_channels=1024, kernel_size=3, stride=2, padding=1)

        self.fc1 = nn.Linear(1024 * 7 * 7, 4096)
        self.fc2 = nn.Linear(4096,
                             num_classes * 6)

    def forward(self, x):
        x = self.conv1(x)
        x = nn.functional.relu(x)
        x = self.conv2(x)
        x = nn.functional.relu(x)
        x = self.conv3(x)
        x = nn.functional.relu(x)
        x = self.conv4(x)
        x = nn.functional.relu(x)
        x = self.conv5(x)
        x = nn.functional.relu(x)
        x = self.conv6(x)
        x = nn.functional.relu(x)

        x = x.view(x.size(0), -1)

        x = self.fc1(x)
        x = nn.functional.relu(x)
        x = self.fc2(x)

        return x

class YOLOLoss(nn.Module):
    def __init__(self, num_classes=1, lambda_coord=5, lambda_noobj=0.5):
        super(YOLOLoss, self).__init__()
        self.num_classes = num_classes
        self.lambda_coord = lambda_coord
        self.lambda_noobj = lambda_noobj

    def forward(self, outputs, targets):
        batch_size = outputs.size(0)
        grid_size = outputs.size(2)
        stride = 640 // grid_size

        class_predictions = outputs[:, :self.num_classes, :, :]
        box_predictions = outputs[:, self.num_classes:, :, :].view(batch_size, -1, grid_size, grid_size, 6)


        class_targets = targets[:, :, 0].long().unsqueeze(2)
        box_targets = targets[:, :, 1:6].unsqueeze(3)
        objectness_targets = targets[:, :, 6].unsqueeze(2)


        objectness_loss = nn.BCEWithLogitsLoss()(box_predictions[..., 0], objectness_targets)


        class_loss = nn.CrossEntropyLoss()(class_predictions.view(-1, self.num_classes), class_targets.view(-1))



        x_pred, y_pred, w_pred, h_pred, angle_pred = box_predictions[..., 1], box_predictions[..., 2], \
            box_predictions[..., 3], box_predictions[..., 4], \
            box_predictions[..., 5]
        x_target, y_target, w_target, h_target, angle_target = box_targets[..., 0], box_targets[..., 1], \
            box_targets[..., 2], box_targets[..., 3], \
            box_targets[..., 4]


        coord_loss = (torch.sqrt(torch.pow(x_pred - x_target, 2) + torch.pow(y_pred - y_target, 2)) +
                      torch.sqrt(torch.pow(w_pred - w_target, 2) + torch.pow(h_pred - h_target, 2)) +
                      torch.abs(angle_pred - angle_target)).mean()


        total_loss = self.lambda_coord * coord_loss + class_loss + self.lambda_noobj * objectness_loss

        return total_loss
