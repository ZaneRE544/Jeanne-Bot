from typing import Literal
from discord import ButtonStyle, Color, Embed, Interaction, ui, app_commands as Jeanne, utils
from discord.ext.commands import Cog, Bot
from db_functions import Botban
from assets.helpassests import HelpMenu


class help_button(ui.View):

    def __init__(self):
        super().__init__()

        wiki_url = 'https://jeannebot.gitbook.io/jeannebot/help'
        orleans_url = 'https://discord.gg/jh7jkuk2pp'
        tos_and_policy_url = 'https://jeannebot.gitbook.io/jeannebot/tos-and-privacy'

        self.add_item(
            ui.Button(style=ButtonStyle.link,
                      label="Jeanne Webiste",
                      url=wiki_url))
        self.add_item(
            ui.Button(style=ButtonStyle.link,
                      label="Support Server",
                      url=orleans_url))
        self.add_item(
            ui.Button(style=ButtonStyle.link,
                      label="ToS and Privacy Policy",
                      url=tos_and_policy_url))


class help(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @Jeanne.command(
        description=
        "Get help from the wiki or join the support server for further help")
    async def help(self, ctx: Interaction):
        if Botban(ctx.user).check_botbanned_user() == True:
            return

        view = help_button()
        help = Embed(
            description=
            "Click on one of the buttons to open the documentation or get help on the support server"
        , color=Color.random())
        await ctx.response.send_message(embed=help, view=view)

    helpgroup=Jeanne.Group(name='help', description="...")

    @helpgroup.command(description="Get help on a specific module")
    async def module(self, ctx:Interaction, modules:Literal['Currency', 'Fun', 'Hentai', 'Image', 'Info', 'Inventory', 'Levelling', 'Manage', 'Moderation', 'Reactions', 'Utilities']):
        view=HelpMenu(self.bot, modules)
        await ctx.followup.send("Click here", view=view)


async def setup(bot: Bot):
    await bot.add_cog(help(bot))



