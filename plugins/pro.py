from pyrogram import filters, Client as AFK
from main import LOGGER as LOGS, prefixes, Config, Msg
from pyrogram.types import Message
from handlers.tg import TgClient, TgHandler
import os
import sys
import shutil
from handlers.downloader import download_handler, get_link_atributes
from handlers.uploader import Upload_to_Tg

@AFK.on_message(
    (filters.chat(Config.GROUPS) | filters.chat(Config.AUTH_USERS)) &
    filters.incoming & filters.command("pro", prefixes=prefixes)
)
async def Pro(bot: AFK, m: Message):
    sPath = f"{Config.DOWNLOAD_LOCATION}/{m.chat.id}"
    tPath = f"{Config.DOWNLOAD_LOCATION}/FILE/{m.chat.id}"
    os.makedirs(sPath, exist_ok=True)

    error_list = []  # 🔴 Error list init yahan hona chahiye

    BOT = TgClient(bot, m, sPath)

    try:
        nameLinks, num, caption, quality, Token, txt_name, userr = await BOT.Ask_user()
        Thumb = None  # ✅ Thumbnail skip kar diya (no user prompt)
    except Exception as e:
        LOGS.error(str(e))
        await TgHandler.error_message(bot=bot, m=m, error=f"from User Input - {e}")
        await m.reply_text("Wrong Input")
        return

    for i in range(num, len(nameLinks)):
        try:
            name = BOT.parse_name(nameLinks[i][0])
            link = nameLinks[i][1]
            wxh = get_link_atributes().get_height_width(link=link, Q=quality)
            caption_name = f"**{str(i+1).zfill(3)}.** - {name} {wxh}"
            file_name = f"{str(i+1).zfill(3)}. - {BOT.short_name(name)} {wxh}"

            Show = await bot.send_message(
                chat_id=m.chat.id,
                text=Msg.SHOW_MSG.format(
                    file_name=file_name,
                    file_link=link,
                ),
                disable_web_page_preview=True
            )

            url = get_link_atributes().input_url(link=link, Q=quality)
            DL = download_handler(name=file_name, url=url, path=sPath, Token=Token, Quality=quality)
            dl_file = await DL.start_download()

            if os.path.isfile(dl_file):
                if dl_file.endswith(".mp4"):
                    cap = f"{caption_name}.mp4\n\n<b>𝗕𝗮𝘁𝗰𝗵 𝗡𝗮𝗺𝗲 : </b>{caption}\n\n<b>𝗘𝘅𝘁𝗿𝗮𝗰𝘁𝗲𝗱 𝗯𝘆 ➤ </b> **{userr}**"
                    UL = Upload_to_Tg(bot=bot, m=m, file_path=dl_file, name=caption_name,
                                      Thumb=Thumb, path=sPath, show_msg=Show, caption=cap)
                    await UL.upload_video()
                else:
                    ext = dl_file.split(".")[-1]
                    cap = f"{caption_name}.{ext}\n\n<b>𝗕𝗮𝘁𝗰𝗵 𝗡𝗮𝗺𝗲 : </b>{caption}\n\n<b>𝗘𝘅𝘁𝗿𝗮𝗰𝘁𝗲𝗱 𝗯𝘆 ➤ </b> **{userr}**"
                    UL = Upload_to_Tg(bot=bot, m=m, file_path=dl_file, name=caption_name,
                                      Thumb=Thumb, path=sPath, show_msg=Show, caption=cap)
                    await UL.upload_doc()
            else:
                raise Exception("Downloaded file not found or invalid")

        except Exception as r:
            LOGS.error(str(r))
            err_name = nameLinks[i][0] if i < len(nameLinks) and len(nameLinks[i]) > 0 else f"Line {i+1}"
            error_list.append(f"❌ {err_name} → {str(r)}")

            try:
                await Show.delete()
            except:
                pass

            await bot.send_message(
                chat_id=Config.LOG_CH,
                text=Msg.ERROR_MSG.format(
                    error=str(r),
                    no_of_files=len(error_list),
                    file_name=err_name,
                    file_link=nameLinks[i][1] if i < len(nameLinks[i]) else "Unknown",
                )
            )
            continue

    shutil.rmtree(sPath)
    try:
        if os.path.exists(tPath):
            if os.path.isfile(tPath):
                os.remove(tPath)
    except Exception as e1:
        LOGS.error(str(e1))
        shutil.rmtree(tPath)

    await BOT.linkMsg2(error_list)

    # ✅ Final Error Summary
    if error_list:
        summary = "\n".join(error_list)
        await m.reply_text(f"⚠️ {len(error_list)} errors occurred:\n\n{summary[:4000]}")
    else:
        await m.reply_text("✅ All files processed successfully.")
