

import PIL
from PIL import Image
import os
from os.path import abspath, dirname, join
WHERE_AM_I = abspath(dirname(__file__))

#os.chdir("/mydir")
pics = []
for pic in os.listdir("."):
    if "small" in pic:
        os.remove(join(WHERE_AM_I,pic))
    elif pic.endswith(".png"):
        pics.append(pic)



for pic in pics:
    basewidth = 200
    img = Image.open(pic)
    wpercent = (basewidth/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((basewidth,hsize), PIL.Image.ANTIALIAS)
    img.save(pic.replace(".png","_small.png"))