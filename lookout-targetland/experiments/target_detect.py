#!/usr/bin/env python2
import math
import cv2
import numpy as np

#color settings
hue_lower = 15
hue_upper = 75
saturation_lower = 80
saturation_upper = 256
value_lower = 30
value_upper = 256
min_contour_area = 400 # the smallest number of pixels in a contour before it will register this as a target

#camera
horizontal_fov = 118.2 * math.pi/180
vertical_fov = 69.5 * math.pi/180
horizontal_resolution = 1280
vertical_resolution = 720

def get_target_coords(capture):
    hsvcapture = cv2.cvtColor(capture,cv2.COLOR_RGB2HSV)
    inrangepixels = cv2.inRange(hsvcapture,np.array((hue_lower,saturation_lower,value_lower)),np.array((hue_upper,saturation_upper,value_upper)))#in opencv, HSV is 0-180,0-255,0-255
    tobecontourdetected = inrangepixels.copy()

    #TODO filter better. binary morphology would be a good start.
    cross = cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5))
    tobecontourdetected = cv2.morphologyEx(tobecontourdetected, cv2.MORPH_OPEN, cross)
    contours,hierarchy = cv2.findContours(tobecontourdetected,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)

    contour_sizes=[]
    contour_centroids = []
    for contour in contours:
        real_area = cv2.contourArea(contour)
        if real_area > min_contour_area:
            M = cv2.moments(contour) #moment is centroid
            cx,cy = int(M['m10']/M['m00']), int(M['m01']/M['m00'])
            cv2.circle(capture,(cx,cy),5,(0,0,255),-1)
            contour_sizes.append(real_area)
            contour_centroids.append((cx,cy))

    #find biggest contour (by area)
    biggest_contour_index = 0
    for i in range(1,len(contour_sizes)):
        if contour_sizes[i] > contour_sizes[biggest_contour_index]:
            biggest_contour_index = i
    biggest_contour_centroid = None
    if len(contour_sizes)>0:
        biggest_contour_centroid=contour_centroids[biggest_contour_index]

    x = None
    y = None

    #if the biggest contour was found, color it blue and send the message
    if biggest_contour_centroid is not None:
        cv2.circle(capture,biggest_contour_centroid,5,(255,0,0),-1)
        x,y = biggest_contour_centroid

    return x, y, capture, inrangepixels
