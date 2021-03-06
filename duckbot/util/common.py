# Last Updated: 2.3.0
# Python imports
import re
import random
# Project imports
from util.bidict import bidict

# Util constants
RTM_READ_DELAY = 1
USER_REGEX = "U[A-Z0-9]{8}"
LABEL_REGEX = "\[:LABEL:(:.+:)+\]"
EMOJI_REGEX = ":.+?:"
#{{{ - Exit codes
EXIT_CODES = {
         "INVALID_BOT_ID"     : 10
        ,"RTM_CONNECT_FAILED" : 11
        ,"RTM_BAD_CONNECTION" : 12
        ,"RTM_GENERIC_ERROR"  : 20
        ,"RTM_TIMEOUT_ERROR"  : 21
        ,"MALFORMED_USER_ID"  : 30
        }
#}}}
#{{{ - Emoji rolls
EMOJI_ROLLS={
         ":ONE:"        : 1
        ,":TWO:"        : 2
        ,":THREE:"      : 3
        ,":FOUR:"       : 4
        ,":FIVE:"       : 5
        ,":SIX:"        : 6
        ,":SEVEN:"      : 7
        ,":EIGHT:"      : 8
        ,":NINE:"       : 9
        ,":KEYCAP_TEN:" : 10
        ,":100:"        : 100
        ,":HERB:"       : 420
        }
#}}}
#{{{ - Commands
COMMANDS = bidict({
    'HI'        :  1,
    'UPDATE'    :  2,
    'HELP'      :  3,
    'ROLL'      :  4,
    'COIN'      :  5,
    'EIGHTBALL' :  6,
    'FACTOID'   :  7,
    'PICKIT'    :  8,
    'JOIN'      :  9,
    'CHECKBUX'  : 10,
    'BET'       : 11,
    'PULL'      : 12,
    'CHECKPOOL' : 13,
})
COMMANDS_ALT = {
    'HELLO'      : 1, 'KWEH'       : 1,
    '?'          : 3, ':QUESTION:' : 3,
    ':GAME_DIE:' : 4,
    ':8BALL:'    : 6, '8BALL'      : 6,
}
#}}}
#{{{ - Games
GAMES = {
    'COIN' : 1,
    'DICE' : 2,
}
#}}}
#{{{ - Eightball Responses
EIGHTBALL_RESPONSES = [
     "It is certain"
    ,"It is decidedly so"
    ,"Without a doubt"
    ,"Yes, definitely"
    ,"You may rely on it"
    ,"As I see it, yes"
    ,"Most likely"
    ,"Outlook good"
    ,"Yes"
    ,"Signs point to yes"
    ,"Reply hazy, try again"
    ,"Ask again later"
    ,"Better not tell you now"
    ,"Cannot predict now"
    ,"Concentrate and ask again"
    ,"Don't count on it"
    ,"My reply is no"
    ,"My sources say no"
    ,"Outlook not so good"
    ,"Very doubtful"
    ]
#}}}
#{{{ - Channel labels
LABELS = {
     'DUCKBOT' : ':DUCKBOT:'
    ,'GAMBLE'  : ':SLOT_MACHINE:'
}
#}}}

# Util timers
LOG_TIME        = 1800 # 30 minutes
REGEN_TIME      = 300  #  5 minutes
SAVE_STATE_TIME = 3600 # 60 minutes

# Slackclient, Logger instance
# debug and permanent bank flag
global sc, logger, debug, bank_file

# Send message to designated channel, and notify user if present
# Params: channel - channel id to send message to
#         message - string message to send
#         user    - user id to notify, not required
# Return: None
def sendMessage(channel, message, user = None):
#{{{
    # Prepend user notification if specified
    if user:
        message = "<@" + user + "> " + message
    sc.rtm_send_message(channel, message)
#}}}

# Search for a user id in a string
# Params: id_str - string to search for id
# Return: user id if found, None otherwise
def matchUserId(id_str):
#{{{
    matches = re.search(USER_REGEX,id_str)
    return matches.group(0) if matches else None
#}}}

# Obtain bot id and workspace channels
# Params: sc        - slackclient instance to make api calls
#         bot_token - connection token for the bot
# Return: bot user id and channel dict
def getBotInfo(bot_token):
#{{{
    bot_id = sc.api_call("auth.test")["user_id"]
    channels = getChannelData(bot_token)
    return bot_id, channels
#}}}

# Request channel list and build channel map
# Params: sc        - slackclient instance to make api calls
#         bot_token - connection token for the bot
# Return: dict of channel ids to channel data
def getChannelData(bot_token):
#{{{
    channels = {}
    response = sc.api_call("conversations.list")
    sc.server.parse_channel_data(response["channels"])
    for channel in response["channels"]:
        channels[channel["id"]] = channel
        channels[channel["id"]]["labels"] = parseLabels(channel["purpose"]["value"])
    return channels
#}}}

# Make changes to channels list based on event data
# Params: channels - dict of channels to update
#         event    - event to update from
# Return: updated channel dict
def updateChannels(channels, event):
#{{{
    channel = event.channel
    if event.subtype == 'channel_purpose':
        channels[channel]["purpose"]["value"] = event.text
    elif event.subtype == 'channel_joined':
        if channel not in channels:
            channels[channel] = event.channel_data
    return channels
#}}}

# Split text into a list of labels
# Params: text - string to split up
# Return: list of labels
def parseLabels(text):
#{{{
    labels = []
    text = "".join(text.split()).upper()
    match = re.search(LABEL_REGEX, text, flags=re.IGNORECASE)
    if match:
        text = match.group(1)
        match = re.match(EMOJI_REGEX, text)
        while match:
            labels.append(match.group(0))
            text = text[match.span(0)[1]:]
            match = re.match(EMOJI_REGEX, text)
    return labels
#}}}

# Rolls randomly with the parameters given and returns numbers in a list
# Params: die_size - number of sides on the dice rolling
#         die_num  - number of times to roll the dice
# Return: list of rolls
def doRolls(die_size, die_num = 1):
#{{{
    rolls = []
    for i in range(die_num):
        rolls.append(random.randint(1,die_size))
    return rolls
#}}}
