#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, sqlite3, ast

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from bs4 import BeautifulSoup

from riotwatcher import RiotWatcher, EUROPE_WEST, LoLException, error_404, error_429

from LoLChat import LoLChat
from Chat import Chat

'''
    TrackerBot.
    
    Bot de Telegram para hacer seguimiento del estado de invocadores de League of Legends.
    Se conecta tanto al chat del cliente del League of Legends como a un chat de Telegram, enviando
    información sobre el primero al segundo cuando se le requiera.
    
    Adicionalmente, informará cuando uno de los invocadores a los que se le haga el seguimiento entre
    en cola, dando la opción a la gente de Telegram a enviarle un mensaje al chat de LoL para que
    les espere para jugar.
    
    v0.1.0
        - Release inicial
    v0.1.1
        - Añadido función anti-spam para que no mande mensajes de "<Summoner> en cola" continuamente.
        - Parametrizadas unas constantes para hacer mas rapido el despliegue entre entorno de 
          desarrollo y producción
    v0.2.0
        - Version reconstruida desde cero
        - Se ha eliminado la función anti-spam por no poder afinarse adecuadamente por falta de datos.
          Ahora se pueden silenciar las notificaciones por invocador o para todos los invocadores del
          canal especifco desde el que se envie la orden /mute <summoner ID> o /mute all
        - Se guardan los ajustes de cada canal en una tabla SQLite para cargarse al iniciar el script
          de nuevo.
    v0.2.1
        - Arreglado problema en el seguimiento de los estados de los invocadores.
        
    Requirements:
        python -m pip install telegram
        python -m pip install bs4
        python -m pip install riotwatcher
        python -m pip install sleekxmpp
        python -m pip install dnspython

        League of Legends AUXILIARY account.
        Telegram Bot details.
        
    TODOs:
        - Intentar ahorrarnos la peticion a riot si existe el ID de invocador en la tabla summoners, al agregar un nuevo summoner.
        - Investigar los subscribed y unsuscribed events en clientxmpp de LoLChat (Podríamos liberar recursos y actualizar el "update_roster")
            https://github.com/fritzy/SleekXMPP/wiki/Roster-Management
        - Funcionalidad de Borrar mensaje de aviso de en cola cuando lo implementen en la API BOT de telegram. L(392)
        - SPAM(?)
        
        - Añadir varios summoners a la vez por nombre
        - En vez de mostrar una confirmacion, mostrar la lista de /list
        - Al agregar un nuevo amigo ponerle en el grupo "_Seguimiento"
        - Al añadir un nuevo invocador, no busca su estado, solo cuando cambia
        - Que salga el tiempo que se esta en cola (?)
'''

class LoLTracker():
    
    DESCRIPTION = (
        "TrackerBot v0.2.0.\n"
        "=================\n\n"
        
        "Bot de Telegram para hacer seguimiento del estado de invocadores de League of Legends. "
        "Se conecta tanto al chat del cliente del League of Legends como a un chat de Telegram, enviando"
        "información sobre el primero al segundo cuando se le requiera.\n\n"
        
        "Adicionalmente, informará cuando uno de los invocadores a los que se le haga el seguimiento entre"
        "en cola, dando la opción a la gente de Telegram a enviarle un mensaje al chat de LoL para que"
        "les espere para jugar."
    )
    
    CHANGELOG = (
        "v0.1.0\n"
        "    - Release inicial.\n"
        "v0.1.1\n"
        "    - Añadido función anti-spam para que no mande mensajes de \"<Summoner> en cola\" continuamente.\n"
        "    - Parametrizadas unas constantes para hacer mas rapido el despliegue entre entorno de "
              "desarrollo y producción.\n"
        "v0.2.0\n"
        "    - Version reconstruida desde cero.\n"
        "    - Se ha eliminado la función anti-spam por no poder afinarse adecuadamente por falta de datos. "
              "Ahora se pueden silenciar las notificaciones por invocador o para todos los invocadores del "
              "canal especifco desde el que se envie la orden /mute <summoner ID> o /mute all\n"
        "    - Se guardan los ajustes de cada canal en una tabla SQLite para cargarse al iniciar el script"
              "de nuevo.\n"
    )
    
    HELP = (
        "/start - Inicializa el bot. Obligatorio al añadir el bot a un canal.\n"
        "/help - Imprime esta ayuda.\n"
        "/description - Imprime la descripcion de LoLTracker.\n"
        "/changelog - Imprime los cambios por versión.\n"
        
        "/add <Summoner Name> - Añade un invocador para seguimiento.\n"
        "/del <Summoner Id> - Deja de seguir al invocador especificado.\n"
        "/list - Lista los invocadores configurados.\n"
        "/tracked - Imprime el estado de los invocadores.\n"
        "/mute <Summoner Id / all> - Mutea el invocador especificado.\n"
        "/unmute <Summoner Id / all> - Desmutea el invocador especificado.\n"
        
        "/chat_id - Imprime el identificador del grupo o la conversación actual.\n"
    )
    
    """ Instanciación y configuración de atributos """
    def __init__(self, token, debug_level=logging.INFO):
        # Configuración de logueo
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=debug_level
        )
        
        # Instancia del logger para guardar cosas
        self.logger     = logging.getLogger(__name__)
        
        # Atributos del bot de telegram
        self.token      = token     # Token para conectar el bot
        self.bot        = None      # Instancia del bot
                
        # Diccionario de los Chats del bot
        self.chats      = {}
    
        # Atributos de la base de datos
        self.conn       = sqlite3.connect('data.db', check_same_thread=False)
        self.cursor     = self.conn.cursor()
        
        # Riot Watcher (para sacar el ID del invocador a partir de su nombre)
        self.watcher    = RiotWatcher(RIOT_TOKEN, default_region=EUROPE_WEST)
        
        self.lol_chat = LoLChat(
            server=LOL_SERVER,
            port=LOL_PORT,
            user=LOL_USER,
            pwd=LOL_PWD
        )
        
        # Handler para cuando cambia el status de algún invocador en el chat del lol
        self.lol_chat.add_handler('changed_status', self.xmpp_on_changed_status)

        # Cargamos los chats e invocadores guardados
        self.__load_settings()
        
    """ Carga los chats e invocadores asociados a cada uno de ellos. """
    def __load_settings(self):
        self.logger.info('Cargando configuración...')
        
        query = '''
        CREATE TABLE IF NOT EXISTS chats(
            id    INTEGER PRIMARY KEY, 
            name  TEXT
        );
        '''
        self.cursor.execute(query)
        
        query = '''
        CREATE TABLE IF NOT EXISTS summoners (
            id    INTEGER UNSIGNED PRIMARY KEY, 
            name  TEXT
        );
        '''
        self.cursor.execute(query)

        query = '''
        CREATE TABLE IF NOT EXISTS chats_summoners (
            chat_id       INTEGER,
            summoner_id   INTEGER UNSIGNED,
            noticeable    INTEGER,
            PRIMARY KEY (chat_id, summoner_id),
            FOREIGN KEY(chat_id) REFERENCES chats(id),
            FOREIGN KEY(summoner_id) REFERENCES summoners(id)
        );
        '''
        self.cursor.execute(query)
                
        self.cursor.execute('SELECT id, name FROM chats;')
        results = self.cursor.fetchall()
        
        for chat in results:
            # chat[0] -> id , chat[1] -> name
            self.chats[chat[0]] = Chat(chat[0], chat[1])
        
        self.logger.info('Chats añadidos: {}'.format(len(results)))
        
        query = '''
            SELECT chats_summoners.chat_id, summoners.id, summoners.name, chats_summoners.noticeable
            FROM chats_summoners
            INNER JOIN summoners
            ON chats_summoners.summoner_id = summoners.id
            ORDER BY chats_summoners.chat_id;
        '''
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        for row in results:
            self.chats[row[0]].add_summoner(row[1], row[2], row[3])
        
        self.logger.info('Invocadores añadidos: {}'.format(len(results)))
        
        self.logger.info('Configuración aplicada.')
        
    """ Wrapper: Enviar mensaje por un chat de telegram. """    
    def __send_message(self, chat_id, text, reply_markup=None):
        self.bot.sendChatAction(chat_id=chat_id, action=ChatAction.TYPING)
        self.bot.sendMessage(chat_id=chat_id, text=text, reply_markup=reply_markup)

    """ Wrapper peticion a la API de riot con RiotWatcher. """
    def __get_summoner(self, name, region=EUROPE_WEST):
        response = None
        error = None
        try:
            response = self.watcher.get_summoner(name=name, region=region)
        except LoLException as e:
            if e == error_404:
                error = 'Invocador {} no encontrado en {}.'.format(name, region)
            elif e == error_429:
                error = 'Reintentar en {} segundos.'.format(e.headers['Retry-After'])
            else:
                error = 'Error desconocido.'
            # self.__send_message(error)
            self.logger.info(error)
            
        return response, error

    """ Función para conectar el bot a telegram """
    def connect(self):
        self.lol_chat.connect()

        updater = Updater(self.token)
        self.bot = updater.bot
        
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", self.on_start))
        dp.add_handler(CommandHandler("help", self.on_help))
        dp.add_handler(CommandHandler("description", self.on_description))
        dp.add_handler(CommandHandler("changelog", self.on_changelog))
        
        dp.add_handler(CommandHandler("add", self.on_add_summoner, pass_args=True))
        dp.add_handler(CommandHandler("del", self.on_del_summoner, pass_args=True))
        dp.add_handler(CommandHandler("list", self.on_list_summoners))
        dp.add_handler(CommandHandler("tracked", self.on_tracked_summoners))
        dp.add_handler(CommandHandler("mute", self.on_mute, pass_args=True))
        dp.add_handler(CommandHandler("unmute", self.on_unmute, pass_args=True))
        
        dp.add_handler(CommandHandler("chat_id", self.on_chat_id))

        dp.add_handler(CallbackQueryHandler(self.on_send_wait))

        dp.add_error_handler(self.on_error)
        
        updater.start_polling()
        updater.idle()

    """ Método que loguea cuando haya algún error con el procesamiento de algún mensaje. """
    def on_error(self, bot, update, error):
        self.logger.warn('Update {} causó error {}.'.format(update, error))

    """ Cuando el bot sea iniciado en un chat guardamos su chat_id. """
    def on_start(self, bot, update):
        chat_id = update.message.chat_id
        chat_name = update.message.chat.title
        
        # Si el chat_id ya está añadido no lo machacamos
        if not chat_id in self.chats:
            self.chats[chat_id] = Chat(chat_id, chat_name)
            
            self.cursor.execute('INSERT OR IGNORE INTO chats(id, name) VALUES (?, ?);', (chat_id, chat_name))
            self.conn.commit()

            self.logger.info('Bot iniciado en el chat: {} ({}).'.format(chat_name, chat_id))
        
        # Si no es un chat de grupo, enviamos la descripcion. (Es larga para spamearla por un grupo).
        if chat_id > 0:
            self.__send_message(chat_id, LoLTracker.DESCRIPTION)
        
        # Enviamos los comandos en cualquier caso.
        self.__send_message(chat_id, LoLTracker.HELP)
        
    """ Envía la ayuda. """
    def on_help(self, bot, update):
        chat_id = update.message.chat_id
        self.__send_message(chat_id, LoLTracker.HELP)
    
    """ Envía la descripción. """
    def on_description(self, bot, update):
        chat_id = update.message.chat_id
        self.__send_message(chat_id, LoLTracker.DESCRIPTION)
    
    """ Envía el log de cambios. """
    def on_changelog(self, bot, update):
        chat_id = update.message.chat_id
        self.__send_message(chat_id, LoLTracker.CHANGELOG)
    
    """ Añade un invocador en caso de que la API de riot devuelva uno concreto.
    Sino controla la excepcion y la notifica """
    def on_add_summoner(self, bot, update, args):
        if len(args) < 1:
            update.message.reply_text('Argumentos incorrectos')
            return
        
        chat_id = update.message.chat_id

        summoner_name = ' '.join(args)
        
        # Obtenemos la estructura del invocador de la API de riot.
        summoner, error = self.__get_summoner(name=summoner_name, region=EUROPE_WEST)

        # Si ha habido algun error lo notificamos
        if error:
            self.__send_message(chat_id, error)
            return
        
        # Si el invocador al que se quiere hacer el seguimiento no esta agregado como amigo al chat
        # Lo notificamos y lo agregamos al chat
        if summoner['id'] not in self.lol_chat.roster:
            self.logger.info('El invocador {}({}) no está agregado en el chat. Enviando amistad...'.format(summoner['name'], summoner['id']))
            self.lol_chat.add_friend('sum{}@pvp.net'.format(summoner['id']))
            self.__send_message(
                chat_id,
                'Para poder realizar el seguimiento el invocador debe aceptar la petición de {} amistad que se le acaba de mandar.'.format(self.lol_chat.user)
            )

        # Comprobamos si el invocador ya ha sido agregado
        chat = self.chats[chat_id]
        
        # Sino ha sido agregado lo hacemos y notificamos
        if not chat.has_summoner(summoner['id']) and chat.add_summoner(summoner['id'], summoner['name']):
            self.cursor.execute('INSERT OR IGNORE INTO summoners(id, name) VALUES (?, ?);', (summoner['id'], summoner['name']))
            self.cursor.execute('INSERT OR IGNORE INTO chats_summoners(chat_id, summoner_id, noticeable) VALUES (?, ?, ?);', (chat_id, summoner['id'], 1))
            self.conn.commit()

            result = 'Invocador {} ({}) agregado al chat {}.'.format(summoner['name'], summoner['id'], chat_id)
            self.logger.info(result)
            self.__send_message(chat_id, result)
        
    """ Borra el seguimiento del invocador en el canal desde el que se envia el mensaje. """
    def on_del_summoner(self, bot, update, args):
        if len(args) != 1:
            update.message.reply_text('Argumentos incorrectos')
            return
        
        summoner_id = args[0]
        
        chat_id = update.message.chat_id
        chat = self.chats[chat_id]
        tracked_summoners = chat.get_tracked_summoners()
        
        if summoner_id in tracked_summoners:
            summoner = tracked_summoners[summoner_id]
            if chat.del_summoner(summoner_id):
                self.cursor.execute(
                    'DELETE FROM chats_summoners WHERE chat_id = (?) and summoner_id = (?);',
                    (chat_id, summoner_id)
                )
                self.conn.commit()
                
                result = 'Invocador {} ({}) borrado del chat {}.'.format(summoner.name, summoner.id, chat_id)
                self.logger.info(result)
                self.__send_message(chat_id, result)
                
    """ Envía un mensaje con los invocadores en seguimiento. """
    def on_list_summoners(self, bot, update):
        result = ''
        chat_id = update.message.chat_id
        
        summoners = self.chats[chat_id].get_tracked_summoners()
        
        for _, summoner in summoners.items():
            result += "{}\n".format(summoner)
        
        if not result:
            result = '-'
            
        self.__send_message(chat_id, result)
    
    """ Envía un mensaje con el estado de los invocadores en seguimiento. """
    def on_tracked_summoners(self, bot, update):
        result = ''
        chat_id = update.message.chat_id
        
        summoners = self.chats[chat_id].get_tracked_summoners()
        
        for _, summoner in summoners.items():
            result += summoner.get_status()
        
        if not result:
            result = '-'
            
        self.__send_message(chat_id, result)
 
    """ Mutear las notificaciones de un invocador en un canal específico. """
    def on_mute(self, bot, update, args):
        if len(args) != 1:
            update.message.reply_text('Argumentos incorrectos')
            return
    
        chat_id = update.message.chat_id
        chat = self.chats[chat_id]
        summoner_id = args[0]
        
        if summoner_id == 'all':
            for _, summoner in chat.get_tracked_summoners().items():
                summoner.noticeable = False
            
            self.cursor.execute('UPDATE chats_summoners SET noticeable = 0 WHERE chat_id = (?);', (chat_id, ))
            self.conn.commit()
            msg = 'Todos los invocadores silenciados.'
        elif chat.has_summoner(summoner_id):
            summoner = chat.get_summoner(summoner_id)
            summoner.noticeable = False
            
            self.cursor.execute('UPDATE chats_summoners SET noticeable = 0 WHERE chat_id = (?) AND summoner_id = (?);', (chat_id, summoner_id))
            self.conn.commit()
            
            msg = 'Invocador {} ({}) silenciado.'.format(summoner.name, summoner.id)
        else:
            msg = 'Invocador no encontrado'
        
        self.__send_message(chat_id, msg)
            
    """ Desmutear las notificaciones de un invocador en un canal específico. """
    def on_unmute(self, bot, update, args):
            if len(args) != 1:
                update.message.reply_text('Argumentos incorrectos')
                return
        
            chat_id = update.message.chat_id
            chat = self.chats[chat_id]
            summoner_id = args[0]
            
            if summoner_id == 'all':
                for _, summoner in chat.get_tracked_summoners().items():
                    summoner.noticeable = True
                
                self.cursor.execute('UPDATE chats_summoners SET noticeable = 1 WHERE chat_id = (?);', (chat_id, ))
                self.conn.commit()
                msg = 'Todos los invocadores desilenciados.'
            elif chat.has_summoner(summoner_id):
                summoner = chat.get_summoner(summoner_id)
                summoner.noticeable = True
                
                self.cursor.execute('UPDATE chats_summoners SET noticeable = 1 WHERE chat_id = (?) AND summoner_id = (?);', (chat_id, summoner_id))
                self.conn.commit()
                
                msg = 'Invocador {} ({}) desilenciado.'.format(summoner.name, summoner.id)
            else:
                msg = 'Invocador no encontrado'
            
            self.__send_message(chat_id, msg)

    """ Devuelve el ID del chat """
    def on_chat_id(self, bot, update):
        chat_id = update.message.chat_id
        self.__send_message(chat_id, str(chat_id))
    
    """ Se encarga de enviar el mensaje de 'Espera' al chat del LoL. """
    def on_send_wait(self, bot, update):
        query = update.callback_query
        chat_id = query.message.chat_id
        summoner = self.chats[chat_id].get_summoner(query.data)
        
        jid = 'sum' + summoner.id + '@pvp.net'
        
        if query.from_user.username:
            name = query.from_user.username
        else:
            name = query.from_user.first_name
        
        self.lol_chat.send_message(
            mto=jid,
            mbody='¡ESPERA! ' + name + ' quiere jugar contigo.'
        )
        
        notification_text = 'Aviso enviado.'
        edit_text = 'Aviso a {} enviado por {}.'.format(summoner.name, name)
        
        query.answer(text=notification_text, parse_mode=ParseMode.HTML)
        
        bot.editMessageText(
            text='<i>' + edit_text + '</i>',
            chat_id=chat_id,
            message_id=query.message.message_id,
            parse_mode=ParseMode.HTML
        )
        

    """ Cuando cambie el estado de algún invocador que tenemos en el chat, comprobamos si es un invocador
    que tenemos en seguimiento en alguno de los chats abiertos. Si lo está se realizarán distintas acciones
    dependiendo del nuevo estado que tenga.
    
    Estados posibles:
        'outOfGame'             => 
        'inQueue'               => 
        'championSelect'        => 
        'inGame'                => 
        'hostingPracticeGame'   => 
        'hostingNormalGame'     => 
        'hostingRankedGame'     => 
    """
    def xmpp_on_changed_status(self, presence):
        # Si el stanza que recibimos no tiene remitente pasamos del tema
        if not presence['from']:
            return
        
        # Si lo tiene sacamos el ID de invocador a partir de el
        # 'sum26293218@pvp.net[/{RC, xiff, xiff2}]' -> 26293218
        p_from = str(presence['from'])
        summoner_id = p_from[3:p_from.index('@')]
            
        for chat_id, chat in self.chats.items():
            if chat.has_summoner(summoner_id):
                summoner = chat.get_summoner(summoner_id)
                
                # Si es un stanza de desconexion
                if presence['type'] == 'unavailable':
                    summoner.gamestatus = None
                    continue
                
                soup = BeautifulSoup(presence['status'], 'html.parser')
                
                # Hay presencias que no tienen body bien definido (clientes personalizados, bots, etc)
                if soup.body and soup.body.gamestatus and soup.body.gamestatus.text:
                    
                    summoner.gamestatus = soup.body.gamestatus.text
                    
                    if soup.body.gamequeuetype:
                        summoner.gamequeuetype = soup.body.gamequeuetype.text
                        
                    if soup.body.timestamp:
                        summoner.timestamp = soup.body.timestamp.text
                        
                    if soup.body.gamestatus.text  == 'inQueue':
                        # Guardamos su estado en su summoner correspondiente
                        summoner.gamequeuetype = soup.body.gamequeuetype.text
                        summoner.timestamp = soup.body.timestamp
                        
                        # Si se puede notificar sobre este invocador
                        # Preparamos la notificación y el botón para avisar por el chat
                        if summoner.noticeable:
                            
                            keyboard = [[InlineKeyboardButton('¡Espérame que juego!', callback_data=summoner.id)]]
                            markup = InlineKeyboardMarkup(keyboard)
                            
                            
                            self.__send_message(
                                chat_id,
                                '{} ({}) ha entrado en cola. '.format(summoner.name, summoner.id),
                                reply_markup=markup
                            )
                            
                    elif soup.body.gamestatus.text == 'championSelect':
                        # Delete message send in 'inQueue' state
                        pass

TG_TOKEN    = ''
LOL_SERVER  = 'chat.euw1.lol.riotgames.com'
LOL_PORT    = 5223
LOL_USER    = ''
LOL_PWD     = ''

RIOT_TOKEN  = ''
RIOT_REGION = EUROPE_WEST
if __name__ == '__main__':
    lt = LoLTracker(token=TG_TOKEN)

    lt.connect()