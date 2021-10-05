import os
import subprocess
import time
import importlib
import subprocess

from sys import executable

from telegram import ParseMode, BotCommand
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async
from telegram.error import TimedOut, BadRequest

from bot.gDrive import GoogleDriveHelper
from bot.fs_utils import get_readable_file_size
from bot import *
from bot.decorators import is_authorised, is_owner
from telegram.error import TimedOut, BadRequest
from bot.clone_status import CloneStatus
from bot.msg_utils import deleteMessage, sendMessage
from bot.modules import ALL_MODULES
from bot import LOGGER, dispatcher, updater, bot


for module in ALL_MODULES:
    imported_module = importlib.import_module("bot.modules." + module)
    importlib.reload(imported_module)CLONE_REGEX = r"https://drive\.google\.com/(drive)?/?u?/?\d?/?(mobile)?/?(file)?(folders)?/?d?/(?P<id>[-\w]+)[?+]?/?(w+)?"@run_async

@run_async
def start(update, context):
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(update.message.chat.id, update.message.chat.username, update.message.text))
    sendMessage("Hello! Please send me a Google Drive Shareable Link to Clone to your Drive!" \
        "\nSend /help for checking all available commands.",
    context.bot, update, 'Markdown')
    # ;-;

@run_async
def helper(update, context):
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(update.message.chat.id, update.message.chat.username, update.message.text))
    sendMessage("Here are the available commands of the bot\n\n" \
        "*Usage:* `/clone <link> [DESTINATION_ID]`\n*Example:* \n1. `/clone https://drive.google.com/drive/u/1/folders/0AO-ISIXXXXXXXXXXXX`\n2. `/clone 0AO-ISIXXXXXXXXXXXX`" \
            "\n*DESTIONATION_ID* is optional. It can be either link or ID to where you wish to store a particular clone." \
            "\n\nYou can also *ignore folders* from clone process by doing the following:\n" \
                "`/clone <FOLDER_ID> [DESTINATION] [id1,id2,id3]`\n In this example: id1, id2 and id3 would get ignored from cloning\nDo not use <> or [] in actual message." \
                    "*Make sure to not put any space between commas (,).*", context.bot, update, 'Markdown')

# TODO Cancel Clones with /cancel command.
@run_async
@is_authorised
def cloneNode(update, context):
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(update.message.chat.id, update.message.chat.username, update.message.text))
    args = update.message.text.split(" ")
    if len(args) >= 1:
        link = args[0]
        try:
            ignoreList = args[-1].split(',')
        except IndexError:
            ignoreList = []

        DESTINATION_ID = GDRIVE_FOLDER_ID
        try:
            DESTINATION_ID = args[1]
            print(DESTINATION_ID)
        except IndexError:
            pass
            # Usage: /clone <FolderToClone> <Destination> <IDtoIgnoreFromClone>,<IDtoIgnoreFromClone>

        msg = sendMessage(f"<b>📲 Cloning:</b> <code>{link}</code>", context.bot, update)
        status_class = CloneStatus()
        gd = GoogleDriveHelper(GFolder_ID=DESTINATION_ID)
        sendCloneStatus(update, context, status_class, msg, link)
        result = gd.clone(link, status_class, ignoreList=ignoreList)
        deleteMessage(context.bot, msg)
        status_class.set_status(True)
        if update.message.from_user.username:
            uname = f'@{update.message.from_user.username}'
        else:
            uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
        if uname is not None:
            cc = f'\n\n<b>Clone by: {uname} ID:</b> <code>{update.message.from_user.id}</code>'
        sendMessage(result + cc, context.bot, update)
    else:
        sendMessage("<b>Please Provide a Google Drive Shared Link to Clone.</b>", bot, update)


@run_async
def sendCloneStatus(update, context, status, msg, link):
    old_text = ''
    while not status.done():
        sleeper(3)
        try:
            if update.message.from_user.username:
                uname = f'@{update.message.from_user.username}'
            else:
                uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
            text=f'🔗 *Cloning:* [{status.MainFolderName}]({status.MainFolderLink})\n━━━━━━━━━━━━━━\n' \
                 f'🗃️ *Current File:* `{status.get_name()}`\n📚 *Total File:* `{int(len(status.get_name()))}`\n' \
                 f'⬆️ *Transferred*: `{status.get_size()}`\n📁 *Destination:* [{status.DestinationFolderName}]({status.DestinationFolderLink})\n\n' \
                 f'*👤 Clone by: {uname} ID:* `{update.message.from_user.id}`'
            if status.checkFileStatus():
                text += f"\n🕒 *Checking Existing Files:* `{str(status.checkFileStatus())}`"
            if not text == old_text:
                msg.edit_text(text=text, parse_mode="Markdown", timeout=200)
                old_text = text
        except Exception as e:
            LOGGER.error(e)
            if str(e) == "Message to edit not found":
                break
            sleeper(2)
            continue
    return

def sleeper(value, enabled=True):
    time.sleep(int(value))
    return

@run_async
@is_authorised
def countNode(update,context):
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(update.message.chat.id, update.message.chat.username, update.message.text))
    args = update.message.text.split(" ",maxsplit=1)
    if len(args) > 1:
        link = args[1]
        msg = sendMessage(f"Counting: <code>{link}</code>",context.bot,update)
        gd = GoogleDriveHelper()
        result = gd.count(link)
        deleteMessage(context.bot,msg)
        if update.message.from_user.username:
            uname = f'@{update.message.from_user.username}'
        else:
            uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
        if uname is not None:
            cc = f'\n\n<b>Count by: {uname} ID:</b> <code>{update.message.from_user.id}</code>'
        sendMessage(result + cc,context.bot,update)
    else:
        sendMessage("<b>Provide G-Drive Shareable Link to Count.</b>",context.bot,update)

@run_async
@is_owner
def sendLogs(update, context):
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(update.message.chat.id, update.message.chat.username, update.message.text))
    with open('log.txt', 'rb') as f:
        bot.send_document(document=f, filename=f.name,
                        reply_to_message_id=update.message.message_id,
                        chat_id=update.message.chat_id)

@run_async
@is_owner
def deletefile(update, context):
	msg_args = update.message.text.split(None, 1)
	msg = ''
	try:
		link = msg_args[1]
		LOGGER.info(link)
	except IndexError:
		msg = 'Send a link along with command'

	if msg == '' : 
		drive = gDrive.GoogleDriveHelper()
		msg = drive.deletefile(link)
	LOGGER.info(f"DeleteFileCmd: {msg}")
	reply_message = sendMessage(msg, context.bot, update)





@run_async
@is_owner
def shell(update, context):
    message = update.effective_message
    cmd = message.text.split(' ', 1)
    if len(cmd) == 1:
        message.reply_text('No command to execute was given.')
        return
    cmd = cmd[1]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    reply = ''
    stderr = stderr.decode()
    stdout = stdout.decode()
    if stdout:
        reply += f"*Stdout*\n`{stdout}`\n"
        LOGGER.info(f"Shell - {cmd} - {stdout}")
    if stderr:
        reply += f"*Stderr*\n`{stderr}`\n"
        LOGGER.error(f"Shell - {cmd} - {stderr}")
    if len(reply) > 3000:
        with open('shell_output.txt', 'w') as file:
            file.write(reply)
        with open('shell_output.txt', 'rb') as doc:
            context.bot.send_document(
                document=doc,
                filename=doc.name,
                reply_to_message_id=message.message_id,
                chat_id=message.chat_id)
    else:
        message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

@run_async
@is_owner
def gitpull(update, context):
    msg = update.effective_message.reply_text(
        "Pulling all changes from remote and then attempting to restart.",
    )
    proc = subprocess.Popen("git pull", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    result = proc.communicate(GIT_PASS)

    sent_msg = msg.text + "\n\nChanges pulled... I guess..."

    for i in reversed(range(5)):
        msg.edit_text(sent_msg + str(i + 1))
        time.sleep(1)

    if not result.stdout.read():
        msg.edit_text(f'{result.stderr.read()}')
       #msg.edit_text(f"Do Restart after you see this with /{BotCommands.RestartCommand}.")


@run_async
@is_owner
def restart(update, context):
    restart_message = sendMessage("Restarting, Please wait!", context.bot, update)
    # Save restart message object in order to reply to it after restarting
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    os.execl(executable, executable, "-m", "bot")
botcmds = [
        (f'{CLONE_BOT}','Start Clone'),
        (f'{LOG_BOT}', 'Send log'),
        (f'{DEL_BOT}','Delete file'),
        (f'help','help')
    ]


def main():
    LOGGER.info("Bot Started!")
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("𝐁𝐨𝐭 𝐑𝐞𝐬𝐭𝐚𝐫𝐭𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲!", chat_id, msg_id)
        os.remove(".restartmsg")
    bot.set_my_commands(botcmds)
    
    dispatcher.bot.sendMessage(chat_id=OWNER_ID, text=f"<b>Bot Started Successfully!</b>", parse_mode=ParseMode.HTML)
    clone_handler = MessageHandler(filters=Filters.regex(CLONE_REGEX), callback=cloneNode)
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', helper)
    log_handler = CommandHandler(f'{LOG_BOT}', sendLogs)
    delete_handler = CommandHandler(f'{DEL_BOT}', deletefile)
    count_handler = CommandHandler('count', countNode)
    shell_handler = CommandHandler(['shell', 'sh', 'tr', 'term', 'terminal'], shell)
    GITPULL_HANDLER = CommandHandler('update', gitpull)
    restart_handler = CommandHandler('restart', restart)
    
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(GITPULL_HANDLER)
    dispatcher.add_handler(shell_handler)
    dispatcher.add_handler(count_handler)
    dispatcher.add_handler(log_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(clone_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(delete_handler)
    updater.start_polling()

main()
