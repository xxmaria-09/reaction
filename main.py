import discord
from discord.ext import commands
from discord import app_commands
import json
import os

intents = discord.Intents.default()
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "reaction_roles.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


data = load_data()


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


# =========================
# CREATE CONFIG
# =========================
@bot.tree.command(name="reactionroles_create")
async def create_rr(
    interaction: discord.Interaction,
    name: str,
    title: str,
    description: str,
    emoji1: str,
    role1: discord.Role,
    emoji2: str = None,
    role2: discord.Role = None,
    emoji3: str = None,
    role3: discord.Role = None,
    emoji4: str = None,
    role4: discord.Role = None,
    emoji5: str = None,
    role5: discord.Role = None,
    image: str = None,
    thumbnail: str = None
):
    roles_data = {}
    pairs = [(emoji1, role1), (emoji2, role2), (emoji3, role3), (emoji4, role4), (emoji5, role5)]

    for emoji, role in pairs:
        if emoji and role:
            roles_data[emoji] = role.id

    data[name] = {
        "title": title,
        "description": description,
        "roles": roles_data,
        "image": image,
        "thumbnail": thumbnail
    }

    save_data(data)
    await interaction.response.send_message(f"✅ Created `{name}`", ephemeral=True)


# =========================
# SEND CONFIG
# =========================
@bot.tree.command(name="reactionroles_send")
async def send_rr(interaction: discord.Interaction, name: str, channel: discord.TextChannel):

    if name not in data:
        await interaction.response.send_message("❌ Config not found", ephemeral=True)
        return

    cfg = data[name]

    embed = discord.Embed(
        title=cfg["title"],
        description=cfg["description"],
        color=0xFFFFFF
    )

    if cfg.get("image"):
        embed.set_image(url=cfg["image"])
    if cfg.get("thumbnail"):
        embed.set_thumbnail(url=cfg["thumbnail"])

    msg = await channel.send(embed=embed)

    for emoji in cfg["roles"]:
        await msg.add_reaction(emoji)

    data[name]["message_id"] = msg.id
    data[name]["channel_id"] = channel.id
    save_data(data)

    await interaction.response.send_message("✅ Sent!", ephemeral=True)


# =========================
# EDIT CONFIG
# =========================
@bot.tree.command(name="reactionroles_edit")
async def edit_rr(
    interaction: discord.Interaction,
    name: str,
    title: str = None,
    description: str = None,
    emoji1: str = None,
    role1: discord.Role = None,
    emoji2: str = None,
    role2: discord.Role = None,
    emoji3: str = None,
    role3: discord.Role = None,
    emoji4: str = None,
    role4: discord.Role = None,
    emoji5: str = None,
    role5: discord.Role = None,
    image: str = None,
    thumbnail: str = None
):

    if name not in data:
        await interaction.response.send_message("❌ Config not found", ephemeral=True)
        return

    if title:
        data[name]["title"] = title
    if description:
        data[name]["description"] = description
    if image is not None:
        data[name]["image"] = image
    if thumbnail is not None:
        data[name]["thumbnail"] = thumbnail

    # update roles if provided
    pairs = [(emoji1, role1), (emoji2, role2), (emoji3, role3), (emoji4, role4), (emoji5, role5)]
    new_roles = {}
    for emoji, role in pairs:
        if emoji and role:
            new_roles[emoji] = role.id
    if new_roles:
        data[name]["roles"] = new_roles

    save_data(data)

    # Auto-update message if sent
    if "message_id" in data[name]:
        try:
            channel = bot.get_channel(data[name]["channel_id"])
            msg = await channel.fetch_message(data[name]["message_id"])

            embed = discord.Embed(
                title=data[name]["title"],
                description=data[name]["description"],
                color=0xFFFFFF
            )

            if data[name].get("image"):
                embed.set_image(url=data[name]["image"])
            if data[name].get("thumbnail"):
                embed.set_thumbnail(url=data[name]["thumbnail"])

            await msg.edit(embed=embed)
            await msg.clear_reactions()
            for emoji in data[name]["roles"]:
                await msg.add_reaction(emoji)
        except:
            pass

    await interaction.response.send_message("✅ Updated!", ephemeral=True)


# =========================
# DELETE CONFIG
# =========================
@bot.tree.command(name="reactionroles_delete")
async def delete_rr(interaction: discord.Interaction, name: str):

    if name not in data:
        await interaction.response.send_message("❌ Not found", ephemeral=True)
        return

    if "message_id" in data[name]:
        try:
            channel = bot.get_channel(data[name]["channel_id"])
            msg = await channel.fetch_message(data[name]["message_id"])
            await msg.delete()
        except:
            pass

    del data[name]
    save_data(data)

    await interaction.response.send_message("🗑️ Deleted!", ephemeral=True)


# =========================
# LIST CONFIGS
# =========================
@bot.tree.command(name="reactionroles_list")
async def list_rr(interaction: discord.Interaction):

    if not data:
        await interaction.response.send_message("No configs yet.", ephemeral=True)
        return

    msg = "**Your Reaction Role Systems:**\n"
    for name in data:
        msg += f"\n• {name}"

    await interaction.response.send_message(msg, ephemeral=True)


# =========================
# REACTION HANDLING
# =========================
@bot.event
async def on_raw_reaction_add(payload):
    for cfg in data.values():
        if cfg.get("message_id") == payload.message_id:
            guild = bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            if member.bot:
                return
            role_id = cfg["roles"].get(str(payload.emoji))
            if role_id:
                await member.add_roles(guild.get_role(role_id))


@bot.event
async def on_raw_reaction_remove(payload):
    for cfg in data.values():
        if cfg.get("message_id") == payload.message_id:
            guild = bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role_id = cfg["roles"].get(str(payload.emoji))
            if role_id:
                await member.remove_roles(guild.get_role(role_id))


bot.run("YOUR_BOT_TOKEN")
