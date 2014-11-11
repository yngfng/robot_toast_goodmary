"""
Copyright 2008 Ryan Hoffman

This file is part of Robot Toast.

Robot Toast is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Robot Toast is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Robot Toast.  If not, see <http://www.gnu.org/licenses/>.
"""
#------------------------------------------------------------------------------
#   Imports
#------------------------------------------------------------------------------

import os, math, random
from model_manager import ModelManage
from media_manager import MediaManage
import pygame
from pygame.locals import *
from OpenGL.GL import *


#------------------------------------------------------------------------------
#   Globals
#------------------------------------------------------------------------------

model_manager = ModelManage()
media_manager = MediaManage()

def power2(x):
	"""
	power2(x) -> nearest power of two

    Calculate the nearest power of two that is equal
    or greater than x
    """
	p = math.log(x) / math.log(2)
	return 2 ** int(math.ceil(p))


#------------------------------------------------------------------------------
#   GLSprite Base Classes
#------------------------------------------------------------------------------

class BaseEntity(object):

	def __init__(self):
		self.x = 0.0
		self.y = 0.0
		self.width = 0.0
		self.height = 0.0

	def __getattr__(self, name):
		"""Return calculated x or y value"""
		if name is "left":
			return self.x
		if name is "right":
			return self.x + self.width
		if name is "top":
			return self.y + self.height
		if name is "bottom":
			return self.y
		if name is "centerx":
			return self.x + self.width / 2
		if name is "centery":
			return self.y + self.height / 2


class GLSprite(pygame.sprite.Sprite, BaseEntity):

	def __init__(self):
		pygame.sprite.Sprite.__init__(self)
		self.rect = None
		self.name = "GLsprite"
		self.vx = 0.0
		self.vy = 0.0
		self.facing = 0.0
		self.model = None

	def update(self, interval):
		pygame.sprite.Sprite.update(self)
		if interval is 0:
			return

	def draw(self):
		"""Draw model"""
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glTranslate(self.x, self.y, 0.0)
		glCallList(self.model)


class GLSpriteGroup(pygame.sprite.Group):

	def __init__(self, *args):
		pygame.sprite.Group.__init__(self, *args)

	def draw(self, camera=False):
		if camera:
			for sprite in self:
				if camera.sprite_in_view(sprite):
					sprite.draw()
		else:
			[sprite.draw() for sprite in self]

			
class LevelPages(object):
	
	def __init__(self, level_page_data):
		# data is two dimensional array of sprites
		self.data = level_page_data
		self.length_x = len(self.data)
		self.length_y = len(self.data[0])
		
	def draw(self, camera):
		currentx, currenty = camera.current_page()
		startx = currentx - 1
		stopx = currentx + 2
		start_y = currenty - 1
		stop_y = currenty + 2
		for x in range(startx, stopx):
			if x < 0 or x > self.length_x - 1:
				continue
			for y in range(start_y, stop_y):
				if y < 0 or y > self.length_y:
					continue
				try:
					sprite = self.data[x][y]
				except IndexError:
					continue
				if sprite is None:
					continue
				if camera.sprite_in_view(sprite):
					sprite.draw()
					
	def get_models(self):
		model_list = []
		for x in self.data:
			for y in x:
				model_list.append(y)
				
		return model_list
		

#------------------------------------------------------------------------------
#   Sprites
#------------------------------------------------------------------------------

class ColorBackground(GLSprite):

	def __init__(self, x, y, width, height, color=(0, 0, 0)):
		GLSprite.__init__(self)

		# Position and orientation
		self.x = x
		self.y = y
		self.width = width
		self.height = height

		# Load model
		background = pygame.Surface((1, 1))
		image_name = "background_%s_%s_%s" % (color[0], color[1], color[2])
		background.fill(color)
		texture = media_manager.load_texture(image_name, background)

		self.model = model_manager.textured_quad(texture, width, height)


class ImageBackground(GLSprite):

	def __init__(self, x, y, width, height, image_name=None, sub_dir='images', tile_scale=0):
		GLSprite.__init__(self)

		# Position and orientation
		self.x = x
		self.y = y
		self.width = width
		self.height = height

		image_obj = media_manager.load_image(image_name, sub_dir)
		if tile_scale:
			s = (float(self.width) / tile_scale) / image_obj.get_width()
			t = (float(self.height) / tile_scale) / image_obj.get_height()
		else:
			s = 1.0
			t = 1.0
		tex_coords = ((0.0, 0.0), (s, 0.0), (s, t), (0.0, t))

		# Load model
		texture = media_manager.save_texture(image_name, image_obj)
		self.model = model_manager.textured_quad(texture, width, height, tex_coords)


class TilePage(GLSprite):

	def __init__(self, x, y, width, height, model):
		GLSprite.__init__(self)

		# Position and orientation
		self.x = x
		self.y = y
		self.width = width
		self.height = height

		self.model = model


class GLText(GLSprite):

	def __init__(self, string, x, y, font='Robot.ttf', size=14, 
				 color=(0, 0, 0), halign='left', valign='bottom'):
		GLSprite.__init__(self)
		self.name = "Text"
		self.string = ""

		# Positioning and orientation
		self.x = x
		self.y = y
		self.size = size
		self.facing = 0
		self.valign = valign
		self.halign = halign

		self.font = media_manager.load_font(font, size)
		self.color = color
		self.update_string(string)

		# Reposition for alignment
		if self.halign == "middle":
			self.x -= self.width / 2
		elif self.halign == "right":
			self.x -= self.width
		if self.valign == "middle":
			self.y -= self.height / 2
		elif self.valign == "top":
			self.y -= self.height

	def update_string(self, new_string):
		# Only update new strings
		if new_string == "" or new_string == None or self.string == new_string:
			return

		# Render font
		self.string = str(new_string)
		text = self.font.render(self.string, 1, self.color)

		# Calculate dimensions
		rect = text.get_rect()
		self.width = rect.width
		self.height = rect.height
		width_pow2 = power2(self.width)
		height_pow2 = power2(self.height)
		x_tex = self.width / float(width_pow2)
		y_tex = 1.0 - (self.height / float(height_pow2))

		# Blit texture
		surface = pygame.Surface((width_pow2, height_pow2), SRCALPHA, 32)
		surface.blit(text, (0, 0))
		texture = media_manager.load_texture(self.string, surface)

		# Create model
		tex_coords = ((0.0, y_tex), (x_tex, y_tex), (x_tex, 1.0), (0.0, 1.0))
		self.model = model_manager.textured_quad(texture, self.width, 
												 self.height, tex_coords)


class Actor(GLSprite):
	"""Generic movable/collidable object with gravity"""

	def __init__(self, x, y, gamestate):
		GLSprite.__init__(self)
		# Collision attributes
		self.x = float(x)
		self.y = float(y)
		self.width = 0.0
		self.height = 0.0
		self.gamestate = gamestate
		self.level = self.gamestate.level
		self.collision_properties = {}

		# Textures
		self.texture_width = 0.0
		self.texture_height = 0.0
		self.current_texture = 0
		self.prev_texture = 0

		# Movement
		self.gravity = 0.0019
		self.terminal_velocity = 1

		# Velocity
		self.vx = 0.0
		self.vy = 0.0
		
		# Sounds
		self.sounds = {}
		self.sounds_looping = []

	def draw(self):
		"""Draw model"""
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		x = self.x - (self.texture_width - self.width) / 2
		y = self.y - (self.texture_height - self.height) / 2
		glTranslate(x, y, 0.0)
		glRotatef(self.facing, 0.0, 0.0, 1.0)
		glBindTexture(GL_TEXTURE_2D, self.current_texture)
		glCallList(self.model)

	def kill(self):
		self.vx = 0.0
		self.vy = 0.0
		GLSprite.kill(self)

	def push_x(self, tiles):
		x_push = 0.0
		for tile in tiles:
			if tile.has_property('solid'):
				x_diff = 0.0
				if self.vx > 0:
					x_diff = tile.left - self.right - 0.0001
				elif self.vx < 0:
					x_diff = tile.right - self.left
				if abs(x_diff) > abs(x_push):
					x_push = x_diff
		return x_push

	def push_y(self, tiles):
		y_push = 0.0
		for tile in tiles:
			if tile.has_property('solid'):
				y_diff = 0.0
				if self.vy < 0:
					y_diff = tile.top - self.bottom
				elif self.vy > 0:
					y_diff = tile.bottom - self.top - 0.0001
				if abs(y_diff) > abs(y_push):
					y_push = y_diff
		return y_push

	def add_collision_properties(self, tiles):
		"""Add properties without duplicates"""
		for tile in tiles:
			for property, value in tile.properties.iteritems():
				self.collision_properties[property] = value

	def process_collision_properties(self):
		self.gamestate.process_collision_properties(self.collision_properties, self)
		self.collision_properties = {}
		
	def play_sound(self, sound_name):
		"""Try to play a sound object in self.sounds"""
		try:
			self.sounds[sound_name].play()
		except KeyError:
			print "Sound object not found for %s" % sound_name
		
	def play_sound_loop(self, sound_name):
		"""
		Try to play a sound, looping infinitely
		
		only play if sound isnt already playing
		"""
		if sound_name not in self.sounds_looping:
			try:
				self.sounds[sound_name].play(-1)
				self.sounds_looping.append(sound_name)
			except KeyError:
				print "Sound object not found for %s" % sound_name
		
	def stop_sound_loop(self, sound_name):
		"""Stop a sound if its looping"""
		if sound_name in self.sounds_looping:
			try:
				self.sounds[sound_name].stop()
				self.sounds_looping.remove(sound_name)
			except KeyError:
				print "Sound object not found for %s" % sound_name
				

#------------------------------------------------------
#		MAIN PLAYER STUFF
#------------------------------------------------------

class StickDude(Actor):

	def __init__(self, gamestate):
		Actor.__init__(self, 0.0, 0.0, gamestate)
		# Collision attributes
		self.width = 30.0
		self.height = 62.0

		# Controls
		self.move_x = 0
		self.move_y = 0
		self.jump = 0
		self.fire = 0
		self.tap_jump = False
		self.tap_fire = False
		self.tap_up = False
		self.tap_down = False
		self.tap_left = False
		self.tap_right = False

		# Movement
		self.facing_right = True
		self.wj_right = True
		self.movestate = self.falling
		self.jumpvel = 0.5
		self.jumpcharge = 0
		self.runaccel = 0.002
		self.runspeed = 0.42
		self.launchpos = 0
		self.jumpheight = 0
		self.grabpotential = False
		self.jetpackchargemax = 1000.0 # ms of pack charge, i think
		self.jetpackcharge = 0
		self.hasjetpack = False
		self.hasgrapple = False

		# Textures
		self.texture_width = 64.0
		self.texture_height = 128.0
		totaltextures = []
		self.idleframes = ['ninjabot_idle_1.png']
		totaltextures.extend(self.idleframes)
		self.runframes = ['ninjabot_run_1.png', 'ninjabot_run_2.png', 'ninjabot_run_3.png', 'ninjabot_run_4.png', 'ninjabot_run_5.png', 'ninjabot_run_6.png', 'ninjabot_run_7.png', 'ninjabot_run_8.png', 'ninjabot_run_9.png', 'ninjabot_run_10.png', 'ninjabot_run_11.png', 'ninjabot_run_0.png']
		totaltextures.extend(self.runframes)
		self.wallslideframes = ['ninjabot_wallslide_0.png']
		totaltextures.extend(self.wallslideframes)
		self.ledgegrabframes = ['ninjabot_grab_towards.png']
		totaltextures.extend(self.ledgegrabframes)
		self.jumpframes = ['ninjabot_jump_0.png', 'ninjabot_jump_1.png', 'ninjabot_jump_2.png', 'ninjabot_jump_3.png', 'ninjabot_jump_4.png', 'ninjabot_jump_5.png', 'ninjabot_jump_6.png', 'ninjabot_jump_7.png', 'ninjabot_jump_8.png', 'ninjabot_jump_9.png']
		totaltextures.extend(self.jumpframes)
		self.jumpupframes = ['ninjabot_jumpup_0.png', 'ninjabot_jumpup_1.png', 'ninjabot_jumpup_2.png', 'ninjabot_jumpup_3.png', 'ninjabot_jumpup_4.png', 'ninjabot_jumpup_5.png', 'ninjabot_jumpup_6.png', 'ninjabot_jumpup_7.png']
		totaltextures.extend(self.jumpupframes)
		self.fallingupframes = ['ninjabot_fall_0.png']
		totaltextures.extend(self.fallingupframes)
		self.fallingframes = ['ninjabot_jump_8.png']
		totaltextures.extend(self.fallingframes)
		self.jetpackframes = ['ninjabot_jetpack_0.png', 'ninjabot_jetpack_1.png', 'ninjabot_jetpack_2.png', 'ninjabot_jetpack_3.png', 'ninjabot_jetpack_4.png', 'ninjabot_jetpack_5.png', 'ninjabot_jetpack_6.png', 'ninjabot_jetpack_7.png', 'ninjabot_jetpack_8.png', 'ninjabot_jetpack_9.png']
		totaltextures.extend(self.jetpackframes)
		self.grappleframes = ['ninjabot_swinging.png']
		totaltextures.extend(self.grappleframes)
		self.currentframes = self.idleframes
		self.frameindex = 0
		self.framedelay = 0

		# create texture dictionary for GL storage and shit, with texture names as keys
		self.textures = {}
		for tex in totaltextures:
			self.textures[tex] = media_manager.load_texture(tex)
		self.current_texture = self.textures[self.idleframes[0]]

		# Model 
		self.model_left = model_manager.untextured_quad('stick_dude_left', self.texture_width, self.texture_height)
		self.model_right = model_manager.untextured_quad('stick_dude_right', self.texture_width, self.texture_height, 
														 tex_coords=((1.0, 0.0), (0.0, 0.0), (0.0, 1.0), (1.0, 1.0)))
		self.model = self.model_left

		# Grapple - create model, which always exists, but doesnt always draw
		self.grapplinghook = Grapple(self, self.x, self.y, 'grapple_rod.png' )
		
		# Sounds
		self.wilhelm = media_manager.load_sound('Wilhelm.ogg')
		self.wilhelm.set_volume(0.1)
		self.sounds = {
			"explosion": media_manager.load_sound('explosion.wav'),
			"jet": media_manager.load_sound('jet.wav'),
			"jump": media_manager.load_sound('jump.wav'),
			"run": media_manager.load_sound('run.wav'),
			"land": media_manager.load_sound('land.wav'),
			"clink": media_manager.load_sound('clink.wav')
			}
		self.sounds['run'].set_volume(0.2)
		self.sounds['jump'].set_volume(0.2)
		self.sounds['jet'].set_volume(0.6)
		self.sounds['land'].set_volume(0.1)
		self.sounds['clink'].set_volume(0.3)

	def draw(self):
		if self.grapplinghook.on:
			self.grapplinghook.draw()
		Actor.draw(self)

	def update(self, interval):
		Actor.update(self, interval)
		if interval is 0:
			return

		#fire the grapple, if tapped
		if self.tap_fire and self.hasgrapple:
			self.grapplinghook.fire(self.move_x, self.move_y)

		#charge jetpack
		if self.movestate != self.jetpacking and self.hasjetpack:
			self.jetpackcharge += interval
			if self.jetpackcharge > self.jetpackchargemax:
				self.jetpackcharge = self.jetpackchargemax
			# Kill sound effect if not jet packing
			self.stop_sound_loop('jet')
				
		# Set previous move state
		self.previousmovestate = self.movestate

		# set base velocity based on current state and user inputs
		self.movestate(interval)
		self.grapplinghook.update(interval)

		if self.vx > self.terminal_velocity:
			self.vx = self.terminal_velocity
		if self.vx < -self.terminal_velocity:
			self.vx = -self.terminal_velocity
		if self.vy > self.terminal_velocity:
			self.vy = self.terminal_velocity
		if self.vy < -self.terminal_velocity:
			self.vy = -self.terminal_velocity

		# move on x axis, detect collisions and react
		self.x += self.vx * interval
		tiles = self.level.tile_collide(self)
		self.add_collision_properties(tiles)
		push_x = self.push_x(tiles)
		if push_x:
			# check for wallslide
			self.upjump = False
			#if self.vx > 0 and self.move_x > 0 and self.movestate == self.falling and self.vy < 1:
			if self.vx > 0 and push_x < 0 and self.movestate == self.falling:
				self.movestate = self.wallslide
				self.wj_right = True
			#elif self.vx < 0 and self.move_x < 0 and self.movestate == self.falling and self.vy < 1:
			elif self.vx < 0 and push_x > 0 and self.movestate == self.falling:
				self.movestate = self.wallslide
				self.wj_right = False
			self.x += push_x
			self.vx = 0

		# same on y
		self.y += self.vy * interval
		tiles = self.level.tile_collide(self)
		self.add_collision_properties(tiles)
		push_y = self.push_y(tiles)
		if push_y:
			self.upjump = False
			self.y += push_y
			if push_y > 0:
				self.movestate = self.grounded
			self.vy = 0
		elif self.movestate == self.grounded:
			if self.grapplinghook.on:
				self.movestate = self.grappling
			else:
				self.movestate = self.falling

		# Pass special collisions back to gamestate
		self.process_collision_properties()

		# ANIMATE!!!!
		# set animation based on movement state and some other craps
		if self.movestate == self.grounded and self.move_x:
			self.currentframes = self.runframes
		elif self.movestate == self.wallslide:
			self.currentframes = self.wallslideframes
		elif self.movestate == self.ledgegrab:
			self.currentframes = self.ledgegrabframes
		elif self.movestate == self.jetpacking:
			self.currentframes = self.jetpackframes
		elif self.movestate == self.falling:
			if self.vy > 0:
				if self.upjump == True:
					self.currentframes = self.jumpupframes
				else:
					self.currentframes = self.jumpframes
			else:
				if self.upjump == True:
					self.currentframes = self.fallingupframes
				else:
					self.currentframes = self.fallingframes
		elif self.movestate == self.grappling:
			self.currentframes = self.grappleframes
		else:
			self.currentframes = self.idleframes

		# do dat animashyon loop theeng
		self.framedelay += interval
		if self.framedelay > 60 or self.previousmovestate != self.movestate:
			self.framedelay = 0
			if self.frameindex > len(self.currentframes) - 1 or self.previousmovestate != self.movestate:
				self.frameindex = 0
			self.current_texture = self.textures[self.currentframes[self.frameindex]]
			self.frameindex += 1

		# set facing based on intended move
		if self.move_x > 0:
			self.facing_right = True
			self.model = self.model_right
		elif self.move_x < 0:
			self.facing_right = False
			self.model = self.model_left
			
		# Sounds based on animation
		if self.current_texture != self.prev_texture:
			if self.movestate == self.grounded and self.move_x:
				if self.current_texture == self.textures['ninjabot_run_1.png']:
					self.play_sound('run')
				elif self.current_texture == self.textures['ninjabot_run_7.png']:
					self.play_sound('run')
		
		# sounds based on collision
		if self.movestate != self.previousmovestate:
			if self.movestate == self.grounded or self.movestate == self.wallslide:
				self.play_sound('land')

				
		# Set previous texture
		self.prev_texture = self.current_texture
			
	def kill(self):
		Actor.kill(self)
		self.play_sound('explosion')
		

#------------------------------------------------------
#		MOVESTATES
#------------------------------------------------------

	def bullshitmove(self, interval):
		self.vx = self.move_x
		self.vy = self.move_y

	def grounded(self, interval):
		self.vy -= self.gravity * interval

		if self.move_x:
			self.vx += self.move_x * self.runaccel * interval
			if self.vx > self.runspeed:
				self.vx = self.runspeed
			if self.vx < -self.runspeed:
				self.vx = -self.runspeed
		else:
			self.vx -= self.vx * self.runaccel * interval * 4
			if abs(self.vx) < 0.1:
				self.vx = 0
		if self.tap_jump:
			self.vy = self.jumpvel
			self.jumpcharge = 200
			self.movestate = self.falling
			if not self.move_x:
				self.upjump = True
			#self.launchpos = self.y
			self.play_sound('jump')

	def falling(self, interval):
		if self.tap_jump and self.jetpackcharge > 500:
			self.jetpackcharge -= 50
			self.movestate = self.jetpacking
			return
		if self.jumpcharge > 0 and self.hold_jump:
			self.jumpcharge -= interval
		else:
			self.jumpcharge = 0
			self.vy -= self.gravity * interval
		if (self.vx < self.runspeed and self.move_x > 0) or (self.vx > -self.runspeed and self.move_x < 0):
			self.vx += self.move_x * self.runaccel * interval * 0.5
		#jumpcrap = self.jumpheight
		#if self.launchpos:
			#self.jumpheight = self.y - self.launchpos
			#if jumpcrap > self.jumpheight and self.jumpheight:
				#self.jumpheight = 0
				#self.launchpos = 0

	def jetpacking(self, interval):
		#thrust!
		self.jetpackcharge -= interval
		self.vy -= self.gravity * interval
		if self.hold_jump and self.jetpackcharge > 0:
			if self.vy < self.runspeed / 2:
				self.vy += 0.004 * interval
			if (self.vx < self.runspeed and self.move_x > 0) or (self.vx > -self.runspeed and self.move_x < 0):
				self.vx += self.move_x * self.runaccel * interval
			else:
				self.vx += self.move_x * self.runaccel * interval * 0.2
		else:
			if self.jetpackcharge <= 0:
				self.jetpackcharge = -200
			self.movestate = self.falling
		# Play looping sound if not started yet
		self.play_sound_loop('jet')

	def wallslide(self, interval):
		self.vx += self.move_x * self.runaccel
		self.vy -= self.gravity * interval
		#if self.vy < -1 or self.move_x == 0: # use this to limit fall speed for wallslide
		if self.wj_right:
			jumpx = -1
		else:
			jumpx = 1
		# ---- WALLJUMP!!!!
		if self.tap_jump:
			self.vy += self.jumpvel
			if self.vy > self.jumpvel:
				self.vy = self.jumpvel
			#self.vx = self.runspeed * jumpx * 1
			self.vx = jumpx * self.jumpvel * 0.8
			self.jumpcharge = 200
			self.movestate = self.falling
			self.play_sound('jump')
			return
		if self.model == self.model_right:
			xdelta = 16 # exactly enough to catch it --- TRY ACTUAL SIZE????
		else:
			xdelta = -16
		sliding_tile = self.level.point_collide(self.centerx + xdelta, self.centery)
		st_top = self.level.point_collide(self.centerx + xdelta, self.top)
		if (sliding_tile and sliding_tile.has_property('solid')) or (st_top and st_top.has_property('solid')):
			pass
		else:
			self.movestate = self.falling
			self.grabpotential = False
			return

		# if pushing toward the wall, do friction and grab
		if self.move_x == -jumpx:
			if self.vy < 0:
				bullshitfrictionnumber = 0.0015
				if self.vy < -0.5:
					bullshitfrictionnumber = 0.0018
				self.vy += interval * bullshitfrictionnumber
				# ledge grab check
				if st_top.has_property('solid'):
					if self.grabpotential:
						self.movestate = self.ledgegrab
						self.vx = 0
						self.vy = 0
						self.grabpotential = False
				else:
					self.grabpotential = True

	def ledgegrab(self, interval):
		if self.tap_jump:
			if (self.move_x < 0 and self.wj_right) or (self.move_x > 0 and self.wj_right == False):
				self.vx = self.move_x * self.jumpvel * 0.8
				self.jumpcharge = 200
				jumpmult = 1
			else:
				jumpmult = 1
			self.vy = self.jumpvel * jumpmult
			self.movestate = self.falling
			self.play_sound('jump')
		if self.move_y < 0:
			self.movestate = self.falling

	def grappling(self, interval):
		# movement once the grapple is attached - have to build vectors and all kinda shit
		gh = self.grapplinghook
		if not self.hold_fire:
			self.movestate = self.falling
			self.grapplinghook.reset()
			return

		# adjust length based on user input
		if gh.lengthlock:
			if self.tap_up or self.tap_down:
				gh.lengthlock = False
		else:
			if self.move_y < 0:
				gh.length += interval * 0.2
			if self.move_y > 0:
				gh.length -= interval * 0.2
			if gh.length > gh.maxlength:
				gh.length = gh.maxlength
			if gh.length < gh.minlength:
				gh.length = gh.minlength

		# add linear velocity for swing
		if self.vy < 0:
			self.vx += self.move_x * self.runaccel * interval * 0.1

		# set intended new position based on velocity
		self.vy -= self.gravity * interval
		newposx = self.centerx + self.vx * interval
		newposy = self.centery + self.vy * interval

		# get angle between self.intended position and grappling hook latch point - which way?
		ar = math.atan2(gh.y - newposy, gh.x - newposx)
		ad = math.degrees(ar)

		# add rotational speed for swing and convert back
		ad += self.move_x * interval * 0.001
		ar = math.radians(ad)

		# find allowed new position based on length of grapple
		newposx = gh.x - gh.length * math.cos(ar)
		newposy = gh.y - gh.length * math.sin(ar)
		# set velocity toward new position
		self.vx = (newposx - self.centerx) / interval
		self.vy = (newposy - self.centery) / interval
		#gh.angle = math.degrees(ar)
		#gh.originx = gh.x - gh.length * math.cos(ar)
		#gh.originy = gh.y - gh.length * math.sin(ar)
		#self.vx = (gh.originx - self.centerx) / interval
		#self.vy = (gh.originy - self.centery) / interval
		#self.facing = gh.angle - 90 #THIS DOESNT TRANSFORM PROPERLY

# ----------------------------------------------------
#		GRAPPLE
# ----------------------------------------------------

class Grapple(Actor):

	def __init__(self, parent, x, y, img, sub_dir='images'):
		Actor.__init__(self, x, y, parent.gamestate)
		self.parent = parent

		# Texture
		self.texture_width = 4.0
		self.texture_height = 4.0
		texture = media_manager.load_texture(img, sub_dir=sub_dir)
		self.current_texture = texture

		# Model 
		self.model = model_manager.textured_quad(texture, self.texture_width, self.texture_height)
		self.length = 1.0

		# STUFF
		self.maxlength = 256
		self.minlength = 16
		self.angle = 0
		self.latched = False
		self.lengthlock = True

	def reset(self):
		self.on = False
		self.latched = False
		self.lengthlock = True
		self.angle = 0
		self.length = 1.0
		self.x = self.parent.centerx
		self.y = self.parent.centery

	def fire(self, movex, movey):
		self.on = True
		self.lengthlock = True
		fr = self.parent.facing_right
		if self.parent.movestate == self.parent.wallslide or self.parent.movestate == self.parent.ledgegrab:
			# swap sides if you're on the wall
			movex = -movex
			if fr == True:
				fr = False
			else:
				fr = True
		if fr:
			a = 45
		else:
			a = 135
		if movex > 0 and movey == 0:
			a = 0
		if movex > 0 and movey > 0:
			a = 45
		if movex == 0 and movey > 0:
			a = 90
		if movex < 0 and movey < 0:
			a = 135
		if movex < 0 and movey == 0:
			a = 180
		self.angle = a

	def draw(self):
		"""Draw model"""
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		x = self.x - (self.texture_width - self.width) / 2
		y = self.y - (self.texture_height - self.height) / 2
		glTranslate(x, y, 0.0)
		glRotatef(self.angle + 180, 0.0, 0.0, 1.0)
		glScalef(self.length / 4, 1.0, 1.0)
		glBindTexture(GL_TEXTURE_2D, self.current_texture)
		glCallList(self.model)

	def update(self, interval):
		Actor.update(self, interval)
		if not self.parent.hold_fire:
			self.reset()
			return
		if self.latched:
			ar = math.atan2(self.y - self.parent.centery, self.x - self.parent.centerx)
			self.angle = math.degrees(ar)
			#self.originx = self.parent.centerx
			#self.originy = self.parent.centery
			#self.originx = self.x - self.length * math.cos(ar)
			#self.originy = self.y - self.length * math.sin(ar)
			if self.parent.movestate != self.parent.grappling:
				if self.parent.movestate == self.parent.grounded:
					self.length = math.hypot(self.x - self.parent.centerx, self.y - self.parent.centery)
					if self.length > self.maxlength:
						self.length = self.maxlength
						#self.reset()
						#return
						self.parent.movestate = self.parent.grappling
						self.parent.vy += 0.1
						#self.parent.jumpcharge = 0
				else:
					self.parent.movestate = self.parent.grappling

		else:
			self.originx = self.parent.centerx
			self.originy = self.parent.centery
			self.length += interval * 1
			if self.length > self.maxlength:
				self.reset()
			self.x = self.originx + self.length * math.cos(math.radians(self.angle))
			self.y = self.originy + self.length * math.sin(math.radians(self.angle))

			grab_tile = self.parent.level.point_collide(self.x, self.y)
			if grab_tile:
				if grab_tile.has_property('nograpple') or grab_tile.has_property('kill'):
					self.parent.play_sound('clink')
					self.reset()
					return
				if grab_tile.has_property('solid'):
					self.latched = True
					self.parent.movestate = self.parent.grappling

				
class RobotParticle(Actor):
	"""Particle object used in explosion"""

	def __init__(self, x, y, gamestate, img, sub_dir='images'):
		Actor.__init__(self, x, y, gamestate)
		# Collision attributes
		self.width = 10.0
		self.height = 10.0
		self.ttl = 5000

		# Velocity
		self.vx = random.randrange(-3, 3) * 0.1
		self.vy = random.randrange(1, 10) * 0.1

		# Texture
		self.texture_width = 16.0
		self.texture_height = 16.0
		texture = media_manager.load_texture(img, sub_dir=sub_dir)
		self.current_texture = texture

		# Model 
		self.model = model_manager.textured_quad(texture, self.texture_width, self.texture_height)

	def update(self, interval):
		Actor.update(self, interval)
		# Decrement TTL
		self.ttl -= interval
		if self.ttl < 0:
			self.kill()
			return

		# set base velocity based on current state and user inputs
		self.vy -= self.gravity * interval
		if self.vx > self.terminal_velocity:
			self.vx = self.terminal_velocity
		if self.vx < -self.terminal_velocity:
			self.vx = -self.terminal_velocity

		# move on x axis, detect collisions and react
		tiles = self.level.tile_collide(self)
		push_x = self.push_x(tiles)
		push_y = self.push_y(tiles)
		if push_x or push_y:
			self.vx = 0.0
			self.vy = 0.0
		self.x += self.vx * interval
		self.y += self.vy * interval


#------------------------------------------------------------------------------
#   Entities
#------------------------------------------------------------------------------

class Camera(BaseEntity):

	def __init__(self, x, y, width, height, limit_x, limit_y, subject=None):
		BaseEntity.__init__(self)
		self.width = width
		self.height = height
		# x and y are camera center points
		self.x = x - self.width / 2
		self.y = y - self.height / 2
		self.limit_x = limit_x
		self.limit_y = limit_y
		self.subject = subject

		# Transition stuff
		self.transition_in = False
		self.transition_out = False
		self.transition_x = 0.0
		self.transition_y = 0.0
		self.clamp = True
		self.zoom = 1.0

		self.vx = 0.0
		self.vy = 0.0
		self.update(0)

	def update(self, interval):
		subject = self.subject
		margin = 200.0
		if isinstance(subject, GLSprite):
			# Target Point
			if self.transition_in:
				if self.zoom > 1.993:
					self.zoom -= interval / 500000.0
					target_x = self.transition_x
					target_y = self.transition_y
				else:
					self.zoom -= interval / 3000.0
					if self.zoom < 1.0:
						self.zoom = 1.0
					target_x = subject.centerx + subject.vx * 400 - self.width / 2
					target_y = subject.centery + subject.vy * 300 - self.height / 2
			elif self.transition_out:
				self.zoom -= interval / 4000.0
				if self.zoom < 0.001:
					self.zoom = 0.001
				target_x = self.transition_x
				target_y = self.transition_y
			else:
				try:
					if subject.facing_right is True:
						facing_mod = 128.0
					else:
						facing_mod = -128.0
				except:
					facing_mod = 0.0
				vert_mod = 0.0
				try:
					if subject.vy > 0:
						vert_mod = 64.0
					elif subject.vy < 0:
						vert_mod = -64.0
				except:
					pass
				target_x = subject.centerx + subject.vx * 400 + facing_mod - self.width / 2
				target_y = subject.centery + subject.vy * 500 + vert_mod - self.height / 2
			# Calculate self velocity
			max_vx = (target_x - self.x) / 400
			max_vy = (target_y - self.y) / 400
			self.vx += (max_vx / 1000) * interval
			if abs(self.vx) > abs(max_vx):
				self.vx = max_vx
			self.vy += (max_vy / 1000) * interval
			if abs(self.vy) > abs(max_vy):
				self.vy = max_vy
			# Move based on self velocity
			self.x += self.vx * interval
			self.y += self.vy * interval
			# Clamp camera to level dimensions
			if self.clamp:
				if self.left < 0:
					self.x = 0.0
				if self.right > self.limit_x:
					self.x = self.limit_x - self.width
				if self.bottom < 0:
					self.y = 0.0
				if self.top > self.limit_y:
					self.y = self.limit_y - self.height			

	def current_page(self):
		pagex = int(self.centerx / 512)
		pagey = int(self.centery / 512)
		return pagex, pagey
		
	def sprite_in_view(self, sprite):
		zoom_width = (self.width * self.zoom - self.width)
		zoom_height = (self.height * self.zoom - self.height)
		left = self.left + zoom_width / 2
		right = left + self.width - zoom_width
		bottom = self.bottom + zoom_height / 2
		top = bottom + self.height - zoom_height
		return right >= sprite.left and left <= sprite.right and \
			   bottom <= sprite.top and top >= sprite.bottom

	def get_coords(self, limit_x, limit_y, zoom=True):
		"""Return coordinates for parallaxing backgrounds of different sizes"""

		# Free movement ratio between limit and self.limit
		if self.limit_x != self.width:
			x_ratio = (limit_x - self.width) / (self.limit_x - self.width)
		else:
			x_ratio = 1.0
		if self.limit_y != self.height:
			y_ratio = (limit_y - self.height) / (self.limit_y - self.height)
		else:
			y_ratio = 1.0
		
		# Zoom per axis
		if zoom:
			zoom_width = (self.width * self.zoom - self.width) * x_ratio
			zoom_height = (self.height * self.zoom - self.height) * y_ratio
		else:
			zoom_width = 0.0
			zoom_height = 0.0

		# Camera coordinates
		x = self.x + zoom_width / 2
		y = self.y + zoom_height / 2
		width = self.width - zoom_width
		height = self.height - zoom_height
		if self.clamp:
			if width > limit_x:
				width = limit_x
				height = width * (self.height / float(self.width))
			elif height > limit_y:
				height = limit_y
				width = height * (self.width / float(self.height))

		left = x * float(x_ratio)
		right = left + width
		bottom = y * float(y_ratio)
		top = bottom + height

		return left, right, bottom, top

	def start_transition(self, into=True):
		if into:
			self.transition_in = True
			self.zoom = 1.999999999
		else:
			self.transition_out = True
			self.zoom = 1.0
		self.transition_x = self.x
		self.transition_y = self.y
		self.clamp = False

	def stop_transition(self):
		self.transition_in = False
		self.zoom = 1.0
		self.clamp = True

	def zoom_in(self, interval):
		self.zoom += interval / 1000.0

	def zoom_out(self, interval):
		self.zoom -= interval / 1000.0
		if self.zoom < 0.01:
			self.zoom = 0.01

	def zoom_reset(self):
		self.zoom = 1.0
		
		
class CameraFocalPoint(BaseEntity):
	
	def __init__(self, x, y):
		BaseEntity.__init__(self)
		self.x = x
		self.y = y
		self.vx = 0.0
		self.vy = 0.0
		
	
class PlayerStart(BaseEntity):

	def __init__(self, x, y, index):
		BaseEntity.__init__(self)
		self.x = x
		self.y = y
		self.index = index
