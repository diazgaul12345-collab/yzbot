import os
import re
import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetParticipantRequest, EditBannedRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsAdmins

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "7150694117"))

client = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

groups = set()
warns = {}
welcome_msg = {}
leave_msg = {}

LINK_REGEX = re.compile(r"(https?://|t\.me/|www\.)", re.I)

MUTE_5MIN = ChatBannedRights(until_date=300, send_messages=True)
LOCK = ChatBannedRights(send_messages=True)
UNLOCK = ChatBannedRights(send_messages=False)

# ================= UTILS =================
async def is_admin(chat, user):
    try:
        p = await client(GetParticipantRequest(chat, user))
        return p.participant.admin_rights or p.participant.creator
    except:
        return False

# ================= EVENTS =================
@client.on(events.NewMessage)
async def any_slash(event):
    if event.text.startswith("/") and not event.text.startswith((
        "/tagall","/ping","/welcome","/leave","/kick","/lock","/unlock"
    )):
        await event.reply(
            "/tagall (pesan)\n"
            "/ping\n"
            "/welcome set pesan\n"
            "/leave set pesan\n"
            "/kick @user\n"
            "/lock /unlock"
        )

# =============== TAGALL ===================
@client.on(events.NewMessage(pattern="/tagall"))
async def tagall(event):
    if not event.is_group:
        return

    chat = event.chat
    sender = await event.get_sender()

    if not (await is_admin(chat, sender.id) or sender.id == OWNER_ID):
        return

    text = event.text.replace("/tagall", "").strip()
    if not text:
        text = "."

    members = []
    async for u in client.iter_participants(chat):
        if not u.bot:
            members.append(u)

    for _ in range(4):
        hidden = "".join(["\u2063" for _ in members])
        await event.respond(f"{text}{hidden}")

# =============== ANTI LINK =================
@client.on(events.NewMessage)
async def anti_link(event):
    if not event.is_group:
        return

    if not event.text:
        return

    if not LINK_REGEX.search(event.text):
        return

    sender = await event.get_sender()
    chat = event.chat

    if await is_admin(chat, sender.id):
        return

    warns[sender.id] = warns.get(sender.id, 0) + 1

    if warns[sender.id] > 5:
        await client.kick_participant(chat, sender.id)
        return

    await client(EditBannedRequest(chat, sender.id, MUTE_5MIN))

# =============== WELCOME / LEAVE ===========
@client.on(events.ChatAction)
async def welcome_leave(event):
    chat = event.chat

    if event.user_joined or event.user_added:
        if chat.id in welcome_msg:
            msg = await event.reply(
                welcome_msg[chat.id].replace("(user)", f"[{event.user.first_name}](tg://user?id={event.user.id})")
            )
            await asyncio.sleep(300)
            await msg.delete()

    if event.user_left or event.user_kicked:
        if chat.id in leave_msg:
            msg = await event.reply(
                leave_msg[chat.id].replace("(user)", event.user.first_name)
            )
            await asyncio.sleep(300)
            await msg.delete()

# =============== SET WELCOME ===============
@client.on(events.NewMessage(pattern="/welcome"))
async def set_welcome(event):
    if not await is_admin(event.chat, event.sender_id):
        return
    welcome_msg[event.chat_id] = event.text.replace("/welcome", "").strip()

@client.on(events.NewMessage(pattern="/leave"))
async def set_leave(event):
    if not await is_admin(event.chat, event.sender_id):
        return
    leave_msg[event.chat_id] = event.text.replace("/leave", "").strip()

# =============== ADMIN TAG =================
@client.on(events.NewMessage)
async def admin_tag(event):
    if not event.is_group:
        return
    if not event.entities:
        return

    admins = []
    async for a in client.iter_participants(event.chat, filter=ChannelParticipantsAdmins):
        admins.append(a.id)

    for e in event.entities:
        if hasattr(e, "user_id") and e.user_id in admins:
            await event.reply("sabar bang")
            break

# =============== COMMANDS ==================
@client.on(events.NewMessage(pattern="/ping"))
async def ping(event):
    await event.reply("pong")

@client.on(events.NewMessage(pattern="/groups"))
async def list_groups(event):
    if event.sender_id != OWNER_ID:
        return
    txt = "\n".join(str(g) for g in groups)
    await event.reply(txt or "kosong")

@client.on(events.NewMessage(pattern="/kick"))
async def kick(event):
    if not await is_admin(event.chat, event.sender_id):
        return
    if event.reply_to_msg_id:
        r = await event.get_reply_message()
        await client.kick_participant(event.chat, r.sender_id)

@client.on(events.NewMessage(pattern="/lock"))
async def lock(event):
    if await is_admin(event.chat, event.sender_id):
        await client(EditBannedRequest(event.chat, event.chat_id, LOCK))

@client.on(events.NewMessage(pattern="/unlock"))
async def unlock(event):
    if await is_admin(event.chat, event.sender_id):
        await client(EditBannedRequest(event.chat, event.chat_id, UNLOCK))

# =============== TRACK GROUP ===============
@client.on(events.NewMessage)
async def track(event):
    if event.is_group:
        groups.add(event.chat_id)

print("BOT READY")
client.run_until_disconnected()
