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
import math
from sprites import *
from model_manager import ModelManage
from media_manager import MediaManage


#------------------------------------------------------------------------------
#   Globals
#------------------------------------------------------------------------------

media_manage = MediaManage()
model_manage = ModelManage()


#------------------------------------------------------------------------------
#   Level
#------------------------------------------------------------------------------

class Tile(BaseEntity):
	
	def __init__(self, grid_x, grid_y, tile_size):
		BaseEntity.__init__(self)
		# Coordinate location
		self.x = float(grid_x * tile_size)
		self.y = float(grid_y * tile_size)
		self.width = tile_size
		self.height = tile_size
		# Location in collision grid
		self.grid_x = grid_x
		self.grid_y = grid_y
		# Properties
		self.properties = {}
		
	def add_property(self, property, value):
		if property != "":
			self.properties[property] = value
				
	def has_property(self, property):
		return property in self.properties
	
	
class Level(BaseEntity):
	
	def __init__(self, level_file):
		BaseEntity.__init__(self)
		self.tile_size = 32
		self.page_size = 512
		self.name = level_file
		self.collision_map = None
		
		self.xml_doc = media_manage.load_xml(level_file)
		self.layers = self.xml_doc.getElementsByTagName('g')
		
		# Get level dimensions
		for layer in self.layers:
			if layer.attributes['inkscape:label'].value == "LEVEL_BOUNDS":
				xml_rect = layer.getElementsByTagName('rect')[0]
				break
		self.width = round(float(xml_rect.attributes['width'].value))
		self.height = round(float(xml_rect.attributes['height'].value))
		
		# Load collision map
		self.collision_map = self.load_collision_map()
			
	def load_collision_map(self):
		#
		# Collision Map
		#
		
		# Create 2d array
		collision_map = []
		for x in range(int(math.ceil(self.width / self.tile_size))):
			collision_map_y = []
			for y in range(int(math.ceil(self.height / self.tile_size))):
				collision_map_y.append(Tile(x, y, self.tile_size))
			collision_map.append(collision_map_y)
		
		collision_rects = []
		for layer in self.layers:
			try:
				if layer.attributes['inkscape:label'].value == "COLLISION":
					collision_rects.extend(layer.getElementsByTagName('rect'))
				elif layer.attributes['inkscape:label'].value == "SPECIAL":
					collision_rects.extend(layer.getElementsByTagName('rect'))
			except KeyError:
				pass
		
		for rect in collision_rects:
			# Pixel coordinates
			width = int(round(float(rect.attributes['width'].value)))
			height = int(round(float(rect.attributes['height'].value)))
			x = int(round(float(rect.attributes['x'].value)))
			y = self.height - int(round(float(rect.attributes['y'].value))) - height
			
			# Ignore out of bounds tiles
			if x < 0 or x > self.width or y < 0 or y > self.height:
				#print "Collision rect out of bounds - x: %s, y: %s" % (x, y)
				continue
			
			# Collision map coordinates
			grid_width = width / self.tile_size
			grid_height = height / self.tile_size
			grid_x = int(x / self.tile_size)
			grid_y = int(y / self.tile_size)
			
			# rect properties
			try:
				property = rect.attributes['property'].value
				value = rect.attributes['value'].value
			except:
				print "Collision rect missing property or value"
				property = ""
				value = ""
				
			# Add tiles to collision map
			for tile_x in range(grid_x, grid_x + grid_width):
				for tile_y in range(grid_y, grid_y + grid_height):
					try:
						collision_map[tile_x][tile_y].add_property(property, value)
					except:
						print "Error adding to collision map: ", grid_x, grid_y
		
		return collision_map
	
	def load_collision_as_sprites(self):
		#
		# Level Model
		#
		
		# Create page grid to assemble display tiles into
		page_grid = []
		page_group_data = []
		for x in range(int(math.ceil(self.width / self.page_size))):
			page_grid_y = []
			page_group_y = []
			for y in range(int(math.ceil(self.height / self.page_size))):
				page_grid_y.append([])
				page_group_y.append(None)
			page_grid.append(page_grid_y)
			page_group_data.append(page_group_y)
		
		# Iterate through all tiles
		for layer in self.layers:
			try:
				if layer.attributes['inkscape:label'].value == "COLLISION":
					rect_list = layer.getElementsByTagName('rect')
					break
			except KeyError:
				pass
			
		texture = media_manage.load_texture('thistiledoesntexist.png')
		
		for rect in rect_list:
			rect_width = int(rect.attributes['width'].value)
			rect_height = int(rect.attributes['height'].value)
			rect_x = int(round(float(rect.attributes['x'].value)))
			rect_y = self.height - int(round(float(rect.attributes['y'].value))) - rect_height
			
			# Collision map coordinates
			grid_width = rect_width / self.tile_size
			grid_height = rect_height / self.tile_size
			grid_x = int(rect_x / self.tile_size)
			grid_y = int(rect_y / self.tile_size)
			
			# Add tiles to collision map
			for tile_x in range(grid_x, grid_x + grid_width):
				for tile_y in range(grid_y, grid_y + grid_height):
					x = tile_x * self.tile_size
					y = tile_y * self.tile_size
					
					# Ignore out of bounds tiles
					if x < 0 or x > self.width or y < 0 or y > self.height:
						#print "Tile out of bounds - x: %s, y: %s" % (x, y)
						continue
					
					page_grid_x = int(x / self.page_size)
					page_grid_y = int(y / self.page_size)
					x -= self.page_size * page_grid_x
					y -= self.page_size * page_grid_y
					try:
						page_grid[page_grid_x][page_grid_y].append((x, y, 32.0, 32.0, texture))
					except IndexError:
						#print "Tile outside of page grid - x: %s, y: %s" \
						#	  % (page_grid_x, page_grid_y)
						pass
		
		# Create level models
		x = 0
		for data_x in page_grid:
			y = 0
			for tile_data in data_x:
				model_name = "%s_%s_%s" % (self.name, x, y)
				gl_model = model_manage.tiled_quads(model_name, tile_data)
				if gl_model is False:
					y += 1
					continue
				page_x = self.page_size * x
				page_y = self.page_size * y
				page_sprite = TilePage(page_x, page_y, self.page_size, self.page_size, gl_model)
				page_group_data[x][y] = page_sprite
				y += 1
			x += 1
		
		level_pages = LevelPages(page_group_data)
		return level_pages
	
	def load_level_sprites(self):
		#
		# Level Model
		#
		
		# Create page grid to assemble display tiles into
		page_grid = []
		page_group_data = []
		for x in range(int(math.ceil(self.width / self.page_size))):
			page_grid_y = []
			page_group_y = []
			for y in range(int(math.ceil(self.height / self.page_size))):
				page_grid_y.append([])
				page_group_y.append(None)
			page_grid.append(page_grid_y)
			page_group_data.append(page_group_y)
		
		# Iterate through all tiles
		for layer in self.layers:
			try:
				if layer.attributes['inkscape:label'].value == "TILE1":
					tile_list = layer.getElementsByTagName('image')
					break
			except KeyError:
				pass
		
		for tile in tile_list:
			imageparts = tile.attributes['xlink:href'].value.split('\\')
			image = ''
			for part in imageparts:
				image = path.join(image, part)
			sub_dir = 'levels'
			texture = media_manage.load_texture(image, sub_dir=sub_dir)
			
			width = int(tile.attributes['width'].value)
			height = int(tile.attributes['height'].value)
			x = int(round(float(tile.attributes['x'].value)))
			y = self.height - int(round(float(tile.attributes['y'].value))) - height
			
			# Ignore out of bounds tiles
			if x < 0 or x > self.width or y < 0 or y > self.height:
				#print "Tile out of bounds - x: %s, y: %s" % (x, y)
				continue
	
			page_grid_x = int(x / self.page_size)
			page_grid_y = int(y / self.page_size)
			x -= self.page_size * page_grid_x
			y -= self.page_size * page_grid_y
			try:
				page_grid[page_grid_x][page_grid_y].append((x, y, width, height, texture))
			except IndexError:
				#print "Tile outside of page grid - x: %s, y: %s" \
				#	  % (page_grid_x, page_grid_y)
				pass
		
		# Create level models
		x = 0
		for data_x in page_grid:
			y = 0
			for tile_data in data_x:
				model_name = "%s_%s_%s" % (self.name, x, y)
				gl_model = model_manage.tiled_quads(model_name, tile_data)
				if gl_model is False:
					y += 1
					continue
				page_x = self.page_size * x
				page_y = self.page_size * y
				page_sprite = TilePage(page_x, page_y, self.page_size, self.page_size, gl_model)
				page_group_data[x][y] = page_sprite
				y += 1
			x += 1
		level_pages = LevelPages(page_group_data)
		return level_pages
	
	def load_entities(self, entity_name):
		#
		# Sprites and Entities
		#
		
		entity_objects = {"PLAYERSTART": PlayerStart}
		
		for layer in self.layers:
			try:
				if layer.attributes['inkscape:label'].value == "SPRITES":
					entity_elements = layer.getElementsByTagName('image')
					break
			except:
				pass
		
		entities = {}
		for entity in entity_elements:
			try:
				name = entity.attributes['name'].value
				value = entity.attributes['value'].value
			except:
				print "Entity load failure: element missing attribute"
				continue
			if name == entity_name:
				width = int(entity.attributes['width'].value)
				height = int(entity.attributes['height'].value)
				x = int(round(float(entity.attributes['x'].value)))
				y = self.height - int(round(float(entity.attributes['y'].value))) - height
				
				# Ignore out of bounds tiles
				if x < 0 or x > self.width or y < 0 or y > self.height:
					print "Entity out of bounds - x: %s, y: %s" % (x, y)
					continue
				
				entities[value] = entity_objects[name](x, y, value)
		
		return entities
			
			
	def point_collide(self, x, y):
		tile_size = self.tile_size
		grid_x = int(x / tile_size)
		grid_y = int(y / tile_size)
		try:
			return self.collision_map[grid_x][grid_y]
		except IndexError:
			return False
		
	def tile_collide(self, sprite):
		tile_size = self.tile_size
		tiles = []
		properties = []
		grid_x1 = int(sprite.left / tile_size)
		grid_x2 = int((sprite.right - 0.0001) / tile_size)
		grid_y1 = int(sprite.bottom / tile_size)
		grid_y2 = int((sprite.top - 0.0001) / tile_size)
		for x in range(grid_x1, grid_x2 + 1):
			for y in range(grid_y1, grid_y2 + 1):
				try:
					tile = self.collision_map[x][y]
				except IndexError:
					pass
				else:
					tiles.append(tile)
		return tiles
