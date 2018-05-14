# Project imports
import util
from util import DiagMessage
# Event handler imports
from eventHandlers import MessageHandler
from eventHandlers import BotHandler
from eventHandlers import Event

# Duckbot class delegates event handlers and keeps track of time
class Duckbot:

    # Constructor for the bot
    # Params: bot_id       - bot user id, used to detect mentions
    #         bot_channels - dict containing channel ids to channel data
    #         debug        - bool to display debug messages or not
    # Return: Duckbot instance
    def __init__(self, bot_id, bot_channels, debug = False):
    #{{{
        # Param fields
        self.id = bot_id
        self.channels = bot_channels
        self.debug = debug

        self.logger = util.logger
        self.bots = {}
        self.ticks = 0
        self.cooldown_g = 0

        # Create main event handlers
        self.msg_handler = MessageHandler(bot_id, bot_channels)
        self.bot_handler = BotHandler()
    #}}}

    # Handles incoming events, calling event specific handlers as needed
    # Params: event_p - incoming event to process
    # Return: 0 - everything processed successfully
    #         1 - an error was found
    #         2 - bot needs to update
    def handleEvent(self, event_p):
    #{{{
#         print(event_p)
        # Create standardized event
        event = Event(event_p)

        # No event type, get out
        if event.type == None:
            return 0

        # Message event, pass to message handler
        elif event.type == "message":
        #{{{
            # Display user and their message
            if event.text:
                self.logger.log(DiagMessage(event.user,event.text))
            response = self.msg_handler.act(event)

            # Send message if one was returned
            if response:
                util.sendMessage(event.channel, response, event.user)
                return 0
            # None response signals an update needed
            elif response == None:
                util.sendMessage(event.channel,
                    "Shutting down for update. Kweh! :duckbot:")
                return 2
            # Otherwise do nothing
            else:
                return 0
        #}}}

        # Bot message event
        elif event.type == "bot_message":
        #{{{
            bot_added = self.bot_handler.checkBotId(event.user)
            if self.debug:
                if bot_added:
                    self.logger.log(DiagMessage("BH ADDED ",
                        "Bot id added to bot hander"))
                else:
                    self.logger.log(DiagMessage("BH STATIC",
                        "Bot id not added to handler"))
            # Do something sassy with the bot
            if not self.cooldown_g:
                self.cooldown_g = 120
                messages = self.bot_handler.act(event)
                for msg in messages:
                    util.sendMessage(msg[0], msg[1], msg[2])
            return 0
        #}}}

        # Update event, respond based on the event subtype
        elif event.type == "update":
        #{{{
            # channel_purpose and channel_joined require channel list update
            if (event.subtype == "channel_purpose" or
                event.subtype == "channel_joined"):
                self._channelListUpdate(event)
            return 0
        #}}}

        # Unhandled event type
        else:
            # Don't do anything right now
            return 0
    #}}}

    # Handle tick based bot functions
    # Params: None
    # Return: None
    def tick(self):
    #{{{
        # Tick function is called roughly every second, so the tick count rolls
        # over about every hour. Roll over point can be changed if time needs to
        # be tracked longer than an hour at a time.
        self.ticks = (self.ticks + 1) % 3600
        # Flush the buffer every hour or so if there aren't enough messages
        if self.ticks % self.logger.LOG_TIME == 0:
            self.logger.log(DiagMessage("FLUSH    ",
                "Auto flushing buffer", flush=True))
        # Tick down the global cooldown
        if self.cooldown_g:
            self.cooldown_g -= 1
    #}}}

    # Make updates to channel lists
    # Params: event - Event containing data to update with
    # Return: None
    def _channelListUpdate(self, event):
    #{{{
        # Make change to internal channel list
        self.channels = util.updateChannels(self.channels, event)
        # Update gambler channel list
        event.channel = self.channels[event.channel]
        labels = util.parseLabels(event.channel["purpose"]["value"])
        gamble_handler = self.msg_handler.gamble_handler
        result = gamble_handler.checkChannel(event.channel["id"], labels)
        # Print debug message if desired
        if self.debug:
            if result == 1:
                self.logger.log(DiagMessage("GC INSERT",event.channel["name"]))
            elif result == -1:
                self.logger.log(DiagMessage("GC REMOVE",event.channel["name"]))
            elif not result:
                self.logger.log(DiagMessage("GC STATIC",
                    "No change to gamble channels made"))
    #}}}
