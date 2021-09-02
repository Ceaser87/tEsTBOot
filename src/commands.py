import boto3
import os
import random
import requests

import wolframalpha
from discord import Embed
from discord.ext import commands
from discord.ext import tasks
from mcstatus import MinecraftServer

COLOR = [0xFFE4E1, 0x00FF7F, 0xD8BFD8, 0xDC143C, 0xFF4500, 0xDEB887, 0xADFF2F, 0x800000, 0x4682B4, 0x006400, 0x808080,
         0xA0522D, 0xF08080, 0xC71585, 0xFFB6C1, 0x00CED1]
LOADING_EMOJI = ["➕", "➗", "➖", "➗"]

AWS_SERVER_PUBLIC_KEY = os.getenv('AWS_SERVER_PUBLIC_KEY')
AWS_SERVER_SECRET_KEY = os.getenv('AWS_SERVER_SECRET_KEY')
WOLFRAM_APPID = os.getenv('WOLFRAM_APPID')

conf = {
    "timeout_random": 60,
    "aws_mc_checktime": 1,
    "aws_mc_server_adress": "ratius99.aternos.me"
}


class MainCommands(commands.Cog):
    """A couple of commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='random')
    async def random(self, ctx: commands.Context, number_of_dice: int, number_of_sides: int):
        """Simulates rolling dice."""
        print("random event!")

        embed = Embed(title="Zufallszahlen", color=random.choice(COLOR),
                      description=f"{number_of_dice} Würfel mit {number_of_sides} Seiten:")

        for _ in range(number_of_dice):
            w = str(random.choice(range(1, number_of_sides + 1)))
            embed.add_field(name=w, value="_" * len(w) + "/" + str(number_of_sides), inline=True)

        timeout = conf["timeout_random"]
        embed.set_footer(text=f"Selbstlöschend nach {timeout} Sekunden.")

        await ctx.message.delete()
        await ctx.send(embed=embed, delete_after=timeout)

    @commands.command(name='hi')
    async def hi(self, ctx: commands.Context, number_of_hi: int = 1):
        """Say \"Hi!\" multiple times."""
        print("hi!")

        for _ in range(number_of_hi):
            await ctx.send('Hi!')

    @commands.command(name='echo', help='Echo string.')
    async def echo(self, ctx: commands.Context, *, txt: str):
        """Echos input string."""
        print("echo!")

        await ctx.send(txt)

    @commands.command(name='emoji')
    async def emoji(self, ctx: commands.Context, emoji_name: str, image_url: str):
        """Creates custom server emoji. 
        Supports .jpg .gif .png."""
        print("emoji!")

        response = requests.get(image_url)
        img = response.content
        img = await ctx.guild.create_custom_emoji(name=emoji_name, image=img)
        await ctx.send(">> Emoji created: " + str(img))

    @commands.command(name='molec')
    async def molec(self, ctx: commands.Context, smile_string: str):
        """'Visualize a given molecule string. Supports MIME and other structural identifier. 
        Note: Triple bonds in SMILES strings represented by \'\#\' have to be URL-escaped as \'%23\' and \'?\' as \'%3F\'."""
        print('molec!')

        url1 = 'http://cactus.nci.nih.gov/chemical/structure/' + smile_string + '/image'
        await ctx.send(">> Molecule: " + str(url1))


class WolframCommands(commands.Cog):
    """A couple of commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.wolframclient = wolframalpha.Client(WOLFRAM_APPID)

    @commands.command(name='wolfram')
    async def wolfram(self, ctx: commands.Context, *, question_string: str):
        """Use Wolfram Alpha (API) to solve Math or ask random stuff It can do ...
        everything WolframAlpha can do: Equations, Weather  (Overview: https://www.wolframalpha.com/)"""
        print('wolfram! ' + question_string)

        res = self.wolframclient.query(question_string)
        if not res.success:
            await ctx.send(">> Wolfram Weisnisch Weiter... ")
            return
        try:
            message = next(res.results).text
        except StopIteration:
            message = "No short result found. Try \"!wolfram-l\"."
        await ctx.send(">> Wolfram: " + message)

    @commands.command(name='wolfall')
    async def wolfall(self, ctx: commands.Context, *, question_string: str):
        """See !wolfram. Returns long informative answer"""
        print('wolfram! ' + question_string)

        res = self.wolframclient.query(question_string)
        if not res.success:
            await ctx.send(">> Wolfram Weisnisch Weiter... ")
            return

        message = ""
        for pod in res.pods:
            if pod.title == res.datatypes:
                message += str(pod.subpod.img.src) + "\n"
            for sub in pod.subpods:
                if sub.plaintext:
                    message += str(sub.plaintext) + "\n"
        await ctx.send(">> Wolfram: " + message)

    @commands.command(name='wolfget')
    async def wolfget(self, ctx: commands.Context, image_title: str, question_string: str):
        """See !wolfram. Returns image with given title"""
        print('wolfram! ' + question_string)

        res = self.wolframclient.query(question_string)
        if not res.success:
            await ctx.send(">> Wolfram Weisnisch Weiter... ")
            return

        message = ""
        try:
            message = next(res.results).text + "\n"
        except StopIteration:
            pass
        for pod in res.pods:
            if pod.title == image_title:
                message += str(pod.subpod.img.src) + "\n"
        await ctx.send(">> Wolfram: " + message)


class AWSCommands(commands.Cog):
    """A couple of commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.startuploop.start()
        self.aws_status = 0
        self.aws_loading_count = 0

    # Tasks

    @commands.tasks.loop(minutes=1)
    async def startuploop(self, bot):
        print("loopaws")

        self.aws_loading_count += 1

        try:
            server = MinecraftServer.lookup("3.125.141.61")
            status = server.status()
            players = status.players.online
            self.aws_status = 1

        except Exception:
            if self.aws_status == 1:
                self.aws_status = 0

        channel = bot.get_channel(852114543759982592)
        if self.aws_status == 0:
            await channel.edit(name='❌OFFLINE')
        if self.aws_status == 1:
            await channel.edit(name=f"✔ONLINE ({str(players) if players else 0} Spieler)")
        if self.aws_status == 2:
            await channel.edit(name=f'{LOADING_EMOJI[self.aws_loading_count % len(LOADING_EMOJI)]}WAITING')
        if self.aws_status == 22:
            await channel.edit(name=f'{LOADING_EMOJI[self.aws_loading_count % len(LOADING_EMOJI)]}STARTING')

    @commands.command(name='aws')
    async def aws(self, ctx: commands.Context, command: str):
        """Controll minecraft server hosted on aws ec2 instance. Type \"aws -start\", \"aws -stop\". """
        print(f"aws + {command}.")

        session = boto3.Session(
            aws_access_key_id=AWS_SERVER_PUBLIC_KEY,
            aws_secret_access_key=AWS_SERVER_SECRET_KEY,
            region_name="eu-central-1"
        )

        ec2 = session.resource('ec2')
        self.instance = ec2.Instance('i-07baa970d1c82bb08')

        def turnOffInstance():
            try:
                self.instance.stop()
                return True
            except Exception as e:
                print(e)
                return False

        def turnOnInstance():
            try:
                self.instance.start()
                self.startuploop.start()
                return True
            except Exception as e:
                print(e)
                return False

        def getInstanceState():
            return self.instance.state['Name']

        def rebootInstance():
            try:
                self.instance.reboot()
                return True
            except Exception as e:
                print(e)
                return False

        if 'stop' in command:
            if turnOffInstance():
                await ctx.send('AWS Instance stopping')
            else:
                await ctx.send('Error stopping AWS Instance')
        elif 'start' in command:
            if turnOnInstance():
                await ctx.send('AWS Instance starting')
            else:
                await ctx.send('Error starting AWS Instance')
        elif 'state' in command:
            await ctx.send('AWS Instance state is: ' + getInstanceState())
        elif 'reboot' in command:
            if rebootInstance():
                await ctx.send('AWS Instance rebooting')
            else:
                await ctx.send('Error rebooting AWS Instance')
