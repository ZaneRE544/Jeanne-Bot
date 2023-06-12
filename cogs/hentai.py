from random import randint
from discord import Color, Embed, Interaction, app_commands as Jeanne
from discord.ext.commands import Cog, Bot
from functions import Botban, Hentai, shorten_url
from typing import Literal, Optional
from assets.components import ReportContent, ReportSelect


class nsfw(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Jeanne.command(description="Get a random hentai from Jeanne", nsfw=True)
    @Jeanne.describe(rating="Do you want questionable or explicit content?")
    async def hentai(
        self,
        ctx: Interaction,
        rating: Optional[Literal["questionable", "explicit"]] = None,
    ) -> None:
        await ctx.response.defer(thinking=False)
        if Botban(ctx.user).check_botbanned_user() == True:
            return

        hentai, source = Hentai().hentai(rating)

        if hentai.endswith("mp4"):
            view = ReportContent(hentai)
            await ctx.followup.send(hentai)

        else:
            embed = (
                Embed(color=Color.purple())
                .set_image(url=hentai)
                .set_footer(
                    text="Fetched from {} • Credits must go to the artist".format(
                        source
                    )
                )
            )
            view = ReportContent(hentai)
            await ctx.followup.send(embed=embed, view=view)

    @Jeanne.command(description="Get a random media content from Gelbooru", nsfw=True)
    @Jeanne.describe(
        rating="Do you want questionable or explicit content?",
        tag="Add your tag",
        plus="Need more content? (up to 4)",
    )
    async def gelbooru(
        self,
        ctx: Interaction,
        rating: Optional[Literal["questionable", "explicit"]],
        tag: Optional[str] = None,
        plus: Optional[bool] = None,
    ) -> None:
        await ctx.response.defer(thinking=False)
        if Botban(ctx.user).check_botbanned_user():
            return

        image = Hentai(plus).gelbooru(rating, tag)

        if plus:
            images = [image[randint(1, 100) - 1] for _ in range(4)]
            view = ReportSelect(*[img["file_url"] for img in images])

            if "mp4" in image:
                media = [img["file_url"] for img in images]
                await ctx.followup.send("\n".join(media), view=view)
            else:
                color = Color.random()
                embeds = [
                    Embed(color=color, url="https://gelbooru.com").set_image(
                        url=img["file_url"]
                    )
                    for img in images
                ]
                await ctx.followup.send(embeds=embeds, view=view)
        else:
            view = ReportContent(image)
            if image.endswith("mp4"):
                await ctx.followup.send(image, view=view)
            else:
                embed = (
                    Embed(color=Color.purple())
                    .set_image(url=image)
                    .set_footer(
                        text="Fetched from Gelbooru • Credits must go to the artist"
                    )
                )
                await ctx.followup.send(embed=embed, view=view)

    @gelbooru.error
    async def gelbooru_error(self, ctx: Interaction, error: Jeanne.AppCommandError):
        if isinstance(error, Jeanne.CommandInvokeError):
            if IndexError or KeyError:
                no_tag = Embed(
                    description="The tag could not be found", color=Color.red()
                )
                await ctx.channel.send(embed=no_tag)

    @Jeanne.command(description="Get a random hentai from Yande.re", nsfw=True)
    @Jeanne.describe(
        rating="Do you want questionable or explicit content?",
        tag="Add your tag",
        plus="Need more content? (up to 4)",
    )
    async def yandere(
        self,
        ctx: Interaction,
        rating: Optional[Literal["questionable", "explicit"]],
        tag: Optional[str] = None,
        plus: Optional[bool] = None,
    ) -> None:
        await ctx.response.defer(thinking=False)
        if Botban(ctx.user).check_botbanned_user() == True:
            return

        if tag == "02":
            await ctx.followup.send(
                "Tag has been blacklisted due to it returning extreme content and guro"
            )

        else:
            image = Hentai(plus).yandere(rating, tag)

            if plus == True:
                image1 = image[randint(1, 100) - 1]
                image2 = image[randint(1, 100) - 1]
                image3 = image[randint(1, 100) - 1]
                image4 = image[randint(1, 100) - 1]
                view = ReportSelect(
                    shorten_url(str(image1["file_url"])),
                    shorten_url(str(image2["file_url"])),
                    shorten_url(str(image3["file_url"])),
                    shorten_url(str(image4["file_url"])),
                )
                color = Color.random()
                embed1 = (
                    Embed(color=color, url="https://yande.re")
                    .set_image(url=image1["file_url"])
                    .set_footer(
                        text="Fetched from Yande.re • Credits must go to the artist"
                    )
                )
                embed2 = Embed(color=color, url="https://yande.re").set_image(
                    url=image2["file_url"]
                )
                embed3 = Embed(color=color, url="https://yande.re").set_image(
                    url=image3["file_url"]
                )
                embed4 = Embed(color=color, url="https://yande.re").set_image(
                    url=image4["file_url"]
                )
                embeds = [embed1, embed2, embed3, embed4]
                try:
                    embed1.set_footer(
                        text="Fetched from Yande.re • Credits must go to the artist"
                    )
                    await ctx.followup.send(embeds=embeds, view=view)
                except:
                    embed1.set_footer(
                        text="Fetched from Yande.re • Credits must go to the artist\nIfyou see an illegal content, please use /botreport and attach the link when reporting"
                    )
                    await ctx.followup.send(embeds=embeds)
            else:
                yandere = Embed(color=Color.random())
                yandere.set_image(url=image)
                yandere.set_footer(
                    text="Fetched from Yande.re • Credits must go to the artist"
                )
                try:
                    yandere.set_footer(
                        text="Fetched from Yande.re • Credits must go to the artist"
                    )
                    view = ReportContent(shorten_url(str(image)))
                    await ctx.followup.send(embed=yandere, view=view)
                except:
                    yandere.set_footer(
                        text="Fetched from Yande.re • Credits must go to the artist\nIfyou see an illegal content, please use /botreport and attach the link when reporting"
                    )

                    await ctx.followup.send(embed=yandere)

    @yandere.error
    async def yandere_error(self, ctx: Interaction, error: Jeanne.AppCommandError):
        if isinstance(error, Jeanne.CommandInvokeError):
            if IndexError or KeyError:
                no_tag = Embed(
                    description="The tag could not be found", color=Color.red()
                )
                await ctx.followup.send(embed=no_tag)

    @Jeanne.command(description="Get a random hentai from Konachan")
    @Jeanne.describe(
        rating="Do you want questionable or explicit content?",
        tag="Add your tag",
        plus="Need more content (up to 4)",
    )
    async def konachan(
        self,
        ctx: Interaction,
        rating: Optional[Literal["questionable", "explicit"]],
        tag: Optional[str] = None,
        plus: Optional[bool] = None,
    ) -> None:
        await ctx.response.defer(thinking=False)
        if Botban(ctx.user).check_botbanned_user() == True:
            return

        image = Hentai(plus).konachan(rating, tag)

        if plus == True:
            image1 = image[randint(1, 100) - 1]
            image2 = image[randint(1, 100) - 1]
            image3 = image[randint(1, 100) - 1]
            image4 = image[randint(1, 100) - 1]
            view = ReportSelect(
                shorten_url(str(image1["file_url"])),
                shorten_url(str(image2["file_url"])),
                shorten_url(str(image3["file_url"])),
                shorten_url(str(image4["file_url"])),
            )
            color = Color.random()
            embed1 = (
                Embed(color=color, url="https://konachan.com")
                .set_image(url=image1["file_url"])
                .set_footer(
                    text="Fetched from Konachan • Credits must go to the artist"
                )
            )
            embed2 = Embed(color=color, url="https://konachan.com").set_image(
                url=image2["file_url"]
            )
            embed3 = Embed(color=color, url="https://konachan.com").set_image(
                url=image3["file_url"]
            )
            embed4 = Embed(color=color, url="https://konachan.com").set_image(
                url=image4["file_url"]
            )
            embeds = [embed1, embed2, embed3, embed4]
            try:
                embed1.set_footer(
                    text="Fetched from Konachan • Credits must go to the artist"
                )
                await ctx.followup.send(embeds=embeds, view=view)
            except:
                embed1.set_footer(
                    text="Fetched from Konachan • Credits must go to the artist\nIfyou see an illegal content, please use /botreport and attach the link when reporting"
                )
                await ctx.followup.send(embeds=embeds)
        else:
            konachan = Embed(color=Color.random())
            konachan.set_image(url=image)

            try:
                konachan.set_footer(
                    text="Fetched from Konachan • Credits must go to the artist"
                )
                view = ReportContent(shorten_url(str(image)))
            except:
                konachan.set_footer(
                    text="Fetched from Konachan • Credits must go to the artist\nIfyou see an illegal content, please use /botreport and attach the link when reporting"
                )
                view = None
            await ctx.followup.send(embed=konachan, view=view)

    @konachan.error
    async def konachan_error(self, ctx: Interaction, error: Jeanne.AppCommandError):
        if isinstance(error, Jeanne.CommandInvokeError):
            if IndexError or KeyError:
                no_tag = Embed(
                    description="The tag could not be found", color=Color.red()
                )
                await ctx.followup.send(embed=no_tag)


async def setup(bot: Bot):
    await bot.add_cog(nsfw(bot))
