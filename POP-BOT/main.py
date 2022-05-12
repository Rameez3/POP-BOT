#Imports
import discord
from discord_ui import UI, SlashOption, StageChannel
from discord.utils import get
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions
import os
import asyncio
from discord import Member
from discord.ext.commands import has_permissions, MissingPermissions
import random
from dotenv import load_dotenv



#Loading the dotenv environment variables for the discord token
load_dotenv()

#Setting the intents for the discord bot to give its proper permissions and set the command prefix to !
intents = discord.Intents.default()
intents.members = True
# client = discord.Client(intents=intents)
client = commands.Bot(command_prefix='!')
"""
Setting the appropriate array and dictionary to keep track of who is active on the server
active_list: Keep track of who is active based on a certain amount of sentences they send
sentence_dict_list: Keeps track of how many sentences each person has said so that when they reach a certain threshold, they wil be added to the active list and be immune from the purge

"""

active_list = []
sentence_dict_list = {}


# A simple hello command to test the replying mechanism for the bot
@client.command()
async def hello(ctx):
    await ctx.reply('Hello!', mention_author=True)


# A simple add role command to test the permissions of the bot (Possibly removing this)
@client.command()
@commands.has_role("Hype"
                   )  # This must be exactly the name of the appropriate role
async def addrole(ctx):
    member = ctx.message.author
    role = get(member.roles, name="Test")
    await client.add_roles(member, role)


# This function will assign the Mute Role to the user where they will be unable to talk on the server for a set amount of time. (Possibly removing this too/ Further refine this function)
@client.command()
async def mutemember(ctx, member: discord.Member = None, reason=None):
    guild = ctx.guild
    Muted = discord.utils.get(guild.roles, name="Muted")

    if not Muted:
        Muted = await guild.create_role(name="Muted")
        for channel in guild.channels:
            await channel.set_permissions(Muted,
                                          speak=False,
                                          send_messages=False,
                                          read_message_history=True,
                                          read_messages=False)
            await member.add_roles(Muted, reason=reason)
            await ctx.send(
                f"{member.mention} was muted by {ctx.author.mention}")


@mutemember.error  # <- the name of the command + .error
async def mutemember_member_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("The member does not exist!")


#Muting command where a member who only has the permission of muting members can use. This will mute everyone in the vc
@client.command()
@commands.has_permissions(mute_members=True)
async def vcmute(ctx):
    vc = ctx.author.voice.channel
    for member in vc.members:
        await member.edit(mute=True)


#This will undo the previous function by unmuting all members in the vc
@client.command()
@commands.has_permissions(mute_members=True)
async def vcunmute(ctx):
    vc = ctx.author.voice.channel
    for member in vc.members:
        await member.edit(mute=False)


#This command is only available for those who have the permission to kick members (Admins). The admin can also enter a reason for the kick and can kick anyone they wish except for the owner and bots
@client.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    if reason == None:
        reason = "no reason provided"
    await ctx.guild.kick(member)
    await ctx.send(f'User {member.mention} has been kicked for {reason}')


#These wil handle an error if it arises


@kick.error
async def kick_member_error(ctx, error):
    if isinstance(error, discord.MemberNotFound):
        await ctx.reply(
            "Member is not found in the server! (Maybe you mispelled it?)",
            mention_author=True)


@kick.error
async def member_argument_missing(ctx, error):
    if isinstance(error, discord.MissingRequiredArgument):
        await ctx.reply("Please enter a member name", mention_author=True)


@kick.error
async def member_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.reply("Unable to kick member", mention_author=True)


#This command is only available for those who have the permission to ban members (Admins). The admin can also enter a reason for the ban and can ban anyone they wish except for the owner and bots
@client.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    if reason == None:
        reason = "no reason provided"
    await ctx.guild.ban(member)
    await ctx.send(f'User {member.mention} has been kicked for {reason}')


# This function will see how many sentences the user has written from the sentence_dict_list and output the result. If they've never written one a separate message will be sent
@client.command()
async def amiactive(ctx):
    try:
        user_id = ctx.author.id
        await ctx.reply(
            f"You have sent a total of {sentence_dict_list[user_id]} sentence(s)!",
            mention_author=True)

    except:
        await ctx.reply("You've never written a sentence before!",
                        mention_author=True)


"""
The function below will invoke the quiz operation where the contestant will receive a
contestant role and will not be able to see the general chat. Then they will have access
to a separate text channel (quiz) where the quizzer will ask their question to the contestant. 
The question wil also be sent to the general chat where the members can discuss on their 
own accord without the contestant's knowledge. The contestant has a set amount of time and
if they get it right, possibly a role will be assigned to them, and a victory notification will be 
sent into the general chat. The member will then be granted access back into the general chat and the quiz channel
wil be removed from their access.
"""


@client.command()
@commands.has_role("Hype"
                   )  # This must be exactly the name of the appropriate role
async def quiz(ctx, member: discord.Member):

    channel = client.get_channel(966071156207657060)
    global member_occurence
    member_occurence = member

    if (member != ctx.author):
        member_role = get(ctx.guild.roles, name="Member")
        contestant = get(ctx.guild.roles, name="Contestant")
        await member.add_roles(contestant)
        await member.remove_roles(member_role)

        await ctx.reply(
            f"Ok! Now quizzing {member.mention}! {member.mention}, you now have access to the <#966071156207657060> channel and your question will be asked there! Spectators, when the quizzer sends their question, the question will be posted here for you all to discuss about without the contestant's knowledge!"
        )

        await channel.send(
            f"{member.mention}, your question will be asked in here!")

    else:
        await ctx.reply("You cannot quiz yourself!", mention_author=True)


# Handles the error when a member is not found when the quizzer invokes the quiz command
@quiz.error  # <- the name of the command + .error
async def quiz_member_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.reply("The member does not exist!", mention_author=True)


# Followup command for the quizzer to input their question so that it can be sent into general chat
@client.command()
@commands.has_role("Hype")
async def question(ctx, *, message: str):
    general_chat_id = client.get_channel(361640154915405827)
    global question
    question = 0
    if (ctx.channel.id == 966071156207657060):
        await ctx.send(
            f"{member_occurence.mention}, your question is, **{message}**")
        question = 1

        await general_chat_id.send(f"@everyone, the question is, **{message}**"
                                   )

    else:
        await ctx.reply("Please use this command in the quiz channel!",
                        mention_author=True)


# Handles error if someone else other than an admin/quizzer invokes the command
@question.error
async def question_permission_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have permission to execute this command!")


@client.command()
@commands.has_role("Contestant")
async def answer(ctx, *, answer: str):
    if (ctx.channel.id == 966071156207657060 and question == 1):
        await ctx.send(answer)
        print(question)

    else:
        await ctx.send(
            "And error occurred! Either you did not answer in the correct channel or the question hasn't been asked yet!"
        )


# Handles the eror where the user does not put anything after the !answer command
@answer.error
async def missing_argument(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please put your answer after the answer command!")


# Handles the error where the user doesn't have the Contestant Role
@question.error
async def missing_role_answer(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have permission to execute this command!")


class Buttons(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
    @discord.ui.button(label="Button",style=discord.ButtonStyle.gray)
    async def gray_button(self,button:discord.ui.Button,interaction:discord.Interaction):
        await interaction.response.edit_message(content=f"This is an edited button response!")

@client.command()
async def button(ctx):
    await ctx.send("This message has buttons!",view=Buttons())

# Function where the bot keeps track of how many sentences each user has said throughout their lifetime. If the user has said more than 7 sentences, they will be added to the activre list and be immune from banning/kicking due to inactivity.
@client.event
async def on_message(ctx):
    user_id = ctx.author.id
    words = len(ctx.content.split(" "))
    if ctx.author == client.user:
        return
    if ctx.author.bot: return

    if words > 7:
        if user_id not in sentence_dict_list:
            sentence_dict_list[user_id] = 1

        else:
            sentence_dict_list[user_id] += 1
            print(
                f"{user_id} has sent a total of {sentence_dict_list[user_id]} sentence(s)!"
            )
            print(sentence_dict_list)

        if sentence_dict_list[user_id] == 10:
            active_list.append(user_id)
            await ctx.reply(
                "You met the requirements to have the active role! Thanks for contributing to the server!",
                mention_author=True)
            active = get(ctx.guild.roles, name="Active")

            await ctx.author.add_roles(active)

    await client.process_commands(ctx)


#Retrieves OS Token from the .env file
client.run(os.getenv("DISCORD_TOKEN"))
