from typing import Any, List, Mapping

import discord
from discord.ext import commands
from discord import app_commands

from menus import generate_static_preset_menu

data_dict = {
    "networth":    ("[username]",    "Checks the total value of a profile for a user."),
    "auctions":    ("[username]",    "Shows someone's auctions and BINs."),
    "bazaar":      ("<item>",        "Shows the bazaar price for a certain item, e.g. 'cobblestone'."),
    "dungeons":    ("[username]",    "Shows data about someone's dungeon level, including what floors they've beaten."),
    "duped":       ("[username]",    "Shows duped items that a player has on them."),
    "help":        ("<None>",        "Takes you to this command."),
    "invite":      ("<None>",        "Provides instructions on how to invite the bot to your server."),
    "kills":       ("[username]",    "Shows the most mobs a player has killed."),
    "leaderboard": ("[profile_type]","Shows the top 100 players with the highest combined networth!"),
    "link":        ("[ign]",         "Links your in-game name to your discord id so you can leave it out in commands."),
    "lowest_bin":  ("<item>",        "Shows the lowest bin on auction house with that name, use .lb for short!"),
    "maxer":       ("[username]",    "Shows all the attributes and enchantments of the item you select."),
    "minions":     ("[username]",    "Shows the cheapest minions to craft to increase your unique crafted minions count."),
    "missing":     ("[username]",    "Shows the top tier accessories that the player is missing."),
    "price_check": ("<item>",        "Shows historic pricing data about the given item, use .p for short!"),
    "set_prefix":  ("<prefix>",      "Allows an admin to change the prefix of the bot."),
    "skills":      ("[username]",    "Shows a summary of all a users skills, including average."),
    "sky":         ("[username]",    "Links you to someone's sky.shiiyu.moe page, for convenience."),
    "slayer":      ("[username]",    "Shows a summary of someone's slayer data, including how many of each tier someone's killed."),
    "rank":        ("[username]",    "Shows where you place amongst other players with the value of your profile."),
    "weight":      ("[username]",    "Shows a menu of weights which represent how far into the game the player is."),
    "wiki":        ("<item>",        "Shows a page from the Hypixel wiki, to assist in finding a page or item."),
    "weights":     ("[username]",    "Shows someone's senither weight (and overflow weight) in different sections."),
}

categories = {
    "Player Stats Commands": ["dungeons", "kills", "missing", "rank", "skills", "sky", "slayer", "weights"],
    "Price Data Commands":   ["auctions", "bazaar", "lowest_bin", "networth", "price_check"],
    "General Info Commands": ["duped", "leaderboard", "maxer", "minions", "rank", "wiki"],
    "Settings Commands":     ["help", "invite", "link", "set_prefix"],
}

EMOJI_LIST = ["<:stats:915209828983537704>", "<:general_info:915210726900125706>", "<:price_data:915211058728275980>", "<:settings:915211248684134420>"]

class Help(commands.HelpCommand):
    async def send_bot_help(self, mapping) -> None:
        list_of_embeds = []
        for category, commands in categories.items():
            embed = discord.Embed(title=category, colour=0x3498DB)
            for command in commands:
                param, description = data_dict[command]
                param = "" if param == "<None>" else f" {param}"
                embed.add_field(name=f"{command}{param}", value=description, inline=False)            
            
            embed.set_footer(text=f"Command executed by {self.context.author.display_name} | Elise (Community Bot Remade)")
            list_of_embeds.append(embed)

        await generate_static_preset_menu(ctx=self.context, list_of_embeds=list_of_embeds, emoji_list=EMOJI_LIST, is_response=False)

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = Help()
        bot.help_command.cog = self
    
    def cog_unload(self):
        self.bot.help_command = self._original_help_command

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))