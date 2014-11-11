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

from os import path
import pygame
from pygame import image, mixer, font
from OpenGL.GL import *
from xml.dom import minidom


#------------------------------------------------------------------------------
#   Media Manager
#------------------------------------------------------------------------------

class MediaManage:
	
	def __init__(self):
		self.base_dir = "data"
		self.textures = {}
		self.sounds = {}
		self.fonts = {}
		self.default_image = pygame.Surface((1, 1))
		self.default_image.fill((255, 0, 255))
	
	def load_image(self, name, sub_dir='images'):
		"""Load image from file, return dimensions"""
		try:
			proper_sub_dir = ""
			for dir in sub_dir.replace('\\', '/').split('/'):
				proper_sub_dir = path.join(proper_sub_dir, dir)
			fqpn = path.join(self.base_dir, proper_sub_dir, name)
			image_obj = image.load(fqpn).convert_alpha()
			return image_obj
		except:
			print "Error occurred loading %s from %s" % \
				  (name, fqpn)
			return self.default_image
			
	def save_texture(self, name, image_obj):
		"""Add pygame surface to video memory"""
		self.textures[name] = glGenTextures(1)
		
		texture_data = image.tostring(image_obj, "RGBA", 1)
		glBindTexture(GL_TEXTURE_2D, self.textures[name])
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_obj.get_width(),
					 image_obj.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, 
					 texture_data);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

		return self.textures[name]
	
	def load_texture(self, name, image_obj=None, sub_dir='images'):
		"""
		Load texture into video memory
		Return GL texture index
		"""
		try:
			return self.textures[name]
		except KeyError:
			if image_obj is None:
				image_obj = self.load_image(name, sub_dir)
			return self.save_texture(name, image_obj)
	
	def clear_textures(self):
		self.textures = {}
		
	def load_sound(self, name):
		"""Load Sound at 40% volume by default"""
		try:
			return self.sounds[name]
		except KeyError:
			try:
				fqpn = path.join(self.base_dir, 'sounds', name)
				sound_obj = mixer.Sound(fqpn)
				sound_obj.set_volume(0.4)
				self.sounds[name] = sound_obj
				return sound_obj
			except:
				print "Error occurred loading %s from %s" % \
					  (name, fqpn)
				raise SystemExit
	
	def clear_sounds(self):
		self.sounds = {}
		
	def load_font(self, name, size):
		font_name = "%s_%s" % (name, size)
		try:
			return self.fonts[font_name]
		except KeyError:
			try:
				fqpn = path.join(self.base_dir, 'fonts', name)
				font_obj = font.Font(fqpn, size)
				self.fonts[font_name] = font_obj
				return font_obj
			except:
				print "Error occurred loading %s from %s" % \
					  (name, fqpn)
				raise SystemExit
			
	def clear_fonts(self):
		self.fonts = {}
		
	def load_xml(self, xml_file):
		"""Load XML file, return, don't keep in media manager"""
		fqpn = path.join('data', 'levels', xml_file)
		try:
			xml_doc = minidom.parse(fqpn)
			return xml_doc
		except:
			print "Error occurred loading %s from %s" % \
				  (xml_file, fqpn)
			raise SystemExit
