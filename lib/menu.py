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

import gamestate
from gamestate import GameState
from sprites import GLSpriteGroup, ColorBackground, ImageBackground, GLText
from media_manager import MediaManage

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import gluOrtho2D


#------------------------------------------------------------------------------
#   Globals
#------------------------------------------------------------------------------

media_manager = MediaManage()


#------------------------------------------------------------------------------
#   Menu
#------------------------------------------------------------------------------

class MenuLoader(GameState):
	"""Load main menu"""
	
	def __init__(self, parent):
		GameState.__init__(self, parent)
		
		# White background
		self.g_background = GLSpriteGroup()
		background = ColorBackground(0.0, 0.0, 800.0, 600.0, (255, 255, 255))
		self.g_background.add(background)
		
		self.timer = 1500
		self.menu_added = False
		self.background_alpha = 1.0
		
	def tick(self, interval):
		# Add main menu
		if not self.menu_added:
			self.parent.add_game_state(MainMenu(self.parent))
			self.menu_added = True
			
		# Wait for timer then stop
		self.timer -= interval
		if self.timer < 500:
			self.background_alpha -= interval / 500.0
			if self.background_alpha < 0.0:
				self.background_alpha = 0.0
		if self.timer <= 0:
			self.stop()
		
		glColor4f(1.0, 1.0, 1.0, self.background_alpha)
		self.g_background.draw()
		glColor4f(1.0, 1.0, 1.0, 1.0)
		

class Menu(GameState):
	"""Menu Game State"""
	
	def __init__(self, parent):
		GameState.__init__(self, parent)
		pygame.mouse.set_visible(True)
		# Menu Items
		self.menu_items = []
		self.current_menu = 0	
	
	def stop(self):
		GameState.stop(self)
		pygame.mouse.set_visible(False)
		
	def point_in_sprite(self, x1, y1, sprite):
		"""x,y coordinate to rectangle collision"""
		if x1 > sprite.left and x1 < sprite.right:
			if y1 > sprite.bottom and y1 < sprite.top:
				return True
		return False
	
		
class MainMenu(Menu):
	
	def __init__(self, parent):
		Menu.__init__(self, parent)
		center_x = self.width / 2
		center_y = self.height / 2
		# Sprite Groups
		self.g_background = GLSpriteGroup()
		self.g_menu = GLSpriteGroup()
		# Sprites
		background = ColorBackground(0, 0, self.width, self.height, (255, 255, 255))
		robot_toast = ImageBackground(-112.0, center_y + 20, 1024.0, 256.0, 'logo.png')
		robot = ImageBackground(self.width - 350, -95.0, 256.0, 512.0, 'ninjabot_stand_big.png')
		start_game = GLText('Start', center_x, center_y - 10, size=40, halign='middle')
		start_game.action = self.start_game
		quit_ = GLText('Quit', center_x, center_y - 70, size=40, halign='middle')
		quit_.action = self.quit_game
		self.cursor = GLText('>', center_x - (start_game.width / 2) - 10, 
							 start_game.y, size=20, halign='right', font='Vera.ttf')
		# Add Sprites to Groups
		self.g_background.add(background)
		self.g_menu.add(robot_toast, robot, start_game, quit_, self.cursor)
		
		# Menu Items
		self.menu_items = [start_game, quit_]
		self.current_menu = 0
		
		# Setup transition
		self.zoom = 1.0
		self.x = 0.0
		self.y = 0.0
		self.background_alpha = 0.0
		self.menu_alpha = 0.0
		self.transition_in = True
		self.transition_out = False
		
		# Music
		self.music = media_manager.load_sound('title_screen_intro.ogg')
		#self.intro_music = media_manager.load_sound('title_screen_loop.ogg')
		self.music.play()

	def start_game(self):
		self.transition_out = True
		print "Loading level"
		self.parent.add_game_state(gamestate.Level1(self.parent))
		self.music.fadeout(1000)
		
	def quit_game(self):
		self.parent.running = False
		
	def handle_event(self, event):
		"""Handle events specific to game state"""
		Menu.handle_event(self, event)
		center_x = self.width / 2
		menu_items = self.menu_items
		if event.type == KEYDOWN:
			if event.key == K_DOWN:
				self.current_menu += 1
				if self.current_menu > len(menu_items) - 1:
					self.current_menu = 0
				self.cursor.y = menu_items[self.current_menu].y
				self.cursor.x = center_x - (menu_items[self.current_menu].width / 2) - self.cursor.width - 10
			if event.key == K_UP:
				self.current_menu -= 1
				if self.current_menu < 0:
					self.current_menu = len(menu_items) -1
				self.cursor.y = menu_items[self.current_menu].y
				self.cursor.x = center_x - (menu_items[self.current_menu].width / 2) - self.cursor.width - 10
			if event.key == K_RETURN:
				menu_items[self.current_menu].action()
		if event.type == JOYBUTTONDOWN: # CHEAT
			menu_items[self.current_menu].action()
			
		if event.type == MOUSEBUTTONUP:
			posx, posy = pygame.mouse.get_pos()
			posy = self.height - posy
			for stuff in self.menu_items:
				if self.point_in_sprite(posx, posy, stuff):
					stuff.action()
		return True
	
	def tick(self, interval):
		"""Functions called every frame """
		Menu.tick(self, interval)
		posx, posy = pygame.mouse.get_pos()
		posy = self.height - posy
		
		for item in self.menu_items:
			if self.point_in_sprite(posx, posy, item):
				self.current_menu = self.menu_items.index(item)
				self.cursor.y = item.y
				self.cursor.x = (self.width / 2) - (item.width / 2) - self.cursor.width - 10

		if self.transition_in:
			if self.menu_alpha < 1.0:
				self.menu_alpha += interval / 500.0
				if self.menu_alpha >= 1.0:
					self.menu_alpha = 1.0
			elif self.background_alpha < 1.0:
				self.background_alpha += interval / 500.0
				if self.background_alpha >= 1.0:
					self.background_alpha = 1.0
					#self.intro_music.play()
					self.transition_in = False
		if self.transition_out:
			self.zoom -= interval / 5000.0
			if self.zoom < 0.5:
				self.menu_alpha -= interval / 500.0
				if self.menu_alpha < 0.0:
					self.menu_alpha = 0.0
				self.background_alpha -= interval / 500.0
				if self.background_alpha < 0.0:
					self.background_alpha = 0.0
			if self.zoom < 0.002:
				self.stop()
				
		glColor4f(1.0, 1.0, 1.0, self.background_alpha)
		self.g_background.draw()
		
		# Zoom for menu
		zoom_width = (self.width * self.zoom - self.width)
		zoom_height = (self.height * self.zoom - self.height)
		left = self.x + zoom_width / 2
		right = left + self.width - zoom_width
		bottom = self.y + zoom_height / 2
		top = bottom + self.height - zoom_height
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(left, right, bottom, top)
		glColor4f(1.0, 1.0, 1.0, self.menu_alpha)
		self.g_menu.draw()
		
		# Reset view
		glColor4f(1.0, 1.0, 1.0, 1.0)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(0.0, self.width, 0.0, self.height)
		

class GameMenu(Menu):
	
	def __init__(self, parent, level):
		Menu.__init__(self, parent)
		center_x = self.width / 2
		center_y = self.height / 2
		# Sprite Groups
		self.g_background = GLSpriteGroup()
		self.g_menu = GLSpriteGroup()
		# Sprites
		background = ColorBackground(0, 0, self.width, self.height, (255, 255, 255))
		resume_game = GLText('Resume', center_x, center_y + 50, size=40, halign='middle')
		resume_game.action = self.resume_game
		restart = GLText('Restart', center_x, center_y, size=40, halign='middle')
		restart.action = self.restart_level
		quit_ = GLText('Exit', center_x, center_y - 50, size=40, halign='middle')
		quit_.action = self.quit_game
		self.cursor = GLText('>', center_x - (resume_game.width / 2) - 10, 
							 resume_game.y, size=20, halign='right', font='Vera.ttf')
		# Add Sprites to Groups
		self.g_background.add(background)
		self.g_menu.add(resume_game, restart, quit_, self.cursor)
		# Menu Items
		self.menu_items = [resume_game, restart, quit_]
		self.current_menu = 0
		# Base alpha value for all sprites
		self.alpha = 0.0
		self.fade_in = False
		self.fade_out = False
		# Restart Level
		self.restart_level = False
		self.level = level
		
	def start(self):
		Menu.start(self)
		self.parent.pause(self)
		self.fade_in = 0.005
		
	def stop(self):
		Menu.stop(self)
		self.parent.unpause()
		
	def resume_game(self):
		self.fade_out = 0.01
		
	def restart_level(self):
		self.restart_level = True
		self.fade_out = 0.01
		
	def quit_game(self):
		self.parent.running = False
		
	def handle_event(self, event):
		"""Handle events specific to game state"""
		Menu.handle_event(self, event)
		center_x = self.width / 2
		menu_items = self.menu_items
		if event.type == KEYDOWN:
			if event.key == K_ESCAPE:
				self.fade_out = 0.01
			if event.key == K_DOWN:
				self.current_menu += 1
				if self.current_menu > len(menu_items) - 1:
					self.current_menu = 0
				self.cursor.y = menu_items[self.current_menu].y
				self.cursor.x = center_x - (menu_items[self.current_menu].width / 2) - self.cursor.width - 10
			if event.key == K_UP:
				self.current_menu -= 1
				if self.current_menu < 0:
					self.current_menu = len(menu_items) -1
				self.cursor.y = menu_items[self.current_menu].y
				self.cursor.x = center_x - (menu_items[self.current_menu].width / 2) - self.cursor.width - 10
			if event.key == K_RETURN:
				menu_items[self.current_menu].action()
			
		if event.type == MOUSEBUTTONUP:
			posx, posy = pygame.mouse.get_pos()
			posy = self.height - posy
			for stuff in self.menu_items:
				if self.point_in_sprite(posx, posy, stuff):
					stuff.action()
		return True
	
	def tick(self, interval):
		"""Functions called every frame """
		Menu.tick(self, interval)
		posx, posy = pygame.mouse.get_pos()
		posy = self.height - posy
		
		for item in self.menu_items:
			if self.point_in_sprite(posx, posy, item):
				self.current_menu = self.menu_items.index(item)
				self.cursor.y = item.y
				self.cursor.x = (self.width / 2) - (item.width / 2) - self.cursor.width - 10
		
		if self.fade_in:
			self.alpha += self.fade_in * interval
			if self.alpha >= 1.0:
				self.alpha = 1.0
				self.fade_in = False
		if self.fade_out:
			self.alpha -= self.fade_out * interval
			if self.alpha <= 0.0:
				self.alpha = 0.0
				self.fade_out = False
				if self.restart_level:
					self.level.leave_level()
					self.parent.add_game_state(self.level.current_level(self.parent))
				self.stop()
		glColor4f(1.0, 1.0, 1.0, self.alpha * 0.7)
		self.g_background.draw()
		glColor4f(1.0, 1.0, 1.0, self.alpha)
		self.g_menu.draw()
		glColor4f(1.0, 1.0, 1.0, 1.0)
		