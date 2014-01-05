__author__ = 'Will'
import urllib
from os.path import abspath, dirname, join
import os
import pi3d
WHERE_AM_I = abspath(dirname(__file__))

cachedir = join(WHERE_AM_I, "cache")


def ensure_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)


def try_to_remove(filename):
    try:
        os.remove(filename)
        return True
    except Exception as e:
        print( "could not delete" , filename, e)
        return False

class ImageLoader(object):
    def __init__(self):
        self.address = "http://mt0.google.com/vt/lyrs=y&hl=en&x={0}&s=&y={1}&z={2}"
        self.shader = pi3d.Shader("uv_flat")

    def getCache(self):
        filename = join(WHERE_AM_I, "loading.png")
        return pi3d.ImageSprite(filename, self.shader, w=256.0, h=256.0, z=5.0)

    def remove(self,x,y,z):
        level_dir = join(cachedir, str(z))
        filename = join(level_dir, "{0}-{1}.png".format(x,y))
        print ("removing" , filename)
        print (try_to_remove(filename))

    def get_image(self, lat, long, level):
        got_image = False
        lat = int(lat)
        long = int(long)
        level = int(level)
        level_dir = join(cachedir, str(level))
        ensure_dir(level_dir)
        filename = join(level_dir, "{0}-{1}.png".format(lat, long))
        try:
            image = open(filename)
            image.close()
            got_image = True
        except Exception as e:
            #print e
            pass

        if not got_image:
            image_url = self.address.format(lat, long, level)
            print ("miss, loading image from " , image_url)
            temp_file = open(filename,'wb')
            temp_file.write(urllib.urlopen(image_url).read())
            temp_file.close()
        image = pi3d.ImageSprite(filename, self.shader, w=256.0, h=256.0, z=5.0)
        #print image , type(image)
        return image
