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
# AUTOCOMPLETE
# =========================
async def rr_autocomplete(interaction, current):
    return [
        app_commands.Choice(name=k, value=k)
        for k in data["roles"]
        if current.lower() in k.lower()
    ][:25]

async def embed_autocomplete(interaction, current):
    return [
        app_commands.Choice(name=k, value=k)
        for k in data["embeds"]
        if current.lower() in k.lower()
    ][:25]

# =========================
# MODAL
# =========================
class FullModal(discord.ui.Modal):
    def __init__(self, title_name, defaults=None):
        super().__init__(title=title_name)
        defaults = defaults or {}

        self.title_input = discord.ui.TextInput(label="Title", default=defaults.get("title", ""), required=False)

        self.description = discord.ui.TextInput(
            label="Description",
            style=discord.TextStyle.paragraph,
            default=defaults.get("description", ""),
            required=False
        )

        self.color = discord.ui.TextInput(label="Color (#FFFFFF)", default=defaults.get("color", "#FFFFFF"), required=False)
        self.image = discord.ui.TextInput(label="Image URL", default=defaults.get("image", ""), required=False)
        self.thumbnail = discord.ui.TextInput(label="Thumbnail URL", default=defaults.get("thumbnail", ""), required=False)

        self.add_item(self.title_input)
        self.add_item(self.description)
        self.add_item(self.color)
        self.add_item(self.image)
        self.add_item(self.thumbnail)

    async def on_submit(self, interaction: discord.Interaction):
        self.value = {
            "title": self.title_input.value,
            "description": self.description.value,
            "color": self.color.value,
            "image": self.image.value,
            "thumbnail": self.thumbnail.value
        }
        await interaction.response.defer()

# =========================
# READY + FORCE SYNC
# =========================
    GUILD_ID = 1448390622888198278  # replace this

    @bot.event
    async def on_ready():
        try:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild")
        except Exception as e:
            print(e)

        print("Bot Ready")

# =========================
# REACTION ROLES
# =========================
@bot.tree.command(name="reactionroles_create")
async def rr_create(
    interaction: discord.Interaction,
    name: str,
    emoji1: str, role1: discord.Role,
    emoji2: str = None, role2: discord.Role = None,
    emoji3: str = None, role3: discord.Role = None,
    emoji4: str = None, role4: discord.Role = None,
    emoji5: str = None, role5: discord.Role = None,
):

    modal = FullModal("Create Reaction Roles")
    await interaction.response.send_modal(modal)
    await modal.wait()

    v = modal.value

    roles = {}
    for e, r in [(emoji1, role1),(emoji2, role2),(emoji3, role3),(emoji4, role4),(emoji5, role5)]:
        if e and r:
            roles[e] = r.id

    data["roles"][name] = {
        "title": v["title"],
        "description": v["description"],
        "color": int(v["color"].replace("#",""),16) if v["color"] else 0xFFFFFF,
        "image": v["image"],
        "thumbnail": v["thumbnail"],
        "roles": roles,
        "messages": []
    }

    save(data)
    await interaction.followup.send(f"✅ Created `{name}`", ephemeral=True)


@bot.tree.command(name="reactionroles_send")
@app_commands.autocomplete(name=rr_autocomplete)
async def rr_send(interaction: discord.Interaction, name: str, channel: discord.TextChannel):

    cfg = data["roles"][name]

    embed = discord.Embed(title=cfg["title"], description=cfg["description"], color=cfg["color"])
    if cfg["image"]:
        embed.set_image(url=cfg["image"])
    if cfg["thumbnail"]:
        embed.set_thumbnail(url=cfg["thumbnail"])

    msg = await channel.send(embed=embed)

    for emoji in cfg["roles"]:
        await msg.add_reaction(emoji)

    cfg["messages"].append({"channel": channel.id, "message": msg.id})
    save(data)

    await interaction.response.send_message("✅ Sent", ephemeral=True)


@bot.tree.command(name="reactionroles_edit")
@app_commands.autocomplete(name=rr_autocomplete)
async def rr_edit(interaction: discord.Interaction, name: str):

    cfg = data["roles"][name]

    modal = FullModal("Edit Reaction Roles", {
        "title": cfg["title"],
        "description": cfg["description"],
        "color": f"#{cfg['color']:06x}",
        "image": cfg["image"],
        "thumbnail": cfg["thumbnail"]
    })

    await interaction.response.send_modal(modal)
    await modal.wait()

    v = modal.value

    cfg["title"] = v["title"]
    cfg["description"] = v["description"]
    cfg["image"] = v["image"]
    cfg["thumbnail"] = v["thumbnail"]
    if v["color"]:
        cfg["color"] = int(v["color"].replace("#",""),16)

    for m in cfg["messages"]:
        try:
            ch = bot.get_channel(m["channel"])
            msg = await ch.fetch_message(m["message"])

            embed = discord.Embed(title=cfg["title"], description=cfg["description"], color=cfg["color"])
            if cfg["image"]:
                embed.set_image(url=cfg["image"])
            if cfg["thumbnail"]:
                embed.set_thumbnail(url=cfg["thumbnail"])

            await msg.edit(embed=embed)
            await msg.clear_reactions()
            for emoji in cfg["roles"]:
                await msg.add_reaction(emoji)
        except:
            pass

    save(data)
    await interaction.followup.send("✅ Updated", ephemeral=True)


# 🔥 EDIT ROLES COMMAND (NEW)
@bot.tree.command(name="reactionroles_edit_roles")
@app_commands.autocomplete(name=rr_autocomplete)
async def rr_edit_roles(
    interaction: discord.Interaction,
    name: str,
    emoji1: str, role1: discord.Role,
    emoji2: str = None, role2: discord.Role = None,
    emoji3: str = None, role3: discord.Role = None,
    emoji4: str = None, role4: discord.Role = None,
    emoji5: str = None, role5: discord.Role = None,
):

    cfg = data["roles"][name]

    new_roles = {}
    for e, r in [(emoji1, role1),(emoji2, role2),(emoji3, role3),(emoji4, role4),(emoji5, role5)]:
        if e and r:
            new_roles[e] = r.id

    cfg["roles"] = new_roles

    for m in cfg["messages"]:
        try:
            ch = bot.get_channel(m["channel"])
            msg = await ch.fetch_message(m["message"])

            await msg.clear_reactions()
            for emoji in new_roles:
                await msg.add_reaction(emoji)
        except:
            pass

    save(data)
    await interaction.response.send_message("✅ Roles updated", ephemeral=True)


@bot.tree.command(name="reactionroles_delete")
@app_commands.autocomplete(name=rr_autocomplete)
async def rr_delete(interaction: discord.Interaction, name: str):

    for m in data["roles"][name]["messages"]:
        try:
            ch = bot.get_channel(m["channel"])
            msg = await ch.fetch_message(m["message"])
            await msg.delete()
        except:
            pass

    del data["roles"][name]
    save(data)

    await interaction.response.send_message(f"🗑️ Deleted `{name}`", ephemeral=True)


@bot.tree.command(name="reactionroles_list")
async def rr_list(interaction: discord.Interaction):
    await interaction.response.send_message("\n".join(data["roles"].keys()) or "None", ephemeral=True)

# =========================
# REACTION EVENTS
# =========================
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    for cfg in data["roles"].values():
        for m in cfg["messages"]:
            if m["message"] == payload.message_id:
                guild = bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)

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

# =========================
# RUN
# =========================
bot.run(os.getenv("TOKEN"))
