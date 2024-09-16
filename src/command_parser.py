from image_detector import find_optimal_scale, match_images, find_rect_center, get_platform_size
from platform_detector import PlatformCoordsPredictor
from capture_and_transfer import capture_image

# offset_x = 33 + 21
# offset_y = 10
# const_offset_screw = 5

class Parameters:
  def __init__(self, offset_x=None, offset_y=None, const_offset_screw=None, platform_coords=None):
    self.offset_x = offset_x
    self.offset_y = offset_y
    self.const_offset_screw = const_offset_screw
    self.platform_coords = platform_coords

class Command:
  def __init__(self, img_from_camera, params):
    self.img_from_camera = img_from_camera
    self.params = params
  def perform():
    return None

class SetScreenCommand(Command):
    def __init__(self, img_from_camera, params):
      super().__init__(img_from_camera, params)
    def perform(self, screen_img):
      return find_optimal_scale(screen_img, self.params.platform_coords)
  
class SetCameraCommand(Command):
    def __init__(self, img_from_camera, params):
      super().__init__(img_from_camera, params)
    def perform(self, screen_img):
      return find_optimal_scale(screen_img, self.params.platform_coords)
    
class FindCommand(Command):
  def __init__(self, img_from_camera, params):
    super().__init__(img_from_camera, params)
  def img_coords_to_gcode_coords(self, point):
    h_platform, w_platform = get_platform_size(self.params.platform_coords)
    pixels_per_millimeter_x = w_platform / 208
    pixels_per_millimeter_y = h_platform / 208
    btr = self.params.platform_coords["bottom_right"]
    new_point = (btr[0] - point[0], btr[1] - point[1])
    X = new_point[0] / pixels_per_millimeter_x - self.params.offset_x - self.params.const_offset_screw  # offset_x = 56, const_offset_screw = 5.5 
    Y = new_point[1] / pixels_per_millimeter_y - self.params.offset_y - self.params.const_offset_screw  # offset_x = 29, const_offset_screw = 5.5 
    return (X, Y)
  def perform(self, key_img, screen_img):
    scale = SetScreenCommand(self.img_from_camera, self.params).perform(screen_img)
    top_left, bottom_right, score = match_images(self.img_from_camera, key_img, self.params.platform_coords, scale)
    if score > 0.1:
      return find_rect_center((top_left, bottom_right))
    else:
      return (-1, -1)

class TapCommand(Command):
  def __init__(self, img_from_camera, params):
    super().__init__(img_from_camera, params)
  def perform(self, key_img, screen_img):
    if (FindCommand(self.img_from_camera, self.params).perform(key_img, screen_img)[0] != -1) and (FindCommand(self.img_from_camera, self.params).perform(key_img, screen_img)[1] != -1):
      point_coords = FindCommand(self.img_from_camera, self.params).perform(key_img, screen_img)
      gcode_coords = FindCommand(self.img_from_camera, self.params).img_coords_to_gcode_coords(point_coords)
      gcode = "G00 X" + str(gcode_coords[0]) + " Y" + str(gcode_coords[1]) + " Z8\nG4 P100\nG00 Z0\nG4 P100\nG00 Z8"
      gcode_lines = gcode.split('\n')
      # print(gcode)
      return gcode_lines
    else:
      return "M81"
    
class SwipeCommand(Command):
  def __init__(self, img_from_camera, params):
    super().__init__(img_from_camera, params)
  def perform(self, img1, img2, screen_img):
    if (FindCommand(self.img_from_camera, self.params).perform(img1, screen_img)[0] != -1) and (FindCommand(self.img_from_camera, self.params).perform(img1, screen_img)[1] != -1):
      if (FindCommand(self.img_from_camera, self.params).perform(img2, screen_img)[0] != -1) and (FindCommand(self.img_from_camera, self.params).perform(img2, screen_img)[1] != -1):
        point1_coords = FindCommand(self.img_from_camera, self.params).perform(img1, screen_img)
        point2_coords = FindCommand(self.img_from_camera, self.params).perform(img2, screen_img)
        gcode1_coords = list(FindCommand(self.img_from_camera, self.params).img_coords_to_gcode_coords(point1_coords))
        gcode2_coords = list(FindCommand(self.img_from_camera, self.params).img_coords_to_gcode_coords(point2_coords))
        gcode = "G00 X" + str(gcode1_coords[0] + 3) + " Y" + str(gcode1_coords[1]) + " Z15\nG4 P100\nG00 Z0\nG4 P100\nG00 X" + str(gcode2_coords[0] - 3) + " Y" + str(gcode2_coords[1])+ " Z0\nG4 P100\nG00 Z8"
        gcode_lines = gcode.split('\n')
        # print(gcode)
        return gcode_lines
      else:
        return "M81"
    else:
      return "M81"

class CommandParser:
  def __init__(self, screen_img=None, ser=None, params=None, img_from_camera=None):
    self.screen_img = screen_img
    self.ser = ser
    self.params = params
    self.img_from_camera = img_from_camera
    # self.params.offset_x = params.offset_x
    # self.params.offset_y = params.offset_y
    # self.params.const_offset_screw = params.const_offset_screw
    # self.params.platform_coords = params.platform_coords
  
  def gcode_to_device(self, gcode_str):
    line = gcode_str + '\r\n'
    # print(line)
    self.ser.write(line.encode('utf-8'))
    while True:
        response = self.ser.readline()
        # print(response)
        if response == b'ok\n':
          break
  
  def parse_command(self, cmd_txt):
    command_name = cmd_txt.split(" ")[0]
    if (command_name == "SET_SCREEN"):
      screen_img = cmd_txt.split(" ")[1]
      # print(screen_img)
      self.screen_img = screen_img
      scale = SetScreenCommand(self.img_from_camera, self.params).perform(screen_img)
      # print("Set screen image:", self.screen_img)
      # print("Scale:", scale)
      print("SET SCREEN: OK")
      return True
    if (command_name == "SET_CAMERA"):
      self.gcode_to_device("G01 X50 Y-10 F3000")
      capture_image()
      self.img_from_camera = "img_from_camera.jpg"
      self.params.platform_coords = PlatformCoordsPredictor("screw_weights.pth").predict_coords(self.img_from_camera)
      # print("Set camera image:", self.img_from_camera)
      print("SET CAMERA: OK")
      return True
    if (command_name == "FIND"):
      key_img = cmd_txt.split(" ")[1]
      if (FindCommand(self.img_from_camera, self.params).perform(key_img, self.screen_img)[0] != -1) and (FindCommand(self.img_from_camera, self.params).perform(key_img, self.screen_img)[1] != -1):
        # print(key_img, "location:", FindCommand(self.img_from_camera, self.params).perform(key_img, self.screen_img))
        print("FIND", key_img + ":", "OK")
        return True
      else:
        print(key_img, "NOT FOUND")
        return False
    if (command_name == "TAP"):
      key_img = cmd_txt.split(" ")[1]
      cmd = TapCommand(self.img_from_camera, self.params).perform(key_img, self.screen_img)
      for line in cmd:
        if line == "M81":
          return False
        self.gcode_to_device(line)
      print("TAP", key_img + ":", "OK")
      return True
    if (command_name == "SWIPE"):
      img1 = cmd_txt.split(" ")[1]
      img2 = cmd_txt.split(" ")[2]
      cmd = SwipeCommand(self.img_from_camera, self.params).perform(img1, img2, self.screen_img)
      for line in cmd:
        if line == "M81":
          return False
        self.gcode_to_device(line)
      print("SWIPE", img1, "to", img2 + ":", "OK")
      return True
