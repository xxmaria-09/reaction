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
    return [app_commands.Choice(name=k, value=k) for k in data["roles"] if current.lower() in k.lower()][:25]

async def embed_autocomplete(interaction, current):
    return [app_commands.Choice(name=k, value=k) for k in data["embeds"] if current.lower() in k.lower()][:25]

# =========================
# FULL MODAL
# =========================
class FullModal(discord.ui.Modal):
    def __init__(self, title_name, defaults=None):
        super().__init__(title=title_name)
        defaults = defaults or {}

        self.title_input = discord.ui.TextInput(
            label="Title",
            default=defaults.get("title", ""),
            required=False
        )

        self.description = discord.ui.TextInput(
            label="Description",
            style=discord.TextStyle.paragraph,
            default=defaults.get("description", ""),
            required=False
        )

        self.color = discord.ui.TextInput(
            label="Color (#FFFFFF)",
            default=defaults.get("color", "#FFFFFF"),
            required=False
        )

        self.image = discord.ui.TextInput(
            label="Image URL",
            default=defaults.get("image", ""),
            required=False
        )

        self.thumbnail = discord.ui.TextInput(
            label="Thumbnail URL",
            default=defaults.get("thumbnail", ""),
            required=False
        )

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
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot Ready")

# =========================
# REACTION ROLES CREATE
# =========================
@bot.tree.command(name="reactionroles_create")
async def rr_create(interaction: discord.Interaction, name: str):

    modal = FullModal("Create Reaction Roles")
    await interaction.response.send_modal(modal)
    await modal.wait()

    v = modal.value

    data["roles"][name] = {
        "title": v["title"],
        "description": v["description"],
        "color": int(v["color"].replace("#",""),16) if v["color"] else 0xFFFFFF,
        "image": v["image"],
        "thumbnail": v["thumbnail"],
        "roles": {},
        "messages": []
    }

    save(data)
    await interaction.followup.send(f"✅ Created `{name}`", ephemeral=True)

# =========================
# REACTION ROLES SEND
# =========================
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

    cfg["messages"].append({"channel": channel.id, "message": msg.id})
    save(data)

    await interaction.response.send_message("✅ Sent", ephemeral=True)

# =========================
# REACTION ROLES EDIT
# =========================
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
        except:
            pass

    save(data)
    await interaction.followup.send("✅ Updated", ephemeral=True)

# =========================
# EMBED CREATE
# =========================
@bot.tree.command(name="embed_create")
async def embed_create(interaction: discord.Interaction, name: str):

    modal = FullModal("Create Embed")
    await interaction.response.send_modal(modal)
    await modal.wait()

    v = modal.value

    data["embeds"][name] = {
        "title": v["title"],
        "description": v["description"],
        "color": int(v["color"].replace("#",""),16) if v["color"] else 0xFFFFFF,
        "image": v["image"],
        "thumbnail": v["thumbnail"],
        "messages": []
    }

    save(data)
    await interaction.followup.send(f"✅ Created `{name}`", ephemeral=True)

# =========================
# EMBED SEND
# =========================
@bot.tree.command(name="embed_send")
@app_commands.autocomplete(name=embed_autocomplete)
async def embed_send(interaction: discord.Interaction, name: str, channel: discord.TextChannel):

    cfg = data["embeds"][name]

    embed = discord.Embed(title=cfg["title"], description=cfg["description"], color=cfg["color"])
    if cfg["image"]:
        embed.set_image(url=cfg["image"])
    if cfg["thumbnail"]:
        embed.set_thumbnail(url=cfg["thumbnail"])

    msg = await channel.send(embed=embed)

    cfg["messages"].append({"channel": channel.id, "message": msg.id})
    save(data)

    await interaction.response.send_message("✅ Sent", ephemeral=True)

# =========================
# EMBED EDIT
# =========================
@bot.tree.command(name="embed_edit")
@app_commands.autocomplete(name=embed_autocomplete)
async def embed_edit(interaction: discord.Interaction, name: str):

    cfg = data["embeds"][name]

    modal = FullModal("Edit Embed", {
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
        except:
            pass

    save(data)
    await interaction.followup.send("✅ Updated", ephemeral=True)

# =========================
# RUN
# =========================
bot.run(os.getenv("TOKEN"))
