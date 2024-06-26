# -*- coding: utf-8 -*-
"""platform_detector.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/119_dzp3hiyZ609Sy5odUNughEWyIwD_P

# **Platform detector**

**Load data from Google Drive**
"""

"""**Import all libraries**"""

import numpy as np
import torch
import torch.nn as nn
import torchvision
# from torchvision.tv_tensors import Mask
from torchvision.transforms import v2 as T
import random
# from PIL import Image
import cv2
import math as m 
# import PIL.ImageDraw as ImageDraw
# import PIL.Image as Image

# Fix random seed
random.seed(0)
torch.manual_seed(0)

"""**Assign ROOT_FOLDER to folder containing dataset and masks**"""

# Commented out IPython magic to ensure Python compatibility.
ROOT_FOLDER = './'

assert ROOT_FOLDER is not None, "[!] Enter the foldername."

"""**Select device**"""

device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Необходимые преобразования 
def get_transform():
    transforms = []
    transforms.append(T.ToImage())
    transforms.append(T.Resize(size=(800, 600), antialias=True))
    transforms.append(T.ToDtype(torch.float, scale=True))
    transforms.append(T.Normalize(
            mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
        ))
    return T.Compose(transforms)

# Предобученная модель с весами weights_path, распознающими края платформы
class PlatformCoordsPredictor(nn.Module):
    def __init__(self, weights_path):
        super(PlatformCoordsPredictor, self).__init__()
        self.model = torchvision.models.segmentation.fcn_resnet50(weights="DEFAULT")
        self.model.classifier[4] = nn.Conv2d(512, 2, 1)
        self.model.load_state_dict(torch.load(weights_path,map_location=device))

    def forward(self, x):
        x = self.model(x)
        return x

    def predict_coords(self, image):
        coords = []
        pos_to_coords = {}
        image = cv2.imread(image)
        h_init, w_init,_ = image.shape
        transform = get_transform()
        image = transform(image).to(device)
        _, h, w = image.size()
        image = image.unsqueeze(0)
        self.model.eval()
        outputs = self.model(image)['out'] 
        platform_mask = (outputs.argmax(1) == 1).cpu().numpy().astype(np.uint8)
        contours,_ = cv2.findContours(platform_mask[0], cv2.RETR_TREE,
                                cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            M = cv2.moments(contour)
            if M['m00'] != 0.0:
                x = int(M['m10']/M['m00'] * w_init / w) # координата х центра шурупа
                y = int(M['m01']/M['m00'] * h_init / h) # координата у центра шурупа
                coords.append([x, y])
        dists = [m.sqrt(x*x + y*y) for (x, y) in coords]
        inverse_dists = [m.sqrt((h_init - x)*(h_init - x) + y*y) for (x, y) in coords]
        max_dist = max(dists)
        max_inv_dist = max(inverse_dists)
        min_dist = min(dists)
        min_inv_dist = min(inverse_dists)
        # Для задания системы координат необходимо знать расположение точек друг относительно друга
        for coord in coords:
            x = coord[0]
            y = coord[1]
            dist = m.sqrt(x*x + y*y)
            inverse_dist = m.sqrt((h_init - x)*(h_init - x) + y*y)
            if dist == min_dist:
                pos_to_coords["top_left"] = coord
                continue
            if dist == max_dist:
                pos_to_coords["bottom_right"] = coord
                continue
            if inverse_dist == min_inv_dist:
                pos_to_coords["top_right"] = coord
                continue
            if inverse_dist == max_inv_dist:
                pos_to_coords["bottom_left"] = coord 
                continue
        # print(pos_to_coords)
        return pos_to_coords
    
    # def get_coords_position(coords, image):
    #     inverse_dist_min = 2^32-1
    #     dist_min = 2^32-1
    #     inverse_dist_max = 0
    #     dist_max = 0
    #     for coord in coords:
    #         for x,y in coord:
    #             dist = 




# def get_model(num_classes):
#     model = torchvision.models.segmentation.fcn_resnet50(weights='DEFAULT')
#     model.classifier[4] = nn.Conv2d(512, num_classes, 1)
#     model.to(device)
#     model.load_state_dict(torch.load(ROOT_FOLDER + '/screw_weights.pth',map_location=device))
#     return model

# """**Additional functions for dataset and model**"""

# def points_to_keypoints_tensor(points):
#     keypoints = torch.zeros(1, len(points) // 2, 2, dtype=torch.float)
#     xs = torch.zeros(len(points) // 2)
#     ys = torch.zeros(len(points) // 2)
#     for index in range(len(points)):
#         if index % 2 == 0:
#             xs[index // 2] = points[index]
#         else:
#             ys[index // 2] = points[index]
#     for index in range(len(xs)):
#         keypoints[0, index, 0] = xs[index]
#         keypoints[0, index, 1] = ys[index]
#     return keypoints

# def coords_to_masks(coords):
#     result = torch.zeros(2, 800, 600)
#     xs = []
#     ys = []
#     platform_image = Image.new(mode='L',size=(600, 800), color=0)
#     background_image = Image.new(mode='L',size=(600, 800), color=255)
#     for point in coords:
#         xs.append(float(point[0]))
#         ys.append(float(point[1]))
#     polygon_shape = [(x, y) for x, y in zip(xs, ys)]
#     platform_draw = ImageDraw.Draw(platform_image)
#     background_draw = ImageDraw.Draw(background_image)
#     offset = 7.5
#     for coord in polygon_shape:
#       x0 = coord[0] - offset
#       y0 = coord[1] - offset
#       x1 = coord[0] + offset
#       y1 = coord[1] + offset
#       platform_draw.ellipse([(x0, y0), (x1, y1)], outline="white", fill="white")
#       background_draw.ellipse([(x0, y0), (x1, y1)], outline="black", fill="black")
#     result[1] = Mask(platform_image)
#     result[0] = Mask(background_image)
#     return result.to(device)

# """**Model evaluation**"""

# def coords_from_mask_prediction(image, model):
#     transform = get_transform(train=False)
#     image = transform(image).to(device)
#     image = image.unsqueeze(0) # add a batch dimension
#     outputs = model(image)['out']
#     platform_mask = (outputs.argmax(1) == 1).cpu().numpy().astype(np.uint8)
#     contours,_ = cv2.findContours(platform_mask[0], cv2.RETR_TREE,
#                             cv2.CHAIN_APPROX_SIMPLE)
#     approx_polygon = cv2.approxPolyDP(contours[0], 0.02 * cv2.arcLength(contours[0], True), True)
#     return approx_polygon

def predict_coords(image, model):
    coords = []
    h_init, w_init, _ = image.shape
    # print(w_init)
    transform = get_transform(train=False)
    image = transform(image).to(device)
    # print(image.size())
    _, h, w = image.size()
    image = image.unsqueeze(0) # add a batch dimension
    outputs = model(image)['out']
    platform_mask = (outputs.argmax(1) == 1).cpu().numpy().astype(np.uint8)
    contours,_ = cv2.findContours(platform_mask[0], cv2.RETR_TREE,
                            cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
      M = cv2.moments(contour)
      if M['m00'] != 0.0:
          x = int(M['m10']/M['m00'] * w_init / w)
          y = int(M['m01']/M['m00'] * h_init / h)
          coords.append([x, y])
    return np.array(coords)