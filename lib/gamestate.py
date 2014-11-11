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

from sprites import *
import level
import pygame
import menu
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import gluOrtho2D


#------------------------------------------------------------------------------
#   Game State
#------------------------------------------------------------------------------

class GameState:
	"""Base Game State"""

	def __init__(self, parent):
		self.running = False
		self.parent = parent
		pygame.mouse.set_visible(False)
		self.width = self.parent.width
		self.height = self.parent.height

	def start(self):
		"""Load required resources"""
		self.running = True

	def stop(self):
		"""Remove self from parent"""
		self.running = False
		self.parent.rem_game_state(self)

	def handle_event(self, event):
		"""Handle events specific to game state"""
		pass

	def tick(self, interval):
		"""Functions to execute every frame"""
		pass


#------------------------------------------------------------------------------
#   Game
#------------------------------------------------------------------------------

class Game(GameState):
	"""Base Gameplay"""
	
	def __init__(self, parent):
		"""self.level and self.player must be defined before calling init"""
		GameState.__init__(self, parent)
		
		# Sprite Groups
		self.g_actors = GLSpriteGroup()
		self.g_layer2 = GLSpriteGroup()
		self.g_transition = GLSpriteGroup()
		
		# Entities
		self.spawn_points = self.level.load_entities('PLAYERSTART')
		self.checkpoint = self.spawn_points['1']
		
		# Sprites
		transition_player = ImageBackground(self.checkpoint.x - 16.5, 
											self.checkpoint.y - 34.0,
											64.0, 128.0, 'ninjabot_transition.png')
		
		# Add Sprites to Groups
		self.g_transition.add(transition_player)
		self.spawn_player()
		
		self.level_pages = self.level.load_level_sprites()
		
		# Setup camera and transition
		cam_x = transition_player.centerx - 4.5
		cam_y = transition_player.centery + 21.0
		self.camera = Camera(cam_x, cam_y, 800.0, 600.0, self.level.right, self.level.top, self.player)
		self.camera.start_transition(into=True)
		self.player_alpha = 0.0
		self.background_alpha = 0.0
		self.transition_alpha = 1.0
		self.transition_in = True
		self.transition_out = False
		
		# Level states
		self.respawn_timer = 0
		self.goal_reached = False
		
		# Input retardation
		self.allow_control = False
		self.jumplock = False
		#self.hold_jump = False
		self.firelock = False
		#self.hold_fire = False
		self.uplock = False
		self.downlock = False
		self.leftlock = False
		self.rightlock = False
		
	def stop(self):
		# Remove GL display lists from memory
		for model in self.level_pages.get_models():
			try:
				glDeleteLists(model, 1)
			except:
				pass
		GameState.stop(self)
		
	def handle_event(self, event):
		"""Handle events specific to game state"""
		GameState.handle_event(self, event)
		cp = False
		if event.type == KEYDOWN:
			if event.key == K_ESCAPE:
				self.parent.add_game_state(menu.GameMenu(self.parent, self))
				return True
			if self.transition_in:
				if event.key == K_RETURN or event.type == JOYBUTTONDOWN:
					self.transition_in = False
					self.allow_control = True
					self.camera.stop_transition()
					self.background_alpha = 1.0
					self.player_alpha = 1.0
					self.transition_alpha = 0.0
					return True
			
			# **Dev stuff
			if event.key == K_F6:
				print "Player x, y: ", self.player.x, self.player.y
			if event.key == K_0:
				cp = '0'
			if event.key == K_1:
				cp = '1'
			if event.key == K_2:
				cp = '2'
			if event.key == K_3:
				cp = '3'
			if event.key == K_4:
				cp = '4'
			if event.key == K_5:
				cp = '5'
			if event.key == K_6:
				cp = '6'
			if event.key == K_7:
				cp = '7'
			if event.key == K_8:
				cp = '8'
			if event.key == K_9:
				cp = '9'
			try:
				if cp:
					self.checkpoint = self.spawn_points[cp]
					self.spawn_player()
			except:
				pass
		return True

	def tick(self, interval):
		""" Functions called every frame """
		GameState.tick(self, interval)
		
		# Handle Key down
		pressed = pygame.key.get_pressed()
		# Get stick inputs
		stick_x = 0
		stick_y = 0
		stick_button0 = 0
		stick_button1 = 0
		if self.parent.stick:
			stick_x = round(self.parent.stick.get_axis(0))
			stick_y = round(self.parent.stick.get_axis(1))
			stick_button0 = self.parent.stick.get_button(0)
			stick_button1 = self.parent.stick.get_button(1)
	
		# Player
		player = self.player
		player.move_y = 0
		player.move_x = 0

		player.tap_jump = False
		player.tap_fire = False
		player.tap_up = False
		player.tap_down = False
		player.tap_left = False
		player.tap_right = False

		# Controls 
		if self.allow_control:
			if pressed[K_UP] or pressed[K_w] or stick_y == -1:
				player.move_y += 1
				if not self.uplock:
					player.tap_up = True
				self.uplock = True
			else:
				self.uplock = False
			if pressed[K_DOWN] or pressed[K_s] or stick_y == 1:
				player.move_y -= 1
				if not self.downlock:
					player.tap_down = True
				self.downlock = True
			else:
				self.downlock = False
			if pressed[K_RIGHT] or pressed[K_d] or stick_x == 1:
				player.move_x += 1
				if not self.rightlock:
					player.tap_right = True
				self.rightlock = True
			else:
				self.rightlock = False
			if pressed[K_LEFT] or pressed[K_a] or stick_x == -1:
				player.move_x -= 1
				if not self.leftlock:
					player.tap_left = True
				self.leftlock = True
			else:
				self.leftlock = False
			if pressed[K_SPACE] or pressed[K_z] or stick_button0:
				player.hold_jump = True
				if not self.jumplock:
					player.tap_jump = True
				self.jumplock = True
			else:
				player.hold_jump = False
				self.jumplock = False
			if pressed[K_LSHIFT] or pressed[K_RSHIFT] or pressed[K_x] or stick_button1:
				player.hold_fire = True
				if not self.firelock:
					player.tap_fire = True
				self.firelock = True
			else:
				player.hold_fire = False
				self.firelock = False
	
			# Dev controls
			#if pressed[K_F7]:
			#	self.camera.zoom_in(interval)
			#if pressed[K_F8]:
			#	self.camera.zoom_out(interval)
			if pressed[K_b]:
				player.movestate = player.bullshitmove
				#player.wilhelm.play()
			if pressed[K_b] and pressed[K_LSHIFT]:
				player.movestate = player.falling
			#if pressed[K_j]:
			#	player.hasjetpack = True
			#if (pressed[K_j] and pressed[K_LSHIFT]) or (pressed[K_j] and pressed[K_RSHIFT]):
			#	player.hasjetpack = False
			#	player.jetpackcharge = 0
			#if (pressed[K_j] and pressed[K_LCTRL]) or (pressed[K_j] and pressed[K_RCTRL]):
			#	player.jetpackchargemax = 100000
			#	player.jetpackcharge = 100000
			#if pressed[K_l]:
			#	self.parent.ticklock = True
			#if pressed[K_l] and pressed[K_RSHIFT]:
			#	self.parent.ticklock = False
				
		# Update sprites
		self.g_actors.update(interval)
		self.g_layer2.update(interval)
		self.camera.update(interval)
		
		# Check to respawn
		if self.respawn_timer > 0:
			self.respawn_timer -= interval
			if self.respawn_timer <= 0:
				self.spawn_player()
		# Transition in
		if self.transition_in:
			if self.camera.zoom < 1.99:
				if self.player_alpha < 1.0:
					self.player_alpha += interval / 50.0
					if self.player_alpha > 1.0:
						self.player_alpha = 1.0
				if self.background_alpha < 1.0:
					self.background_alpha += interval / 300.0
					if self.background_alpha > 1.0:
						self.background_alpha = 1.0
				elif self.transition_alpha > 0.0:
					self.transition_alpha -= interval / 100.0
					if self.transition_alpha < 0.0:
						self.transition_alpha = 0.0
			if self.camera.zoom == 1.0:
				self.camera.stop_transition()
				if self.background_alpha == 1.0:
					self.transition_in = False
					self.allow_control = True
		# Transition out
		if self.transition_out:
			if self.camera.zoom < 0.5:
				self.background_alpha -= interval / 1000.0
				self.player_alpha -= interval / 1000.0
				if self.player_alpha < 0.0:
					self.player_alpha = 0.0
				if self.background_alpha < 0.0:
					self.background_alpha = 0.0
				if self.camera.zoom <= 0.002:
					self.stop()
					
		current_page = self.camera.current_page()
	
	def leave_level(self):
		self.transition_out = True
		self.music.fadeout(1000)
		self.camera.start_transition(into=False)
		
	def process_collision_properties(self, properties, sprite):
		"""Process collisions of sprite"""
		for property, value in properties.iteritems():
			if property == "kill":
				self.kill(sprite)
			if property == "checkpoint":
				self.checkpoint = self.spawn_points[str(value)]
			if property == "goal":
				if self.goal_reached is False:
					self.parent.add_game_state(self.next_level(self.parent))
					self.leave_level()
					self.goal_reached = True
	
	def kill(self, sprite):
		if sprite in self.g_actors:
			self.spawn_explosion(sprite.centerx, sprite.centery)
		sprite.kill()
		self.respawn_timer = 2000
		
	def spawn_player(self):
		self.player.x = self.checkpoint.x
		self.player.y = self.checkpoint.y
		self.g_actors.add(self.player)
		
	def spawn_explosion(self, x, y):
		particles = []
		for i in range(10):
			particles.append(RobotParticle(x, y, self, 'particle.png'))
		self.g_layer2.add(particles)
		
		
		
class TestLevel(Game):
	"""Test Level, NEVER USE!"""
	
	def __init__(self, parent):
		# Level
		self.level = level.Level('level0.svg')
		self.current_level = TestLevel
		self.next_level = TestLevel2
		
		# Sprites
		self.player = StickDude(self)
		self.background = ImageBackground(0, 0, 1100.0, 1100.0, 'level2_background_1.png')
		self.background2 = ImageBackground(0, 0, 1250.0, 1250.0, 'level2_background_2.png')
		self.background3 = ImageBackground(0, 0, 1650.0, 1650.0, 'level2_background_3.png')
		
		Game.__init__(self, parent)
		
		# **Temporary collision sprites
		self.level_pages_dev = self.level.load_collision_as_sprites()
				
	def tick(self, interval):
		""" Functions called every frame """
		Game.tick(self, interval)
		
		cam = self.camera
		
		# Draw Backgrounds
		glColor4f(1.0, 1.0, 1.0, self.background_alpha)
		left, right, bottom, top = cam.get_coords(self.background.width, self.background.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background.draw()
		left, right, bottom, top = cam.get_coords(self.background2.width, self.background2.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background2.draw()
		left, right, bottom, top = cam.get_coords(self.background3.width, self.background3.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background3.draw()
		
		# Move view to camera
		left, right, bottom, top = cam.get_coords(self.level.width, self.level.height)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)	
		
		# Draw Level
		self.level_pages_dev.draw(cam)
		self.level_pages.draw(cam)
		glColor4f(1.0, 1.0, 1.0, self.player_alpha)
		self.g_actors.draw()
		if self.transition_in:
			glColor4f(1.0, 1.0, 1.0, self.transition_alpha)
			self.g_transition.draw()
		glColor4f(1.0, 1.0, 1.0, 1.0)
		self.g_layer2.draw()
				
		# Zoom Out
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(0.0, self.width, 0.0, self.height)


class Level1(Game):
	"""Computer Time"""
	
	def __init__(self, parent):
		# Level
		self.level = level.Level('level1.svg')
		self.current_level = Level1
		self.next_level = Level2
		
		# Sprites
		self.player = StickDude(self)
		self.player.hasjetpack = False
		self.player.hasgrapple = False
		self.background = ImageBackground(0, 0, 1000.0, 1000.0, 'level1_background_1.png')
		self.background2 = ImageBackground(0, 0, 1300.0, 1300.0, 'level1_background_2.png', tile_scale = 1.2)
		self.background3 = ImageBackground(0, 0, 1650.0, 1650.0, 'level1_background_4.png', tile_scale = 2)
		self.background4 = ImageBackground(0, 0, 1700.0, 1700.0, 'level1_background_5.png', tile_scale = 2)
		
		# Music
		self.music = media_manager.load_sound('level1_song.ogg')
		self.music.play(-1)
		
		Game.__init__(self, parent)
				
	def tick(self, interval):
		""" Functions called every frame """
		Game.tick(self, interval)
		
		cam = self.camera
		
		# Draw Backgrounds
		glColor4f(1.0, 1.0, 1.0, self.background_alpha)
		left, right, bottom, top = cam.get_coords(self.background.width, self.background.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background.draw()
		left, right, bottom, top = cam.get_coords(self.background2.width, self.background2.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background2.draw()
		left, right, bottom, top = cam.get_coords(self.background3.width, self.background3.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background3.draw()
		left, right, bottom, top = cam.get_coords(self.background4.width, self.background4.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background4.draw()
		
		# Move view to camera
		left, right, bottom, top = cam.get_coords(self.level.width, self.level.height)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)	
		
		# Draw Level
		self.level_pages.draw(cam)
		glColor4f(1.0, 1.0, 1.0, self.player_alpha)
		self.g_actors.draw()
		if self.transition_in:
			glColor4f(1.0, 1.0, 1.0, self.transition_alpha)
			self.g_transition.draw()
		glColor4f(1.0, 1.0, 1.0, 1.0)
		self.g_layer2.draw()
				
		# Zoom Out
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(0.0, self.width, 0.0, self.height)
		
		
class Level2(Game):
	"""The Machine"""
	
	def __init__(self, parent):
		# Level
		self.level = level.Level('level2.svg')
		self.current_level = Level2
		self.next_level = Level3
		
		# Sprites
		self.player = StickDude(self)
		self.player.hasjetpack = False
		self.player.hasgrapple = True
		self.background = ImageBackground(0, 0, 1100.0, 1100.0, 'level2_background_1.png', tile_scale = 1.0)
		self.background2 = ImageBackground(0, 0, 1250.0, 1250.0, 'level2_background_2.png', tile_scale = 1.0)
		self.background3 = ImageBackground(0, 0, 1650.0, 1650.0, 'level2_background_3.png', tile_scale = 1.0)
		
		# Music
		self.music = media_manager.load_sound('level2_song.ogg')
		self.music.play(-1)
		
		Game.__init__(self, parent)
				
	def tick(self, interval):
		""" Functions called every frame """
		Game.tick(self, interval)
		
		cam = self.camera
		
		# Draw Backgrounds
		glColor4f(1.0, 1.0, 1.0, self.background_alpha)
		left, right, bottom, top = cam.get_coords(self.background.width, self.background.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background.draw()
		left, right, bottom, top = cam.get_coords(self.background2.width, self.background2.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background2.draw()
		left, right, bottom, top = cam.get_coords(self.background3.width, self.background3.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background3.draw()
		
		# Move view to camera
		left, right, bottom, top = cam.get_coords(self.level.width, self.level.height)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)	
		
		# Draw Level
		self.level_pages.draw(cam)
		glColor4f(1.0, 1.0, 1.0, self.player_alpha)
		self.g_actors.draw()
		if self.transition_in:
			glColor4f(1.0, 1.0, 1.0, self.transition_alpha)
			self.g_transition.draw()
		glColor4f(1.0, 1.0, 1.0, 1.0)
		self.g_layer2.draw()
				
		# Zoom Out
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(0.0, self.width, 0.0, self.height)
		
		
class Level3(Game):
	"""In the toaster"""
	
	def __init__(self, parent):
		# Level
		self.level = level.Level('level3.svg')
		self.current_level = Level3
		self.next_level = ToastWin
		
		# Sprites
		self.player = StickDude(self)
		self.player.hasjetpack = True
		self.player.hasgrapple = True
		self.background = ImageBackground(0, 0, 1100.0, 1100.0, 'level3_background_1.png', tile_scale = 1.0)
		self.background2 = ImageBackground(0, 0, 1250.0, 1250.0, 'level3_background_2.png', tile_scale = 1.0)
		self.background3 = ImageBackground(0, 0, 1650.0, 1650.0, 'level3_background_3.png', tile_scale = 1.0)
		self.background4 = ImageBackground(0, 0, 1660.0, 1660.0, 'level3_background_4.png', tile_scale = 1.0)
		
		# Music
		self.music = media_manager.load_sound('level3_song.ogg')
		self.music.play(-1)
		
		Game.__init__(self, parent)
				
	def tick(self, interval):
		""" Functions called every frame """
		Game.tick(self, interval)
		
		cam = self.camera
		
		# Draw Backgrounds
		glColor4f(1.0, 1.0, 1.0, self.background_alpha)
		left, right, bottom, top = cam.get_coords(self.background.width, self.background.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background.draw()
		left, right, bottom, top = cam.get_coords(self.background2.width, self.background2.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background2.draw()
		left, right, bottom, top = cam.get_coords(self.background3.width, self.background3.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background3.draw()
		left, right, bottom, top = cam.get_coords(self.background4.width, self.background4.height, False)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		self.background4.draw()
		
		# Move view to camera
		left, right, bottom, top = cam.get_coords(self.level.width, self.level.height)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)	
		
		# Draw Level
		self.level_pages.draw(cam)
		glColor4f(1.0, 1.0, 1.0, self.player_alpha)
		self.g_actors.draw()
		if self.transition_in:
			glColor4f(1.0, 1.0, 1.0, self.transition_alpha)
			self.g_transition.draw()
		glColor4f(1.0, 1.0, 1.0, 1.0)
		self.g_layer2.draw()
				
		# Zoom Out
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(0.0, self.width, 0.0, self.height)
		
		
class ToastWin(GameState):
	
	def __init__(self, parent):
		GameState.__init__(self, parent)
		
		self.current_level = ToastWin
		self.next_level = Credits
		
		# Sprite Groups
		self.g_background = GLSpriteGroup()
		self.g_middle = GLSpriteGroup()
		self.g_toaster_lever = GLSpriteGroup()
		self.g_toaster = GLSpriteGroup()
		self.g_front = GLSpriteGroup()
		
		# Sprites
		background = ColorBackground(0.0, 0.0, 800.0, 600.0, (255, 255, 255))
		toast_x = (self.width - 512.0) / 2
		toast_y = (self.height - 512.0 - 90.0) / 2
		self.toast = ImageBackground(toast_x, toast_y, 512.0, 512.0, 'toast.png')
		self.ninjabot1 = ImageBackground(self.width / 2 - 32, self.height / 2 - 64, 64.0, 128.0, 'ninjabot_jumpup_0.png')
		self.ninjabot2 = ImageBackground(self.width / 2 - 256.0, self.height + 100.0, 
										 512.0, 1024.0, 'ninjabot_splat.png')
		self.toaster = ImageBackground(toast_x, toast_y, 512.0, 512.0, 'toaster.png')
		self.toaster_lever = ImageBackground(self.width / 2 - 260.0, 190.0, 64.0, 64.0, 'toaster_lever.png')
		
		# Add sprites to groups
		self.g_background.add(background)
		self.g_middle.add(self.toast, self.ninjabot1)
		self.g_toaster_lever.add(self.toaster_lever)
		self.g_toaster.add(self.toaster)
		self.g_front.add(self.ninjabot2)
		
		# Setup transition
		self.zoom = 1.99
		self.x = 0.0
		self.y = 0.0
		self.background_alpha = 0.0
		self.middle_alpha = 0.0
		self.toaster_alpha = 0.0
		self.transition_in = True
		self.transition_out = False
		
		# Animation
		self.animation_running = False
		self.wilhelm_played = False
		self.timer = 3000
		
		self.toast_pop = media_manager.load_sound('toaster.wav')
		self.wilhelm = media_manager.load_sound('wilhelm.ogg')
		
	def handle_event(self, event):
		"""Handle events specific to game state"""
		GameState.handle_event(self, event)
		if event.type == KEYDOWN:
			if event.key == K_ESCAPE:
				self.parent.add_game_state(menu.GameMenu(self.parent, self))
		return True
				
	def tick(self, interval):
		""" Functions called every frame """
		GameState.tick(self, interval)
		
		# Transition in
		if self.transition_in:
			if self.toaster_alpha < 1.0:
				self.toaster_alpha += interval / 1000.0
				if self.toaster_alpha > 1.0:
					self.toaster_alpha = 1.0
			else:
				self.middle_alpha = 1.0
			if self.background_alpha < 1.0:
				self.background_alpha += interval / 300.0
				if self.background_alpha > 1.0:
					self.background_alpha = 1.0
			if self.zoom > 1.0:
				self.zoom -= interval / 5000.0
				if self.zoom < 1.0:
					self.zoom = 1.0
					if self.background_alpha == 1.0:
						self.transition_in = False
						self.animation_running = True
						
		# Animation
		if self.animation_running:
			if self.timer > 0:
				self.timer -= interval
				if self.timer <= 0:
					self.timer = 0
					self.toast.vy = 1.5
					self.ninjabot1.vy = 1.0
					self.toaster_lever.vy = 0.7
					self.toast_pop.play()
			elif self.ninjabot2.vy == 0.0:
				self.toast.vy -= interval / 120.0
				self.toast.y += self.toast.vy * interval
				self.ninjabot1.y += self.ninjabot1.vy * interval
				self.toaster_lever.y += self.toaster_lever.vy * interval
				if self.toaster_lever.y > 290.0:
					self.toaster_lever.y = 290.0
				if self.toast.vy < 0.0 and self.toast.y < self.toaster.y + 90:
					self.toast.y = self.toaster.y + 90
					self.toast.vy = 0.0
					if self.ninjabot1.y > self.height + 700:
						self.ninjabot2.vy = -2.0
			else:
				self.ninjabot2.y += self.ninjabot2.vy * interval
				if self.ninjabot2.y < 200.0 and not self.wilhelm_played:
					self.wilhelm.play()
					self.wilhelm_played = True
				if self.ninjabot2.y < -2000.0:
					self.animation_running = False
					# Credits screen needs self passed
					self.parent.add_game_state(self.next_level(self.parent, self))
					# Credits will call transition out
						
		# Transition out
		if self.transition_out:
			self.stop()
					
		self.g_background.draw()
		
		# Zoom
		zoom_width = (self.width * self.zoom - self.width)
		zoom_height = (self.height * self.zoom - self.height)
		left = self.x + zoom_width / 2
		right = left + self.width - zoom_width
		bottom = self.y + zoom_height / 2
		top = bottom + self.height - zoom_height
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		
		glColor4f(1.0, 1.0, 1.0, self.middle_alpha)
		self.g_middle.draw()
		glColor4f(1.0, 1.0, 1.0, self.toaster_alpha)
		self.g_toaster_lever.draw()
		self.g_toaster.draw()
		self.g_front.draw()
		
		glColor4f(1.0, 1.0, 1.0, 1.0)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(0.0, self.width, 0.0, self.height)
		
	def leave_level(self):
		self.animation_running = False
		self.transition_out = True
		

class Credits(GameState):
	
	def __init__(self, parent, toast_win):
		GameState.__init__(self, parent)
		
		self.current_level = Credits
		self.next_level = menu.MainMenu
		self.toast_win = toast_win
		
		align_x = self.width / 2.0
		text_height = 40.0
		align_y = 0.0 - text_height
		
		# Sprite Groups
		self.g_background = GLSpriteGroup()
		self.g_text = GLSpriteGroup()
		
		# Credits
		credits_dict = {
			"Ryan 'Erlandr' Hoffman": ('Programming', 'Sound Effects'),
			"Paul 'III Demon' Good": ('Programming', 'Level Design'),
			"Dusty 'Tresch' Peterson": ('Character Animation', 'Background Artwork', 'Sound Engineering', 'Music Composition'),
                        "Drew 'AmericanPianist' Walker": ('Music Composition', 'Level Design'),
                        "Chris 'PrimeTime' Hettinger": ('Tile Artwork',),
                        "Allie 'Mauricia' MacAlister": ('Animation Cell Finishing',),
                        "Special Thanks To": ("David 'RoboButler' Duke", "Holly 'Metachaos' Hunt", "Dave 'DChamp' Champion", "For helping with level design!")
			}
		
		# Sprites
		background = ColorBackground(0.0, 0.0, 800.0, 600.0, (255, 255, 255))
		for name_, task_list in credits_dict.iteritems():
			self.g_text.add(GLText(name_, align_x, align_y, size=31, 
								   color=(41, 45, 111), halign='middle'))
			align_y -= text_height
			for task in task_list:
				self.g_text.add(GLText(task, align_x, align_y, size=29, 
									   color=(0, 0, 0), halign='middle'))
				align_y -= text_height
			align_y -= text_height
		self.robot_toast = ImageBackground(-112.0, align_y - 200, 1024.0, 256.0, 'logo.png')
		
		# Add sprites to groups
		self.g_background.add(background)
		self.g_text.add(self.robot_toast)
		
		# Setup transition
		self.background_alpha = 0.0
		self.text_alpha = 1.0
		self.transition_in = True
		self.transition_out = False
		self.transition_wait = False
		self.timer = 2000
		
		# Animation
		self.animation_running = True
		self.y = self.height
		
		# Music
		self.music = media_manager.load_sound('end_credits.ogg')
		self.music.play()
		
	def stop(self):
		GameState.stop(self)
		self.music.stop()
		
	def handle_event(self, event):
		"""Handle events specific to game state"""
		GameState.handle_event(self, event)
		if event.type == KEYDOWN:
			if event.key == K_ESCAPE:
				self.parent.add_game_state(menu.GameMenu(self.parent, self))
				return True
				
	def tick(self, interval):
		""" Functions called every frame """
		GameState.tick(self, interval)
		
		# Transition in
		if self.transition_in:
			self.background_alpha += interval / 5000.0
			if self.background_alpha > 0.7:
				self.background_alpha = 0.7
			if self.background_alpha == 0.7:
				self.transition_in = False
						
		# Animation
		if self.animation_running:
			for text in self.g_text:
				text.y += interval / 25.0
			if self.robot_toast.y >= self.height / 2 + 20:
				self.robot_toast = self.height / 2 + 20
				self.animation_running = False
				self.transition_out = True
				self.music.fadeout(1000)
						
		# Transition out
		if self.transition_out:
			self.background_alpha += interval / 500.0
			if self.background_alpha > 1.0:
				self.background_alpha = 1.0
			if self.background_alpha == 1.0:
				self.toast_win.stop()
				self.parent.add_game_state(self.next_level(self.parent))
				self.transition_out = False
				self.transition_wait = True
				
		# Wait for timer then stop
		if self.transition_wait:
			self.timer -= interval
			if self.timer < 1000:
				self.background_alpha -= interval / 500.0
				if self.background_alpha < 0.0:
					self.background_alpha = 0.0
			if self.timer <= 0:
				self.stop()
					
		glColor4f(1.0, 1.0, 1.0, self.background_alpha)
		self.g_background.draw()
		
		glColor4f(1.0, 1.0, 1.0, self.text_alpha)
		self.g_text.draw()
		glColor4f(1.0, 1.0, 1.0, 1.0)

		
	def leave_level(self):
		self.animation_running = False
		self.transition_out = True

