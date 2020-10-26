from my_globals import sqlitecursor, sqliteconnection
from my_globals import DB, tech
import os
import discord
import time
import sys
import random
import math

guild_name = 'borderline innovations'
client = discord.Client()

@client.event
async def on_ready():
    guild = discord.utils.find(lambda g: g.name == guild_name, client.guilds)
    print(f'{client.user} has connected to Discord!')
    print(f'{guild.name}(id: {guild.id})')

    for member in guild.members: # does'nt work, suposed to print all members
        print(f'{member} -- ({member.name})')

@client.event
async def on_message(message):
    """
    event trigger, all messages are processed
    except for the ones that bot self prints
    """
    if message.author == client.user:
        return

    else:
        bot = DiscordBot(message.content)
        if bot.finalmessage != None:
            await message.channel.send(bot.finalmessage)

def beginning_of_launch():
    sqlitecursor.execute('select * from settings where id is 1')
    data = sqlitecursor.fetchone()
    if data == None:
        query, values = tech.empty_insert_query('settings')
        values[DB.Settings.discord_token] = input('DISCORD TOKEN: ')
        with sqliteconnection:
            sqlitecursor.execute(query, values)

class DiscordBot:
    def __init__(self, message):
        self.daysback = 90
        self.message = message.lower()

        self.printlist = []
        self.priceprint = []
        self.candidates = {}
        self.freshest_price = None
        self.daysback_price = None
        self.finalmessage = None

        self.study_message_magic_cards()

        if self.candidates != {}:
            self.get_best_card()
            self.get_price()
            # if card has been viewed within x time, it is rejected 
            if self.best_candidate[DB.Cards.time_limit] == None or time.time() - self.best_candidate[DB.Cards.time_limit] > 84600:
                with sqliteconnection:
                    sqlitecursor.execute('update cards set time_limit = (?) where id = (?)', (math.floor(time.time()), self.best_candidate[0],))

                self.freshest_price = list(self.freshest_price)
                self.daysback_price = list(self.daysback_price)

                cycle = [self.freshest_price, self.daysback_price]
                for i in cycle: # None -> N/A
                    if i != None:
                        for count in range(len(i)):
                            if i[count] == None:
                                i[count] = 'N/A'

                if len(self.candidates[self.best_candidate[DB.Cards.name]]) > 1:
                    self.printlist.append(
                        f'From {len(self.candidates[self.best_candidate[DB.Cards.name]])} different versions I choose -> https://scryfall.com/card/{self.best_candidate[DB.Cards.scryfall_id]}')
                else:
                    self.printlist.append(f'https://scryfall.com/card/{self.best_candidate[DB.Cards.scryfall_id]}')

                if self.best_candidate[DB.Cards.text] != None:
                    self.printlist.append(f'{self.best_candidate[DB.Cards.text]}')
                else:
                    if self.best_candidate[DB.Cards.flavor_text] != None:
                        self.printlist.append(f'Flavortext: {self.best_candidate[DB.Cards.flavor_text]}')

                if self.best_candidate[DB.Cards.power] != None and self.best_candidate[DB.Cards.toughness] != None:
                    self.printlist.append(f'{self.best_candidate[DB.Cards.power]}/{self.best_candidate[DB.Cards.toughness]}')

                if self.freshest_price != None:
                    self.priceprint.append(
                        f'[LATEST PRICE] EU REG: {self.freshest_price[DB.Prices.eu_reg]} EU FOIL: {self.freshest_price[DB.Prices.eu_foil]}')
                    if self.daysback_price != None:
                        self.priceprint.append(
                            f'[{self.daysback} DAYS BACK] EU REG: {self.daysback_price[DB.Prices.eu_reg]} EU FOIL: {self.daysback_price[DB.Prices.eu_foil]}')
                
                self.finalmessage = '\n'.join(self.printlist[:1]) + '\n```' +  '\n'.join(self.printlist[1:]) + '```' # Discord box ``` + ```
                if self.priceprint != None:
                    self.finalmessage += '```' + '\n'.join(self.priceprint) + '```'
        else:
            if self.finalmessage == None:
                self.fetch_joke() # if card isnt found, try jokes
            if self.finalmessage == None:
                self.commands()

    def commands(self):
        if self.message.find('!timelimit') != -1:
            with sqliteconnection:
                sqlitecursor.execute('update cards set time_limit = (?) where time_limit is not NULL', (None,))

    def get_price(self):
        """
        :self.daysback_price:
        :self.freshest_price:

        self.freshest_price is the most recent price
        self.daysback_price is the one that exceeds 
        the self.daysback integer
        """
        sqlitecursor.execute('select * from prices where uuid = (?)', (self.best_candidate[DB.Cards.uuid],))
        data = sqlitecursor.fetchall()
        if len(data) > 0:
            self.freshest_price = data[-1]
            self.daysback_price = None
            if len(data) > 1:
                for i in range(len(data)-2,-1,-1):
                    if self.freshest_price[DB.Prices.unix_time] - data[i][DB.Prices.unix_time] >= 84600 * self.daysback:
                        self.daysback_price = data[i]
                        break
                if self.daysback_price == None:
                    self.daysback_price = data[0]
            return self.freshest_price, self.daysback_price

    def study_message_magic_cards(self):
        """
        :self.candidates:

        takes all cards that can be found inside each text
        and narrows them down to one card with greatest length
        """
        sqlitecursor.execute('select * from cards')
        data = sqlitecursor.fetchall()
        for eachcard in data:
            if eachcard[DB.Cards.supertypes] == None or eachcard[DB.Cards.supertypes].find('Basic') == -1:
                if self.message.find(eachcard[DB.Cards.name].lower()) != -1:
                    try:
                        self.candidates[eachcard[DB.Cards.name]].append(eachcard)
                    except KeyError:
                        self.candidates.update({eachcard[DB.Cards.name]:[eachcard]})
        if len(self.candidates) > 1:
            save = sorted(self.candidates.keys(), reverse=True, key=lambda s: len(self.candidates.get(s)))
            self.candidates = {save[0]:self.candidates[save[0]]}
        
    def get_best_card(self):
        """
        :self.best_candidate:
        if just one card, no speciall action and
        if name of the set is mentioned within the
        message, that card is favored.
        else:
            most recent dated card from either 
            expansion or core is set as: 
            self.best_candidate
        """
        for _, j in self.candidates.items():
            if len(j) == 1:
                self.best_candidate = j[0]
                return
        
        # set name mention
        for _, cardlist in self.candidates.items(): 
            for eachcard in cardlist:
                setdata = tech.set_details(eachcard[DB.Cards.set_code])
                if self.message.find(setdata[DB.Sets.name].lower()) != -1:
                    self.best_candidate = eachcard
                    return

        # gathers all cards
        choices = {}
        for _, cardlist in self.candidates.items(): 
            for eachcard in cardlist:
                setdata = tech.set_details(eachcard[DB.Cards.set_code])
                try:
                    choices[setdata[DB.Sets.release_date]].append(eachcard)
                except KeyError:
                    choices.update({setdata[DB.Sets.release_date]: [eachcard]})

        # sort by date, most recent first
        release_sort = {k: v for k, v in sorted(
            choices.items(), key=lambda item: item[0], reverse=True)}

        # favor 'expansion' or 'core'
        for _, cardlist in release_sort.items():
            for i in cardlist:
                set_details = tech.set_details(i[DB.Cards.set_code])
                stype = set_details[DB.Sets.set_type]
                if stype == 'expansion' or stype == 'core':
                    if i[DB.Cards.is_promo] == False:
                        if i[DB.Cards.promo_types] == None:
                            if i[DB.Cards.is_online_only] == False: 
                                self.best_candidate = i
                                return

        # else, just set the most recent card
        for _, cardlist in release_sort.items():
            for i in cardlist:
                if i[DB.Cards.is_online_only] == False: 
                    self.best_candidate = i
                    return
    
    def fetch_joke(self):
        query = None
        if self.message.find('chuck norris') != -1:
            query = f'select * from chuck_norris'
        elif self.message.find('skämt') != -1:            
            query = f'select * from bad_jokes'
        elif self.message.find('joke') != -1:            
            query = f'select * from one_liners'

        if query != None:
            sqlitecursor.execute(query)
            data = sqlitecursor.fetchall()
            if len(data) > 0:
                random.shuffle(data)
                self.finalmessage = data[0][1]

beginning_of_launch()
client.run(tech.api_key())