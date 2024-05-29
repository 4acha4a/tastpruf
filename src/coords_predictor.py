from platform_detector import PlatformCoordsPredictor

coords = PlatformCoordsPredictor("screw_weights.pth").predict_coords("./spike/camera_image.jpg")

f = open("coords.txt", "w")
f.write(str(coords), "w")
