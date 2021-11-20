# bot.py
import os
import requests
import json
import hashlib
import sqlite3
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
LASTFMAPIKEY = os.getenv('LASTFM_APIKEY')
LASTFMSECRET = os.getenv('LASTFM_SECRET')

bot = commands.Bot(command_prefix='!')
bot.dbcon = sqlite3.connect('rhizal.db')
bot.dbcur = bot.dbcon.cursor()


@bot.event
async def on_ready():
    payload = {'method' : 'auth.gettoken', 'api_key' : LASTFMAPIKEY, 'format' : 'json'}
    r = requests.get('http://ws.audioscrobbler.com/2.0/', params = payload)
    bot.lastfmToken = json.loads(r.text)["token"]
    load_sk_from_db()
    print_startup()

def print_startup():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'lastFM token: {bot.lastfmToken}')

    
@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise
            
@bot.command(name='lfmlogin', help="sends authorization url for lastfm")
async def send_lfm_auth(ctx):
    await ctx.author.dm_channel.send(f"http://www.last.fm/api/auth/?api_key={LASTFMAPIKEY}&token={bot.lastfmToken}")

@bot.command(name='lfmgetsession', help="use once authed")
async def lfm_get_sessionkey(ctx):
    sessionJSON = fetch_lfm_session()
    bot.sk = json.loads(sessionJSON)["key"]
    bot.fmUser = json.loads(sessionJSON)["name"]
    try:
        bot.dbcur.execute('''CREATE TABLE sessions(user text, key text)''')
        bot.dbcur.execute(f"INSERT INTO sessions VALUES ('{bot.fmUser}', '{bot.sk}'")
        bot.dbcon.commit()
    except sqlite3.OperationalError:
        print("SQLite Error")
        pass

#tofix: gets last session key added to DB
def load_sk_from_db():
    try:
        for row in bot.dbcur.execute('SELECT key FROM sessions'):
            bot.sk = row[0]
    except:
        print("sessionkey/db not setup yet")
        pass


@bot.command(name='wtracks', help="tells you what's up")
async def pick_song(ctx, user):
    payload = {'method' : 'user.getWeeklyTrackChart', 'api_key' : LASTFMAPIKEY, 'user' : user, 'format' : 'json', }
    result = requests.get('http://ws.audioscrobbler.com/2.0/', params = payload)
    resultJSON = json.loads(result.text)
    await ctx.send(user + "'s weekly top 5:")
    top = 5
    for song in resultJSON['weeklytrackchart']['track']:
        if top == 0:
            break
        artist = song['artist']['#text']
        track = song['name']
        plays = song['playcount']
        await ctx.send(track + " - " + artist + " : " + plays + " plays")
        top -= 1

def lastfm_sign(params):
    keys = params.keys().sort()
    pstring = ''
    for k in keys:
        pstring += k
        pstring += params[k]
    pstring += LASTFMSECRET
    
    return hashlib.md5(pstring.encode('utf-8')).hexdigest()

def signed_payload(payload):
    signedPayload = payload + {'api_sig' : lastfm_sign(payload)}
    return signedPayload

def fetch_lfm_session():
    payload = {'method' : 'auth.getSession', 'api_key' : LASTFMAPIKEY, 'token' : bot.lastfmToken, 'format' : 'json'}
    return lfm_request(payload)

#takes a payload and signs it and returns the result of the request
def lfm_request(payload):
    return requests.get('http://ws.audioscrobbler.com/2.0/', params = signed_payload(payload))

bot.run(TOKEN)
