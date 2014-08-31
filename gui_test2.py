import pygame
from pygame.locals import *

pygame.init()

import numpy

import math, random, time

from libs.GUI import *


class TestElement(Element):
	def triggerMouseHover(self, mouse_pos):
		self.set_bg_color((255, 255, 0))

	def triggerMouseOut(self, mouse_pos):
		self.set_bg_color((127, 127, 0))

	def triggerMousePressed(self, mouse_pos, button):
		self.set_bg_color((0, 255, 0))

	def triggerMouseRelease(self, mouse_pos, button):
		self.set_bg_color((255, 0, 0))


class Main(object):
	def __init__(self):
		self.screen_size = (854, 480)
		self.screen = pygame.display.set_mode(self.screen_size, RESIZABLE)

		self.framerate = 60
		self.clock = pygame.time.Clock()

		self.stills = []
		self.still_freq = 1 / 10.0
		self.last_still = time.time() - self.still_freq

		self.reset()
		self.run()

	def reset(self):
		self.controller = None  # Controllers are used to control the application while something is being taken care of.

		# SETS UP THE GUI
		self.element_level = 0

		self.updated_elements = []
		self.elements_to_pack = {}

		self.needs_to_pack = False
		self.main_element = Element(self, self, (0, 0), self.screen_size, always_count_hover=True)
		self.focus = None

		for i in xrange(10):
			element = TestElement(self, self.main_element, None, ("20%", "20%"), (127, 0, 0))
			element.padding = [10, 10, 10, 10]

		self.manage_pack_requests()

	def _setup_for_pack(self):
		# THIS SHOULD NOT BE CALLED UNLESS YOU KNOW WHAT YOU'RE DOING!!
		if self.needs_to_pack == False:
			self.needs_to_pack = True
			level_name = str(self.element_level)
			if level_name not in self.elements_to_pack:
				level = []
				self.elements_to_pack[level_name] = level
			else:
				level = self.elements_to_pack[level_name]
			level.append(self)

	def manage_pack_requests(self):
		# managed elements needing to be packed
		while len(self.elements_to_pack) > 0:
			#first we find the highest level needed to be packed
			keys = self.elements_to_pack.keys()
			highest = int(keys[0])
			for key in keys[1:]:
				highest = min(highest, int(key))
			#next, we make each element in that level pack
			elements_to_pack = self.elements_to_pack.pop(str(highest))
			for element in elements_to_pack:
				element.pack()

	def update(self):
		for e in self.events:
			if e.type == MOUSEMOTION:
				self.main_element.update_for_mouse_move(e.pos)
			elif e.type == MOUSEBUTTONDOWN:
				self.main_element.update_for_mouse_button_press(e.pos, e.button)
			elif e.type == MOUSEBUTTONUP:
				self.main_element.update_for_mouse_button_release(e.pos, e.button)

			elif e.type == KEYDOWN:
				if self.focus != None:
					self.focus.update_for_keydown(e.key)
			elif e.type == KEYUP:
				if self.focus != None:
					self.focus.update_for_keyup(e.key)

			elif e.type == VIDEORESIZE:
				self.screen_size = e.size
				self.screen = pygame.display.set_mode(self.screen_size, RESIZABLE)
				self.main_element.flag_for_rerender()
				self.main_element.flag_for_pack()

		for element in self.updated_elements:
			element.update()

		if self.controller != None:
			self.controller.update()

	def move(self):
		if self.controller != None:
			self.controller.move()

	def pack(self):
		if self.needs_to_pack:
			self.needs_to_pack = False

			new_pos = (0, 0)
			new_size = self.screen_size
			redo = False
			if new_pos != self.main_element.pos:
				redo = True
				self.main_element.pos = new_pos
			if new_size != self.main_element.size:
				redo = True
				self.main_element.size = new_size
				self.main_element._setup_for_pack()
			if redo:
				self.main_element.update_rect()
				self.main_element.flag_for_rerender()

	def render(self):
		self.main_element.render()

		if self.controller != None:
			self.controller.render()

		pygame.display.flip()

		"""
		if self.time > self.last_still+self.still_freq:
			self.last_still = float(self.time)
			copy = self.screen.copy()
			temp = pygame.Surface((10,10))
			temp.fill((255,255,255))
			temp.blit(copy,(5-self.mouse_pos[0],5-self.mouse_pos[1]),special_flags = BLEND_RGB_SUB)
			copy.blit(temp,(self.mouse_pos[0]-5,self.mouse_pos[1]-5))
			self.stills.append(copy)
		"""

	def run(self):
		self.running = True
		while self.running:
			self.time = time.time()
			self.keys = list(pygame.key.get_pressed())
			self.mouse_pos = pygame.mouse.get_pos()
			self.mouse_button = pygame.mouse.get_pressed()
			self.events = pygame.event.get()

			self.update()
			self.manage_pack_requests()
			self.move()
			self.manage_pack_requests()
			self.render()

			for e in self.events:
				if e.type == QUIT or e.type == KEYDOWN and e.key == K_ESCAPE:
					self.running = False

			self.clock.tick(self.framerate)

		for i in xrange(len(self.stills)):
			pygame.image.save(self.stills[i], "stills/" + str(len(self.stills) - i) + ".bmp")

		pygame.quit()


main = Main()