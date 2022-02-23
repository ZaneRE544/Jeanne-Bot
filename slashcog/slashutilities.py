from sqlite3 import connect
from nextcord import *
from nextcord import slash_command as jeanne_slash
from aiohttp import ClientSession
from nextcord.ext.commands import Cog
from config import WEATHER
from py_expression_eval import Parser

parser=Parser()

db=connect("database.db")
class slashutilities(Cog):
    def __init__(self, bot):
        self.bot = bot
               

    @jeanne_slash(description="Get weather information on a city")
    async def weather(self, interaction: Interaction, type=SlashOption(description="City or ZIP Code", choices=["city", "ZIP code"]), place=SlashOption(description="Which place are you looking for weather info", required=True), country_code=SlashOption(description="Required if you are using ZIP code", required=False)):
        try:
            botbanquery = db.execute(
                f"SELECT * FROM botbannedData WHERE user_id = {interaction.user.id}")
            botbanned_data = botbanquery.fetchone()
            botbanned = botbanned_data[0]
            reason = botbanned_data[1]

            botbanned_user = await self.bot.fetch_user(botbanned)
            if interaction.user.id == botbanned_user.id:
                await interaction.response.send_message(f"You have been botbanned for:\n{reason}", ephemeral=True)
        except:
            if type=="city":
                urlil = f'http://api.openweathermap.org/data/2.5/weather?q={place}&appid={WEATHER}&units=metric'
                async with ClientSession() as session:
                    async with session.get(urlil) as r:
                        if r.status == 200:
                            js = await r.json()
                            tempp = js['main']['temp']
                            desc = js['weather'][0]["description"]
                            count = js['sys']['country']
                            hum = js['main']['humidity']
                            pres = js['wind']['speed']
                            windir=js['wind']['deg']
                            embed = Embed(
                                title=f'⛅ Weather details of {place} ⛅', description=f':earth_africa: Country: {count}', colour=0x00FFFF)
                            embed.add_field(name=':thermometer: Temperature:',
                                            value=f'{tempp}° Celsius', inline=True)
                            embed.add_field(name=':newspaper: Description:',
                                            value=f'{desc}', inline=True)
                            embed.add_field(name=":droplet: Humidity:",
                                            value=f'{hum}', inline=True)
                            embed.add_field(name=":cloud: Pressure:",
                                            value=f'{pres} Pa', inline=True)
                            embed.add_field(name=":arrow_right: Wind Direction:",
                                            value=f'{windir}° degrees', inline=True)
                            await interaction.response.send_message(embed=embed)

            if type=="ZIP code":
                urlil = f'http://api.openweathermap.org/data/2.5/weather?zip={place},{country_code}&appid={WEATHER}&units=metric'
                async with ClientSession() as session:
                    async with session.get(urlil) as r:
                        if r.status == 200:
                            js = await r.json()
                            name=js['name']
                            tempp = js['main']['temp']
                            desc = js['weather'][0]["description"]
                            count = js['sys']['country']
                            hum = js['main']['humidity']
                            pres = js['wind']['speed']
                            windir = js['wind']['deg']
                            embed = Embed(
                                title=f'⛅ Weather details of {name} ⛅', description=f':earth_africa: Country: {count}', colour=0x00FFFF)
                            embed.add_field(name=':thermometer: Temperature:',
                                            value=f'{tempp}° Celsius', inline=True)
                            embed.add_field(name=':newspaper: Description:',
                                            value=f'{desc}', inline=True)
                            embed.add_field(name=":droplet: Humidity:",
                                            value=f'{hum}', inline=True)
                            embed.add_field(name=":cloud: Pressure:",
                                            value=f'{pres} Pa', inline=True)
                            embed.add_field(name=":arrow_right: Wind Direction:",
                                            value=f'{windir}° degrees', inline=True)
                            await interaction.response.send_message(embed=embed)


    @jeanne_slash(description="Do a calculation")
    async def calculator(self, interaction: Interaction, calculate=SlashOption(description="What do you want to calculate?")):
        try:
            botbanquery = db.execute(
                f"SELECT * FROM botbannedData WHERE user_id = {interaction.user.id}")
            botbanned_data = botbanquery.fetchone()
            botbanned = botbanned_data[0]
            reason = botbanned_data[1]

            botbanned_user = await self.bot.fetch_user(botbanned)
            if interaction.user.id == botbanned_user.id:
                await interaction.response.send_message(f"You have been botbanned for:\n{reason}", ephemeral=True)
        except:
            answer = parser.parse(calculate).evaluate({})
            calculation = Embed(title="Result", color=0x00FFFF)
            calculation.add_field(name=calculate, value=answer)
            await interaction.response.send_message(embed=calculation)
        
def setup(bot):
    bot.add_cog(slashutilities(bot))
