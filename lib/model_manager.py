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

from pygame import image
from OpenGL.GL import *


#------------------------------------------------------------------------------
#   Model Manager
#------------------------------------------------------------------------------

class ModelManage:

	def __init__(self):
		self.models = {}
		
	def untextured_quad(self, name, width, height, tex_coords=None):
		model_name = "%s-%s-%s" % (name, width, height)
		try:
			return self.models[model_name]
		except KeyError:
			if tex_coords is None:
				tex_coords = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
			gl_list = glGenLists(1)
			glNewList(gl_list, GL_COMPILE)
			glBegin(GL_QUADS)
			glTexCoord2f(tex_coords[0][0], tex_coords[0][1])
			glVertex3f(0.0, 0.0, 0.0)
			glTexCoord2f(tex_coords[1][0], tex_coords[1][1])
			glVertex3f(width, 0.0, 0.0)
			glTexCoord2f(tex_coords[2][0], tex_coords[2][1])
			glVertex3f(width,  height, 0.0)
			glTexCoord2f(tex_coords[3][0], tex_coords[3][1])
			glVertex3f(0.0,  height, 0.0)
			glEnd()
			glEndList()

			self.models[model_name] = gl_list
			return gl_list
	
	def textured_quad(self, texture, width, height, tex_coords=None):
		model_name = "%s-%s-%s" % (texture, width, height)
		try:
			return self.models[model_name]
		except KeyError:
			if tex_coords is None:
				tex_coords = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
			gl_list = glGenLists(1)
			glNewList(gl_list, GL_COMPILE)
			glBindTexture(GL_TEXTURE_2D, texture)
			glBegin(GL_QUADS)
			glTexCoord2f(tex_coords[0][0], tex_coords[0][1])
			glVertex3f(0.0, 0.0, 0.0)
			glTexCoord2f(tex_coords[1][0], tex_coords[1][1])
			glVertex3f(width, 0.0, 0.0)
			glTexCoord2f(tex_coords[2][0], tex_coords[2][1])
			glVertex3f(width,  height, 0.0)
			glTexCoord2f(tex_coords[3][0], tex_coords[3][1])
			glVertex3f(0.0,  height, 0.0)
			glEnd()
			glEndList()

			self.models[model_name] = gl_list
			return gl_list
		
	def tiled_quads(self, name, tile_list):
		"""
		Return GL display model for a glBindTexture object
		
		tile_list is in the format [(x, y, width, height, texture), ...]
		these display lists should all be unique, so don't save to self.models
		"""
		if len(tile_list) < 1:
			return False
		tex_coords = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
		
		gl_list = glGenLists(1)
		glNewList(gl_list, GL_COMPILE)
		for tile in tile_list:
			x = float(tile[0])
			y = float(tile[1])
			width = float(tile[2])
			height = float(tile[3])
			texture = tile[4]
			
			glPushMatrix()
			glTranslate(x, y, 0.0)
			glBindTexture(GL_TEXTURE_2D, texture)
			glBegin(GL_QUADS)
			glTexCoord2f(tex_coords[0][0], tex_coords[0][1])
			glVertex3f(0.0, 0.0, 0.0)
			glTexCoord2f(tex_coords[1][0], tex_coords[1][1])
			glVertex3f(width, 0.0, 0.0)
			glTexCoord2f(tex_coords[2][0], tex_coords[2][1])
			glVertex3f(width,  height, 0.0)
			glTexCoord2f(tex_coords[3][0], tex_coords[3][1])
			glVertex3f(0.0,  height, 0.0)
			glEnd()
			glPopMatrix()
		glEndList()

		return gl_list
