import aiohttp

from utils import error, PROFILE_NAMES

import discord
from discord.ext import commands  # type: ignore

from os import environ as env

from typing import Union, Optional

API_KEY = env.get("HYPIXEL_API_KEY")

ALLOWED_CHARS = {"_", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"}

async def input_to_uuid(interaction: discord.Interaction, provided_username: Optional[str]) -> Optional[tuple[str, str]]:
    """
    This will take a already given username, but if one isn't given, it will
    first check if they've linked their account, if not, it will try
    parsing their ign from their discord nicks, by trimming off their tag,
    e.g. '[Admin] Notch' will get parsed as 'Notch'.
    """
    nick = False  # Used to detect if we fell back on parsing nick
    if provided_username is None:  # If no username is given
        if (linked_account := interaction.bot.linked_accounts.get(f"{interaction.author.id}")):  # Check if they've linked their account
            username = linked_account
        else:  # If not, parse their nickname
            username = interaction.author.display_name
            nick = True
    else:
        username = provided_username

    # Remove tags and wrong chars
    username = username.split("]")[1] if "]" in username else username
    username = "".join([char for char in username if char.lower() in ALLOWED_CHARS])

    # If it's a username, get their uuid
    if len(username) <= 16:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}") as response:
                if response.status > 200:
                    return await error(interaction, "Error! Username was incorrect.", "Make sure you spelled the target player's name correctly.")

                # When we can't find a username, request.text will be '', if we can, it'll be the json string
                if not (uuid_request := await response.json()):
                    if not nick:
                        return await error(interaction, "Error! Username was incorrect.", "Make sure you spelled the target player's name correctly.")
                    else:
                        return await error(interaction, "Error, could not parse username from discord nickname.", "Make sure you spelled the target player's name correctly")

                uuid = uuid_request["id"]
    else:
        # if it's a uuid
        uuid = username
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}") as response:
                if response.status > 200:
                    return await error(interaction, "Error! UUID was incorrect.", "Could not find that player's uuid.")
                username_request = await response.json()
                if not username_request:
                    return await error(interaction, "Error! UUID was incorrect.", "Could not find that player's uuid.")
                username = username_request["name"]
        
    return username, uuid

async def get_profile_data(interaction: discord.Interaction, username: Optional[str], profile_provided: Optional[str] = None, return_profile_list: bool = False) -> Optional[dict]:
    """
    This will take a username, or None, and return a dictionary with
    Their profile data, with a few extra bits for convenience
    """
    # If they want to use auto-name and give a profile
    if username is not None and username.lower() in PROFILE_NAMES:
        profile_provided = username
        username = None
    # Convert username/linked_account/nick to uuid
    data = await input_to_uuid(interaction, username)
    if data is None:
        return None
    username, uuid = data
    
    #################################
    # Fetch profile from hypixel's API with uuid
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.hypixel.net/skyblock/profiles?key={API_KEY}&uuid={uuid}") as response:
                profile_list = await response.json()
    except:
        return await error(interaction, "Error, the Hypixel API is in maintenance mode!", "Please try again in a few hours!")


    if profile_list == {'success': False, 'cause': 'Invalid API key'}:
        print("############################### Error, key has failed again!")
        return await error(interaction, "Error, the api key used to run this bot has failed.", "This is because Hypixel randomly kill API keys. Please be patient, a fix is coming soon!")

    # profiles can be None, or not exist as key
    if profile_list is None or profile_list.get('profiles') is None:  # If we can't find any profiles, they never made one
        return await error(interaction, "That user has never joined Skyblock before!", "Make sure you typed the name correctly and try again.")

    # For networth only
    if return_profile_list:
        return {"data": (username, uuid, profile_list, profile_provided)}

    #################################
    # Either try find the given profile or use the latest joined
    if profile_provided is not None:  # If they gave their own profile
        if not (profiles := [x for x in profile_list["profiles"] if x["cute_name"].lower() == profile_provided.lower()]):
            return await error(interaction, "Error, couldn't find that profile name", "Make sure you type it correctly and try again.")
        profile = profiles[0]
    else:  # If they leave it for auto
        if not (valid_profiles := [x for x in profile_list["profiles"] if uuid in x['members'] and "selected" in x]):
            return await error(interaction, "Error, cannot find profiles for this user!", "Make sure you spelled the target player's name correctly")
    
        profile = max(valid_profiles, key=lambda x: x['selected'])

    #################################
    # Save the profile data and some other bits because they're handy
    profile_dict = profile["members"][uuid]

    profile_dict["uuid"] = uuid
    profile_dict["username"]= username
    profile_dict["profile_id"] = profile["profile_id"]
    profile_dict["cute_name"] = profile["cute_name"]

    return profile_dict
