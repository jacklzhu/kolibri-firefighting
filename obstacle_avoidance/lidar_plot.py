import thread, time, sys, traceback, math
import numpy as np
import matplotlib.pyplot as plt

plt.ion()

com_port = "/dev/cu.usbmodem1411" # example: 5 == "COM6" == "/dev/tty5"
baudrate = 115200

offset = 140
init_level = 0
index = 0

distances = np.zeros(360)
qualities = np.zeros(360)
speed = 0

def convert_data(data):
    x = data[0]
    x1= data[1]
    x2= data[2]
    x3= data[3]

    dist_mm = x | (( x1 & 0x3f) << 8) # distance is coded on 13 bits ? 14 bits ?
    quality = x2 | (x3 << 8) # quality is on 16 bits

    return (dist_mm, quality)

def update_view(index, data):
    dist_mm, quality = convert_data(data)
    distances[index] = dist_mm
    qualities[index] = quality
    # print index, dist_mm, quality

def checksum(data):
    """Compute and return the checksum as an int.

    data -- list of 20 bytes (as ints), in the order they arrived in.
    """
    # group the data by word, little-endian
    data_list = []
    for t in range(10):
        data_list.append( data[2*t] + (data[2*t+1]<<8) )

    # compute the checksum on 32 bits
    chk32 = 0
    for d in data_list:
        chk32 = (chk32 << 1) + d

    # return a value wrapped around on 15bits, and truncated to still fit into 15 bits
    checksum = (chk32 & 0x7FFF) + ( chk32 >> 15 ) # wrap around to fit into 15 bits
    checksum = checksum & 0x7FFF # truncate to 15 bits
    return int( checksum )

def compute_speed(data):
    speed_rpm = float( data[0] | (data[1] << 8) ) / 64.0
    return speed_rpm

def read_Lidar():
    global init_level, angle, index, speed

    nb_errors = 0
    while True:
        try:
            time.sleep(0.00001) # do not hog the processor power

            if init_level == 0 :
                b = ord(ser.read(1))
                # start byte
                if b == 0xFA :
                    init_level = 1
                    #print lidarData
                else:
                    init_level = 0
            elif init_level == 1:
                # position index
                b = ord(ser.read(1))
                if b >= 0xA0 and b <= 0xF9 :
                    index = b - 0xA0
                    init_level = 2
                elif b != 0xFA:
                    init_level = 0
            elif init_level == 2 :
                # speed
                b_speed = [ ord(b) for b in ser.read(2)]

                # data
                b_data0 = [ ord(b) for b in ser.read(4)]
                b_data1 = [ ord(b) for b in ser.read(4)]
                b_data2 = [ ord(b) for b in ser.read(4)]
                b_data3 = [ ord(b) for b in ser.read(4)]

                # for the checksum, we need all the data of the packet...
                # this could be collected in a more elegent fashion...
                all_data = [ 0xFA, index+0xA0 ] + b_speed + b_data0 + b_data1 + b_data2 + b_data3

                # checksum
                b_checksum = [ ord(b) for b in ser.read(2) ]
                incoming_checksum = int(b_checksum[0]) + (int(b_checksum[1]) << 8)

                # verify that the received checksum is equal to the one computed from the data
                if checksum(all_data) == incoming_checksum:
                    speed_rpm = compute_speed(b_speed)
                    speed = speed_rpm
                    update_view(index * 4 + 0, b_data0)
                    update_view(index * 4 + 1, b_data1)
                    update_view(index * 4 + 2, b_data2)
                    update_view(index * 4 + 3, b_data3)
                else:
                    # the checksum does not match, something went wrong...
                    nb_errors +=1

                    # display the samples in an error state
                    update_view(index * 4 + 0, [0, 0x80, 0, 0])
                    update_view(index * 4 + 1, [0, 0x80, 0, 0])
                    update_view(index * 4 + 2, [0, 0x80, 0, 0])
                    update_view(index * 4 + 3, [0, 0x80, 0, 0])

                init_level = 0 # reset and wait for the next packet

            else: # default, should never happen...
                init_level = 0
        except :
            traceback.print_exc(file=sys.stdout)

import serial
ser = serial.Serial(com_port, baudrate)
th = thread.start_new_thread(read_Lidar, ())

dist_max = 6000

dist_copy = np.zeros(360)
# colors_copy = np.zeros(360)

while True:
    theta = np.arange(0,360, dtype='float') / (360) * 2 * np.pi

    # ax = plt.subplot(111, projection='polar')
    ax1 = plt.subplot(121, polar=True)
    ax1.clear()
    for i,d in enumerate(distances):
        dist_copy[i] = d if d < dist_max else dist_max

    # distances = np.random.rand(360)
    # ax.scatter(theta, distances, color='r', linewidth=1)

    c = ax1.scatter(theta, distances,
                   c=qualities,
                   cmap='cool',
                   edgecolors='none')
    ax1.set_rmax(dist_max)
    ax1.grid(True)
    ax1.set_title("VX-11 Lidar Output", va='bottom')

    ax2 = plt.subplot(122)
    ax2.clear()
    ax2.hist(qualities, bins=20)
    ax2.set_title("Speed: %s" % speed)

    plt.pause(0.05)

time.sleep(10000)
th.join()

ser.close()
