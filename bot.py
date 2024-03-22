from typing import Literal, Optional

import time

import discord
from discord.ext import commands

import asyncio

from dotenv import load_dotenv

import os
from os import environ as env

import logging

import jishaku

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

logger = logging.getLogger("My_app")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

ch.setFormatter(CustomFormatter())

logger.addHandler(ch)

load_dotenv()

def get_prefix(bot: commands.Bot, msg: discord.Message):
    if env.get('LOCAL_BOT') == 'true':
        return '!'
    
    return '.'

class Bot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix,
                         intents=discord.Intents.all(),
                         owner_id=env.get('OWNER_ID'),
                         status=discord.Status.online,
                         activity=discord.Activity(name='in development (wont be finished prolly)'))
    
    async def setup_hook(self):
        logger.info(f'Logged in as {self.user.name} ({self.user.id})')

        for filename in os.listdir('cogs'):
            if filename.endswith('.py') and not filename.startswith("_"):
                await bot.load_extension(f'cogs.{filename[:-3]}')
        
        await bot.load_extension("jishaku")

bot = Bot()
bot.logger = logger

@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

@bot.command(hidden=True)
@commands.is_owner()
async def load(ctx, extension):
    loaded_cogs = ''
    if extension != '~':
        await bot.load_extension(extension)
        loaded_cogs += f'\U000023eb {extension}'
    else:
        for filename in os.listdir('cogs'):
            if filename.endswith('.py'):
                await bot.load_extension(f'cogs.{filename[:-3]}')
                loaded_cogs += f'\U000023eb cogs.{filename[:-3]}\n\n'
        loaded_cogs = loaded_cogs[:-2]
    await ctx.send(loaded_cogs)


@bot.command(hidden=True)
@commands.is_owner()
async def unload(ctx, extension):
    unloaded_cogs = ''
    if extension != '~':
        await bot.unload_extension(extension)
        unloaded_cogs += f'\U000023ec {extension}'
    else:
        for filename in os.listdir('cogs'):
            if filename.endswith('.py'):
                await bot.unload_extension(f'cogs.{filename[:-3]}')
                unloaded_cogs += f'\U000023ec cogs.{filename[:-3]}\n\n'
        unloaded_cogs = unloaded_cogs[:-2]
    await ctx.send(unloaded_cogs)


@bot.command(hidden=True)
@commands.is_owner()
async def reload(ctx, extension="~"):
    reload_start = time.time()
    reloaded_cogs = ''
    if extension != '~':
        await bot.unload_extension(extension)
        await bot.load_extension(extension)
        reloaded_cogs += f'\U0001f502 {extension}'
    else:
        for filename in os.listdir('cogs'):
            if filename.endswith('.py') and not filename.startswith("_"):
                try:
                    await bot.unload_extension(f'cogs.{filename[:-3]}')
                except commands.ExtensionNotLoaded:
                    pass
                await bot.load_extension(f'cogs.{filename[:-3]}')
                reloaded_cogs += f'\U0001f501 cogs.{filename[:-3]}\n\n'
        reloaded_cogs = reloaded_cogs[:-2]
    reload_end = time.time()
    await ctx.send(f'{reloaded_cogs}\nTook {reload_end - reload_start} to reload all')

os.environ['JISHAKU_NO_UNDERSCORE'] = 'true'
bot.run(env.get('BOT_TOKEN'))