__author__ = 'will'
import pi3d


class Pointer(object):
    def __init__(self, main_app):
        self.main_app = main_app
        self.display = main_app.display
        self.camera = main_app.camera
        self.width = self.display.width
        self.height = self.display.height

        self.pointer_x = 0
        self.pointer_y = 0

        self.shader = pi3d.Shader("uv_flat")   # must unify the shaders later, not sure if affecting performance

        pointer_img = pi3d.Texture("textures/pointer.png", blend=True)
        pointer_img.mipmap = True
        self.pointer = pi3d.Sprite(camera=self.camera, w=14, h=22, x=0, y=0, z=0.1)
        self.pointer.set_draw_details(self.shader, [pointer_img], 0, 0)

        self.display.add_sprites(self.pointer)

    def on_move(self, dx, dy):
        self.width = self.display.width
        self.height = self.display.height
        #dx = x#-self.pointer_x
        #dy = y# - self.pointer_y
        self.pointer_x, self.pointer_y = self.pointer_x+dx, self.pointer_y+dy

        #limit boundaries
        if self.pointer_x > self.width:
            self.pointer_x = self.width
        if self.pointer_x < 0:
            self.pointer_x = 0
        if self.pointer_y < 0:
            self.pointer_y = 0
        if self.pointer_y > self.height:
            self.pointer_y = self.height

        ## check if dragging

    def update(self):
        self.pointer.position(self.pointer_x - self.width/2, -self.pointer_y+self.height/2, 0.1)
