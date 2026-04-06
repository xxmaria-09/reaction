import discord
from discord.ext import commands
from discord import app_commands
import json, os

intents = discord.Intents.default()
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

FILE = "data.json"

def load():
    if not os.path.exists(FILE):
        return {"roles": {}, "embeds": {}}
    with open(FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load()

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

# =========================
# REACTION ROLE CREATE
# =========================
@bot.tree.command(name="reactionroles_create")
async def rr_create(interaction: discord.Interaction, name: str, title: str, description: str,
                    emoji1: str, role1: discord.Role,
                    emoji2: str = None, role2: discord.Role = None,
                    emoji3: str = None, role3: discord.Role = None,
                    emoji4: str = None, role4: discord.Role = None,
                    emoji5: str = None, role5: discord.Role = None,
                    image: str = None, thumbnail: str = None, color: str = None):

    roles = {}
    for e, r in [(emoji1, role1),(emoji2, role2),(emoji3, role3),(emoji4, role4),(emoji5, role5)]:
        if e and r:
            roles[e] = r.id

    data["roles"][name] = {
        "title": title,
        "description": description,
        "roles": roles,
        "image": image,
        "thumbnail": thumbnail,
        "color": int(color.replace("#",""),16) if color else 0xFFFFFF,
        "messages": []
    }

    save(data)
    await interaction.response.send_message(f"✅ Created `{name}`", ephemeral=True)

# =========================
# SEND RR
# =========================
@bot.tree.command(name="reactionroles_send")
async def rr_send(interaction: discord.Interaction, name: str, channel: discord.TextChannel):

    if name not in data["roles"]:
        return await interaction.response.send_message("❌ Not found", ephemeral=True)

    cfg = data["roles"][name]

    embed = discord.Embed(title=cfg["title"], description=cfg["description"], color=cfg["color"])
    if cfg["image"]: embed.set_image(url=cfg["image"])
    if cfg["thumbnail"]: embed.set_thumbnail(url=cfg["thumbnail"])

    msg = await channel.send(embed=embed)

    for e in cfg["roles"]:
        await msg.add_reaction(e)

    cfg["messages"].append({"channel": channel.id, "message": msg.id})
    save(data)

    await interaction.response.send_message("✅ Sent!", ephemeral=True)

# =========================
# EDIT RR
# =========================
@bot.tree.command(name="reactionroles_edit")
async def rr_edit(interaction: discord.Interaction, name: str,
                  title: str=None, description: str=None,
                  emoji1: str=None, role1: discord.Role=None,
                  emoji2: str=None, role2: discord.Role=None,
                  emoji3: str=None, role3: discord.Role=None,
                  emoji4: str=None, role4: discord.Role=None,
                  emoji5: str=None, role5: discord.Role=None,
                  image: str=None, thumbnail: str=None, color: str=None):

    if name not in data["roles"]:
        return await interaction.response.send_message("❌ Not found", ephemeral=True)

    cfg = data["roles"][name]

    if title: cfg["title"] = title
    if description: cfg["description"] = description
    if image is not None: cfg["image"] = image
    if thumbnail is not None: cfg["thumbnail"] = thumbnail
    if color: cfg["color"] = int(color.replace("#",""),16)

    new_roles = {}
    for e, r in [(emoji1, role1),(emoji2, role2),(emoji3, role3),(emoji4, role4),(emoji5, role5)]:
        if e and r:
            new_roles[e] = r.id
    if new_roles:
        cfg["roles"] = new_roles

    # update all messages of THIS config only
    for m in cfg["messages"]:
        try:
            ch = bot.get_channel(m["channel"])
            msg = await ch.fetch_message(m["message"])

            embed = discord.Embed(title=cfg["title"], description=cfg["description"], color=cfg["color"])
            if cfg["image"]: embed.set_image(url=cfg["image"])
            if cfg["thumbnail"]: embed.set_thumbnail(url=cfg["thumbnail"])

            await msg.edit(embed=embed)
            await msg.clear_reactions()
            for e in cfg["roles"]:
                await msg.add_reaction(e)
        except:
            pass

    save(data)
    await interaction.response.send_message("✅ Updated!", ephemeral=True)

# =========================
# DELETE RR
# =========================
@bot.tree.command(name="reactionroles_delete")
async def rr_delete(interaction: discord.Interaction, name: str):

    if name not in data["roles"]:
        return await interaction.response.send_message("❌ Not found", ephemeral=True)

    for m in data["roles"][name]["messages"]:
        try:
            ch = bot.get_channel(m["channel"])
            msg = await ch.fetch_message(m["message"])
            await msg.delete()
        except:
            pass

    del data["roles"][name]
    save(data)

    await interaction.response.send_message("🗑️ Deleted", ephemeral=True)

# =========================
# LIST RR
# =========================
@bot.tree.command(name="reactionroles_list")
async def rr_list(interaction: discord.Interaction):
    names = list(data["roles"].keys())
    await interaction.response.send_message("\n".join(names) if names else "None", ephemeral=True)

# =========================
# EMBED SYSTEM
# =========================
@bot.tree.command(name="embed_create")
async def embed_create(interaction: discord.Interaction, name: str, title: str, description: str,
                       image: str=None, thumbnail: str=None, color: str=None):

    data["embeds"][name] = {
        "title": title,
        "description": description,
        "image": image,
        "thumbnail": thumbnail,
        "color": int(color.replace("#",""),16) if color else 0xFFFFFF,
        "messages": []
    }

    save(data)
    await interaction.response.send_message(f"✅ Created embed `{name}`", ephemeral=True)

@bot.tree.command(name="embed_send")
async def embed_send(interaction: discord.Interaction, name: str, channel: discord.TextChannel):

    if name not in data["embeds"]:
        return await interaction.response.send_message("❌ Not found", ephemeral=True)

    cfg = data["embeds"][name]

    embed = discord.Embed(title=cfg["title"], description=cfg["description"], color=cfg["color"])
    if cfg["image"]: embed.set_image(url=cfg["image"])
    if cfg["thumbnail"]: embed.set_thumbnail(url=cfg["thumbnail"])

    msg = await channel.send(embed=embed)

    cfg["messages"].append({"channel": channel.id, "message": msg.id})
    save(data)

    await interaction.response.send_message("✅ Sent!", ephemeral=True)

@bot.tree.command(name="embed_edit")
async def embed_edit(interaction: discord.Interaction, name: str,
                     title: str=None, description: str=None,
                     image: str=None, thumbnail: str=None, color: str=None):

    if name not in data["embeds"]:
        return await interaction.response.send_message("❌ Not found", ephemeral=True)

    cfg = data["embeds"][name]

    if title: cfg["title"] = title
    if description: cfg["description"] = description
    if image is not None: cfg["image"] = image
    if thumbnail is not None: cfg["thumbnail"] = thumbnail
    if color: cfg["color"] = int(color.replace("#",""),16)

    for m in cfg["messages"]:
        try:
            ch = bot.get_channel(m["channel"])
            msg = await ch.fetch_message(m["message"])

            embed = discord.Embed(title=cfg["title"], description=cfg["description"], color=cfg["color"])
            if cfg["image"]: embed.set_image(url=cfg["image"])
            if cfg["thumbnail"]: embed.set_thumbnail(url=cfg["thumbnail"])

            await msg.edit(embed=embed)
        except:
            pass

    save(data)
    await interaction.response.send_message("✅ Updated!", ephemeral=True)

@bot.tree.command(name="embed_delete")
async def embed_delete(interaction: discord.Interaction, name: str):

    if name not in data["embeds"]:
        return await interaction.response.send_message("❌ Not found", ephemeral=True)

    for m in data["embeds"][name]["messages"]:
        try:
            ch = bot.get_channel(m["channel"])
            msg = await ch.fetch_message(m["message"])
            await msg.delete()
        except:
            pass

    del data["embeds"][name]
    save(data)

    await interaction.response.send_message("🗑️ Deleted", ephemeral=True)

@bot.tree.command(name="embed_list")
async def embed_list(interaction: discord.Interaction):
    names = list(data["embeds"].keys())
    await interaction.response.send_message("\n".join(names) if names else "None", ephemeral=True)

# =========================
# REACTIONS
# =========================
@bot.event
async def on_raw_reaction_add(payload):
    for cfg in data["roles"].values():
        for m in cfg["messages"]:
            if m["message"] == payload.message_id:
                guild = bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                if member.bot: return
                role_id = cfg["roles"].get(str(payload.emoji))
                if role_id:
                    await member.add_roles(guild.get_role(role_id))

@bot.event
async def on_raw_reaction_remove(payload):
    for cfg in data["roles"].values():
        for m in cfg["messages"]:
            if m["message"] == payload.message_id:
                guild = bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                role_id = cfg["roles"].get(str(payload.emoji))
                if role_id:
                    await member.remove_roles(guild.get_role(role_id))

import os
bot.run(os.getenv("TOKEN"))
