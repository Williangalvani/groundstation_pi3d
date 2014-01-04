#!/usr/bin/python
from __future__ import absolute_import, division, print_function, unicode_literals

from os.path import abspath, dirname

#http://maps.googleapis.com/maps/api/staticmap?center=#X,#Y&zoom=#Z&size=200x200&sensor=false
WHERE_AM_I = abspath(dirname(__file__))
from tileLoader import TileLoader
from math import ceil
from datetime import datetime
from horizon.horizon import Horizon
import sys
from comm import TelemetryReader
from Tkinter import *

import pi3d

#   import pdb
arialFont = pi3d.Font("fonts/FreeMonoBoldOblique.ttf", (221,0,170,255))   #load ttf font and set the font colour to 'raspberry'

class MyApp(object):

    def __init__(self, width=-1,height=-1):

        self.DISPLAY = pi3d.Display.create(x=0,y=0,w=width, h=height,frames_per_second=10)

        pi3d.Light((0, 0, 10))#.ambient(10)
        #self.tkframe.bind("<Button-1>", self.callback)
        self.shader = pi3d.Shader("uv_flat")
        self.CAMERA = pi3d.Camera(is_3d=False)
        #self.CAMERA3D = self.CAMERA# = pi3d.Camera(is_3d=True)

        #self.mykeys = pi3d.Keyboard()
        #self.mymouse = pi3d.Mouse(restrict = 1)
        #self.mymouse.start()

        self.inputs = pi3d.InputEvents()
        self.inputs.get_mouse_movement()

        self.win = self.DISPLAY.tkwin
        self.width = self.DISPLAY.width
        self.height = self.DISPLAY.height
        """Create the Screen"""
        #self.screen = pygame.display.set_mode((self.width,self.height),HWSURFACE | RESIZABLE | DOUBLEBUF,32 )
        self.last_scroll = datetime.now()
        self.window = self.DISPLAY
        #self.FPS = 60
        #self.FPSCLOCK = pygame.time.Clock()http://hobbyking.com/hobbyking/store/uh_viewItem.asp?idProduct=13421
        self.longitude = -48.519688
        self.latitude =  -27.606899
        self.points = [(self.longitude,self.latitude),(0.0,0.0),(180,36.8),(-47.886829,-15.793751)]
        self.tracked = [0,0,0]
        self.tracking = True
        self.zoom = 2
        self.button = 0
        self.x,self.y = 0,0
        self.pointer_x = 0
        self.pointer_y = 0
        self.dx = 0
        self.dy = 0

        self.to_draw = True
        self.tiles = []
        self.tiles_set = set()
        self.draw_gui_only_flag = False
        self.updated = True
        flatsh = pi3d.Shader("uv_flat")



        self.gps_info = pi3d.String(font=arialFont, string="Now the Raspberry Pi really does rock")
        self.gps_info.set_shader(flatsh)


#mystring.translate(0.0, 0.0, 1)

        pointerimg = pi3d.Texture("textures/pointer.png", blend=True)
        self.pointer = pi3d.Sprite(camera=self.CAMERA, w=14, h=22, x=0, y=0, z=0.1)
        self.pointer.set_draw_details(flatsh, [pointerimg],0,0)

        crosshairimg = pi3d.Texture("textures/crosshair4040.png", blend=True)
        self.crosshair = pi3d.Sprite(camera=self.CAMERA, w=40, h=40, x=0, y=0, z=0.1)
        self.crosshair.set_draw_details(flatsh, [crosshairimg],0,0)

        waypointimg = pi3d.Texture("textures/waypoint.png", blend=True)
        self.waypoint_sprite = pi3d.Sprite(camera=self.CAMERA, w=20, h=20, x=0, y=0, z=0.1)
        self.waypoint_sprite.set_draw_details(flatsh, [crosshairimg],0,0)

        tracked_img = pi3d.Texture("textures/gpspointer6060.png", blend=True)
        self.tracked_sprite = pi3d.Sprite(camera=self.CAMERA, w=60, h=60, x=0, y=0, z=0.1)
        self.tracked_sprite.set_draw_details(flatsh, [tracked_img],0,0)
        self.tracked_sprite.scale(0.8,0.8,0.8)


        # Connect signals
        self.tile_loader = TileLoader(self)

        self.horizon = Horizon(self.CAMERA,self.DISPLAY)
        self.telemetry_reader = TelemetryReader(self)
        #print(dir(self.win))
     #   self.win.bind("<Button-1>", self.callback)
        self.main_loop()

        print("done")


    def zoom_in(self,widget = None,event = None):
        self.zoom+=1
        if self.zoom>20:
            self.zoom = 20

    def zoom_out(self,widget = None,event = None):
        self.zoom-=1
        if self.zoom < 2:
            self.zoom = 2


    def on_scroll(self,zoom_in):
        if (datetime.now() - self.last_scroll).microseconds > 100000:
            if zoom_in > 0: # UP
                self.zoom_in()
            elif zoom_in < 0:
                self.zoom_out()
            self.queue_draw()
            self.last_scroll = datetime.now()
            print(self.zoom)

    def on_click(self,button):
        #print self.tile_loader.cache["loading"]
        if button ==1:
            self.button = 1
        elif button ==4:
            self.on_scroll(1)
        elif button ==5:
            self.on_scroll(0)
    def on_release(self,event):
        self.button = 0


    def set_zoom(self,zoom):
        self.zoom = zoom

    def set_focus(self,long,lat):
        self.longitude = long
        self.latitude = lat



    def on_move(self,x,y):
        #x, y = event.pos
        dx = x-self.pointer_x
        dy = y - self.pointer_y
        self.pointer_x, self.pointer_y = x, y
        if self.pointer_x > self.width:
            self.pointer_x = self.width
        if self.pointer_x < 0:
            self.pointer_x = 0
        if self.pointer_y < 0:
            self.pointer_y = 0
        if self.pointer_y > self.height:
            self.pointer_y = self.height
        if self.button == 1:
            dlongitude, dlatitude = self.tile_loader.dpix_to_dcoord(dx, self.latitude, dy, self.zoom)
            self.longitude -= dlongitude
            self.latitude -= dlatitude
            self.updated = True
           # print "dragged"

            if self.longitude >  180:
                self.longitude = 180.0
            if self.longitude <  -180:
                self.longitude = -180.0
            if self.latitude >  85.0:
                self.latitude = 85.0
            if self.latitude <  -85.0:
                self.latitude = -85.0
            #print(self.longitude,self.latitude)
            self.queue_draw()
        #print(self.longitude,self.latitude)

    def draw_center_circle(self, x_pos, y_pos):
        self.waypoint_sprite.position(x_pos,-y_pos,0.1)
        self.waypoint_sprite.draw()


        #pygame.draw.circle(self.screen, (255,0,0), (int(x_pos),int(y_pos)), 5, 2)


    def draw_cross(self):
        self.crosshair.draw()
        # x_center = self.width/2# - 128
        # y_center = self.height/2# -
        # pointsx = [(x_center+10,y_center),
        #           (x_center-10,y_center)]
        # pointsy = [(x_center,y_center+10),
        #           (x_center,y_center-10)]
        #
        # pygame.draw.lines(self.screen, (0,0,0), False, pointsx, 2)
        # pygame.draw.lines(self.screen, (0,0,0), False, pointsy, 2)



    def drawInfo(self):
        pending = len(self.tile_loader.pending_tiles) + len(self.tile_loader.loading_tiles)
        self.gps_info._unload_opengl()
        self.gps_info = pi3d.String(font=arialFont, string="{0} tiles pending".format(pending))
        self.gps_info.draw()



    def draw_points(self):
        for point in self.points:
            x,y = self.tile_loader.dcord_to_dpix(point[0],self.longitude,point[1],self.latitude,self.zoom)
            #print (x,y)
            self.draw_center_circle(x,y)

    def draw_tracked_object(self):
        if self.tracking:
            point = self.tracked
            x,y = self.tile_loader.dcord_to_dpix(point[0],self.longitude,point[1],self.latitude,self.zoom)
            self.tracked_sprite.position(x,-y,0.1)
            self.tracked_sprite.rotateToZ(-point[2])
            self.tracked_sprite.draw()


    def set_tracked_position(self,longitude,latitude,yaw):
        if self.tracked[0] != longitude or self.tracked[1] != latitude:
            self.tracked = (longitude,latitude,yaw)
            self.queue_draw(gui_only=True)

    def set_attitude(self,roll,pitch,yaw=0):
        if self.horizon.tilt != pitch or self.horizon.roll != roll or self.horizon.yaw != yaw:
            self.horizon.tilt = pitch
            self.horizon.roll = roll
            self.horizon.yaw = yaw
            self.queue_draw(gui_only=True)


    def draw_tiles(self):
        span_x = self.width
        span_y = self.height
        tiles_x = int(ceil(span_x/256.0))
        tiles_y = int(ceil(span_y/256.0))
        if self.updated:
            #for line in self.tiles:
            #    for tile in line:
            #        tile._unload_opengl()
            #print("reloading")
            newset = set()
            newtiles = self.tile_loader.load_area(self.longitude,self.latitude,self.zoom,tiles_x,tiles_y)
            for line in newtiles:
                for tile in line:
                    newset.add(tile)
            for tile in self.tiles_set:
                if tile not in newset:
                    tile._unload_opengl()
            self.tiles_set = newset
            self.tiles = newtiles

            tile_number=0
            line_number=0
            x_center = 0#self.width/2
            y_center = 0#self.height/2
            offset_x,offset_y = self.tile_loader.gmap_tile_xy_from_coord(self.longitude,self.latitude,self.zoom)

            xtiles = len(self.tiles[0])
            ytiles = len(self.tiles)

            #self.screen.fill((1,1,1))
            #tiles.reverse()
            for line in self.tiles:
                for tile in line:
                    x = (tile_number - int(xtiles/2)) * 256 + x_center
                    y = (line_number - int(ytiles/2)) * 256 + y_center
                    finalx = x - offset_x+ 128
                    finaly = y - offset_y+ 128
                    tile.position(finalx+self.dx, -(finaly+self.dy), 100.0)
                    tile.draw()
                    #self.sprites.add(tile)
                    tile_number += 1
                tile_number = 0
                line_number += 1
            self.updated = False
        else:
            for sprites in self.tiles:
                for sprite in sprites:
                    sprite.draw()

        #self.sprites.draw(self.screen)
        self.to_draw = False

    def draw(self):
        self.draw_tiles()
        #print("drawing")
        self.draw_gui()
        #pygame.display.flip()

    def draw_gui(self):
        #self.drawInfo()
        if self.draw_gui_only_flag:
            self.draw_cross()
            self.draw_points()
            self.draw_tracked_object()
            self.draw_instruments()
            self.pointer.position(self.pointer_x - self.width/2, -self.pointer_y+self.height/2, 0.1)
            self.pointer.draw()

    def draw_instruments(self):
        #bottom = self.height-self.horizon.newsurf.get_rect().height
        self.horizon.update()
        #self.screen.blit(self.horizon.newsurf,(0,bottom))


    def queue_draw(self,gui_only=False):
        self.updated = not gui_only
        self.draw_gui_only_flag = True

    def update_mouse(self):
        #print("updating mouse")
        self.inputs.do_input_events()
        imx, imy, zoom, imh, imd = self.inputs.get_mouse_movement()
        self.on_move(self.pointer_x+imx,self.pointer_y+imy)
        if self.inputs.key_state("BTN_LEFT"):
            self.button = 1
        else:
            self.button = 0
        if zoom:
            self.on_scroll(zoom)

    def main_loop(self):

        """This is the Main Loop of the Game"""
        while self.DISPLAY.loop_running():
            #self.win.update()
            self.update_mouse()
            if self.inputs.key_state(27):
                #self.mykeys.close()
                self.DISPLAY.destroy()
                self.tile_loader.run = False
                self.telemetry_reader.run = False
            self.draw()



if __name__ == '__main__':
    gui = MyApp()
