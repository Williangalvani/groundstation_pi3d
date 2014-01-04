__author__ = 'Will'

from os.path import abspath, dirname, join
import pi3d
WHERE_AM_I = abspath(dirname(__file__))



class Horizon():

    def __init__(self, camera, display):
        self.camera = camera
        self.roll = 45
        self.tilt = 0
        self.yaw = 0
        self.initialized = False

        self.frame = self.load_image_sprite("horizon/horizon_frame.png", 479, 480)
        self.background_texture = pi3d.Texture("textures/horizon_bg_bigger.png")
        self.background_sphere = pi3d.Sphere(x=-display.width/2+100,
                                             y=-display.height/2 + 100,
                                             radius=100.0,
                                             slices=24,
                                             sides=24,
                                             name="earth",
                                             z=100)

        self.background = self.load_image_sprite("horizon/horizon_interior_small.png")
        self.shader = pi3d.Shader("uv_reflect")
        self.update()

    def load_image_sprite(self, name, width =10, height=10):
        flat_shader = pi3d.Shader("uv_flat")
        img = pi3d.Texture(name, blend=True)
        sprite = pi3d.Sprite(camera=self.camera, w=width, h=height, x=0, y=0, z=0.1)
        sprite.set_draw_details(flat_shader, [img], 0, 0)
        return sprite


    def set_attitude(self, roll, pitch, yaw):
        self.roll = roll
        self.tilt = pitch
        self.yaw = yaw
        self.initialized = True

    def update(self):
        if self.initialized:
            self.background_sphere.rotateToY(self.yaw)
            self.background_sphere.rotateToX(self.tilt)
            self.background_sphere.rotateToZ(self.roll)
            self.background_sphere.draw(self.shader, [self.background_texture])


