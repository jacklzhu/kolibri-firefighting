import target_detect

while True:
    (x,y) = target_detect.get_target_coords(True)
    if x is not None and y is not None:
        x = (float(x) - target_detect.horizontal_resolution/2)\
        /target_detect.horizontal_resolution
        y = (target_detect.vertical_resolution/2 - float(y) )\
        /target_detect.vertical_resolution
        print x,y
