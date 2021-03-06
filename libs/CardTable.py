def xcoords_to_index(xcoords, card_type):
	x,y = xcoords
	index = (x/3,y/3)
	if card_type == "pony":
		return ("pony",index)
	elif card_type == "ship":
		pos = (index[0]*3+1,index[1]*3+1)
		dif = (x-pos[0],y-pos[1])
		index = (pos[0]/3,pos[1]/3)
		if dif[0]%2 != dif[1]%2:
			if dif[0]%2 == 1:
				#This is a h_ship position.
				index = (index[0]-1,index[1]-1)
				if dif[0] > 0:
					index = (index[0]+1,index[1])
				return ("h ship",index)
			else:
				#This is a v_ship position.
				index = (index[0]-1,index[1]-1)
				if dif[1] > 0:
					index = (index[0],index[1]+1)
				return ("v ship",index)
		else:
			print "ERROR! This is not a legal position: ",index, pos, dif
	else:
		print "ERROR! This is not a legal card type!"
	return (None,(0,0))


class XY_Range(object):
	def __init__(self):
		self.is_empty = True

	def extend(self, pos, size=(0, 0)):
		if self.is_empty:
			self.min_x = pos[0]
			self.min_y = pos[1]
			self.max_x = pos[0] + size[0]
			self.max_y = pos[1] + size[1]
		else:
			self.min_x = min(pos[0], self.min_x)
			self.min_y = min(pos[1], self.min_y)
			self.max_x = max(pos[0] + size[0], self.max_x)
			self.max_y = max(pos[1] + size[1], self.max_y)
		self.is_empty = False


class CardTable(object):
	def __init__(self, size=(3, 3)):
		self.size = size

		self.pony_cards = []
		for y in xrange(size[1]):
			row = []
			for x in xrange(size[0]):
				row.append(None)
			self.pony_cards.append(row)

		self.v_ship_cards = []
		for y in xrange(size[1] - 1):
			row = []
			for x in xrange(size[0]):
				row.append(None)
			self.v_ship_cards.append(row)

		self.h_ship_cards = []
		for y in xrange(size[1]):
			row = []
			for x in xrange(size[0] - 1):
				row.append(None)
			self.h_ship_cards.append(row)

	def refactor(self):
		# this function resizes and realligns everything
		xy = XY_Range()

		for y in xrange(self.size[1]):
			for x in xrange(self.size[0]):
				if self.pony_cards[y][x] != None:
					xy.extend((x - 1, y - 1), (1, 1))

		for y in xrange(self.size[1] - 1):
			for x in xrange(self.size[0]):
				if self.v_ship_cards[y][x] != None:
					xy.extend((x, y), (0, 0))

		for y in xrange(self.size[1]):
			for x in xrange(self.size[0] - 1):
				if self.h_ship_cards[y][x] != None:
					xy.extend((x, y), (0, 0))

		#now that we have our ranges, we need to make a new table
		if xy.is_empty:
			ct = CardTable()
			self.pony_cards = ct.pony_cards
			self.v_ship_cards = ct.v_ship_cards
			self.h_ship_cards = ct.h_ship_cards
		else:
			new_size = (max(xy.max_x - xy.min_x + 2, 3), max(xy.max_y - xy.min_y + 2, 3))
			ct = CardTable(new_size)

			for y in xrange(self.size[1]):
				for x in xrange(self.size[0]):
					if ct.check_if_legal_index((x - xy.min_x, y - xy.min_y), "pony"):
						ct.pony_cards[y - xy.min_y][x - xy.min_x] = self.pony_cards[y][x]

			for y in xrange(self.size[1] - 1):
				for x in xrange(self.size[0]):
					if ct.check_if_legal_index((x - xy.min_x, y - xy.min_y), "v ship"):
						ct.v_ship_cards[y - xy.min_y][x - xy.min_x] = self.v_ship_cards[y][x]

			for y in xrange(self.size[1]):
				for x in xrange(self.size[0] - 1):
					if ct.check_if_legal_index((x - xy.min_x, y - xy.min_y), "h ship"):
						ct.h_ship_cards[y - xy.min_y][x - xy.min_x] = self.h_ship_cards[y][x]

			self.pony_cards = ct.pony_cards
			self.v_ship_cards = ct.v_ship_cards
			self.h_ship_cards = ct.h_ship_cards

			self.size = new_size
		return xy

	def check_if_legal_index(self, index, type, replacable_cards=[]):
		if type == "pony":
			return index[0] >= 0 and index[0] <= self.size[0] - 1 and index[1] >= 0 and index[1] <= self.size[1] - 1 and (self.pony_cards[index[1]][index[0]] in [None] + list(replacable_cards))
		elif type == "v ship":
			test1 = index[0] >= 0 and index[0] < self.size[0] - 2 and index[1] >= 0 and index[1] < self.size[1] - 1
			if test1:
				test2 = (self.v_ship_cards[index[1]][index[0]] in [None] + list(replacable_cards))
				return test2
			return False
		elif type == "h ship":
			test1 = index[0] >= 0 and index[0] < self.size[0] - 1 and index[1] >= 0 and index[1] < self.size[1] - 2
			if test1:
				test2 = (self.h_ship_cards[index[1]][index[0]] in [None] + list(replacable_cards))
				return test2
			return False
		raise TypeError("This is not a legal type: " + type)

	def get_transmit(self, master_deck):
		s = ""
		#the first part is the size of the table
		s += str(self.size[0]) + "," + str(self.size[1]) + ":"
		#the second part is the list of pony cards on the grid
		first = True
		for row in self.pony_cards:
			for card in row:
				if first:
					first = False
				else:
					s += ","
				if card == None:
					s += "_"
				else:
					s += str(master_deck.cards.index(card))
		s += ":"
		#the third part is the ship cards on the vertical axis
		first = True
		for row in self.v_ship_cards:
			for card in row:
				if first:
					first = False
				else:
					s += ","
				if card == None:
					s += "_"
				else:
					s += str(master_deck.cards.index(card))
		s += ":"
		#the forth part is the ship cards on the horizontal axis
		first = True
		for row in self.h_ship_cards:
			for card in row:
				if first:
					first = False
				else:
					s += ","
				if card == None:
					s += "_"
				else:
					s += str(master_deck.cards.index(card))
		return s

	def parse_message(self, master_deck, message):
		#first we must break apart the message into it's sections.
		sections = message.split(":")
		if len(sections) != 4: raise RuntimeError("Received a bad table.")
		#next we must parse the first section to determine the size of the grid.
		s = sections[0]
		parts = s.split(",")
		if len(parts) != 2: raise RuntimeError("Received a bad table.")
		size = (int(parts[0]),int(parts[1]))
		#we must change our size to this size.
		self.__init__(size)
		#next we must parse the pony card list
		parts = sections[1].split(",")
		for y in xrange(self.size[1]):
			for x in xrange(self.size[0]):
				s = parts.pop(0)
				if s != "_":
					self.pony_cards[y][x] = master_deck.cards[int(s)]
		#next we must parse the vertical ship card list
		parts = sections[2].split(",")
		for y in xrange(self.size[1] - 1):
			for x in xrange(self.size[0]):
				s = parts.pop(0)
				if s != "_":
					self.v_ship_cards[y][x] = master_deck.cards[int(s)]
		#finally we must parse the horizontal ship card list
		parts = sections[3].split(",")
		for y in xrange(self.size[1]):
			for x in xrange(self.size[0] - 1):
				s = parts.pop(0)
				if s != "_":
					self.h_ship_cards[y][x] = master_deck.cards[int(s)]

