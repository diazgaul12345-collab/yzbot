import os
import re
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import ChatBannedRights, ChannelParticipantsAdmins
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantRequest

# ===== ENV =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

client = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ===== DATA =====
warns = {}
welcome_msg = {}
leave_msg = {}
groups = set()
depositors = {}  # Untuk +N penyetor

LINK_REGEX = re.compile(r"(https?://|t\.me/|www\.)", re.I)

# ===== RIGHTS =====
MUTE_5MIN = ChatBannedRights(until_date=300, send_messages=True)

LOCK = ChatBannedRights(
    until_date=None,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True
)

UNLOCK = ChatBannedRights(
    until_date=None,
    send_messages=False,
    send_media=False,
    send_stickers=False,
    send_gifs=False,
    send_games=False,
    send_inline=False,
    embed_links=False
)

# ===== UTILS =====
async def is_admin(chat, user_id):
    try:
        p = await client(GetParticipantRequest(chat, user_id))
        return bool(p.participant.admin_rights or p.participant.creator)
    except:
        return False

# ===== AUTO HELP (SEMUA / ) =====
@client.on(events.NewMessage)
async def auto_help(event):
    if event.text and event.text.startswith("/") and not event.text.startswith((
        "/tagall","/ping","/welcome","/leave","/kick","/lock","/unlock","/stats","/list"
    )):
        await event.reply(
            "/tagall (pesan)\n"
            "/ping\n"
            "/welcome teks\n"
            "/leave teks\n"
            "/kick (reply user)\n"
            "/lock /unlock\n"
            "/list\n"
            "+N (penyetor)"
        )

# ===== TAGALL (HIDDEN MENTION REAL) =====
@client.on(events.NewMessage(pattern=r"^/tagall"))
async def tagall(event):
    if not event.is_group:
        return

    if not (await is_admin(event.chat, event.sender_id) or event.sender_id == OWNER_ID):
        return

    text = event.text.replace("/tagall", "").strip() or "."

    mentions = ""
    async for u in client.iter_participants(event.chat_id):
        if not u.bot:
            mentions += f"[‎](tg://user?id={u.id})"

    # kirim 4x
    for _ in range(4):
        await event.respond(f"{text}\n{mentions}", parse_mode="md")

# ===== ANTI LINK =====
@client.on(events.NewMessage)
async def anti_link(event):
    if not event.is_group or not event.text:
        return
    if not LINK_REGEX.search(event.text):
        return
    if await is_admin(event.chat, event.sender_id):
        return

    uid = event.sender_id
    warns[uid] = warns.get(uid, 0) + 1

    if warns[uid] > 5:
        await client.kick_participant(event.chat_id, uid)
        return

    await client(EditBannedRequest(event.chat_id, uid, MUTE_5MIN))

# ===== WELCOME / LEAVE (AUTO DELETE 5 MENIT) =====
@client.on(events.ChatAction)
async def welcome_leave(event):
    chat_id = event.chat_id

    if event.user_joined or event.user_added:
        if chat_id in welcome_msg:
            msg = await event.reply(
                welcome_msg[chat_id].replace(
                    "(user)",
                    f"[{event.user.first_name}](tg://user?id={event.user.id})"
                )
            )
            await asyncio.sleep(300)
            await msg.delete()

    if event.user_left or event.user_kicked:
        if chat_id in leave_msg:
            msg = await event.reply(
                leave_msg[chat_id].replace("(user)", event.user.first_name)
            )
            await asyncio.sleep(300)
            await msg.delete()

@client.on(events.NewMessage(pattern=r"^/welcome"))
async def set_welcome(event):
    if await is_admin(event.chat, event.sender_id):
        welcome_msg[event.chat_id] = event.text.replace("/welcome", "").strip()
        await event.reply(f"Pesan welcome di seting: {welcome_msg[event.chat_id]}")

@client.on(events.NewMessage(pattern=r"^/leave"))
async def set_leave(event):
    if await is_admin(event.chat, event.sender_id):
        leave_msg[event.chat_id] = event.text.replace("/leave", "").strip()
        await event.reply(f"Pesan leave di seting: {leave_msg[event.chat_id]}")

# ===== TAG ADMIN → REPLY =====
@client.on(events.NewMessage)
async def admin_tag(event):
    if not event.is_group or not event.entities:
        return
    admins = []
    async for a in client.iter_participants(event.chat_id, filter=ChannelParticipantsAdmins):
        admins.append(a.id)
    for e in event.entities:
        if hasattr(e, "user_id") and e.user_id in admins:
            await event.reply("sabar bang")
            break

# ===== COMMANDS =====
@client.on(events.NewMessage(pattern="/ping"))
async def ping(event):
    await event.reply("pong")

@client.on(events.NewMessage(pattern="/kick"))
async def kick(event):
    if await is_admin(event.chat, event.sender_id) and event.reply_to_msg_id:
        r = await event.get_reply_message()
        await client.kick_participant(event.chat_id, r.sender_id)

@client.on(events.NewMessage(pattern="/lock"))
async def lock(event):
    if await is_admin(event.chat, event.sender_id):
        await client(EditBannedRequest(event.chat_id, event.chat_id, LOCK))

@client.on(events.NewMessage(pattern="/unlock"))
async def unlock(event):
    if await is_admin(event.chat, event.sender_id):
        await client(EditBannedRequest(event.chat_id, event.chat_id, UNLOCK))

# ===== TRACK GROUP =====
@client.on(events.NewMessage)
async def track(event):
    if event.is_group:
        groups.add(event.chat_id)

# ===== PENYETOR +N =====
@client.on(events.NewMessage)
async def depositors_handler(event):
    if not event.is_group or not event.text:
        return
    if not event.text.startswith("+"):
        return
    try:
        n = int(event.text[1:].split()[0])
    except:
        return
    # Cek admin/owner
    if not (await is_admin(event.chat, event.sender_id) or event.sender_id == OWNER_ID):
        return
    reply = await event.get_reply_message()
    if not reply:
        return
    uid = reply.sender_id
    depositors.setdefault(event.chat_id, {})
    depositors[event.chat_id][uid] = depositors[event.chat_id].get(uid, 0) + n
    name = reply.sender.first_name
    await event.reply(f"{name} Menyetor {depositors[event.chat_id][uid]} 留言或帖子")

@client.on(events.NewMessage(pattern="/list"))
async def list_depositors(event):
    if not event.is_group:
        return
    if event.chat_id not in depositors or not depositors[event.chat_id]:
        await event.reply("Belum ada penyetor.")
        return
    msg = "Daftar penyetor:\n"
    for uid, count in depositors[event.chat_id].items():
        user = await client.get_entity(uid)
        msg += f"{user.first_name} Menyetor {count} 留言或帖子\n"
    await event.reply(msg)

print("BOT READY")
client.run_until_disconnected()
