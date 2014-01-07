__author__ = 'will'
from datetime import datetime
import pi3d


class TextWidget():
    def __init__(self, display, camera):
            self.display = display
            self.camera = camera

            self.shader = pi3d.Shader("uv_flat")
            self.arial_font = pi3d.Font("fonts/FreeMonoBoldOblique.ttf",
                                        (180, 0, 140, 255),
                                        background_color=(255, 255, 255, 180))
            self.arial_font.blend = True
            self.arial_font.mipmap = True

            self.string = "string not set!"

            self.gps_info = pi3d.String(font=self.arial_font, string="Now the Raspberry Pi really does rock")
            self.gps_info.set_shader(self.shader)

            self.last_info_update = datetime.now()
            self.update_rate = 3

    def set_update_rate(self, rate):
        self.update_rate = rate

    def set_text(self, string):
        self.string = string

    def update(self):
            """
            draws text data on the screen, currently, gps data and pending tiles to draw

            usually takes 1~5ms
            250ms when updating!
            """
            if (datetime.now() - self.last_info_update).seconds > self.update_rate:
                width = self.display.width
                height = self.display.height
                self.gps_info._unload_opengl()

                self.gps_info = pi3d.String(font=self.arial_font,
                                            string=self.string,
                                            x=-width/2, y=height/2, z=3,
                                            is_3d=False,
                                            camera=self.camera,
                                            justify='L',
                                            size=0.15)
                bounds = self.gps_info.get_bounds()
                size = bounds[4] - bounds[1]
                self.gps_info.position(-width/2,
                                       height/2-size/2,
                                       3)

                self.gps_info.set_shader(self.shader)
                self.last_info_update = datetime.now()
            self.gps_info.draw()