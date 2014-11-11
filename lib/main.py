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

import sys
from menu import MenuLoader
from gamestate import ToastWin, Level3

# Pygame
try:
	import pygame
except ImportError:
	sys.exit('Pygame was not found')
else:
	from pygame.locals import *

# OpenGL
try:
	from OpenGL.GL import *
	from OpenGL.GLU import gluOrtho2D
	import OpenGL
except ImportError:
	sys.exit('PyOpenGL was not found')


#------------------------------------------------------------------------------
#   Main
#------------------------------------------------------------------------------

class Main:
	"""
	Run main loop
	
	Manage game states
	"""

	def __init__(self):
		"""Initialize base attributes"""
		self.running = False
		# List of GameState objects
		self.active_state = []
		# Window resolution
		self.res_x = 800
		self.res_y = 600
		# Gameplay area
		self.width = 800.0
		self.height = 600.0

	def add_game_state(self, game_state):
		"""Append Game State object to list"""
		self.active_state.append(game_state)
		game_state.start()

	def rem_game_state(self, game_state):
		"""Remove Game State object from list"""
		try:
			self.active_state.remove(game_state)
		except:
			print "Remove gamestate failed: not found in list"
	
	def pause(self, *white_list):
		"""
		Pause gamestates
		
		Set running = False for all gamestates except those passed as arguments
		"""
		for game_state in self.active_state:
			if game_state not in white_list:
				game_state.running = False
				
	def unpause(self, *white_list):
		"""
		Un-Pause gamestates
		
		Set running = True for all gamestates except those passed as arguments
		"""
		for game_state in self.active_state:
			if game_state not in white_list:
				game_state.running = True
		
	def handle_event(self, event):
		"""
        Handle pygame event

        Stop program gracefully if QUIT event is received,
        else pass event to .handle_event() method of primary
        active_state object.
        """
		if event.type == QUIT:
			self.running = False
			return True
		for state in reversed(self.active_state):
			if state.running == True:
				if state.handle_event(event) == True:
					return True

	def tick(self, interval):
		"""Execute tick() method for each active_state object"""
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		for game_state in self.active_state:
			if game_state.running == True:
				game_state.tick(interval)
			else:
				game_state.tick(0)
		pygame.display.flip()
	
	def run(self):
		"""
        Run game

        Initialize pygame, the game window, and the game clock.
        Run main loop until self.running is no longer True.
        Exit program when main loop finishes.
        """
		width = self.width
		height = self.height
		res_x = self.res_x
		res_y = self.res_y
		# Pygame
		if pygame.image.get_extended() == False:
			error_message = "Your build of pygame does not support extended \
						  image formats"
			sys.exit(error_message)
		pygame.init()
		pygame.font.init()
		pygame.mixer.init()
		self.screen = pygame.display.set_mode((res_x, res_y), OPENGL | DOUBLEBUF)
		pygame.display.set_caption('Robot Toast')
		
		# JOYSTIX!!
		self.stick = False
		numstix = pygame.joystick.get_count()
		for s in range(numstix):
			stik = pygame.joystick.Joystick(s)
			stik.init()
			print stik.get_id()
			print stik.get_numaxes()
			if not stik.get_numaxes(): # skip this stick
				pass
			else:
				self.stick = stik
				break

		# OpenGL viewport
		glViewport(0, 0, res_x, res_y)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluOrtho2D(0.0, float(width), 0.0, float(height))
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()

		# OpenGL options
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glShadeModel(GL_SMOOTH)
		glClearColor(0.0, 0.0, 0.0, 0.0)
		glClearDepth(1.0)
		glEnable(GL_DEPTH_TEST)
		glDepthFunc(GL_LEQUAL)
		#OpenGL.error.ErrorChecker.registerChecker(error.ErrorChecker.nullGetError)

		# Clock
		clock = pygame.time.Clock()
		last_tick = this_tick = pygame.time.get_ticks()
		timer = 0
		fps_timer = 0
		self.ticklock = True

		# Initial Game State
		self.add_game_state(MenuLoader(self))
		self.running = True

		while self.running:
			# Do every frame
			if self.ticklock:
				interval = clock.tick(60)
			else:
				interval = clock.tick()
			if interval > 50:
				interval = 50
			timer += interval
			self.tick(interval)
			[self.handle_event(event) for event in pygame.event.get()]
			
			# Print FPS
			fps_timer += interval
			if fps_timer >= 1000:
				#print self.active_state
				print "%2d FPS" % clock.get_fps()
				fps_timer = 0

		pygame.quit()