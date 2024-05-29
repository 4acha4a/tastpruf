from command_parser import CommandParser, Parameters
import os
import serial
import time
ser = serial.Serial(
    port='/dev/tty.wchusbserial10',
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE
) # 3D-принтер, на который будет посылаться Gcode
# Необходимо задать значения отклонения по координатам для задания нулевого положения 3D-принтера на ЧПУ
offset_x = 33 + 23.35
offset_y = 28.6
const_offset_screw = 5.5 

if __name__ == "__main__":
    file_path = './test_hito/test_query.txt'
    file = open(file_path).read() # Считывание комманд с файла
    os.chdir('./test_hito')
    params = Parameters(offset_x, offset_y, const_offset_screw)
    cmd_parser = CommandParser(params=params, ser=ser) 
    lines = file.split('\n')
    cmd_parser.gcode_to_device("G28")
    for line in lines:
        result = cmd_parser.parse_command(line) # Обработка комманд с файла
        if result == False:
            print("Aborting")
            break
    cmd_parser.gcode_to_device("M81")
    print("That's all!")
    ser.close()
