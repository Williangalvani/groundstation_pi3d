__author__ = 'will'

import pi3d


class TrackedObject(object):
    def __init__(self, display, camera, tile_loader):
        self.display = display
        self.camera = camera
        self.tile_loader = tile_loader

        self.shader = pi3d.Shader("uv_flat")   # must unify the shaders later, not sure if affecting performance

        tracked_img = pi3d.Texture("textures/gpspointer6060.png", blend=True)
        self.tracked_sprite = pi3d.Sprite(camera=self.camera, w=60, h=60, x=0, y=0, z=10)
        self.tracked_sprite.rotateToY(0)
        self.tracked_sprite.rotateToX(0)
        self.tracked_sprite.rotateToZ(0)
        self.tracked_sprite.set_draw_details(self.shader, [tracked_img], 0, 0)
        self.tracked_sprite.scale(0.8, 0.8, 0.8)
        self.display.add_sprites(self.tracked_sprite)

    def draw(self, tracking, tracked_object_position, longitude, latitude, zoom):
        if tracking:
            x, y = self.tile_loader.dcord_to_dpix(tracked_object_position[0],
                                                  longitude,
                                                  tracked_object_position[1],
                                                  latitude,
                                                  zoom)
            self.tracked_sprite.position(x, -y, 1)
            self.tracked_sprite.rotateToZ(-tracked_object_position[2])
            self.tracked_sprite.draw()