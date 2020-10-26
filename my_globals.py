import sqlite3
from sqlite3 import Error

sqliteconnection = sqlite3.connect('/home/plutonergy/Documents/Discord/database.sqlite')
sqlitecursor = sqliteconnection.cursor()

global techdict
techdict = {
    'sqlite': {},
    'token': None,
    'expansions': {}
}

class tech:
    global techdict

    @staticmethod
    def empty_insert_query(table):
        sqlitecursor.execute('PRAGMA table_info("{}")'.format(table,))
        tables = sqlitecursor.fetchall()
        query = f"insert into {table} values({','.join(['?']*len(tables))})"
        values = [None] * len(tables)
        return query, values

    @staticmethod
    def api_key():
        if techdict['token'] == None:
            sqlitecursor.execute('select * from settings where id is 1')
            data = sqlitecursor.fetchone()
            techdict['token'] = data[DB.Settings.discord_token]
        return techdict['token']

    @staticmethod
    def set_details(set_code):
        if set_code not in techdict['expansions']:
            sqlitecursor.execute('select * from sets where code = (?)', (set_code,))
            data = sqlitecursor.fetchone()
            techdict['expansions'].update({set_code:data})
        return techdict['expansions'][set_code]

def sqlite_function(**kwargs):
    global techdict
    if kwargs['table'] not in techdict['sqlite']:
        techdict['sqlite'][kwargs['table']] = {}
    if kwargs['column'] not in techdict['sqlite'][kwargs['table']]:
        query = f'select * from {kwargs["table"]}'
        try:
            sqlitecursor.execute(query)
        except Error:
            with sqliteconnection:
                query1 = f'create table {kwargs["table"]} (id INTEGER PRIMARY KEY AUTOINCREMENT)'
                query2 = f'select * from {kwargs["table"]}'
                sqlitecursor.execute(query1)
                sqlitecursor.execute(query2)
        col_names = sqlitecursor.description
        for count, row in enumerate(col_names):
            if row[0] == kwargs['column']:
                techdict['sqlite'][kwargs['table']][kwargs['column']] = count
                return count
        with sqliteconnection:
            query = f'alter table {kwargs["table"]} add column {kwargs["column"]} {kwargs["type"]}'
            sqlitecursor.execute(query)
        return len(col_names)

class DB:
    class Settings:
        discord_token = sqlite_function(table="settings", column="discord_token", type="TEXT")

    class Prices:
        uuid        = sqlite_function(table="prices", column="uuid",     type="TEXT")
        mtgo_foil   = sqlite_function(table="prices", column="mtgoFoil", type="FLOAT")
        mtgo_reg    = sqlite_function(table="prices", column="mtgoReg",  type="FLOAT")
        us_reg      = sqlite_function(table="prices", column="usReg",    type="FLOAT")
        us_foil     = sqlite_function(table="prices", column="usFoil",   type="FLOAT")
        eu_reg      = sqlite_function(table="prices", column="euReg",    type="FLOAT")
        eu_foil     = sqlite_function(table="prices", column="euFoil",   type="FLOAT")
        weight      = sqlite_function(table="prices", column="weight",   type="FLOAT")
        unix_time   = sqlite_function(table="prices", column="unixTime", type="INTEGER")

    class Cards:
        uuid            = sqlite_function(table="cards", column="uuid",         type="TEXT")        
        text            = sqlite_function(table="cards", column="text",         type="TEXT")        
        power           = sqlite_function(table="cards", column="power",        type="TEXT")        
        toughness       = sqlite_function(table="cards", column="toughness",    type="TEXT")        
        flavor_text     = sqlite_function(table="cards", column="flavorText",   type="TEXT")      
        set_code        = sqlite_function(table="cards", column="setCode",      type="TEXT")        
        supertypes      = sqlite_function(table="cards", column="supertypes",   type="TEXT")     
        name            = sqlite_function(table="cards", column="name",         type="TEXT")     
        promo_types     = sqlite_function(table="cards", column="promoTypes",   type="TEXT")   
        scryfall_id     = sqlite_function(table="cards", column="scryfallId",   type="TEXT")  

        time_limit      = sqlite_function(table="cards", column="time_limit",   type="FLOAT")  

        is_promo        = sqlite_function(table="cards", column="isPromo",      type="INTEGER")     
        is_online_only  = sqlite_function(table="cards", column="isOnlineOnly", type="INTEGER")  

    class Sets:
        name         = sqlite_function(table="sets", column="name",         type="TEXT")        
        set_code     = sqlite_function(table="sets", column="code",         type="TEXT")                
        set_type     = sqlite_function(table="sets", column="type",         type="TEXT")                
        release_date = sqlite_function(table="sets", column="releaseDate",  type="TEXT")   

    class ChuckNorris:
        joke         = sqlite_function(table="chuck_norris",column="joke", type="TEXT")    
    class OneLiners:
        joke         = sqlite_function(table="one_liners",  column="joke", type="TEXT")                
    class BadJokes:
        joke         = sqlite_function(table="bad_jokes",   column="joke", type="TEXT")                