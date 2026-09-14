import os, asyncio
import yt_dlp
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- CODE ---
API_ID = int(os.getenv("37146575"))
API_HASH = os.getenv("4617e8b7d1040d7d895ec39de8eae4e5")
BOT_TOKEN = os.getenv("8252566284:AAH84AVugAXHYgvrJvPqI7-6QfC3GCwLYZ8")
SESSION_STRING = os.getenv("BQI2z88ASotzhCfCbI024XcDPNqOuzV7a7mkxUeqEPOhV_-J1zQMsCFem1M2DlT5rdvDi5E-GyXmvlL8jiKqvZPyLKTqIbceF7PXctsaW4T6zSnwIhPML5-q9x8x_E5u6uH8JfhJIPWpH0J29QzQt1gxn3oVvatVcwjh0lveIFwjkMu2hoFC0LGwoSEF6Jyw7k8OLQhBSGciwSBesvCvze0aw6Ls_-3XErM1GbQlJtkShPavbG_gN_MQ3Fo00VGLfI9qWyGetrH6TpbtXL3Z_PsYaSj1yBkA6pbKrBZcCu28UZNRdcaQqG0PDDVYqQCp_GDo87Va5SOqLGqfK8WvxTIQXcBnZgAAAAH3BaEwAA")
# --------------------------------

app = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_app = Client("UserBot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(user_app)

queues = {}
WATERMARK = "\n\n@epic_india"

def get_url(query):
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True, 'default_search': 'ytsearch1'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info: info = info['entries'][0]
        return info['url'], info['title']

@call_py.on_stream_end()
async def on_end(_, update):
    chat_id = update.chat_id
    if chat_id in queues and queues[chat_id]:
        queues[chat_id].pop(0)
        if queues[chat_id]:
            data = queues[chat_id][0]
            url, title = await asyncio.to_thread(get_url, data['query'])
            await call_py.play(chat_id, MediaStream(url))
            await app.send_message(chat_id, f"▶️ **Now Playing:** {title}\n👤 Requested by: {data['mention']}{WATERMARK}")

@app.on_message(filters.command(["play","vplay","stop","skip","queue"]) & filters.group)
async def handler(_, m):
    user_mention = m.from_user.mention if m.from_user else "Unknown"
    cmd = m.command[0]

    if cmd == "stop":
        queues.pop(m.chat.id, None)
        try: await call_py.leave(m.chat.id)
        except: pass
        await m.reply(f"⏹ **Stopped & Queue cleared**\nBy: {user_mention}{WATERMARK}")
        return

    if cmd == "skip":
        if m.chat.id in queues and queues[m.chat.id]:
            old = queues[m.chat.id].pop(0)
            if queues[m.chat.id]:
                data = queues[m.chat.id][0]
                url, title = await asyncio.to_thread(get_url, data['query'])
                await call_py.play(m.chat.id, MediaStream(url))
                await m.reply(f"⏭ **Skipped:** {old['title']}\n▶️ **Now Playing:** {title}\n👤 Requested by: {data['mention']}{WATERMARK}")
            else:
                try: await call_py.leave(m.chat.id)
                except: pass
                await m.reply(f"⏭ Skipped, Queue empty{WATERMARK}")
        return

    if cmd == "queue":
        q = queues.get(m.chat.id, [])
        if not q: await m.reply(f"Queue khali hai{WATERMARK}"); return
        text = "**Queue:**\n"
        for i, d in enumerate(q):
            text += f"{i+1}. {d['title']} - {d['mention']}\n"
        await m.reply(text + WATERMARK)
        return

    # /play /vplay
    if len(m.command) < 2:
        await m.reply(f"Gaane ka naam de bhai! Ex: `/play kesariya`{WATERMARK}")
        return

    query = m.text.split(None, 1)[1]
    msg = await m.reply(f"🔎 **Searching:** {query}\nBy: {user_mention}{WATERMARK}")

    url, title = await asyncio.to_thread(get_url, query)

    if m.chat.id not in queues: queues[m.chat.id] = []

    data = {"query": query, "title": title, "mention": user_mention, "user_id": m.from_user.id}

    if not queues[m.chat.id]:
        queues[m.chat.id].append(data)
        try:
            await call_py.play(m.chat.id, MediaStream(url))
            await msg.edit(f"▶️ **Now Playing:** {title}\n👤 **Requested by:** {user_mention}\n📢 **Updates in Group**{WATERMARK}")
        except Exception as e:
            await msg.edit(f"Error: {e}{WATERMARK}")
    else:
        queues[m.chat.id].append(data)
        await msg.edit(f"➕ **Added to Queue at #{len(queues[m.chat.id])}**\n🎵 {title}\n👤 **Requested by:** {user_mention}{WATERMARK}")

async def main():
    await user_app.start()
    await app.start()
    await call_py.start()
    print("ok chal raha hai")
    await asyncio.Event().wait()

asyncio.run(main())        
