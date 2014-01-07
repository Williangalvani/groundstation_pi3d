__author__ = 'will'
import pi3d


class Crosshair(object):
    def __init__(self, display, camera):
        self.display = display
        self.camera = camera

        self.shader = pi3d.Shader("uv_flat")   # must unify the shaders later, not sure if affecting performance

        crosshair_img = pi3d.Texture("textures/crosshair4040.png", blend=True)
        self.crosshair = pi3d.Sprite(camera=self.camera, w=40, h=40, x=0, y=0, z=0.1)
        self.crosshair.set_draw_details(self.shader, [crosshair_img], 0, 0)
        self.display.add_sprites(self.crosshair)