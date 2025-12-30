import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

# ===== ENV =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== DATA =====
warns = {}
welcome_msg = {}
leave_msg = {}
groups = set()
penyetor = {}  # untuk +7, +10, dll

LINK_REGEX = re.compile(r"(https?://|t\.me/|www\.)", re.I)

# ===== UTILS =====
async def is_admin(chat_id, user_id):
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in ["administrator", "creator"]

# ===== AUTO HELP / SEMUA COMMAND BARU =====
@bot.on_message(~filters.regex(r"^/(tagall|ping|welcome|leave|kick|lock|unlock|stats|list)"))
async def auto_help(client, message: Message):
    if message.text.startswith("/"):
        await message.reply(
            "/tagall (pesan)\n"
            "/ping\n"
            "/welcome teks\n"
            "/leave teks\n"
            "/kick (reply user)\n"
            "/lock /unlock\n"
            "/list"
        )

# ===== TAGALL =====
@bot.on_message(filters.command("tagall"))
async def tagall(client, message: Message):
    if not message.chat.type in ["group", "supergroup"]:
        return
    if not (await is_admin(message.chat.id, message.from_user.id) or message.from_user.id == OWNER_ID):
        return
    text = " ".join(message.command[1:]) or "."
    mentions = ""
    async for u in bot.iter_chat_members(message.chat.id):
        if not u.user.is_bot:
            mentions += f"[‎](tg://user?id={u.user.id})"
    for _ in range(4):
        await message.reply(f"{text}\n{mentions}")

# ===== ANTI LINK =====
@bot.on_message(filters.text & filters.group)
async def anti_link(client, message: Message):
    if LINK_REGEX.search(message.text):
        if await is_admin(message.chat.id, message.from_user.id):
            return
        uid = message.from_user.id
        warns[uid] = warns.get(uid, 0) + 1
        if warns[uid] > 5:
            await bot.kick_chat_member(message.chat.id, uid)
            return
        await bot.restrict_chat_member(message.chat.id, uid, can_send_messages=False, until_date=300)

# ===== WELCOME / LEAVE AUTO DELETE 5MENIT =====
@bot.on_message(filters.command("welcome") & filters.group)
async def set_welcome(client, message: Message):
    if await is_admin(message.chat.id, message.from_user.id):
        welcome_msg[message.chat.id] = " ".join(message.command[1:])
        await message.reply("Welcome di set!")

@bot.on_message(filters.command("leave") & filters.group)
async def set_leave(client, message: Message):
    if await is_admin(message.chat.id, message.from_user.id):
        leave_msg[message.chat.id] = " ".join(message.command[1:])
        await message.reply("Leave di set!")

@bot.on_message(filters.group)
async def welcome_leave(client, message: Message):
    if message.new_chat_members:
        if message.chat.id in welcome_msg:
            txt = welcome_msg[message.chat.id]
            for u in message.new_chat_members:
                msg = await message.reply(txt.replace("(user)", f"[{u.first_name}](tg://user?id={u.id})"))
                await asyncio.sleep(300)
                await msg.delete()
    if message.left_chat_member:
        if message.chat.id in leave_msg:
            txt = leave_msg[message.chat.id]
            msg = await message.reply(txt.replace("(user)", message.left_chat_member.first_name))
            await asyncio.sleep(300)
            await msg.delete()

# ===== TAG ADMIN REPLY =====
@bot.on_message(filters.group & filters.reply)
async def admin_tag(client, message: Message):
    if message.entities:
        chat_admins = [a.user.id for a in await bot.get_chat_members(message.chat.id, filter="administrators")]
        for e in message.entities:
            if hasattr(e, "user") and e.user.id in chat_admins:
                await message.reply("sabar bang")
                break

# ===== COMMANDS PENDUKUNG =====
@bot.on_message(filters.command("ping"))
async def ping(client, message: Message):
    await message.reply("pong")

@bot.on_message(filters.command("kick"))
async def kick(client, message: Message):
    if await is_admin(message.chat.id, message.from_user.id) and message.reply_to_message:
        await bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id)

@bot.on_message(filters.command("lock"))
async def lock(client, message: Message):
    if await is_admin(message.chat.id, message.from_user.id):
        await bot.set_chat_permissions(message.chat.id, can_send_messages=False)

@bot.on_message(filters.command("unlock"))
async def unlock(client, message: Message):
    if await is_admin(message.chat.id, message.from_user.id):
        await bot.set_chat_permissions(message.chat.id, can_send_messages=True, can_send_media_messages=True)

# ===== PENYETOR +7/+10/+… =====
@bot.on_message(filters.group & filters.regex(r"^\+\d+"))
async def add_penyetor(client, message: Message):
    if not (await is_admin(message.chat.id, message.from_user.id) or message.from_user.id == OWNER_ID):
        return
    if message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        val = int(message.text.replace("+",""))
        penyetor[uid] = penyetor.get(uid, 0) + val
        await message.reply(f"[{message.reply_to_message.from_user.first_name}](tg://user?id={uid}) Menyetor {penyetor[uid]} 留言或帖子")

@bot.on_message(filters.command("list") & filters.group)
async def list_penyetor(client, message: Message):
    if not penyetor:
        await message.reply("Belum ada penyetor")
        return
    txt = ""
    for uid, val in penyetor.items():
        user = await bot.get_users(uid)
        txt += f"[{user.first_name}](tg://user?id={uid}) Menyetor {val} 留言或帖子\n"
    await message.reply(txt)

# ===== TRACK GROUP =====
@bot.on_message(filters.group)
async def track_groups(client, message: Message):
    groups.add(message.chat.id)

print("BOT READY")
bot.run()
