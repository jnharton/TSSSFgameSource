import os

#VERSION INFO
CLIENT_VERSION = "a9"
SERVER_VERSION = "a4"

# GAME CONSTANTS
CARD_SIZE = (394, 544)
CARD_ART_SIZE = (385, 284)
MIN_PLAYERS = 1
MAX_PLAYERS = 10
MIN_CARDS_IN_HAND = 7

# SOCKET CONSTANTS
PING_MESSAGE = "PING"  # message sent when a server/client needs to know that a client/server is still connected.
PONG_MESSAGE = "PONG"  # response sent back to the server/client by the client/server after they get a PING_MESSAGE.
TIMEOUT_TIME = 10.0  # seconds before a player is dropped for timing-out
PING_FREQUENCY = 2.0  # ping the server/client every X seconds to ensure there's still a connection.
BUFFERSIZE = 2048  # the size of the buffer used in the sockets
MESSAGE_DELAY = 0.025  # the delay between sent messages to prevent buffer overflows
ESCAPE_CHARACTER = str(chr(3)) + str(chr(4)) + str(chr(5)) + str(chr(6))
DEBUG_LOCALHOST = False  # This is for testing on one machine.
if not DEBUG_LOCALHOST:
	DEFAULT_PORT = 27015
else:
	DEFAULT_PORT = 10000

# FILE CONSTANTS
try:
	# TODO: Make this work on all platforms.
	APPDATA_LOCATION = os.getenv('APPDATA').replace("\\", "/")
	DATA_LOCATION = APPDATA_LOCATION + "/TSSSF"
except:
	APPDATA_LOCATION = None
	DATA_LOCATION = None

# TEXT ALIGNMENT CONSTANTS
ALIGN_TOPLEFT = 0
ALIGN_MIDDLELEFT = 1
ALIGN_MIDDLE = 2

# GUI CONSTANTS
LAYOUT_FLOW = 0
LAYOUT_VERTICAL = 1
LAYOUT_HORIZONTAL = 2
LAYOUT_SPLIT = 3

SCROLLBAR_VERTICAL = 0
SCROLLBAR_HORIZONTAL = 1
SCROLLBAR_WIDTH = 20
SCROLLBAR_BAR_MINSIZE = 15

DEBUG_MOUSEBUTTONPRESS_TRACE = False
DEBUG_FOCUS_TRACE = False

#MISC.
PRINTABLE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~`!@#$%^&*()_+-={}|:\"<>?[]\\;',./ "
PLAYERNAME_MAX_LENGTH = 12

#CLIENT-SIDE
CLIENT_PRECACHE_DECK = True
CLIENT_PRERENDER_DECK = True
CLIENT_RERENDER_DECK_IN_BACKGROUND = True
CLIENT_DEBUG_PRINT_STREAM = False
CLIENT_BERRYTUBE_DRINKCALLS = False

#SERVER-SIDE
SERVER_MAX_GAMES_BEFORE_SHUTDOWN = 15  #This is how many games a server will play before automatically closing down. Anything less than 1 is never.
SERVER_GAMESTART_DELAY = 15
SERVER_DEBUG_QUICKSTART = False
SERVER_TURN_MAX_DURATION = 60 * 10.0  #This is the length of a player's turn once they've played their first card.
SERVER_TURN_START_DURATION = 60 * 3.0  #This is the length of a player's before they've played their first card.
SERVER_TURN_ALERT_DURATION = 60 * 1.0  #When the timer reaches this amount, the server will alert the player that their turn is almost over.
SERVER_HARDKICK_DELAY = 60 * 3.0 #This is how long it'll take before a player is removed from a game after disconnecting.