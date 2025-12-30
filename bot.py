import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, Message

# ===== ENV =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# ===== DATA =====
warns = {}
welcome_msg = {}
leave_msg = {}
penyetor = {}
groups = set()
LINK_REGEX = re.compile(r"(https?://|t\.me/|www\.)", re.I)

# ===== UTILS =====
async def is_admin(chat_id, user_id):
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in ["administrator", "creator"]

# ===== AUTO HELP =====
@bot.on_message(filters.command(None) & ~filters.regex(r"^/(tagall|ping|welcome|leave|kick|lock|unlock|stats|list)"))
async def auto_help(client, message):
    await message.reply(
        "/tagall (pesan)\n"
        "/ping\n"
        "/welcome teks\n"
        "/leave teks\n"
        "/kick (reply user)\n"
        "/lock /unlock\n"
        "/list\n"
        "+{angka} (reply user) untuk menyetor"
    )

# ===== TAGALL =====
@bot.on_message(filters.command("tagall"))
async def tagall(client, message):
    if not message.chat.type in ["group", "supergroup"]:
        return
    if not (await is_admin(message.chat.id, message.from_user.id) or message.from_user.id == OWNER_ID):
        return
    text = " ".join(message.command[1:]) or "."
    mentions = ""
    async for u in client.get_chat_members(message.chat.id):
        if not u.user.is_bot:
            mentions += f"[‎](tg://user?id={u.user.id})"
    for _ in range(4):
        await message.reply(f"{text}\n{mentions}")

# ===== ANTI LINK =====
@bot.on_message(filters.group & filters.text)
async def anti_link(client, message):
    if not LINK_REGEX.search(message.text):
        return
    if await is_admin(message.chat.id, message.from_user.id):
        return
    uid = message.from_user.id
    warns[uid] = warns.get(uid, 0) + 1
    if warns[uid] > 5:
        await message.chat.kick_member(uid)
        return
    await message.chat.restrict_member(uid, ChatPermissions(can_send_messages=False), until_date=300)

# ===== WELCOME / LEAVE =====
@bot.on_message(filters.command("welcome"))
async def set_welcome(client, message):
    if await is_admin(message.chat.id, message.from_user.id):
        welcome_msg[message.chat.id] = " ".join(message.command[1:]) or "Selamat datang (user)"
        await message.reply(f"Welcome di-set: {welcome_msg[message.chat.id]}")

@bot.on_message(filters.command("leave"))
async def set_leave(client, message):
    if await is_admin(message.chat.id, message.from_user.id):
        leave_msg[message.chat.id] = " ".join(message.command[1:]) or "Sampai jumpa (user)"
        await message.reply(f"Leave di-set: {leave_msg[message.chat.id]}")

@bot.on_message(filters.status_update)
async def welcome_leave(client, message):
    chat_id = message.chat.id
    if message.new_chat_members:
        for u in message.new_chat_members:
            if chat_id in welcome_msg:
                msg = await message.reply(welcome_msg[chat_id].replace("(user)", f"{u.first_name}"))
                await asyncio.sleep(300)
                await msg.delete()
    if message.left_chat_member:
        if chat_id in leave_msg:
            msg = await message.reply(leave_msg[chat_id].replace("(user)", f"{message.left_chat_member.first_name}"))
            await asyncio.sleep(300)
            await msg.delete()

# ===== TAG ADMIN =====
@bot.on_message(filters.group)
async def admin_tag(client, message):
    if not message.entities:
        return
    admins = [m.user.id for m in await bot.get_chat_members(message.chat.id, filter="administrators")]
    for e in message.entities:
        if getattr(e, "user_id", None) in admins:
            await message.reply("sabar bang")
            break

# ===== PING =====
@bot.on_message(filters.command("ping"))
async def ping(client, message):
    await message.reply("pong")

# ===== KICK =====
@bot.on_message(filters.command("kick"))
async def kick(client, message):
    if await is_admin(message.chat.id, message.from_user.id) and message.reply_to_message:
        await message.chat.kick_member(message.reply_to_message.from_user.id)

# ===== LOCK / UNLOCK =====
@bot.on_message(filters.command("lock"))
async def lock(client, message):
    if await is_admin(message.chat.id, message.from_user.id):
        await message.chat.set_permissions(ChatPermissions(can_send_messages=False))

@bot.on_message(filters.command("unlock"))
async def unlock(client, message):
    if await is_admin(message.chat.id, message.from_user.id):
        await message.chat.set_permissions(ChatPermissions(can_send_messages=True))

# ===== PENYETOR +X =====
@bot.on_message(filters.regex(r"^\+(\d+)$"))
async def penyetor_add(client, message):
    if not await is_admin(message.chat.id, message.from_user.id) and message.from_user.id != OWNER_ID:
        return
    if not message.reply_to_message:
        return
    jumlah = int(message.text.replace("+", ""))
    uid = message.reply_to_message.from_user.id
    penyetor[uid] = penyetor.get(uid, 0) + jumlah
    await message.reply(f"{message.reply_to_message.from_user.first_name} Menyetor {penyetor[uid]} 留言或帖子")

# ===== LIST PENYETOR =====
@bot.on_message(filters.command("list"))
async def list_penyetor(client, message):
    if not penyetor:
        await message.reply("Belum ada penyetor.")
        return
    text = ""
    for i, (uid, total) in enumerate(sorted(penyetor.items(), key=lambda x: -x[1]), 1):
        user = await bot.get_users(uid)
        text += f"{i}. {user.first_name} Menyetor {total} 留言或帖子\n"
    await message.reply(text)

# ===== TRACK GROUP =====
@bot.on_message(filters.group)
async def track(client, message):
    groups.add(message.chat.id)

print("BOT READY")
bot.run()
