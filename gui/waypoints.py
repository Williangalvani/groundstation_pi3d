__author__ = 'will'
import pi3d

class WaypointsWidget(object):
    def __init__(self, display, camera,tile_loader):
        self.display = display
        self.camera = camera
        self.tile_loader = tile_loader

        self.shader = pi3d.Shader("uv_flat")   # must unify the shaders later, not sure if affecting performance

        self.waypoint_img = pi3d.Texture("textures/crosshair4040.png", blend=True)
        self.waypoint_sprite = pi3d.Sprite(camera=self.camera, w=20, h=20, x=0, y=0, z=0.1)
        self.waypoint_sprite.set_draw_details(self.shader, [self.waypoint_img], 0, 0)
        self.waypoint_sprite_list = []

        self.points = []

    def set_points(self, points):
        self.points = points

    def draw_circle_at(self, x_pos, y_pos):
        """draws a circle centered at (x_pos,y_pos)"""
        self.waypoint_sprite.position(x_pos, -y_pos, 0.1)
        self.waypoint_sprite.draw()

    #@timeit
    def draw_points(self, updated, longitude, latitude, zoom):
        """
        draws each of the self.points on the screen as circles
        """

        if updated:
            number_of_points = len(self.points)
            if number_of_points != len(self.waypoint_sprite_list):
                for i in self.waypoint_sprite_list:
                    i._unload_opengl()
                for i in range(number_of_points):
                    sprite = pi3d.Sprite(camera=self.camera, w=20, h=20, x=0, y=0, z=1)
                    sprite.set_draw_details(self.shader, [self.waypoint_img], 0, 0)
                    self.waypoint_sprite_list.append(sprite)
                self.display.add_sprites(*self.waypoint_sprite_list)
            for point, sprite in zip(self.points, self.waypoint_sprite_list):
                x, y = self.tile_loader.dcord_to_dpix(point[0],
                                                      longitude,
                                                      point[1],
                                                      latitude,
                                                      zoom)
                sprite.position(x, -y, 10)
