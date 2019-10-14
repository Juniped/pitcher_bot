import re, os, time, sys, datetime, json, asyncio, random
import discord
import requests

token = os.environ['TOKEN']
api_url = os.environ['API_URL']
client = discord.Client()
current_pitcher = ""
current_pitcher_id = ""
current_info = {}


@client.event
async def on_ready():
    print("Weapons Online")


@client.event
async def on_message(message):
    try:
        if message.author == client.user:
            return
        if message.content.startswith("."): 
            content = message.content[1:]
            if content.startswith("pitcher"):# Set Pitcher
                pitcher_string = content[7:].strip()
                pitcher_results = search_pitchers(pitcher_string)
                if len(pitcher_results) == 0:
                    await message.channel.send("No players by that name found")
                elif len(pitcher_results) > 1:
                    names = [player['name'] for player in pitcher_results]
                    return_string = "Too many results, please be more specific\n" + "\n".join(names)
                    await message.channel.send(return_string)
                else:
                    player = pitcher_results[0]
                    if message.author.id not in current_info.keys():
                        current_info[message.author.id] = {}
                    current_info[message.author.id]['current_pitcher'] = player
                    current_info[message.author.id]['current_pitcher_id'] = player['id']
                    await message.channel.send(f"Current Pitcher set to {current_info[message.author.id]['current_pitcher']['name']}")
            elif content.startswith("current"): # Get Current Pitcher
                await message.channel.send(f"Current Pitcher is {current_info[message.author.id]['current_pitcher']['name']}")
            elif content.startswith("pitch"):
                pitches = get_pitches(current_info[message.author.id]['current_pitcher_id'])
                if len(pitches) < 5:
                    await message.channel.send("Pitcher does not have enough pitches, please select a different pitcher")
                else:
                    selected = select_pitches(pitches)
                    current_info[message.author.id]['last_pitch'] = selected['last_pitch']
                    current_info[message.author.id]['plist'] = selected['plist']

                    await message.channel.send(
                        f"{message.author.name}\nLast Pitches:\n" + "\n".join([p for p in selected['plist']]) 
                    )
                    current_info[message.author.id]['awaiting_guess'] = True
            elif content.startswith("swing"):
                if message.author.id not in current_info.keys():
                    await message.channel.send("You do not have a pitcher set yet, please do that first")
                if current_info[message.author.id]['awaiting_guess']:
                    guess = content[5:].strip()
                    guess_int = int(guess)
                    pitch = current_info[message.author.id]['last_pitch']
                    pitch_int = int(pitch)
                    diff = abs(pitch_int - guess_int)
                    if abs(diff) > 500:
                        diff = 1000 - abs(diff)
                    await message.channel.send(f"{message.author.name}\nSwing: {guess}\nPitch: {pitch}\nDifference:{diff}")
                    current_info[message.author.id]['awaiting_guess'] = False
                    current_info[message.author.id]['last_pitch'] = ""
                    current_info[message.author.id]['plist'] = []
                else:
                    await message.channel.send(f"{message.author.name}\nNot currently waiting for you to guess, please use .pitch to start the process")
            elif content.startswith("help"):
                string = (
                    f".help Generates this help message"
                    f".pitcher <pitcher name> sets the current pitcher you are hitting against"
                    f".pitch gets a list of pitches and sets up for the swing"
                    f".swing <swing> guess a number after getting a list of pitches"
                )
                await message.channel.send(string)
        except Exception as e:
            print(e)

def search_pitchers(pitcher_string):
    search_url = f"{api_url}/api/v1/players/search"
    params = {"query": pitcher_string}
    r = requests.get(search_url, params=params)
    json_results = r.json()
    return json_results
        
def get_pitches(id):
    url = f"{api_url}/api/v1/players/{id}/plays/pitching"
    r = requests.get(url)
    return r.json()

def select_pitches(pitches):
    games = {}
    for pitch in pitches:
        if pitch['pitch'] is not None:
            if pitch['game']['id'] in games.keys():
                games[pitch['game']['id']].append(f"{pitch['pitch']} -> {pitch['result']}")
            else:
                games[pitch['game']['id']] = [f"{pitch['pitch']} -> {pitch['result']}",]
    # Pick a game
    # print(games)
    # print(pitches)
    game_id = list(games.keys())[random.randint(0,len(list(games.keys())) -1)]
    # print(game_id)
    game_list = games[game_id]
    if len(game_list) < 6:
        last_pitch = game_list[-1].split(" ")[0]
        plist = game_list[:-1]
        return {'plist':plist, 'last_pitch':last_pitch}
    # print(game_list)
    start_value = random.randint(0,len(game_list) - 6)
    plist = game_list[start_value:start_value + 5]
    last_pitch = game_list[start_value + 6]
    return {'plist':plist, 'last_pitch':last_pitch}
        
print("Starting Application")
client.run(token)