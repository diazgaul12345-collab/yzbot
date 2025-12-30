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
penyetor = {}

LINK_REGEX = re.compile(r"(https?://|t\.me/|www\.)", re.I)

# ===== UTILS =====
async def is_admin(chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# ===== AUTO HELP =====
@bot.on_message(filters.command(None) & ~filters.regex(r"^/(tagall|ping|welcome|leave|kick|lock|unlock|stats|list)"))
async def auto_help(client, message: Message):
    await message.reply(
        "/tagall (pesan)\n"
        "/ping\n"
        "/welcome teks\n"
        "/leave teks\n"
        "/kick (reply user)\n"
        "/lock /unlock\n"
        "/list\n"
        "+N (penyetor)"
    )

# ===== TAGALL =====
@bot.on_message(filters.command("tagall"))
async def tagall(client, message: Message):
    if message.chat.type not in ["supergroup", "group"]:
        return
    if not (await is_admin(message.chat.id, message.from_user.id) or message.from_user.id == OWNER_ID):
        return

    text = " ".join(message.command[1:]) or "."
    mentions = ""
    async for member in bot.get_chat_members(message.chat.id):
        if not member.user.is_bot:
            mentions += f"[‎](tg://user?id={member.user.id})"
    for _ in range(4):
        await message.reply(f"{text}\n{mentions}")

# ===== ANTI LINK =====
@bot.on_message(filters.regex(LINK_REGEX))
async def anti_link(client, message: Message):
    if message.chat.type not in ["supergroup", "group"]:
        return
    if await is_admin(message.chat.id, message.from_user.id):
        return
    uid = message.from_user.id
    warns[uid] = warns.get(uid, 0) + 1
    if warns[uid] > 5:
        try:
            await bot.kick_chat_member(message.chat.id, uid)
        except:
            pass
        return
    try:
        await bot.restrict_chat_member(
            message.chat.id,
            uid,
            can_send_messages=False,
            until_date=int(asyncio.time() + 300)
        )
    except:
        pass

# ===== WELCOME / LEAVE =====
@bot.on_message(filters.command("welcome"))
async def set_welcome(client, message: Message):
    if await is_admin(message.chat.id, message.from_user.id):
        welcome_msg[message.chat.id] = " ".join(message.command[1:])
        await message.reply(f"Welcome message set: {welcome_msg[message.chat.id]}")

@bot.on_message(filters.command("leave"))
async def set_leave(client, message: Message):
    if await is_admin(message.chat.id, message.from_user.id):
        leave_msg[message.chat.id] = " ".join(message.command[1:])
        await message.reply(f"Leave message set: {leave_msg[message.chat.id]}")

@bot.on_message(filters.new_chat_members)
async def welcome(client, message: Message):
    chat_id = message.chat.id
    for user in message.new_chat_members:
        if chat_id in welcome_msg:
            msg = await message.reply(welcome_msg[chat_id].replace("(user)", f"{user.first_name}"))
            await asyncio.sleep(300)
            await msg.delete()

@bot.on_message(filters.left_chat_member)
async def leave(client, message: Message):
    chat_id = message.chat.id
    user = message.left_chat_member
    if chat_id in leave_msg:
        msg = await message.reply(leave_msg[chat_id].replace("(user)", f"{user.first_name}"))
        await asyncio.sleep(300)
        await msg.delete()

# ===== ADMIN TAG =====
@bot.on_message(filters.reply)
async def admin_tag(client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        if await is_admin(message.chat.id, target_id):
            await message.reply("sabar bang")

# ===== PING =====
@bot.on_message(filters.command("ping"))
async def ping(client, message: Message):
    await message.reply("pong")

# ===== KICK =====
@bot.on_message(filters.command("kick"))
async def kick(client, message: Message):
    if await is_admin(message.chat.id, message.from_user.id):
        if message.reply_to_message:
            try:
                await bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            except:
                pass

# ===== LOCK / UNLOCK =====
@bot.on_message(filters.command("lock"))
async def lock(client, message: Message):
    if await is_admin(message.chat.id, message.from_user.id):
        await bot.set_chat_permissions(
            message.chat.id,
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_stickers=False,
            can_send_animations=False,
            can_send_games=False,
            can_use_inline_bots=False,
            can_add_web_page_previews=False
        )

@bot.on_message(filters.command("unlock"))
async def unlock(client, message: Message):
    if await is_admin(message.chat.id, message.from_user.id):
        await bot.set_chat_permissions(
            message.chat.id,
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_stickers=True,
            can_send_animations=True,
            can_send_games=True,
            can_use_inline_bots=True,
            can_add_web_page_previews=True
        )

# ===== PENYETOR +N =====
@bot.on_message(filters.regex(r"^\+(\d{1,3})$"))
async def penyetor_handler(client, message: Message):
    if not (await is_admin(message.chat.id, message.from_user.id) or message.from_user.id == OWNER_ID):
        return
    if message.reply_to_message and message.reply_to_message.from_user:
        n = int(message.text[1:])
        user = message.reply_to_message.from_user
        penyetor[user.id] = penyetor.get(user.id, 0) + n
        await message.reply(f"{user.first_name} Menyetor {n} 留言或帖子")

# ===== LIST =====
@bot.on_message(filters.command("list"))
async def list_penyetor(client, message: Message):
    text = "Daftar penyetor:\n"
    for uid, n in penyetor.items():
        try:
            user = await bot.get_users(uid)
            text += f"{user.first_name}: {n}\n"
        except:
            pass
    await message.reply(text)

# ===== TRACK GROUP =====
@bot.on_message()
async def track_group(client, message: Message):
    if message.chat.type in ["group", "supergroup"]:
        groups.add(message.chat.id)

# ===== RUN =====
print("BOT READY")
bot.run()
