from ServerController import ServerController
from ..Deck import *
import time, random

class SetupNewgameServerController(ServerController):
	def init(self):
		self.events = 	[
							(self.SendMessage, tuple(["ADD_CHAT:SERVER:The game has begun!"])),
					   		(self.Wait, tuple([0.5])),
					   		(self.SendMessage, tuple(["ADD_CHAT:SERVER:Shuffling decks..."])),
					   		(self.SendMessage, tuple(["ALERT:remove_deck"])),
							(self.Wait, tuple([0.5])),
							(self.SendMessage, tuple(["ALERT:shuffle_deck"])),
							(self.SetupDecks, tuple()),
							(self.Wait, tuple([0.5])),
							(self.SendMessage, tuple(["ALERT:place_deck"])),
							(self.Wait, tuple([1.0])),
							(self.SendMessage, tuple(["ADD_CHAT:SERVER:Finding the start card..."])),
					   		(self.Wait, tuple([0.5])),
							(self.SendMessage, tuple(["ALERT:draw_card_from_deck"])),
							(self.Wait, tuple([0.5])),
							(self.SetupStartCard, tuple()),
							(self.SendMessage, tuple(["ALERT:add_card_to_table"])),
							(self.Wait, tuple([1.5])),
							(self.SendMessage, tuple(["ADD_CHAT:SERVER:Giving players their starting hands..."])),
							(self.SendMessage, tuple(["ALERT:draw_card_from_deck"])),
							(self.Wait, tuple([0.1])),
							(self.SendMessage, tuple(["ALERT:draw_card_from_deck"])),
							(self.Wait, tuple([0.1])),
							(self.SendMessage, tuple(["ALERT:draw_card_from_deck"])),
							(self.Wait, tuple([0.5])),
							(self.GivePlayersStartHands, tuple()),
							(self.SendMessage, tuple(["ALERT:add_card_to_hand"])),
							(self.Wait, tuple([3.0])),
							(self.SendMessage, tuple(["ADD_CHAT:SERVER:Drawing public goals..."])),
							(self.SendMessage, tuple(["ALERT:draw_card_from_deck"])),
							(self.Wait, tuple([0.4])),
							(self.SendMessage, tuple(["ALERT:draw_card_from_deck"])),
							(self.Wait, tuple([0.4])),
							(self.SendMessage, tuple(["ALERT:draw_card_from_deck"])),
							(self.Wait, tuple([0.75])),
							(self.SendMessage, tuple(["ALERT:add_card_to_table"])),
							(self.DrawPublicGoals, tuple()),
							(self.Wait, tuple([3.0])),
							(self.SendMessage, tuple(["ADD_CHAT:SERVER:Let's see who gets to go first!"])),
							(self.Wait, tuple([2.0])),
							(self.PickFirstPlayer, tuple())
						]

		self.waiting = False
		self.wait_duration = 0
		self.wait_start_time = 0

	def update(self):
		if self.waiting:
			t = time.time()
			if t >= self.wait_duration + self.wait_start_time:
				self.waiting = False

		if not self.waiting:
			if len(self.events) > 0:
				event = self.events.pop(0)
				event[0](event[1])
			else:
				self.gameserver.controller = None

	def SendMessage(self, args):
		message = args[0]
		self.gameserver.server.sendall(message)

	def Wait(self, args):
		self.waiting = True
		self.wait_duration = args[0]
		if SERVER_DEBUG_QUICKSTART:
			self.wait_duration = min(self.wait_duration,0.1)
		self.wait_start_time = time.time()

	def SetupDecks(self, args):
		for card in self.gameserver.master_deck.cards:
			if card.type == "pony": self.gameserver.pony_deck.add_card_to_top(card)
			elif card.type == "ship": self.gameserver.ship_deck.add_card_to_top(card)
			elif card.type == "goal": self.gameserver.goal_deck.add_card_to_top(card)
			else: print "ERROR! Got card of unknown type:",card.type

		self.gameserver.pony_deck.shuffle()
		self.gameserver.ship_deck.shuffle()
		self.gameserver.goal_deck.shuffle()

		self.gameserver.send_decks_all()

	def SetupStartCard(self, args):
		c = None
		for card in self.gameserver.pony_deck.cards:
			if card.power == "startcard":
				c = card
				self.gameserver.pony_deck.remove_card(card)
				break
		if c == None:
			raise RuntimeError("There is no start card!")
		self.gameserver.card_table.pony_cards[1][1] = c
		self.gameserver.send_cardtable_all()

		self.gameserver.send_decks_all()

	def GivePlayersStartHands(self, args):
		for player in self.gameserver.players:
			if not player.is_spectating:
				for i in xrange(4):
					player.hand.add_card_to_top(self.gameserver.pony_deck.draw())
				for i in xrange(3):
					player.hand.add_card_to_top(self.gameserver.ship_deck.draw())
				self.gameserver.send_playerhand(player)

		self.gameserver.send_decks_all()

	def DrawPublicGoals(self, args):
		for i in xrange(3):
			self.gameserver.public_goals.add_card_to_top(self.gameserver.goal_deck.draw())
		self.gameserver.send_public_goals_all()

		self.gameserver.send_decks_all()

	def PickFirstPlayer(self, args):
		#We actually scramble the player list.
		specs = []
		i = len(self.gameserver.players)-1
		while i >= 0:
			if self.gameserver.players[i].is_spectating:
				specs.append(self.gameserver.players.pop(i))
			i -= 1
		random.shuffle(self.gameserver.players)
		self.gameserver.players += specs
		self.gameserver.server.sendall("ADD_CHAT:SERVER:"+self.gameserver.players[0].name+" goes first!")
		self.gameserver.setPlayersTurn(0)


