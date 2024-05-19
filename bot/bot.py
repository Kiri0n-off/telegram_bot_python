import logging
import re
import paramiko
import datetime
import pathlib
import os
import psycopg2
from psycopg2 import Error

from telegram import Update, ForceReply, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from pathlib import Path
from dotenv import load_dotenv

# SQL
TOKEN = os.getenv('TOKEN')
connectionSql = None
userSql=os.getenv('DB_USER')
passwordSql=os.getenv('DB_PASSWORD')
hostSql=os.getenv('DB_HOST')
portSql=os.getenv('DB_PORT')
databaseSql=os.getenv('DB_DATABASE')
logDirectory=os.getenv('DB_REPL_LOGS')

# SSH
host=os.getenv('RM_HOST')
port=os.getenv('RM_PORT')
username=os.getenv('RM_USER')
password=os.getenv('DB_REPL_LOGS')

logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')

def connectSSH(commandTo, addArg):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(f'{commandTo} {addArg}')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    return data

def saveToFile(data):
    with open('temp.txt', 'w') as f:
        f.writelines(f"{item}\n" for item in data)

def helpCommand(update: Update, context):
    update.message.reply_text('Help!')

def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return 'FIND'

def findPhoneNumbers (update: Update, context):
    user_input = update.message.text
    phoneNumRegex = re.compile(r'\+?[7|8]{1}[\s,(,-]?\d{3}[\s,),-]?\d{3}[\s,-]?\d{2}[\s,-]?\d{2}')
    phoneNumberList = phoneNumRegex.findall(user_input)
    if not phoneNumberList:
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END
    phoneNumbers = ''
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i + 1}. {phoneNumberList[i]}\n'
    reply_keyboard = [['Да', 'Нет']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(phoneNumbers)
    update.message.reply_text('Желаете сохранить номера в базу данных? Напишите \'Да\' или \'Нет\', или же можете выбрать ответ из всплывающего меню', reply_markup=markup_key,)
    saveToFile(phoneNumberList)
    return 'SAVE'

def saveToDB(update: Update, context):
    if (update.message.text == "Нет"):
        print(update.message.text)
        update.message.reply_text('',reply_markup=ReplyKeyboardRemove(), )
        return ConversationHandler.END
    else:
        try:
            connection = psycopg2.connect(user=userSql, password=passwordSql, host=hostSql, port=portSql, database=databaseSql)
            cursor = connection.cursor()
            f = open('temp.txt', 'r')
            for line in f:
                cursor.execute(f"INSERT INTO phones (phone) VALUES ('{line.replace(chr(10),'')}');")
                connection.commit()
            logging.info("Команда успешно выполнена")
            update.message.reply_text('Данные сохранены в БД. Можете проверить набрав команду /get_phone_numbers', reply_markup=ReplyKeyboardRemove(), )
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто")
    return ConversationHandler.END

def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска почтовых адресов: ')
    return 'FINDE'

def findEmail(update: Update, context):
    user_input = update.message.text
    emailAddrRegex = re.compile(r'\w{1,48}@{1}\w{1,48}\.[a-zA-Z]{2,10}')
    emailAddrList = emailAddrRegex.findall(user_input)
    if not emailAddrList:
        update.message.reply_text('Почтовые адреса не найдены')
        return ConversationHandler.END
    emails = ''
    for i in range(len(emailAddrList)):
        emails += f'{i + 1}. {emailAddrList[i]}\n'
    reply_keyboard = [['Да', 'Нет']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(emails)
    update.message.reply_text(
        'Желаете сохранить номера в базу данных? Напишите \'Да\' или \'Нет\', или же можете выбрать ответ из всплывающего меню',
        reply_markup=markup_key, )
    saveToFile(emailAddrList)
    return 'SAVEE'

def saveToDBE(update: Update, context):
    if (update.message.text == "Нет"):
        print(update.message.text)
        update.message.reply_text('',reply_markup=ReplyKeyboardRemove(), )
        return ConversationHandler.END
    else:
        try:
            connection = psycopg2.connect(user=userSql, password=passwordSql, host=hostSql, port=portSql, database=databaseSql)
            cursor = connection.cursor()
            f = open('temp.txt', 'r')
            for line in f:
                cursor.execute(f"INSERT INTO emails (email) VALUES ('{line.replace(chr(10),'')}');")
                connection.commit()
            logging.info("Команда успешно выполнена")
            update.message.reply_text('Данные сохранены в БД. Можете проверить набрав команду /get_emails', reply_markup=ReplyKeyboardRemove(), )

        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто")
    return ConversationHandler.END

def echo(update: Update, context):
    update.message.reply_text(update.message.text)

def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')
    return 'verify_password'

def verifyPassword(update: Update, context):
    user_input = update.message.text
    points = 0
    if (len(user_input) >= 8):
        points += 1
    passRegexUpperCase = re.compile(r'[A-Z]+')
    passRegexLowerCase = re.compile(r'[a-z]+')
    passRegexNumbers = re.compile(r'[0-9]+')
    passRegexSpec = re.compile(r'[!@#\$%\^&\*\(\)]+')
    if (bool(passRegexUpperCase.search(user_input) and bool(passRegexLowerCase.search(user_input)))):
        points += 2
    if (bool(passRegexNumbers.search(user_input))):
        points += 1
    if (bool(passRegexSpec.search(user_input))):
        points += 1
    if(points == 5):
        answer = f'Пароль сложный\nОценка: {points}/5'
    else:
        answer = f'Пароль простой\nОценка: {points}/5'

    update.message.reply_text(answer)
    return ConversationHandler.END

def getRelease(update: Update, context):
    data = connectSSH("lsb_release -a", "")
    update.message.reply_text(data)
    return ConversationHandler.END

def getUname(update: Update, context):
    data = connectSSH("uname -a", "")
    update.message.reply_text(data)
    return ConversationHandler.END

def getUptime(update: Update, context):
    data = connectSSH("uptime", "")
    update.message.reply_text(data)
    return ConversationHandler.END

def getDf(update: Update, context):
    data = connectSSH("df -h", "")
    update.message.reply_text(data)
    return ConversationHandler.END

def getFree(update: Update, context):
    data = connectSSH("free -h", "")
    update.message.reply_text(data)
    return ConversationHandler.END

def getMpStat(update: Update, context):
    data = connectSSH("mpstat -P ALL", "")
    update.message.reply_text(data)
    return ConversationHandler.END

def getW(update: Update, context):
    data = connectSSH("w", "")
    update.message.reply_text(data)
    return ConversationHandler.END

def getAuth(update: Update, context):
    data = connectSSH("last -10", "")
    update.message.reply_text(data)
    return ConversationHandler.END

def getCritical(update: Update, context):
    data = connectSSH("journalctl -p 2 | tail -n5", "")
    update.message.reply_text(data)
    return ConversationHandler.END

def getPs(update: Update, context):
    data = connectSSH("ps -AH", "")
    str_count = 4096
    l = 1
    if(len(data) > str_count):
        l = int((len(data) + 1) / str_count) + 1
    for i in range(l):
        part = data[(i*str_count):((i+1)*str_count)]
        update.message.reply_text(part)
    return ConversationHandler.END

def getSs(update: Update, context):
    data = connectSSH("ss -tlnp", "")
    update.message.reply_text(data)
    return ConversationHandler.END

def getAptListCommand(update: Update, context):
    update.message.reply_text('Введите all, если хотите посмотреть все установленные программы, либо название конкретной программы: ')
    return 'get_apt_list'
def getAptList(update: Update, context):
    user_input = update.message.text
    if user_input.lower() == 'all':
        prog = ""
    else:
        prog = user_input
    data = connectSSH("apt list --installed", f"{prog}")
    str_count = 4096
    l = 1
    if (len(data) > str_count):
        l = int((len(data) + 1) / str_count) + 1
    for i in range(l):
        part = data[(i * str_count):((i + 1) * str_count)]
        update.message.reply_text(part)
    return ConversationHandler.END

def getService(update: Update, context):
    data = connectSSH("service --status-all | grep \'+\'", "")
    update.message.reply_text(data)
    return ConversationHandler.END

def selectEmailPhone(tableName):
    try:
        connectionSql = psycopg2.connect(user=userSql, password=passwordSql, host=hostSql, port=portSql, database=databaseSql)
        cursor = connectionSql.cursor()
        cursor.execute(f"SELECT * FROM {tableName};")
        data = cursor.fetchall()
        logging.info("Команда успешно выполнена")
        return data
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connectionSql is not None:
            cursor.close()
            connectionSql.close()

def getEmail(update: Update, context):
    data = selectEmailPhone("emails")
    result = "\n".join(map(str, data))
    update.message.reply_text(result)
    return ConversationHandler.END

def getPhoneNumbers(update: Update, context):
    data = selectEmailPhone("phones")
    result = "\n".join(map(str, data))
    update.message.reply_text(result)
    return ConversationHandler.END

def getReplLogs(update: Update, context):
    print(logDirectory)
    os.chdir(logDirectory)
    files = os.listdir()
    data = ""
    for file_name in files:
        if file_name.endswith(".log"):
            abs_path = os.path.abspath(file_name)
            if os.path.isfile(abs_path):
                with open(file_name, 'r') as f:
                    lessons_list = [line.strip() for line in f.readlines()]
                    for i, lesson in enumerate(lessons_list):
                        if "replication" in lesson:
                            data += lessons_list[i] + "\n"
    str_count = 4096
    l = 1
    if (len(data) > str_count):
        l = int((len(data) + 1) / str_count) + 1
    for i in range(l):
        part = data[(i * str_count):((i + 1) * str_count)]
        update.message.reply_text(part)
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'FIND': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'SAVE': [MessageHandler(Filters.regex('^(Да|Нет)'), saveToDB)]
        },
        fallbacks=[]
    )
    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'FINDE': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'SAVEE': [MessageHandler(Filters.regex('^(Да|Нет)'), saveToDBE)]
        },
        fallbacks=[]
    )
    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )
    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, getAptList)],
        },
        fallbacks=[]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(CommandHandler("get_release", getRelease))
    dp.add_handler(CommandHandler("get_uname", getUname))
    dp.add_handler(CommandHandler("get_uptime", getUptime))
    dp.add_handler(CommandHandler("get_df", getDf))
    dp.add_handler(CommandHandler("get_free", getFree))
    dp.add_handler(CommandHandler("get_mpstat", getMpStat))
    dp.add_handler(CommandHandler("get_w", getW))
    dp.add_handler(CommandHandler("get_auths", getAuth))
    dp.add_handler(CommandHandler("get_critical", getCritical))
    dp.add_handler(CommandHandler("get_ps", getPs))
    dp.add_handler(CommandHandler("get_ss", getSs))
    dp.add_handler(CommandHandler("get_services", getService))
    dp.add_handler(CommandHandler("get_emails", getEmail))
    dp.add_handler(CommandHandler("get_phone_numbers", getPhoneNumbers))
    dp.add_handler(CommandHandler("get_repl_logs", getReplLogs))
    dp.add_handler(convHandlerGetAptList)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
