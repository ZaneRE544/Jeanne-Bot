import argparse
import asyncio
from random import randint
from discord import Color, Embed, HTTPException, Member, Message, NotFound, User
from discord.ext.commands import (
    Cog,
    Bot,
    Context,
    BucketType,
    MemberNotFound,
    UserNotFound,
)
import discord.ext.commands as Jeanne
from discord.utils import utcnow, get
from datetime import datetime, timedelta
from humanfriendly import InvalidTimespan, format_timespan, parse_timespan
from functions import (
    Moderation,
    check_botbanned_prefix,
    check_disabled_prefixed_command,
)
from assets.components import Confirmation
from typing import Optional, Union
from reactionmenu import ViewButton, ViewMenu
from assets.argparsers import mod_parser


class ModPrefix(Cog, name="Moderation"):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def commit_ban(
        self,
        ctx: Context,
        member: Union[Member | User],
        reason: str,
        message: Message,
        time: Optional[str] = None,
        delete_message_history: Optional[bool] = None,
    ):
        if delete_message_history:
            dmh = 604800
        else:
            dmh = 86400
        await ctx.guild.ban(
            member,
            reason="{} | {}".format(reason, ctx.author),
            delete_message_seconds=dmh,
        )
        ban = Embed(title="User Banned", color=0xFF0000)
        ban.add_field(name="Name", value=member, inline=True)
        ban.add_field(name="ID", value=member.id, inline=True)
        ban.add_field(name="Moderator", value=ctx.author, inline=True)
        ban.add_field(name="Reason", value=reason, inline=False)
        if time !=None:
            if time != "":
                try:
                    a = parse_timespan(time)
                    await Moderation(ctx.guild).softban_member(member, int(a))
                    time = format_timespan(a)
                except:
                    time = "Invalid time added. User is banned permanently!"
                ban.add_field(name="Duration", value=time, inline=True)
        ban.set_thumbnail(url=member.display_avatar)
        modlog = Moderation(ctx.guild).get_modlog_channel
        if modlog == None:
            if message:
                await message.edit(embed=ban, view=None)
                return
            await ctx.send(embed=ban, view=None)

        banned = Embed(
            description=f"{member} has been banned. Check {modlog.mention}",
            color=0xFF0000,
        )
        await message.edit(embed=banned, view=None)
        await modlog.send(embed=ban)

    async def check_banned(self, ctx: Context, member: User):
        try:
            banned = await ctx.guild.fetch_ban(member)
            if banned:
                already_banned = Embed(
                    description=f"{member} is already banned here",
                    color=Color.red(),
                )
                await ctx.send(embed=already_banned)
        except NotFound:
            return False

    @Jeanne.command(
        description="Ban someone in or outside the server",
        usage="[MEMBER | MEMBER NAME | MEMBER ID | USER ID] <-r REASON> <-t TIME>",
        extras={"bot_perms": "Ban Members", "member_perms": "Ban Members"},
    )
    @Jeanne.has_guild_permissions(ban_members=True)
    @Jeanne.bot_has_guild_permissions(ban_members=True)
    @Jeanne.check(check_disabled_prefixed_command)
    @Jeanne.check(check_botbanned_prefix)
    async def ban(
        self, ctx: Context, member: Union[Member | User], *words: str, parser=mod_parser
    ) -> None:
        try:
            parsed_args = parser.parse_known_args(words)[0]
            reason = " ".join(parsed_args.reason)
            time = None if parsed_args.time == None else " ".join(parsed_args.time)
            delete_message_history: bool = parsed_args.deletemessages
        except SystemExit:
            await ctx.send(
                embed=Embed(
                    description=f"You are missing some arguments or using incorrect arguments for this command",
                    color=Color.red(),
                )
            )
            return
        if member.id == ctx.guild.owner.id:
            failed = Embed(
                description="You can't ban the owner of the server...",
                color=Color.red(),
            )
            await ctx.send(embed=failed)
            return
        if member.id == ctx.author.id:
            failed = Embed(description="You cannot ban yourself...", color=Color.red())
            await ctx.send(embed=failed)
            return
        if member not in ctx.guild.members:
            if await self.check_banned(ctx, member) == False:
                view = Confirmation(ctx.author)
                confirm = Embed(
                    description="Is {} the one you want to ban from your server?".format(
                        member
                    ),
                    color=Color.dark_red(),
                ).set_thumbnail(url=member.display_avatar)
                m = await ctx.send(embed=confirm, view=view)
                await view.wait()

                if view.value == True:
                    await self.commit_ban(ctx, member, reason, m, delete_message_history)
                    return

                if view.value == (False or None):
                    cancelled = Embed(description="Ban cancelled", color=Color.red())
                    await m.edit(embed=cancelled, view=None)
                    return

        if ctx.author.top_role.position <= member.top_role.position:
            failed = Embed(
                description="{}'s position is higher than or same as you...".format(
                    member
                ),
                color=Color.red(),
            )
            await ctx.send(embed=failed)
            return
        await self.commit_ban(ctx, member, reason, m, time, delete_message_history)

    @ban.error
    async def ban_error(self, ctx: Context, error: Jeanne.CommandError):
        if isinstance(error, Jeanne.CommandInvokeError) and isinstance(
            error.original, (HTTPException, ValueError, UserNotFound)
        ):
            embed = Embed()
            embed.description = "Invalid user ID given\nPlease try again"
            embed.color = Color.red()
            await ctx.send(embed=embed)
            return
        if isinstance(error, Jeanne.CommandInvokeError) and isinstance(
            error.original, (HTTPException, ValueError, MemberNotFound)
        ):
            embed = Embed()
            embed.description = "Member is not in this server\nPlease try again"
            embed.color = Color.red()
            await ctx.send(embed=embed)

    @Jeanne.command(
        name="list-warns",
        aliases=["lw"],
        description="View warnings in the server or a member",
        usage="<MEMBER | MEMBER NAME | MEMBER ID>",
    )
    @Jeanne.check(check_disabled_prefixed_command)
    @Jeanne.check(check_botbanned_prefix)
    async def listwarns(self, ctx: Context, *, member: Optional[Member] = None):
        async with ctx.typing():
            record = (
                Moderation(ctx.guild).fetch_warnings_user(member)
                if member is not None
                else Moderation(ctx.guild).fetch_warnings_server()
            )
            if record == None:
                await ctx.send(
                    embed=Embed(
                        description=(
                            f"{member or 'No one'} has no warn IDs"
                            if member
                            else "No warnings up to date"
                        )
                    )
                )
                return
            menu = ViewMenu(
                ctx,
                menu_type=ViewMenu.TypeEmbed,
                disable_items_on_timeout=True,
                style="Page $/&",
            )
            for i in range(0, len(record), 5):
                embed_title = (
                    f"{member}'s warnings"
                    if member is not None
                    else "Currently warned members"
                )
                embed_color = 0xFF0000 if member else Color.red()
                embed = Embed(title=embed_title, colour=embed_color)
                embed.set_thumbnail(
                    url=member.display_avatar if member else ctx.guild.icon
                )
                for j in record[i : i + 5]:
                    mod = await self.bot.fetch_user(j[2])
                    user = await self.bot.fetch_user(j[0])
                    reason = j[3]
                    warn_id = j[4]
                    points = Moderation(ctx.guild).warnpoints(user)
                    date = f"<t:{j[5]}:F>"
                    if member == None:
                        embed.add_field(
                            name=f"{user} | {user.id}",
                            value=f"**Warn ID:** {warn_id}\n**Reason:** {
                                reason}\n**Date:** {date}\n**Points:** {points}",
                            inline=False,
                        )
                    else:
                        embed.add_field(
                            name=f"**Warn ID:** {warn_id}",
                            value=f"**Moderator:** {mod}\n**Reason:** {
                                reason}\n**Date:** {date}",
                            inline=False,
                        )
                        embed.set_footer(text=f"Total warn points: {points}")
                menu.add_page(embed=embed)
            if len(record) < 5:
                await ctx.send(embed=embed)
                return
            menu.add_button(ViewButton.go_to_first_page())
            menu.add_button(ViewButton.back())
            menu.add_button(ViewButton.next())
            menu.add_button(ViewButton.go_to_last_page())
            await menu.start()

    @listwarns.error
    async def listwarns_error(self, ctx: Context, error: Jeanne.CommandError):
        if isinstance(error, Jeanne.CommandInvokeError) and isinstance(
            error.original, (HTTPException, ValueError, MemberNotFound)
        ):
            embed = Embed()
            embed.description = "Member is not in this server\nPlease try again"
            embed.color = Color.red()
            await ctx.send(embed=embed)

    @Jeanne.command(
        description="Warn a member",
        usage="[MEMBER | MEMBER NAME | MEMBER ID] <-r REASON>",
        extras={"member_perms": "Kick Members"},
    )
    @Jeanne.has_guild_permissions(kick_members=True)
    @Jeanne.check(check_disabled_prefixed_command)
    @Jeanne.check(check_botbanned_prefix)
    async def warn(
        self, ctx: Context, member: Member, *words: str, parser=mod_parser
    ) -> None:
        try:
            parsed_args = parser.parse_known_args(words)[0]
            reason = " ".join(parsed_args.reason)
        except SystemExit:
            await ctx.send(
                embed=Embed(
                    description=f"You are using incorrect arguments for this command",
                    color=Color.red(),
                )
            )
            return
        if ctx.author.top_role.position < member.top_role.position:
            failed = Embed(
                description="{}'s position is higher than you...".format(member),
                color=Color.red(),
            )
            await ctx.send(embed=failed)
            return
        if member.id == ctx.guild.owner.id:
            failed = Embed(
                description="You can't warn the owner of the server...",
                color=Color.red(),
            )
            await ctx.send(embed=failed)
            return
        if member == ctx.author:
            failed = Embed(description="You can't warn yourself", color=Color.red())
            await ctx.send(embed=failed)
            return
        reason = reason[:470]
        warn_id = randint(0, 100000)
        date = round(datetime.now().timestamp())
        await Moderation(ctx.guild).warn_user(
            member, ctx.author.id, reason, warn_id, date
        )
        warn = Embed(title="Member warned", color=0xFF0000)
        warn.add_field(name="Member", value=member, inline=True)
        warn.add_field(name="ID", value=member.id, inline=True)
        warn.add_field(name="Moderator", value=ctx.author, inline=True)
        warn.add_field(name="Reason", value=reason, inline=False)
        warn.add_field(name="Warn ID", value=warn_id, inline=True)
        warn.add_field(name="Date", value="<t:{}:F>".format(date), inline=True)
        warn.set_thumbnail(url=member.display_avatar)
        modlog = Moderation(ctx.guild).get_modlog_channel
        if modlog == None:
            await ctx.send(embed=warn)
            return
        warned = Embed(
            description=f"{member} has been warned. Check {modlog.mention}",
            color=0xFF0000,
        )
        await ctx.send(embed=warned)
        await modlog.send(embed=warn)

    @warn.error
    async def warn_error(self, ctx: Context, error: Jeanne.CommandError):
        if isinstance(error, Jeanne.CommandInvokeError) and isinstance(
            error.original, (HTTPException, ValueError, MemberNotFound)
        ):
            embed = Embed()
            embed.description = "Member is not in this server\nPlease try again"
            embed.color = Color.red()
            await ctx.send(embed=embed)

    @Jeanne.command(
        name="clear-warn",
        description="Revoke a warn by warn ID",
        usage="[MEMBER | MEMBER NAME | MEMBER ID] [WARN ID]",
        extras={"member_perms": "Kick Members"},
    )
    @Jeanne.has_guild_permissions(kick_members=True)
    @Jeanne.check(check_disabled_prefixed_command)
    @Jeanne.check(check_botbanned_prefix)
    async def clearwarn(self, ctx: Context, member: Member, warn_id: int) -> None:
        mod = Moderation(ctx.guild)
        result = mod.check_warn_id(member, warn_id)
        if result == None:
            await ctx.send("Invalid warn ID")
            return
        await mod.revoke_warn(member, warn_id)
        revoked_warn = Embed(
            title="Warn removed",
            description=f"{ctx.author} has revoked warn ID ({warn_id})",
        )
        modlog = Moderation(ctx.guild).get_modlog_channel
        if modlog == None:
            await ctx.send(embed=revoked_warn)
            return
        revoke = Embed(
            description=f"Warn revoked. Check {modlog.mention}", color=0xFF0000
        )
        await modlog.send(embed=revoke)
        await ctx.send(embed=revoked_warn)

    @clearwarn.error
    async def clearwarn_error(self, ctx: Context, error: Jeanne.CommandError):
        if isinstance(error, Jeanne.CommandInvokeError) and isinstance(
            error.original, (HTTPException, ValueError, MemberNotFound)
        ):
            embed = Embed()
            embed.description = "Member is not in this server\nPlease try again"
            embed.color = Color.red()
            await ctx.send(embed=embed)

    @Jeanne.command(
        description="Kick a member out of the server",
        usage="[MEMBER | MEMBER NAME | MEMBER ID] <-r REASON>",
        extras={"bot_perms": "Kick Members", "member_perms": "Kick Members"},
    )
    @Jeanne.has_guild_permissions(kick_members=True)
    @Jeanne.bot_has_guild_permissions(kick_members=True)
    @Jeanne.check(check_disabled_prefixed_command)
    @Jeanne.check(check_botbanned_prefix)
    async def kick(
        self, ctx: Context, member: Member, *words: str, parser=mod_parser
    ) -> None:
        try:
            parsed_args = parser.parse_known_args(words)[0]
            reason = " ".join(parsed_args.reason)
        except SystemExit:
            await ctx.send(
                embed=Embed(
                    description=f"You are missing some arguments or using incorrect arguments for this command",
                    color=Color.red(),
                )
            )
            return
        if member.id == ctx.author.id:
            failed = Embed(description="You can't kick yourself out")
            await ctx.send(embed=failed)
            return
        if ctx.author.top_role.position < member.top_role.position:
            failed = Embed(
                description="{}'s position is higher than you...".format(member),
                color=Color.red(),
            )
            await ctx.send(embed=failed)
            return
        if member.id == ctx.guild.owner.id:
            failed = Embed(
                description="You cannot kick the owner of the server out...",
                color=Color.red(),
            )
            await ctx.send(embed=failed)
            return
        if member == ctx.author:
            failed = Embed(description="You can't kick yourself out")
            await ctx.send(embed=failed)
            return
        reason = reason[:470]
        try:
            kickmsg = Embed(
                description=f"You are kicked from **{
                    ctx.guild.name}** for **{reason}**"
            )
            await member.send(embed=kickmsg)
        except:
            pass
        await ctx.guild.kick(member, reason="{} | {}".format(reason, ctx.author))
        kick = Embed(title="Member Kicked", color=0xFF0000)
        kick.add_field(name="Member", value=member, inline=True)
        kick.add_field(name="ID", value=member.id, inline=True)
        kick.add_field(name="Moderator", value=ctx.author, inline=True)
        kick.add_field(name="Reason", value=reason, inline=True)
        kick.set_thumbnail(url=member.display_avatar)
        modlog = Moderation(ctx.guild).get_modlog_channel
        if modlog == None:
            await ctx.send(embed=kick)
            return
        kicked = Embed(
            description=f"{member} has been kicked. Check {modlog.mention}",
            color=0xFF0000,
        )
        await modlog.send(embed=kick)
        await ctx.send(embed=kicked)

    @kick.error
    async def kick_error(self, ctx: Context, error: Jeanne.CommandError):
        if isinstance(error, Jeanne.CommandInvokeError) and isinstance(
            error.original, (HTTPException, ValueError, MemberNotFound)
        ):
            embed = Embed()
            embed.description = "Member is not in this server\nPlease try again"
            embed.color = Color.red()
            await ctx.send(embed=embed)

    @Jeanne.command(
        description="Bulk delete messages",
        usage="<MEMBER | MEMBER NAME | MEMBER ID | USER ID> <LIMIT>",
        extras={"bot_perms": "Manage Messages", "member_perms": "Manage Messages"},
    )
    @Jeanne.has_guild_permissions(manage_messages=True)
    @Jeanne.bot_has_guild_permissions(manage_messages=True)
    @Jeanne.check(check_disabled_prefixed_command)
    @Jeanne.check(check_botbanned_prefix)
    async def prune(
        self,
        ctx: Context,
        limit: Optional[Jeanne.Range[int, None, 100]] = 100,
        *,
        member: Optional[Member] = None,
    ) -> None:

        limit = limit + 1
        if member:

            def is_member(m: Message):
                return m.author == member

            await ctx.channel.purge(limit=limit, check=is_member)
            return
        await ctx.channel.purge(limit=limit)

    @Jeanne.command(
        name="change-nickname",
        aliases=["nick"],
        description="Change someone's nickname",
        usage="[MEMBER | MEMBER NAME | MEMBER ID] [NICKNAME]",
        extras={"bot_perms": "Manage Nicknames", "member_perms": "Manage Nicknames"},
    )
    @Jeanne.has_guild_permissions(manage_nicknames=True)
    @Jeanne.bot_has_guild_permissions(manage_nicknames=True)
    @Jeanne.check(check_disabled_prefixed_command)
    @Jeanne.check(check_botbanned_prefix)
    async def changenickname(
        self,
        ctx: Context,
        *,
        member: Member,
        nickname: Optional[Jeanne.Range[str, 1, 32]] = None,
    ):
        if (not nickname) or (nickname == None):
            await member.edit(nick=None)
            setnick = Embed(color=0x00FF68)
            setnick.add_field(
                name="Nickname changed",
                value=f"{member}'s nickname has been removed",
                inline=False,
            )
            await ctx.send(embed=setnick)
            return
        if member.nick == None:
            embed = Embed(color=Color.red())
            embed.description = f"{member} has no nickname"
            await ctx.send(embed=embed)
            return
        await member.edit(nick=nickname)
        setnick = Embed(color=0x00FF68)
        setnick.add_field(
            name="Nickname changed",
            value=f"{member}'s nickname is now `{nickname}`",
            inline=False,
        )
        await ctx.send(embed=setnick)

    @Jeanne.command(
        description="Unbans a user",
        usage="[USER ID] <-r REASON>",
        extras={"bot_perms": "Ban Members", "member_perms": "Ban Members"},
    )
    @Jeanne.has_guild_permissions(ban_members=True)
    @Jeanne.bot_has_guild_permissions(ban_members=True)
    async def unban(
        self, ctx: Context, user: User, *words: str, parser=mod_parser
    ) -> None:
        try:
            parsed_args = parser.parse_known_args(words)[0]
            reason = " ".join(parsed_args.reason)
        except SystemExit:
            await ctx.send(
                embed=Embed(
                    description=f"You are missing some arguments or using incorrect arguments for this command",
                    color=Color.red(),
                )
            )
            return
        reason = reason[:470]
        banned = await self.check_banned(ctx, user)
        if banned == None:
            await ctx.guild.unban(user, reason="{} | {}".format(reason, ctx.author))
            unban = Embed(title="User Unbanned", color=0xFF0000)
            unban.add_field(name="Name", value=user, inline=True)
            unban.add_field(name="ID", value=user.id, inline=True)
            unban.add_field(name="Moderator", value=ctx.author, inline=True)
            unban.add_field(name="Reason", value=reason, inline=False)
            unban.set_thumbnail(url=user.display_avatar)
            modlog = Moderation(ctx.guild).get_modlog_channel
            if modlog == None:
                await ctx.send(embed=unban)
                return

            unbanned = Embed(
                description=f"{user} has been unbanned. Check {
                    modlog.mention}",
                color=0xFF0000,
            )
            await ctx.send(embed=unbanned)
            await modlog.send(embed=unban)

    @unban.error
    async def unban_error(self, ctx: Context, error: Jeanne.CommandError):
        if isinstance(error, Jeanne.CommandInvokeError) and isinstance(
            error.original, (HTTPException, ValueError, UserNotFound)
        ):
            embed = Embed()
            embed.description = "Invalid user ID given\nPlease try again"
            embed.color = Color.red()
            await ctx.send(embed=embed)

    @Jeanne.command(
        description="Timeout a member",
        usage="[MEMBER | MEMBER NAME | MEMBER ID] <-r REASON> <-t TIME>",
        extras={"bot_perms": "Manage Nicknames", "member_perms": "Manage Nicknames"},
    )
    @Jeanne.has_guild_permissions(moderate_members=True)
    @Jeanne.bot_has_guild_permissions(moderate_members=True)
    @Jeanne.check(check_disabled_prefixed_command)
    @Jeanne.check(check_botbanned_prefix)
    async def timeout(
        self, ctx: Context, member: Member, *words: str, parser=mod_parser
    ) -> None:
        try:
            parsed_args = parser.parse_known_args(words)[0]
            time = "28d" if parsed_args.time == None else " ".join(parsed_args.time)
            reason = " ".join(parsed_args.reason)

        except SystemExit:
            await ctx.send(
                embed=Embed(
                    description=f"You are missing some arguments or using incorrect arguments for this command",
                    color=Color.red(),
                )
            )
            return

        if member == ctx.author:
            failed = Embed(description="You can't time yourself out")
            await ctx.send(embed=failed)
            return
        reason = reason[:470]
        if parse_timespan(time) > 2505600.0 or time == None:
            time = "28d"
        timed = parse_timespan(time)
        await member.edit(
            timed_out_until=utcnow() + timedelta(seconds=timed),
            reason="{} | {}".format(reason, ctx.author),
        )
        mute = Embed(title="Member Timeout", color=0xFF0000)
        mute.add_field(name="Member", value=member, inline=True)
        mute.add_field(name="ID", value=member.id, inline=True)
        mute.add_field(name="Moderator", value=ctx.author, inline=True)
        mute.add_field(name="Duration", value=time, inline=True)
        mute.add_field(name="Reason", value=reason, inline=False)
        mute.set_thumbnail(url=member.display_avatar)
        modlog = Moderation(ctx.guild).get_modlog_channel
        if modlog == None:
            await ctx.send(embed=mute)
            return

        muted = Embed(
            description=f"{member} has been put on timeout. Check {
                modlog.mention}",
            color=0xFF0000,
        )
        await ctx.send(embed=muted)
        await modlog.send(embed=mute)

    @timeout.error
    async def timeout_error(self, ctx: Context, error: Jeanne.CommandError):
        if isinstance(error, Jeanne.CommandInvokeError) and isinstance(
            error.original, InvalidTimespan
        ):
            embed = Embed()
            embed.description = "Invalid time added. Please try again"
            embed.color = Color.red()
            await ctx.send(embed=embed)
            return
        if isinstance(error, Jeanne.CommandInvokeError) and isinstance(
            error.original, (HTTPException, ValueError, MemberNotFound)
        ):
            embed = Embed()
            embed.description = "Member is not in this server\nPlease try again"
            embed.color = Color.red()
            await ctx.send(embed=embed)

    @Jeanne.command(
        description="Untimeouts a member",
        usage="[MEMBER | MEMBER NAME | MEMBER ID] <-r REASON>",
        extras={"bot_perms": "Moderate Members", "member_perms": "Moderate Members"},
    )
    @Jeanne.has_guild_permissions(moderate_members=True)
    @Jeanne.bot_has_guild_permissions(moderate_members=True)
    @Jeanne.check(check_disabled_prefixed_command)
    @Jeanne.check(check_botbanned_prefix)
    async def untimeout(
        self, ctx: Context, member: Member, *words: str, parser=mod_parser
    ) -> None:
        try:
            parsed_args = parser.parse_known_args(words)[0]
            reason = " ".join(parsed_args.reason)
        except SystemExit:
            await ctx.send(
                embed=Embed(
                    description=f"You are missing some arguments or using incorrect arguments for this command",
                    color=Color.red(),
                )
            )
            return

        reason = reason[:470]
        if member == ctx.author:
            failed = Embed(description="You can't untime yourself out")
            await ctx.send(embed=failed)
            return
        await member.edit(
            timed_out_until=None, reason="{} | {}".format(reason, ctx.author)
        )
        untimeout = Embed(title="Member Untimeout", color=0xFF0000)
        untimeout.add_field(name="Member", value=member, inline=True)
        untimeout.add_field(name="ID", value=member.id, inline=True)
        untimeout.add_field(name="Moderator", value=ctx.author, inline=True)
        untimeout.add_field(name="Reason", value=reason, inline=False)
        untimeout.set_thumbnail(url=member.display_avatar)
        modlog = Moderation(ctx.guild).get_modlog_channel
        if modlog == None:
            await ctx.send(embed=untimeout)
            return

        untimeouted = Embed(
            description=f"{member} has been untimeouted. Check {
                modlog.mention}",
            color=0xFF0000,
        )
        await ctx.send(embed=untimeouted)
        await modlog.send(embed=untimeout)

    @Jeanne.command(
        aliases=["massb", "mb"],
        description="Ban multiple members at once. Split each ID with a space",
        usage="[USER IDS] [-r REASON]",
        extras={"bot_perms": "Ban Members", "member_perms": "Administrator"},
    )
    @Jeanne.cooldown(1, 1800, type=BucketType.guild)
    @Jeanne.has_guild_permissions(administrator=True)
    @Jeanne.bot_has_guild_permissions(ban_members=True)
    @Jeanne.check(check_disabled_prefixed_command)
    @Jeanne.check(check_botbanned_prefix)
    async def massban(self, ctx: Context, *words: str, parser=mod_parser):
        try:
            parsed_args = parser.parse_known_args(words)[0]
            user_ids = (
                None if parsed_args.users == None else " ".join(parsed_args.users)
            )
            reason = " ".join(parsed_args.reason)
        except SystemExit:
            await ctx.send(
                embed=Embed(
                    description="You are missing some arguments or using incorrect arguments for this command",
                    color=Color.red(),
                )
            )
            return
        if reason == "Unspecified":
            await ctx.send(
                embed=Embed(
                    description="You didn't add the reason for the massban. Please try again later",
                    color=Color.red(),
                )
            )
            await ctx.send(embed=embed)
            return
        if user_ids == None:
            await ctx.send(
                embed=Embed(
                    description="You didn't add any User IDs\nPlease try again later",
                    color=Color.red(),
                )
            )
        ids = user_ids.split()[:25]
        if len(ids) < 5:
            embed = Embed(
                description=f"There are too few IDs. Please add more and try again after <t:{round((datetime.now() + timedelta(minutes=30)).timestamp())}:R>"
            )
            await ctx.send(embed=embed)
            return
        banned_ids = {entry.user.id async for entry in ctx.guild.bans()}
        author_id = ctx.author.id
        guild_owner_id = ctx.guild.owner.id
        to_ban_ids = [
            user_id
            for user_id in ids
            if user_id not in banned_ids
            and user_id != str(author_id)
            and user_id != str(guild_owner_id)
        ]
        if not to_ban_ids:
            embed = Embed(description="No users can be banned.", color=Color.red())
            await ctx.send(embed=embed)
            return
        view = Confirmation(ctx.author)
        alert = Embed(
            title="Disclaimer",
            description="The developer is **NOT** responsible in any way or form if you mess up, even if it was misused.\n\nDo you want to proceed?",
            color=Color.red(),
        )
        m = await ctx.send(embed=alert, view=view)
        await view.wait()
        if view.value == True:
            em = Embed(
                description="Banning users now <a:loading:1161038734620373062>",
                color=Color.red(),
            )
            await m.edit(embed=em, view=None)
            ban_count = 0
            failed_ids = []
            banned = []
            for user_id in to_ban_ids:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    try:
                        if (
                            ctx.author.top_role.position
                            <= ctx.guild.get_member(user.id).top_role.position
                        ):
                            continue
                    except:
                        continue
                    await ctx.guild.ban(user, reason=reason)
                    banned.append(f"{user} | `{user.id}`")
                    await asyncio.sleep(0.25)
                    ban_count += 1
                except Exception:
                    failed_ids.append(user_id)
                    continue
            if ban_count > 0:
                embed = Embed(
                    title="List of banned users",
                    color=Color.red(),
                )
                embed.description = "\n".join(banned)
                embed.add_field(name="Reason", value=reason, inline=False)
                if failed_ids:
                    embed.add_field(
                        name="Failed to ban",
                        value="\n".join(failed_ids),
                        inline=False,
                    )
            else:
                embed = Embed(description="No users were banned.", color=Color.red())
            modlog = Moderation(ctx.guild).get_modlog_channel
            if modlog == None:
                await m.edit(embed=embed)
                return
            await m.edit(
                embed=Embed(
                    description=f"Successfully banned {ban_count} user(s). Check {
                        modlog.mention}",
                    color=Color.red(),
                )
            )
            await modlog.send(embed=embed)
        elif (view.value == False) or (view.value == None):
            cancelled = Embed(description="Massban cancelled", color=Color.red())
            await m.edit(embed=cancelled, view=None)

    @massban.error
    async def massban_error(self, ctx: Context, error: Jeanne.CommandError):
        if isinstance(error, Jeanne.CommandOnCooldown):
            reset_hour_time = datetime.now() + timedelta(seconds=error.retry_after)
            reset_hour = round(reset_hour_time.timestamp())
            cooldown = Embed(
                description=f"A massban command was already used here in this server.\nTry again after <t:{reset_hour}:R>",
                color=0xFF0000,
            )
            await ctx.send(embed=cooldown)

    @Jeanne.command(
        aliases=["massub", "mub"],
        description="Unban multiple members at once. Split each ID with a space",
        usage="[USER IDS] [-r REASON]",
        extras={"bot_perms": "Ban Members", "member_perms": "Administrator"},
    )
    @Jeanne.cooldown(1, 1800, type=BucketType.guild)
    @Jeanne.bot_has_guild_permissions(ban_members=True)
    @Jeanne.has_guild_permissions(administrator=True)
    @Jeanne.check(check_disabled_prefixed_command)
    @Jeanne.check(check_botbanned_prefix)
    async def massunban(self, ctx: Context, *words: str, parser=mod_parser):
        try:
            parsed_args = parser.parse_known_args(words)[0]
            user_ids = (
                None if parsed_args.users == None else " ".join(parsed_args.users)
            )
            reason = " ".join(parsed_args.reason)
        except SystemExit:
            await ctx.send(
                embed=Embed(
                    description=f"You are missing some arguments or using incorrect arguments for this command",
                    color=Color.red(),
                )
            )
            return
        if user_ids == None:
            await ctx.send(
                embed=Embed(
                    description="You didn't add any User IDs\nPlease try again later",
                    color=Color.red(),
                )
            )
            return
        if reason == "Unspecified":
            await ctx.send(
                embed=Embed(
                    description="You didn't add the reason for the massunban. Please try again later",
                    color=Color.red(),
                )
            )
            await ctx.send(embed=embed)
            return
        ids = user_ids.split()[:25]
        if len(ids) < 5:
            embed = Embed(
                description=f"There are too few IDs. Please add more and try again after <t:{round((datetime.now() + timedelta(minutes=30)).timestamp())}:R>"
            )
            await ctx.send(embed=embed)
            return
        banned_ids = {entry.user.id async for entry in ctx.guild.bans()}
        author_id = ctx.author.id
        guild_owner_id = ctx.guild.owner.id
        to_unban_ids = [
            user_id
            for user_id in ids
            if user_id not in banned_ids
            and user_id != str(author_id)
            and user_id != str(guild_owner_id)
        ]
        if not to_unban_ids:
            embed = Embed(description="No users can be unbanned.", color=Color.red())
            await ctx.send(embed=embed)
            return
        view = Confirmation(ctx.author)
        alert = Embed(
            title="BEWARE",
            description="The developer is **NOT** responsible in any way or form if you mess up, even if it was misused.\n\nDo you want to proceed?",
            color=Color.red(),
        )
        m = await ctx.send(embed=alert, view=view)
        await view.wait()
        if view.value == True:
            em = Embed(
                description="Unbanning users now <a:loading:1161038734620373062>",
                color=Color.red(),
            )
            await m.edit(embed=em, view=None)
            unban_count = 0
            failed_ids = []
            unbanned = []
            for user_id in to_unban_ids:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    await ctx.guild.unban(user, reason=reason)
                    unbanned.append(f"{user} | `{user.id}`")
                    await asyncio.sleep(0.5)
                    unban_count += 1
                except Exception:
                    failed_ids.append(user_id)
                    continue
            if unban_count > 0:
                embed = Embed(
                    title="List of unbanned users",
                    color=Color.red(),
                )
                embed.description = "\n".join(unbanned)
                embed.add_field(name="Reason", value=reason, inline=False)
                if failed_ids:
                    embed.add_field(
                        name="Failed to unban",
                        value="\n".join(failed_ids),
                        inline=False,
                    )
            else:
                embed = Embed(description="No users were unbanned.", color=Color.red())
            modlog = Moderation(ctx.guild).get_modlog_channel
            if modlog == None:
                await m.edit(embed=embed)
                return
            await m.edit(
                embed=Embed(
                    description=f"Successfully unbanned {unban_count} user(s). Check {
                        modlog.mention}",
                    color=Color.red(),
                )
            )
            await modlog.send(embed=embed)
        elif (view.value == False) or (view.value == None):
            cancelled = Embed(description="Massunban cancelled", color=Color.red())
            await m.edit(embed=cancelled, view=None)

    @massunban.error
    async def massunban_error(self, ctx: Context, error: Jeanne.CommandError):
        if isinstance(error, Jeanne.CommandOnCooldown):
            reset_hour_time = datetime.now() + timedelta(seconds=error.retry_after)
            reset_hour = round(reset_hour_time.timestamp())
            cooldown = Embed(
                description=f"A massunban command was already used here in this server.\nTry again after <t:{reset_hour}:R>",
                color=0xFF0000,
            )
            await ctx.send(embed=cooldown)


async def setup(bot: Bot):
    await bot.add_cog(ModPrefix(bot))
