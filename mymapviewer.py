#!/usr/bin/python
from __future__ import absolute_import, division, unicode_literals
from os.path import abspath, dirname
from tileLoader import TileLoader
from math import ceil
from datetime import datetime
from horizon.horizon import Horizon
from comm import TelemetryReader
import pi3d
from utils.timeit import timeit

WHERE_AM_I = abspath(dirname(__file__))
flat_shader = pi3d.Shader("uv_flat")

class GroundStation(object):

        def __init__(self, width=-1, height=-1):
            ### starting display, and 3d part###
            self.display = pi3d.Display.create(x=0, y=0, w=width, h=height,
                                               frames_per_second=20,
                                               background=(0, 0, 0, 255))
            pi3d.Light((0, 0, 10))
            self.shader = pi3d.Shader("uv_flat")

            self.camera = pi3d.Camera(is_3d=False)
            self.camera.was_moved = False

            self.arial_font = pi3d.Font("fonts/FreeMonoBoldOblique.ttf",
                                         (180, 0, 140, 255),
                                         background_color=(255, 255, 255, 180))

            self.arial_font.blend = Truelsu
            self.arial_font.mipmap = True

            self.flat_shader = pi3d.Shader("uv_flat")

            #starting input listeners#
            self.inputs = pi3d.InputEvents()
            self.inputs.get_mouse_movement()

            self.width = self.display.width
            self.height = self.display.height

            self.last_scroll = datetime.now()    # variable to limit zooming speed
            self.last_info_update = datetime.now()  # lets allow only 1 update each 2 seconds, to spare the cpu
            self.window = self.display

            # these are the point where the screen focuses
            self.view_longitude = -48.519688
            self.view_latitude = -27.606899

            #additional points showing on the map
            self.points = [(self.view_longitude, self.view_latitude),
                           (0.0, 0.0),
                           (180, 36.8),
                           (-47.886829, -15.793751)]

            # this will show as an arrow on the map
            self.tracked_object_position = [0, 0, 0]
            self.tracking = True

            #camera should follow tracked object?
            self.following_tracked = True

            #current zoom level
            self.zoom = 10
            #current button state
            self.button = 0

            # mouse coordinates on screen
            self.pointer_x = 0
            self.pointer_y = 0

            # position variations on a "tick"
            self.dx = 0
            self.dy = 0

            #currently loaded tiles
            self.tiles = []
            self.tiles_set = set()
            self.current_center_tile = (0, 0)

            #draw gui only, the avoid redrawing the tiles
            self.draw_gui_only_flag = False

            #should reload the tiles? set on moving the map
            self.updated = True
            self.tile_list_updated = True

            self.gps_info = pi3d.String(font=self.arial_font, string="Now the Raspberry Pi really does rock")
            self.gps_info.set_shader(flat_shader)

            pointer_img = pi3d.Texture("textures/pointer.png", blend=True)
            pointer_img.mipmap = True
            self.pointer = pi3d.Sprite(camera=self.camera, w=14, h=22, x=0, y=0, z=0.1)
            self.pointer.set_draw_details(self.flat_shader, [pointer_img], 0, 0)

            crosshair_img = pi3d.Texture("textures/crosshair4040.png", blend=True)
            self.crosshair = pi3d.Sprite(camera=self.camera, w=40, h=40, x=0, y=0, z=0.1)
            self.crosshair.set_draw_details(self.flat_shader, [crosshair_img], 0, 0)

            self.waypoint_img = pi3d.Texture("textures/crosshair4040.png", blend=True)
            self.waypoint_sprite = pi3d.Sprite(camera=self.camera, w=20, h=20, x=0, y=0, z=0.1)
            self.waypoint_sprite.set_draw_details(self.flat_shader, [self.waypoint_img], 0, 0)
            self.waypoint_sprite_list = []

            tracked_img = pi3d.Texture("textures/gpspointer6060.png", blend=True)
            self.tracked_sprite = pi3d.Sprite(camera=self.camera, w=60, h=60, x=0, y=0, z=10)
            self.tracked_sprite.rotateToY(0)
            self.tracked_sprite.rotateToX(0)
            self.tracked_sprite.rotateToZ(0)
            self.tracked_sprite.set_draw_details(self.flat_shader, [tracked_img], 0, 0)
            self.tracked_sprite.scale(0.8, 0.8, 0.8)

            self.info_sprite = pi3d.Sprite(camera=self.camera, w=100, h=100, x=0, y=0, z=0.1)

            self.display.add_sprites(self.crosshair)
            self.display.add_sprites(self.pointer)
            self.display.add_sprites(self.tracked_sprite)
            #the tile loader gives the tiles around the current position
            self.tile_loader = TileLoader(self)

            #shows the navball
            self.horizon = Horizon(self.camera, self.display)

            #reads telemetry from the serial portarialFont
            self.telemetry_reader = TelemetryReader(self)
            self.data = {}
            self.main_loop()

        def zoom_in(self):
            self.zoom += 1
            if self.zoom > 20:
                self.zoom = 20

        def zoom_out(self):
            self.zoom -= 1
            if self.zoom < 2:
                self.zoom = 2

        def on_scroll(self, zoom_in):
            if (datetime.now() - self.last_scroll).microseconds > 100000:
                if zoom_in > 0:
                    self.zoom_in()
                elif zoom_in < 0:
                    self.zoom_out()
                self.queue_draw(tile=True)
                self.last_scroll = datetime.now()
                print(self.zoom)

        def set_zoom(self, zoom):
            self.zoom = zoom

        def set_focus(self, longitude, latitude):
            self.view_longitude = longitude
            self.view_latitude = latitude
            self.queue_draw(tile=True)

        def on_move(self, x, y):
            dx = x-self.pointer_x
            dy = y - self.pointer_y
            self.pointer_x, self.pointer_y = x, y

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
            if self.button == 1:
                delta_longitude, delta_latitude = self.tile_loader.dpix_to_dcoord(dx, self.view_latitude, dy, self.zoom)
                self.view_longitude -= delta_longitude
                self.view_latitude -= delta_latitude
                self.updated = True

               #check map boundaries
                if self.view_longitude > 180:
                    self.view_longitude = 180.0
                if self.view_longitude < -180:
                    self.view_longitude = -180.0
                if self.view_latitude > 85.0:
                    self.view_latitude = 85.0
                if self.view_latitude < -85.0:
                    self.view_latitude = -85.0
                #asks for update
                self.queue_draw()

        def draw_circle_at(self, x_pos, y_pos):
            """draws a circle centered at (x_pos,y_pos)"""
            self.waypoint_sprite.position(x_pos, -y_pos, 0.1)
            self.waypoint_sprite.draw()

        #@timeit
        def draw_info(self):
            """
            draws text data on the screen, currently, gps data and pending tiles to draw

            usually takes 1~5ms
            250ms when updating!
            """
            #print((datetime.now() - self.last_info_update).seconds)
            if (datetime.now() - self.last_info_update).seconds > 3:
                #print "got in"
                pending = len(self.tile_loader.pending_tiles) + len(self.tile_loader.loading_tiles)
                self.gps_info._unload_opengl()

                # string = "{0} tiles pending\nlat:{1}\nlong:{2}".format(pending,
                #                                                        self.view_latitude,
                #                                                        self.view_longitude)
                string = " lat:{0}\n long:{1}".format(self.view_latitude, self.view_longitude)

                for i in self.data.keys():
                    string = string + "\n {0}:{1}".format(i, self.data[i])

                self.gps_info = pi3d.String(font=self.arial_font,
                                            string=string,
                                            x=-self.width/2, y=self.height/2, z=3,
                                            is_3d=False,
                                            camera=self.camera,
                                            justify='L',
                                            size=0.15)
                bounds = self.gps_info.get_bounds()
                size = bounds[4] - bounds[1]
                self.gps_info.position(-self.width/2,
                                       self.height/2-size/2,
                                       3)

                self.gps_info.set_shader(self.flat_shader)
                self.last_info_update = datetime.now()
            self.gps_info.draw()

        #@timeit
        def draw_points(self):
            """
            draws each of the self.points on the screen as circles
            """
            if self.updated:
                if len(self.points) != len(self.waypoint_sprite_list):
                    for point in self.points:
                        sprite = pi3d.Sprite(camera=self.camera, w=20, h=20, x=0, y=0, z=1)
                        sprite.set_draw_details(self.flat_shader, [self.waypoint_img], 0, 0)
                        self.waypoint_sprite_list.append(sprite)
                    self.display.add_sprites(*self.waypoint_sprite_list)
                for point, sprite in zip(self.points, self.waypoint_sprite_list):
                    x, y = self.tile_loader.dcord_to_dpix(point[0],
                                                          self.view_longitude,
                                                          point[1],
                                                          self.view_latitude,
                                                          self.zoom)
                    sprite.position(x, -y, 10)
                    #sprite.draw()
                    #print x,y

        #@timeit
        def draw_tracked_object(self):
            """
            draws the tracked object on its position, with proper orientation, as an arrow

            takes ~0ms
            """
            if self.tracking:
                point = self.tracked_object_position
                x, y = self.tile_loader.dcord_to_dpix(point[0],
                                                      self.view_longitude,
                                                      point[1],
                                                      self.view_latitude,
                                                      self.zoom)
                self.tracked_sprite.position(x, -y, 0.1)
                self.tracked_sprite.rotateToZ(-point[2])

        def set_tracked_position(self, longitude, latitude, yaw):
            """
            updates tracked object position, called by telemetry reader
            """
            if self.tracked_object_position[0] != longitude or self.tracked_object_position[1] != latitude:
                self.tracked_object_position = (longitude, latitude, yaw)
                #asks to update the gui alone
                self.queue_draw(gui_only=True)

            if self.following_tracked and self.data.has_key("gps_sats") :
                if self.data["gps_sats"] >= 3:
                    self.view_longitude, self.view_latitude = longitude, latitude
                    self.queue_draw(tile=True)

        def set_attitude(self, roll, pitch, yaw=0):
            """
            updates the object attitude, called from telemtry reader, written directly on self.horizon.
            should probably be changed
            """
            if self.horizon.tilt != pitch or self.horizon.roll != roll or self.horizon.yaw != yaw:
                #self.horizon.tilt = pitch
                #self.horizon.roll = roll
                #self.horizon.yaw = yaw
                self.horizon.set_attitude(roll, pitch, yaw)
                self.queue_draw(gui_only=True)


        def draw_tiles(self):
            """
            Core map-drawing function

            checks if the map position has been updated, if not, prints the old tiles.
            if so, reloads the tiles as a bidimensional list, and prints them accordingly
            """
            span_x = self.width
            span_y = self.height
            tiles_x = int(ceil(span_x/256.0))
            tiles_y = int(ceil(span_y/256.0))
            if self.updated:
                # checking which tiles to reload #

                new_center_tile = self.tile_loader.coord_to_gmap_tile_int(self.view_longitude,
                                                                          self.view_latitude,
                                                                          self.zoom)
                if new_center_tile != self.current_center_tile or self.tile_list_updated:
                    #print "reloading" , new_center_tile , self.current_center_tile
                    new_tiles = self.tile_loader.load_area(self.view_longitude,
                                                           self.view_latitude,
                                                           self.zoom,
                                                           tiles_x,
                                                           tiles_y)
                    new_set = set()
                    for line in new_tiles:
                        new_set |= set(line)

                    removing = self.tiles_set-new_set
                    self.display.remove_sprites(*removing)

                    adding = new_set - self.tiles_set
                    self.display.add_sprites(*adding)
                    #print "removing ", len(removing), "adding ", len(adding), "currently ", len(self.display.sprites)
                    self.tiles = new_tiles
                    self.tiles_set = new_set

                self.current_center_tile = new_center_tile

                ### starts the tile loading and drawing
                tile_number = 0
                line_number = 0
                x_center = 0
                y_center = 0
                ## offset to keep the current coordinate centered on the screen
                offset_x, offset_y = self.tile_loader.gmap_tile_xy_from_coord(self.view_longitude,
                                                                              self.view_latitude,
                                                                              self.zoom)

                #size of lines and columns
                x_tiles = len(self.tiles[0])
                y_tiles = len(self.tiles)

                #draw it all, fixing the position
                for line in self.tiles:
                    for tile in line:
                        x = (tile_number - int(x_tiles/2)) * 256 + x_center
                        y = (line_number - int(y_tiles/2)) * 256 + y_center
                        final_x = x - offset_x + 128
                        final_y = y - offset_y + 128
                        tile.position(final_x+self.dx, -(final_y+self.dy), 100.0)
                        #tile.draw()
                        tile_number += 1
                    tile_number = 0
                    line_number += 1

                self.draw_points()  # must move out of here!

                self.updated = False
            else:
                pass

        def draw(self):
            """
            high level draw function, calls the lower ones
            """
            self.draw_tiles()
            self.draw_gui()

        #@timeit
        def draw_gui(self):
            if self.draw_gui_only_flag:
                self.draw_tracked_object()  # 0ms
                self.draw_instruments()     # 0ms

                #draws mouse pointer
                self.pointer.position(self.pointer_x - self.width/2, -self.pointer_y+self.height/2, 0.1)
                self.draw_info()            # 5ms
                #self.create_info_image()

        #@timeit
        def draw_instruments(self):
            """
            draws navball
            takes ~0ms
            """
            self.horizon.update()

        def queue_draw(self, gui_only=False,tile=False):
            """
            schedules a draw on next tick, may be complete, or gui-only
            """
            self.updated = not gui_only
            self.draw_gui_only_flag = True
            self.tile_list_updated = tile

        def update_mouse(self):
            """
            process mouse state
            """
            self.inputs.do_input_events()
            imx, imy, zoom, imh, imd = self.inputs.get_mouse_movement()
            self.on_move(self.pointer_x+imx, self.pointer_y+imy)
            if self.inputs.key_state("BTN_LEFT"):
                self.button = 1
            else:
                self.button = 0
            if zoom:
                self.on_scroll(zoom)

        def set_data(self, string, value):
            self.data[string] = value

        def main_loop(self):
            """
            This is the Main Loop of the Game
            checks for mouse and keyboard inputs,
            draws the screen,
            and quits, if esc is pressed
            """
            time = 0
            start_time = datetime.now()
            while self.display.loop_running():

                self.update_mouse()
                if self.inputs.key_state(27):
                    self.display.destroy()
                    self.tile_loader.run = False
                    self.telemetry_reader.run = False
                self.draw()
                new_time = datetime.now()
                time = ((new_time-start_time).microseconds/1000000.0) * 0.1 + time*0.9
                print "frame took {0:.2f} avg: {1:.2f} , fps:{2:.2f}".format(((new_time-start_time).microseconds/1000000.0), time, 1.0/time)
                start_time = new_time

if __name__ == '__main__':
    gui = GroundStation()
