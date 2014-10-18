import Deck
import netcom
from locals import *
import thread
import time
import math

from ServerControllers.PlayCardServerController import *

from ServerPlayer import Player
import Deck
import CustomDeck
from PickledCard import open_pickledcard
from CardTable import CardTable
from common import *

class GameServer(object):
	def __init__(self, port=DEFAULT_PORT):
		print "= GameServer initializing..."
		self.port = port
		# First we need to load the deck
		print "= Waiting for 'run_main_loop' to be called."
		print
		self.controller = None
		self.server = None

		self.throttled = True
		self.delay = 0.1

		self.players = []

		self.load_custom_deck()

		self.reset()

	def reset(self):
		self.pony_deck = Deck.Deck()
		self.ship_deck = Deck.Deck()
		self.goal_deck = Deck.Deck()
		self.pony_discard = Deck.Deck()
		self.ship_discard = Deck.Deck()
		self.public_goals = Deck.Deck()
		self.card_table = CardTable()
		self.game_started = False

		self.timer_start_amount = 0.0
		self.timer_amount = 0.0
		self.prev_timer_amount = 0.0
		self.timer_start_time = 0.0
		self.timer_running = False

		self.setTimerDuration(float(SERVER_GAMESTART_DELAY))

		self.current_players_turn = None
		for pl in self.players:
			pl.reset()
		if self.server != None:
			self.send_playerlist_all()

	def load_custom_deck(self):
		print "== loading the MasterDeck"
		self.master_deck = Deck.MasterDeck()
		self.custom_deck = CustomDeck.CustomDeck()
		try:
			f = open("your_deck.txt")
		except:
			print("Couldn't find 'your_deck.txt' so we're going to load the default cards only.")
			self.master_deck.load_all_cards()
			return
		instr = f.read()
		f.close()
		print
		print " --- READING CUSTOM DECK INSTRUCTIONS --- "
		print
		self.custom_deck.follow_instructions(instr)
		print
		print " --- DONE --- "
		print
		print "=== loading cards..."
		pc_list = []
		defaults = os.listdir("data/default_cards")
		for card in self.custom_deck.list:
			if card.startswith("R:"):
				pc = open_pickledcard("cards/"+card[2:])
			else:
				if card in defaults:
					pc = open_pickledcard("data/default_cards/"+card)
				else:
					pc = open_pickledcard("cards/"+card)
			pc_list.append(pc)
		self.master_deck.load_all_cards(pc_list)
		print "== MasterDeck loaded."

	def run_main_loop(self):
		# Call this function to get the server running.
		print "= 'run_main_loop' called..."
		print "== starting server now..."
		self.server = netcom.Server(netcom.gethostname(), self.port)
		print "== the server should now operational."
		thread.start_new_thread(self._run(), tuple([]))

	def _run(self):
		# This is the main loop for the entire GameServer class.
		self.running = True
		while self.running:
			self._update()
			self._read_messages()
			self._check_player_status()
			if self.throttled:
				time.sleep(self.delay)

	def _update(self):
		t = time.time()

		if self.timer_running:
			dif = t - self.timer_start_time
			self.timer_amount = self.timer_start_amount - dif
		dif = floorint(self.prev_timer_amount) - floorint(self.timer_amount)
		if dif != 0:
			self.send_timer_all()
			if self.timer_running:
				for t in xrange(dif):
					self.triggerTimerTick(floorint(self.prev_timer_amount-1)-t)
				if self.timer_amount <= 0:
					self.timer_running = False
					self.triggerTimerDone()

		self.prev_timer_amount = float(self.timer_amount)

		if self.controller != None:
			self.controller.update()

	def _read_messages(self):
		for key in self.server.clients.keys():
			message = None
			player = None
			for pl in self.players:
				if pl.address == key:
					player = pl
					break
			try:
				if len(self.server.received_messages[key]) > 0:
					message = self.server.received_messages[key].pop(0)
			except:
				print "= FAILED TO POP AT KEY:",key

			if message != None:
				if message == PING_MESSAGE:
					self.server.sendto(key,PONG_MESSAGE)
				elif message == PONG_MESSAGE:
					pass
				elif message.startswith("CONNECT:"):
					#We get the clients name now and add them to the game.
					#TODO: Kick the client if their name sucks or if the game's already started
					if False:
						pass
					else:
						data = message[len("CONNECT:"):]
						data = data.split(":")
						if len(data) < 2:
							self.server.kick(key,"You seem to be running an older version. Please go updated.")
						else:
							player_key = data[0]
							name = data[1]
							if player == None:
								for pl in self.players:
									if pl.name == name and pl.player_key == player_key:
										player = pl
										break
							if player != None:
								#reconnect player
								if not player.is_connected:
									self.server.sendto(key,"CONNECTED:"+name)
									self.server.sendall("ADD_CHAT:SERVER:"+"Player '"+name+"' has reconnected.")
									player.is_connected = True
									player.address = key
									if self.controller != None:
										self.controller.triggerRejoinPlayer(player)
									print "=Player '"+name+"'", key, "has rejoined the game."
								else:
									#we kick this one, since the player is already connected.
									self.server.kick(key,"This player is already connected.")
							else:
								if not self.game_started:
									#connect new player
									self.server.sendto(key,"CONNECTED:"+name)
									self.server.sendall("ADD_CHAT:SERVER:"+"Player '"+name+"' has connected.")
									self.players.append(Player(key, name, player_key))
									if self.controller != None:
										self.controller.triggerNewPlayer(self.players[-1])
									print "=Player '"+name+"'", key, "has joined the game."
								else:
									self.server.kick(key,"The game's already started. Please come back later.")
							self.send_playerlist_all()
							self.check_ready()
				elif message.startswith("CHAT:"):
					if not player:
						name = "???"
					else:
						name = player.name
					chat = message[len("CHAT:"):]
					self.server.sendall("ADD_CHAT:PLAYER:"+name+": "+chat)
				elif message == "REQUEST_DECK":
					s = ""
					i = 0
					while i < len(self.custom_deck.list):
						card = self.custom_deck.list[i]
						if card.startswith("R:"):
							card = card[2:]
						s += card
						i += 1
						if i < len(self.custom_deck.list):
							s += ","
					self.server.sendto(player.address,"DECK:"+s)
				elif message.startswith("REQUEST_CARDFILE:"):
					index = int(message[len("REQUEST_CARDFILE:"):])
					data = "CARDFILE:"+str(index)+":"+self.master_deck.pc_cards[index]
					#print "SENDING CARD: "+data[:100]
					self.server.sendto(player.address,data)
				elif message.startswith("REQUEST_CARDFILE_ATTRIBUTES:"):
					index = int(message[len("REQUEST_CARDFILE_ATTRIBUTES:"):])
					data = "CARDFILE_ATTRIBUTES:"+str(index)+":"+self.master_deck.cards[index].attributes
					#print "SENDING CARD ATTRIBUTES: "+data[:100]
					self.server.sendto(player.address,data)
				elif message == "DONE_LOADING":
					player.is_loaded = True
					self.server.sendto(player.address, "CLIENT_READY")
					self.server.sendall("ADD_CHAT:SERVER:"+"Player '"+player.name+"' has joined.")
					self.send_playerlist_all()
					self.check_ready()
					if self.game_started:
						self.give_fullupdate(player)
				elif message == "READY":
					if not self.game_started:
						#toggle this player's "is_ready" variable
						t = time.time()
						if t - player.last_toggled_ready < 3:
							self.server.sendto(player.address,"ADD_CHAT:SERVER:You're doing that too often.")
						else:
							player.is_ready = not player.is_ready
							player.last_toggled_ready = t
							if player.is_ready:
								self.server.sendall("ADD_CHAT:SERVER:"+"Player '"+player.name+"' is ready.")
								self.server.sendall("ALERT:player_ready")
							else:
								self.server.sendall("ADD_CHAT:SERVER:"+"Player '"+player.name+"' is NOT ready.")
								self.server.sendall("ALERT:player_not_ready")
							self.send_playerlist_all()
							self.check_ready()
					else:
						self.server.sendto(player.address,"ADD_CHAT:SERVER:The game's already started!")
				elif message == "END_TURN":
					#we end this player's turn.
					if self.game_started:
						if self.players.index(player) == self.current_players_turn:
							#We check if the player has the correct number of cards in their hand.
							if len(player.hand.cards) < MIN_CARDS_IN_HAND:
								self.server.sendto(player.address, "ADD_CHAT:SERVER:You need to draw up to "+str(MIN_CARDS_IN_HAND)+" before you can end your turn.")
							else:
								self.server.sendto(player.address, "ADD_CHAT:SERVER:"+player.name+" has ended their turn.")
								self.nextPlayersTurn()
						else:
							self.server.sendto(player.address,"ADD_CHAT:SERVER:It's not your turn, dummy!")
					else:
						self.server.sendto(player.address,"ADD_CHAT:SERVER:The game hasn't started yet...")
				elif message.startswith("PLAY_CARD:"):
					#we play the selected card.
					if self.game_started:
						if self.players.index(player) == self.current_players_turn:
							#we check if this card is in the player's hand.
							try:
								i = int(message[len("PLAY_CARD:"):])
								works = True
							except:
								works = False
							if works:
								match = False
								for card in player.hand.cards:
									if self.master_deck.cards.index(card) == i:
										match = True
										break
								if match:
									#we attempt to play this card.
									self.controller = PlayCardServerController(self)
									self.controller.selected_card = card
									self.server.sendall("ALERT:draw_card_from_hand")
									self.server.sendto(player.address,"ADD_CHAT:SERVER: Click on the grid where you want to play this card.")
								else:
									self.server.sendto(player.address,"ADD_CHAT:SERVER: Whatthe-...that card's not even in your hand!")
						else:
							self.server.sendto(player.address,"ADD_CHAT:SERVER:It's not your turn, you can't play a card right now!")
					else:
						self.server.sendto(player.address,"ADD_CHAT:SERVER:You can't play a card, the game hasn't started...")
				elif message.startswith("DRAW_1:"):
					s = message[len("DRAW_1:"):]
					if s == "pony":
						if len(self.pony_deck.cards) > 0:
							self.server.sendall("ADD_CHAT:SERVER:"+player.name+" drew a Pony card.")
							self.server.sendall("ALERT:draw_card_from_deck")
							self.server.sendall("ALERT:add_card_to_hand")
							card = self.pony_deck.draw()
							player.hand.add_card_to_top(card)
							self.send_decks_all()
							self.send_playerhand(player)
						else:
							self.server.sendto(player.address,"ADD_CHAT:SERVER:There are no Pony cards to draw...")
					elif s == "ship":
						if len(self.ship_deck.cards) > 0:
							self.server.sendall("ADD_CHAT:SERVER:"+player.name+" drew a Ship card.")
							self.server.sendall("ALERT:draw_card_from_deck")
							self.server.sendall("ALERT:add_card_to_hand")
							card = self.ship_deck.draw()
							player.hand.add_card_to_top(card)
							self.send_decks_all()
							self.send_playerhand(player)
						else:
							self.server.sendto(player.address,"ADD_CHAT:SERVER:There are no Ship cards to draw...")
					else:
						self.server.sendto(player.address,"ADD_CHAT:SERVER:You can't draw that type of card!")
				else:
					if self.controller != None:
						attempt = self.controller.read_message(message, player)
						if not attempt:
							print "ERROR: Received unknown message: "+message[:100]
					else:
						print "ERROR: Received unknown message and no controller: "+message[:100]

	def _check_player_status(self):
		# This function is to check that players are still connected, otherwise it kicks them after no response.
		t = time.time()
		i = len(self.players)-1
		while i >= 0:
			player = self.players[i]
			pa = player.address
			pn = player.name
			if player.is_connected:
				kick_em = False
				# First we check if the player is even still in the server's client listing.
				if pa in self.server.clients:
					#Next we check when we last received a message from that client.
					try:
						lgm = self.server.client_last_got_message[pa]
						dif = t - lgm
						if dif >= PING_FREQUENCY:
							if not player.is_pinged:
								player.is_pinged = True
								self.server.sendto(pa,PING_MESSAGE)
							else:
								# This means the player was already sent a 'ping', and we're waiting for a 'pong'
								if dif >= PING_FREQUENCY + TIMEOUT_TIME:
									#This player has timed out, so we must kick them.
									print "= Client '"+pn+"' has timed-out from '"+pa+"'"
									kick_em = True
						else:
							# This player is likely still connected.
							player.is_pinged = False
					except:
						print "= FAILED TO CHECK ON AND/OR PING PLAYER '"+pn+"' AT '"+pa+"'"
				else:
					print "= Client '"+pn+"' has disconnected from '"+pa+"'"
					kick_em = True
				if kick_em:
					print "= Player '"+pn+"' has been kicked."
					self.server.kick(pa)
					player.is_connected = False
					player.is_ready = False
					player.time_of_disconnect = time.time()
					self.server.sendall("ADD_CHAT:SERVER:"+"Player '"+player.name+"' has disconnected.")
					if self.controller != None:
						self.controller.triggerPlayerDisconnect(player)
					self.send_playerlist_all()
					self.check_ready()
			else:
				if not self.game_started or t - player.time_of_disconnect >= 60:
					#TODO: Discard player's hand
					#TODO: Check if the game needs to reset
					#TODO: Check if it was this player's turn. If it was, change whose turn it is
					self.server.sendall("ADD_CHAT:SERVER:"+"Player '"+player.name+"' has been removed from the game.")
					del self.players[i]
					self.send_playerlist_all()
					self.check_ready()
			i -= 1

	def check_ready(self):
		if not self.game_started:
			number_ready = 0
			for player in self.players:
				if player.is_connected and player.is_ready:
					number_ready += 1

			ready = number_ready >= MIN_PLAYERS and number_ready == len(self.players)

			if ready and not self.timer_running:
				self.runTimer()
				self.server.sendall("ADD_CHAT:SERVER: The game will start in...")
			elif not ready and self.timer_running:
				self.stopTimer()
				self.server.sendall("ADD_CHAT:SERVER: ...Aborted.")

	def setPlayersTurn(self, i):
		if i != self.current_players_turn:
			self.current_players_turn = i
			self.server.sendto(self.players[i].address, "YOUR_TURN")
			self.server.sendall("ADD_CHAT:SERVER: It's now "+self.players[i].name+"'s turn.")
			self.send_playerlist_all()
			self.stopTimer()
			self.setTimerDuration(SERVER_TURN_START_DURATION)
			self.runTimer()

	def nextPlayersTurn(self):
		i = self.current_players_turn + 1
		i %= len(self.players)
		self.setPlayersTurn(i)

	def get_decks_trasmit(self):
		s = "DECKS:"
		s += str(len(self.pony_deck.cards))+","
		s += str(len(self.ship_deck.cards))+","
		s += str(len(self.goal_deck.cards))+","
		s += str(len(self.pony_discard.cards))+","
		s += str(len(self.ship_discard.cards))+":"
		if len(self.pony_discard.cards) > 0:
			s += str(self.master_deck.cards.index(self.pony_discard.cards[-1])) + ","
		else:
			s += "N,"
		if len(self.ship_discard.cards) > 0:
			s += str(self.master_deck.cards.index(self.ship_discard.cards[-1]))
		else:
			s += "N"
		return s

	#Timer Stuff
	def setTimerDuration(self, amount):
		self.timer_start_amount = amount

	def runTimer(self):
		#Resets and runs the timer.
		if not self.timer_running:
			self.timer_running = True
			self.timer_start_time = time.time()
			self.timer_amount = float(self.timer_start_amount)

	def stopTimer(self):
		#Stops and resets the timer.
		if self.timer_running:
			self.timer_running = False
			self.timer_amount = float(self.timer_start_amount)

	def pauseTimer(self):
		if self.timer_running:
			self.timer_running = False

	def resumeTimer(self):
		if not self.timer_running:
			self.timer_running = True
			self.timer_start_time = time.time() - (self.timer_start_time - self.timer_amount)

	#Triggers
	def triggerTimerTick(self, amount):
		#called when the timer ticks 1 second down.
		if self.controller != None:
			self.controller.triggerTimerTick(amount)

		if not self.game_started:
			self.server.sendall("ADD_CHAT:SERVER:..."+str(amount)+"...")
		else:
			if floorint(self.timer_amount) == SERVER_TURN_ALERT_DURATION:
				self.server.sendto(self.players[self.current_players_turn].address, "TURN_ALMOST_OVER")

	def triggerTimerDone(self):
		#called when the timer runs out of time.
		if self.controller != None:
			self.controller.triggerTimerDone()
			self.controller.cleanup()
			self.controller = None

		if not self.game_started:
			#This must be the game start timer, so we start the game.
			self.game_started = True
			self.send_playerlist_all()
			import libs.ServerControllers.SetupNewgameServerController as SetupNewgameServerController
			self.controller = SetupNewgameServerController.SetupNewgameServerController(self)
		else:
			#This means a player ran out of time for their turn.
			self.server.sendall("ADD_CHAT:SERVER: "+self.players[self.current_players_turn].name+" ran out of time.")
			self.nextPlayersTurn()

	#Send Commands
	def send_playerlist_all(self):
		parts = []
		i = 0
		while i < len(self.players):
			player = self.players[i]
			part = ""
			if i == self.current_players_turn:
				part += "CT:"
			if not player.is_connected:
				part += "DC:"
			if not self.game_started:
				if player.is_ready:
					part += "R:"
				else:
					part += "NR:"
			if not player.is_loaded:
				part += "L:"
			part += player.name
			parts.append(part)
			i += 1
		i = 0
		while i < len(self.players):
			s = "PLAYERLIST:"
			j = 0
			while j < len(self.players):
				part = parts[j]
				if j == i:
					part = "YOU:"+str(part)
				s += part
				if j < len(self.players) - 1:
					s += ","
				j += 1
			self.server.sendto(self.players[i].address, s)
			i += 1

	def send_public_goals_all(self):
		self.server.sendall("PUBLICGOALS:"+self.public_goals.get_transmit(self.master_deck))

	def send_public_goals(self, player):
		self.server.sendto(player.address, "PUBLICGOALS:"+self.public_goals.get_transmit(self.master_deck))

	def send_playerhand(self, player):
		self.server.sendto(player.address, "PLAYERHAND:"+player.hand.get_transmit(self.master_deck))

	def send_cardtable_player(self, player):
		self.server.sendto(player.address, "CARDTABLE:"+self.card_table.get_transmit(self.master_deck))

	def send_cardtable_all(self):
		self.server.sendall("CARDTABLE:"+self.card_table.get_transmit(self.master_deck))

	def send_decks_all(self):
		self.server.sendall(self.get_decks_trasmit())

	def send_decks_player(self, player):
		self.server.sendto(player.address, self.get_decks_trasmit())

	def send_timer_all(self):
		self.server.sendall("TIMER:"+str(floorint(self.timer_amount)))

	def send_timer_player(self, player):
		self.server.sendto(player.address, "TIMER:"+str(floorint(self.timer_amount)))

	def give_fullupdate(self, player):
		self.send_playerhand(player)
		self.send_public_goals(player)
		self.send_cardtable_player(player)
		self.send_timer_player(player)
		self.send_decks_player(player)
