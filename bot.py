import os
import re
import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters

# ===== ENV =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ===== DATA =====
warns = {}
welcome_msg = {}
leave_msg = {}
groups = set()
penyetor = {}  # user_id: jumlah
LINK_REGEX = re.compile(r"(https?://|t\.me/|www\.)", re.I)

# ===== UTILS =====
async def is_admin(chat_id, user_id):
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in ["administrator", "creator"]

# ===== AUTO HELP =====
@bot.on_message(filters.text & filters.private)
@bot.on_message(filters.text & filters.group)
async def auto_help(client, message):
    if message.text.startswith("/") and not message.text.split()[0][1:] in [
        "tagall","ping","welcome","leave","kick","lock","unlock","stats","list","+"
    ]:
        await message.reply(
            "/tagall (pesan)\n"
            "/ping\n"
            "/welcome teks\n"
            "/leave teks\n"
            "/kick (reply user)\n"
            "/lock /unlock\n"
            "/list\n"
            "+7/+10 ... (reply pesan)"
        )

# ===== TAGALL HIDDEN =====
@bot.on_message(filters.command("tagall") & filters.group)
async def tagall(client, message):
    if not await is_admin(message.chat.id, message.from_user.id) and message.from_user.id != OWNER_ID:
        return
    text = " ".join(message.command[1:]) or "."
    mentions = "".join([f"[‎](tg://user?id={u.id})" for u in await bot.get_chat_members(message.chat.id) if not u.user.is_bot])
    for _ in range(4):
        await message.reply(f"{text}\n{mentions}")

# ===== ANTI LINK & MUTE =====
@bot.on_message(filters.group & filters.text)
async def anti_link(client, message):
    if LINK_REGEX.search(message.text):
        if await is_admin(message.chat.id, message.from_user.id):
            return
        uid = message.from_user.id
        warns[uid] = warns.get(uid, 0) + 1
        if warns[uid] > 5:
            await bot.kick_chat_member(message.chat.id, uid)
            return
        until = datetime.now() + timedelta(minutes=5)
        await bot.restrict_chat_member(message.chat.id, uid, can_send_messages=False, until_date=until)

# ===== WELCOME / LEAVE =====
@bot.on_message(filters.new_chat_members)
async def welcome(client, message):
    chat_id = message.chat.id
    for user in message.new_chat_members:
        if chat_id in welcome_msg:
            msg = await message.reply(welcome_msg[chat_id].replace("(user)", f"[{user.first_name}](tg://user?id={user.id})"))
            await asyncio.sleep(300)
            await msg.delete()

@bot.on_message(filters.left_chat_member)
async def leave(client, message):
    chat_id = message.chat.id
    if chat_id in leave_msg:
        msg = await message.reply(leave_msg[chat_id].replace("(user)", message.left_chat_member.first_name))
        await asyncio.sleep(300)
        await msg.delete()

@bot.on_message(filters.command("welcome") & filters.group)
async def set_welcome(client, message):
    if await is_admin(message.chat.id, message.from_user.id):
        welcome_msg[message.chat.id] = " ".join(message.command[1:])
        await message.reply("Welcome message set!")

@bot.on_message(filters.command("leave") & filters.group)
async def set_leave(client, message):
    if await is_admin(message.chat.id, message.from_user.id):
        leave_msg[message.chat.id] = " ".join(message.command[1:])
        await message.reply("Leave message set!")

# ===== ADMIN TAG =====
@bot.on_message(filters.group)
async def admin_tag(client, message):
    if not message.entities:
        return
    for e in message.entities:
        if hasattr(e, "user_id"):
            user_id = e.user_id
            member = await bot.get_chat_member(message.chat.id, user_id)
            if member.status in ["administrator","creator"]:
                await message.reply("sabar bang")
                break

# ===== COMMANDS =====
@bot.on_message(filters.command("ping") & filters.group)
async def ping(client, message):
    await message.reply("pong")

@bot.on_message(filters.command("kick") & filters.group)
async def kick(client, message):
    if await is_admin(message.chat.id, message.from_user.id) and message.reply_to_message:
        await bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.reply("User dikick!")

@bot.on_message(filters.command("lock") & filters.group)
async def lock(client, message):
    if await is_admin(message.chat.id, message.from_user.id):
        await bot.set_chat_permissions(message.chat.id, can_send_messages=False)

@bot.on_message(filters.command("unlock") & filters.group)
async def unlock(client, message):
    if await is_admin(message.chat.id, message.from_user.id):
        await bot.set_chat_permissions(message.chat.id, can_send_messages=True)

# ===== PENYETOR +7/+10 & LIST =====
@bot.on_message(filters.group)
async def penyetor_list(client, message):
    if message.text.startswith("+") and message.reply_to_message:
        if not await is_admin(message.chat.id, message.from_user.id) and message.from_user.id != OWNER_ID:
            return
        try:
            jumlah = int(message.text[1:])
            user_id = message.reply_to_message.from_user.id
            penyetor[user_id] = penyetor.get(user_id, 0) + jumlah
            await message.reply(f"[{message.reply_to_message.from_user.first_name}](tg://user?id={user_id}) Menyetor {penyetor[user_id]} 留言或帖子")
        except:
            pass

@bot.on_message(filters.command("list") & filters.group)
async def list_penyetor(client, message):
    if penyetor:
        text = "Daftar penyetor:\n"
        for uid, jumlah in penyetor.items():
            user = await bot.get_users(uid)
            text += f"[{user.first_name}](tg://user?id={uid}) : {jumlah}\n"
        await message.reply(text)
    else:
        await message.reply("Belum ada penyetor.")

# ===== TRACK GROUP =====
@bot.on_message(filters.group)
async def track(client, message):
    groups.add(message.chat.id)

print("BOT READY")
bot.run()
