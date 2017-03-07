#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import sqlite3
import time
import os
import sys
import json
# import utils

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction, ParseMode,\
    InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, InlineQueryHandler
from bs4 import BeautifulSoup
from uuid import uuid4

from riotwatcher import RiotWatcher, LoLException, error_404, error_429

from LoLChat import LoLChat
from Chat import Chat

from settings import *
from decorators import *


class LoLTracker:
    VERSION = 'v0.2.5'

    DESCRIPTION = (
        "TrackerBot " + VERSION + "\n"
        "=================\n"
        "Hace seguimiento del estado de invocadores de League of Legends. "
        "Se conecta tanto al chat del cliente del League of Legends como a un chat de Telegram, enviando "
        "información sobre el primero al segundo cuando se le requiera.\n\n"

        "Adicionalmente, informará cuando uno de los invocadores a los que se le haga el seguimiento entre "
        "en cola, dando la opción a la gente de Telegram a enviarle un mensaje al chat de LoL para que "
        "les espere para jugar."
    )

    CHANGELOG = [
        "v0.2.5\n"
        "   - Corregido un error que hacía que se enviase las estadísticas a un canal distinto del que las había"
        " pedido.\n"
        "   - Corregidos algunos errores tipográficos con los mensajes de descripción y la ayuda de comandos.\n",

        "v0.2.4\n"
        "   - Nuevo método (/restart) para reiniciar el bot, sólo disponible para el dueño @owner.\n"
        "   - Nuevo método (/say) para hablar con un invocador al que se hace seguimiento desde el chat. También es"
        " posible hacerlo desde el modo inline.\n"
        "   - Corregido mensaje de estadísticas y añadidas estadísticas extras utilizando el argumento extended.\n"
        "   - Decoradores pasados a un archivo externo.\n"
        "   - Se ha creado un nuevo decorador de funciones para ejecutarlas sólo si son llamadas desde en sólo en chats"
        " privados (no en grupos).\n"
        "   - Método __list_summoners eliminado.\n"
        "   - Manejador para diferentes eventos de callbacks.\n"
        "   - Nuevo archivo utils.py para separar funciones auxiliares.\n"
        "   - Se ha corregido un error por el que no aparecía el nombre del campeón de un jugador que estuviera en"
        " partida mediante el comando /tracked. Esto era debido a que el campo que informaba del campeón no existe en"
        " la versión del cliente antigua.\n"
        "   - Ahora se proporciona en la descripción de los correspondientes comandos si son de uso privado "
        " (no en conversaciones de grupo) o sólo por el owner.\n"
        "   - Ahora, al conectar el bot, se notifica automáticamente en todos los canales si hay una nueva versión"
        " y sus cambios.\n"
        "   - Ahora al enviar el log de cambios se envia un mensaje por cada version, ya que todos juntos supera la"
        " longitud máxima de 4096 bytes.\n",

        "v0.2.3\n"
        "   - Descripción corregida.\n"
        "   - Añadido soporte para funciones administrativas. Para utilizarlas tan sólo hay que añadir el decorador"
        " @owner al principio del método.\n"
        "   - Aplicados estilos de convención PEP 8 en parte del código.\n"
        "   - Ahora se muestra el campeón que se está jugando.\n"
        "   - Un campo interno de la base de datos (titulo de conversacion) no se guardaba correctamente al iniciar"
        " el bot (/start). Esto era debido a que no consideraba que algunos campos pudieran ser opcionales.\n"
        "   - El diccionario de invocadores de cada chat tendra dos entradas por cada invocador, una con su ID de"
        " invocador y otra con su nombre normalizado (lowercase sin espacios). Puesto que su valor es un puntero a"
        " la misma clase, los cambios de una estarán sincronizados con la otra.\n"
        "   - Las operaciones sobre todos los invocadores todos se pueden hacer con los comodines 'all' y '*'.\n"
        "   - Mover la lógica de mutear, desmutear y borrar invocadores de un chat a la clase Chat.py.\n"
        "   - Mas genericas las funciones de Chat.py de get_summoner (quitar get_summoner_by_name y by id).\n"
        "   - Dejar de mostrar el IDs de invocador, ya que al hacer las operaciones basándonos en el nombre ya"
        " no debería ser necesario..\n"
        "   - Poder Mutear/desmutear varios invocadores, pero no todos.\n"
        "   - Combinar get_tracked_summoners y get_summoners.\n"
        "   - Se ha cambiado la ayuda del bot para reflejar los cambios en los argumentos realizados (* all etc).",

        "v0.2.2\n"
        "   - Se han cambiado los iconos de mute y unmute para que sean mas ilustrativos.\n"
        "   - Ahora intentamos ahorrarnos la petición a riot si existe el invocador en la tabla summoners,"
        " al agregar un nuevo summoner (ya que esa tabla no se borra).\n"
        "   - Creamos settings.orig.py.\n"
        "   - Creamos README.md para el repositorio de github (Pendiente de rellenar).\n"
        "   - Añadida constante con el número de versión.",

        "v0.2.1\n"
        "   - FIX: Si un invocador se desconectaba seguía apareciendo en la lista de seguimiento.\n"
        "   - Ahora se puede agregar a varios invocadores de una sola vez. \"/add name1, name2 ...\".\n"
        "   - Ahora se pueden borrar varios invocadores de una sola vez.\n"
        "   - Ahora se pueden borrar todos los invocadores con la utilizando \"/del all\".\n"
        "   - Se ha mejorado el rendimiento general. Menos bucles empleando conjuntos e intersecciones.\n"
        "   - En las operaciones /add, /del, /mute, /unmute se mostrará la lista de invocadores con los"
        " cambios en vez de una confirmación genérica.\n"
        "   - Se ha añadido un nuevo comando (/last_changes) para mostrar los cambios de la última versión.\n"
        "   - Se ha separado los ajustes de conexión a un archivo aparte para poder ignorarlos en el git.\n"
        "   - Se ha actualizado los comandos de ayuda (/help) en el propio @LoLTrackerBot y con @FatherBot.\n"
        "   - Se ha actualizado la descripción en (/description) y con @FatherBot.",

        "v0.2.0\n"
        "    - Versión reconstruida desde cero.\n"
        "    - Se ha eliminado la función anti-spam por no poder afinarse adecuadamente por falta de datos."
        " Ahora se pueden silenciar las notificaciones por invocador o para todos los invocadores del"
        " canal especifco desde el que se envie la orden /mute <summoner ID> o /mute all\n"
        "    - Se guardan los ajustes de cada canal en una tabla SQLite para cargarse al iniciar el script"
        "de nuevo.",

        "v0.1.1\n"
        "    - Añadido función anti-spam para que no mande mensajes de \"<Summoner> en cola\" continuamente.\n"
        "    - Parametrizadas unas constantes para hacer mas rapido el despliegue entre entorno de"
        " desarrollo y producción.",

        "v0.1.0\n" +
        "    - Release inicial."
    ]

    HELP = (
        "/start - Inicializa el bot. Obligatorio al añadir el bot a un canal.\n"
        "/stop - Borra el registro del chat del bot.\n"
        "/help - Imprime esta ayuda.\n"
        "/description - Imprime la descripción de LoLTracker.\n"
        "/changelog - Imprime los cambios por versión.\n"
        "/last_changes - Imprime los cambios de la última versión.\n"

        "/add <name1[, name2..]> - Sigue a los invocadores especificados.\n"
        "/del <name1[, name2..]> - Deja de seguir a los invocadores especificados.\n"
        "/list - Lista los invocadores configurados.\n"
        "/tracked - Imprime el estado de los invocadores.\n"
        "/mute <* | all | name1[, name2..]> - Mutea al especificado o a todos.\n"
        "/unmute <* | all | name1[, name2..]> - Desmutea al especificado o a todos.\n"

        "/say [<msg> to <name>] - Envía un mensaje a un invocador. Sin argumentos activa el modo inline.\n"

        "/chat_id - (@owner) Imprime el identificador del chat actual.\n"
        "/stats [extended] - (@owner) Mostar estadísticas básicas del bot.\n"
        "/restart - (@owner) Reiniciar el bot."
    )

    MSG_UPDATED = 'LoLTrackerBot actualizado a la versión: {}.\nUtiliza el comando /last_changes para ver los cambios.'

    """ Instanciación y configuración de atributos """
    def __init__(self, token, debug_level=logging.INFO):
        # Configuración de logueo
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=debug_level
        )

        # Instancia del logger para guardar cosas
        self.logger = logging.getLogger(__name__)

        # Atributos del bot de telegram
        self.token = token      # Token para conectar el bot
        self.bot = None         # Instancia del bot
        self.cbs = {}           # Los métodos de los callbacks

        self.summoners = {}

        # Diccionario de los Chats del bot
        self.chats = {}

        # Atributos de la base de datos
        self.conn = sqlite3.connect('data.db', check_same_thread=False)
        self.cursor = self.conn.cursor()

        # Riot Watcher (para sacar el ID del invocador a partir de su nombre)
        self.watcher = RiotWatcher(RIOT_TOKEN, default_region=EUROPE_WEST)

        # Diccionario con el id de campeón como clave y su nombre como valor.
        # ToDo controlar error
        self.champions, error = self.__get_champions()

        self.lol_chat = LoLChat(
            server=LOL_SERVER,
            port=LOL_PORT,
            user=LOL_USER,
            pwd=LOL_PWD
        )

        # Handler para cuando cambia el status de algún invocador en el chat del lol
        self.lol_chat.add_handler('changed_status', self.xmpp_on_changed_status)

        # Cargamos los chats y sus respectivos invocadores.
        self.__load_settings()

    """ Carga los chats e invocadores asociados a cada uno de ellos. """
    def __load_settings(self):
        self.logger.info('Cargando configuración...')

        query = '''
        CREATE TABLE IF NOT EXISTS settings(
            id    INTEGER PRIMARY KEY,
            last_notified_version TEXT UNIQUE,
            created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        '''
        self.cursor.execute(query)

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

        # Precargamos los invocadores que tenemos almacenados en la tabla de summoners.
        # Asi evitamos pedir invocadores a la API en caso de tenerlos en la tabla.
        # ToDo: revisar esto. ¿Se actualiza cuando añadimos un nuevo invocador? Igual no es escalable con muchos summs
        self.cursor.execute('SELECT id, name FROM summoners;')
        results = self.cursor.fetchall()

        # Generamos un diccionario con las claves el nombre del invocador en minúsculas
        self.summoners = {
            summoner[1].replace(' ', '').lower(): {'id': summoner[0], 'name': summoner[1]}
            for summoner in results
        }

        # Cargamos los chats
        self.cursor.execute('SELECT id, name FROM chats;')
        results = self.cursor.fetchall()

        self.chats = {chat[0]: Chat(chat[0], chat[1]) for chat in results}

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
    def __send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        self.bot.sendChatAction(chat_id=chat_id, action=ChatAction.TYPING)
        self.bot.sendMessage(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)

    """ Wrapper peticion a la API de riot con RiotWatcher. """
    def __get_summoners(self, names, region=RIOT_REGION):
        response = None
        error = None
        try:
            response = self.watcher.get_summoners(names=names, region=region)
        except LoLException as e:
            if e == error_404:
                error = 'Invocador: {} no encontrado: en {}.'.format(names, region)
            elif e == error_429:
                error = 'Reintentar en {} segundos.'.format(e.headers['Retry-After'])
            else:
                error = 'Error desconocido. {}'.format(e)
            # self.__send_message(error)
            self.logger.info(error)

        return response, error

    """ Wrapper peticion a la API de riot con RiotWatcher. """
    def __get_champions(self):
        response = None
        error = None
        try:
            response = self.watcher.static_get_champion_list()
            response = {champion['id']: champion['name'] for _, champion in response['data'].items()}
        except LoLException as e:
            error = 'Error desconocido. {}'.format(e)
            # self.__send_message(error)
            self.logger.info(error)

        return response, error

    """ Función para conectar el bot a telegram. """
    def connect(self):
        self.lol_chat.connect()

        updater = Updater(self.token)
        self.bot = updater.bot

        # Comprobamos si hay una nueva versión del bot. Si es así lo notificamos
        self.announce_version()

        dp = updater.dispatcher

        dp.add_handler(CommandHandler("start", self.on_start))
        dp.add_handler(CommandHandler("stop", self.on_stop))
        dp.add_handler(CommandHandler("help", self.on_help))
        dp.add_handler(CommandHandler("description", self.on_description))
        dp.add_handler(CommandHandler("changelog", self.on_changelog))
        dp.add_handler(CommandHandler("last_changes", self.on_last_changes))

        dp.add_handler(CommandHandler("add", self.on_add_summoner, pass_args=True))
        dp.add_handler(CommandHandler("del", self.on_del_summoner, pass_args=True))
        dp.add_handler(CommandHandler("list", self.on_list_summoners))
        dp.add_handler(CommandHandler("tracked", self.on_tracked_summoners))
        dp.add_handler(CommandHandler("mute", self.on_mute, pass_args=True))
        dp.add_handler(CommandHandler("unmute", self.on_unmute, pass_args=True))
        dp.add_handler(CommandHandler("say", self.on_say, pass_args=True))

        dp.add_handler(CommandHandler("chat_id", self.on_chat_id))
        dp.add_handler(CommandHandler("stats", self.on_stats, pass_args=True))
        dp.add_handler(CommandHandler("restart", self.on_restart))

        dp.add_handler(CallbackQueryHandler(self.on_callback))
        self.cbs['send_wait'] = self.cb_send_wait

        dp.add_handler(InlineQueryHandler(self.on_inlinequery))

        dp.add_error_handler(self.on_error)

        updater.start_polling()
        updater.idle()

    """ Comprueba si se notifico la actualización a la última version. En caso de no haberse notificado envía
    un mensaje a cada chat almacenado."""
    def announce_version(self):
        self.cursor.execute('SELECT COUNT(*) FROM settings WHERE last_notified_version = (?);', (self.VERSION,))
        count = self.cursor.fetchone()[0]

        if not count:
            self.cursor.execute('INSERT INTO settings (last_notified_version) VALUES (?);', (self.VERSION,))
            self.conn.commit()
            for _, chat in self.chats.items():
                self.__send_message(chat.id, self.MSG_UPDATED.format(self.VERSION))

            self.logger.info('Versión {} anunciada.'.format(self.VERSION))

    """ Método que loguea cuando haya algún error con el procesamiento de algún mensaje. """
    def on_error(self, _, update, error):
        self.logger.warning('Update {} causó error {}.'.format(update, error))

    """ Cuando el bot sea iniciado en un chat guardamos su chat_id. """
    def on_start(self, _, update):
        chat_id = update.message.chat_id
        chat_name = update.message.chat.title
        if not chat_name:
            chat_name = update.message.chat.first_name
            if update.message.chat.last_name:
                chat_name += ' {}'.format(update.message.chat.last_name)

            if update.message.chat.username:
                chat_name += ' (@{})'.format(update.message.chat.username)

        # Si el chat_id ya está añadido no lo machacamos
        if chat_id not in self.chats:
            self.chats[chat_id] = Chat(chat_id, chat_name)

            self.cursor.execute('INSERT OR IGNORE INTO chats(id, name) VALUES (?, ?);', (chat_id, chat_name))
            self.conn.commit()

            self.logger.info('Bot iniciado en el chat: {} ({}).'.format(chat_name, chat_id))

        # Si no es un chat de grupo, enviamos la descripcion. (Es larga para spamearla por un grupo).
        if chat_id > 0:
            self.__send_message(chat_id, LoLTracker.DESCRIPTION)

        # Enviamos los comandos en cualquier caso.
        self.__send_message(chat_id, LoLTracker.HELP)

    """ Para borrar el registro del chat del bot """
    def on_stop(self, _, update):
        chat_id = update.message.chat_id

        # Si el canal esta cargado
        if chat_id in self.chats:
            # Borramos los registros de la base de datos. Primero la relacion entre chat e invocador.
            self.cursor.execute('DELETE FROM chats_summoners WHERE chat_id = (?);', (chat_id, ))

            # Luego el propio chat. Los invocadores no los borramos nunca.
            self.cursor.execute('DELETE FROM chats WHERE id = (?);', (chat_id, ))
            self.conn.commit()

            # Borramos el chat de la estructura
            self.chats.pop(chat_id)

            # Lo comentamos por el canal
            self.__send_message(chat_id, 'Registro de canal borrado. Inicia con /start para empezar de nuevo')

    """ Envía la ayuda. """
    def on_help(self, _, update):
        chat_id = update.message.chat_id
        self.__send_message(chat_id, LoLTracker.HELP)

    """ Envía la descripción. """
    def on_description(self, _, update):
        chat_id = update.message.chat_id
        self.__send_message(chat_id, LoLTracker.DESCRIPTION)

    """ Envía el log de cambios. """
    def on_changelog(self, _, update):
        chat_id = update.message.chat_id
        for change in self.CHANGELOG:
            self.__send_message(chat_id, change)

    """ Envía los cambios de la última versión. """
    def on_last_changes(self, _, update):
        chat_id = update.message.chat_id
        self.__send_message(chat_id, LoLTracker.CHANGELOG[0])

    """ Añade uno o varios invocadores en caso de que la API de riot los devuelva. """
    def on_add_summoner(self, _, update, args):
        if len(args) == 0:
            update.message.reply_text('Argumentos incorrectos')
            return

        chat_id = update.message.chat_id
        chat = self.chats[chat_id]

        # Tenemos en cuenta los nombres con espacios.
        summoner_names = ' '.join(args).split(', ')

        # La API no admite mas de 40 por petición.
        # Además vamos a quitar los espacios intermedios y convertir todo a minúsculas,
        # ya que el usuario podría generar repeticiones con 'Tzaoh' y 'tzaoh'.
        # A la API da el mismo resultado con 'Dain V', 'dain v' y 'dainv'.
        summoner_names = [name.replace(' ', '').lower() for name in summoner_names[0:40]]

        # Hay que comparar los nombres de la lista con los del diccionario self.summoners.
        # Si están todos en el diccionario, nos podremos ahorrar la petición.
        summoners = {
            name: {'id': self.summoners[name]['id'], 'name': self.summoners[name]['name']}
            for name in summoner_names if name in self.summoners
        }
        error = None

        # Sino tiene el mismo número, quiere decir que hay invocadores no encontrados en nuestra base de datos local.
        # Hacemos una petición a la API de Rito con todos. (Es lo mismo ya que se puede coger hasta 40 en una sola
        # petición).
        if len(summoners) != len(set(summoner_names)):
            summoners, error = self.__get_summoners(names=summoner_names, region=RIOT_REGION)
            self.logger.info('No se han encontrado todos los invocadores en la tabla. Haciendo la petición a Rito.')

        # Si ha habido algun error lo notificamos
        if error:
            self.__send_message(chat_id, error)
            return

        # Lista de de nombres de invocadores que no tenemos añadidos como amigos en el chat del LoL.
        not_subscribed = []

        # Lista de de nombres de invocadores que vamos a seguir (se incluyen los pendientes por aceptar amistad).
        added = []

        for _, summoner in summoners.items():
            # Si el invocador al que se quiere hacer el seguimiento no esta agregado como amigo al chat
            if summoner['id'] not in self.lol_chat.roster_ids:
                not_subscribed.append(summoner['name'])
                self.lol_chat.add_friend('sum{}@pvp.net'.format(summoner['id']))

            # Sino ha sido agregado lo hacemos y notificamos
            if not chat.has_summoner(summoner['id']) and chat.add_summoner(summoner['id'], summoner['name']):
                added.append(summoner['name'])

                self.cursor.execute(
                    'INSERT OR IGNORE INTO summoners(id, name) VALUES (?, ?);',
                    (summoner['id'], summoner['name'])
                )

                self.cursor.execute(
                    'INSERT OR IGNORE INTO chats_summoners(chat_id, summoner_id, noticeable) VALUES (?, ?, ?);',
                    (chat_id, summoner['id'], 1)
                )
        self.conn.commit()

        # Si hay gente que tiene que aceptar lo notificamos y lo enviamos al log.
        if not_subscribed:

            self.logger.info(
                'Los invocadores {} no están agregado en el chat. Petición de amistad enviada.'.format(not_subscribed)
            )

            self.__send_message(
                chat_id,
                'Para activar el seguimiento {} deben aceptar la petición de amistad de {}.'.format(
                    not_subscribed,
                    self.lol_chat.user
                )
            )

        # La gente agregada tambien se loguea. No se notifica, en su lugar se imprime la lista.
        if added:
            self.logger.info('Invocador {} añadidos al chat {}.'.format(added, chat_id))

        self.__send_message(chat_id, chat.list_summoners())

    """ Borra el seguimiento del invocador en el canal desde el que se envia el mensaje. """
    def on_del_summoner(self, _, update, args):
        if len(args) == 0:
            update.message.reply_text('Argumentos incorrectos')
            return

        chat_id = update.message.chat_id
        chat = self.chats[chat_id]
        summoner_names = ' '.join(args).split(', ')

        summoners_deleted = chat.del_summoners(summoner_names)
        # ToDo: Quizás se puede juntar los IDs y los names y sólo hacer un bucle
        summoner_ids = [summoner.id for _, summoner in summoners_deleted.items()]
        summoner_names = [summoner.name for _, summoner in summoners_deleted.items()]

        self.cursor.execute(
            'DELETE FROM chats_summoners WHERE chat_id = (?) and summoner_id IN ({0});'.format(
                ', '.join('?' for _ in summoner_ids)),
            [chat_id] + summoner_ids
        )

        self.conn.commit()
        self.logger.info('Invocador: {} borrado del chat {}.'.format(summoner_names, self.chats[chat_id].name))
        self.__send_message(chat_id, chat.list_summoners())

    """ Envía un mensaje con los invocadores en seguimiento. """
    def on_list_summoners(self, _, update):
        chat_id = update.message.chat_id

        self.__send_message(chat_id, self.chats[chat_id].list_summoners())

    """ Envía un mensaje con el estado de los invocadores en seguimiento. """
    def on_tracked_summoners(self, _, update):
        result = ''
        chat_id = update.message.chat_id

        # summoners = self.chats[chat_id].get_tracked_summoners()
        summoners = self.chats[chat_id].get_summoners()

        for key, summoner in summoners.items():
            result += summoner.get_status()

        if not result:
            result = '-'

        self.__send_message(chat_id, result)

    """ Mutear las notificaciones de un invocador en un canal específico. """
    def on_mute(self, _, update, args):
        if len(args) == 0:
            update.message.reply_text('Argumentos incorrectos')
            return

        chat_id = update.message.chat_id
        chat = self.chats[chat_id]
        summoner_names = ' '.join(args).split(', ')

        summoners_muted = chat.mute_summoners(summoner_names)
        summoner_ids = [summoner.id for _, summoner in summoners_muted.items()]

        self.cursor.execute(
            'UPDATE chats_summoners SET noticeable = 0 WHERE chat_id = (?) AND summoner_id IN ({0});'.format(
                ', '.join('?' for _ in summoner_ids)),
            [chat_id] + summoner_ids
        )

        self.conn.commit()

        self.__send_message(chat_id, chat.list_summoners())

    """ Desmutear las notificaciones de un invocador en un canal específico. """
    def on_unmute(self, _, update, args):
        if len(args) == 0:
            update.message.reply_text('Argumentos incorrectos')
            return

        chat_id = update.message.chat_id
        chat = self.chats[chat_id]
        summoner_names = ' '.join(args).split(', ')

        summoners_unmuted = chat.unmute_summoners(summoner_names)
        summoner_ids = [summoner.id for _, summoner in summoners_unmuted.items()]

        self.cursor.execute(
            'UPDATE chats_summoners SET noticeable = 1 WHERE chat_id = (?) AND summoner_id IN ({0});'.format(
                ', '.join('?' for _ in summoner_ids)),
            [chat_id] + summoner_ids
        )

        self.conn.commit()

        self.__send_message(chat_id, chat.list_summoners())

    """ Método para comunicarte con un invocador desde un chat abierto. """
    def on_say(self, _, update, args):
        chat_id = update.message.chat_id
        chat = self.chats[chat_id]

        if len(args) == 0:
            output = 'Crea un nuevo mensaje: '
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    'Crear mensaje',
                    switch_inline_query_current_chat=''
                )]],
                resize_keyboard=True, one_time_keyboard=True
            )

        else:
            # El invocador que buscar para enviar el mensaje
            slug = args[-1]
            s = chat.get_summoners([slug])
            if s:
                msg = ' '.join(args[:-2])
                summoner = list(s.values())[0]
                output = 'Enviando mensaje "{}" a {}.'.format(msg, summoner.name)

                name = update.message.from_user.username or update.message.from_user.first_name

                self.lol_chat.send_message(
                    mto='sum{}@pvp.net'.format(summoner.id),
                    mbody=name + ': ' + msg
                )
            else:
                output = 'Invocador no encontrado. Agrégale primero con /add a este canal.'

            reply_markup = None

        self.__send_message(chat_id, output, reply_markup=reply_markup)

    """ Devuelve el ID del chat. """
    @owner
    def on_chat_id(self, _, update):
        chat_id = update.message.chat_id
        self.__send_message(chat_id, str(chat_id))

    """ Estadísticas básicas del bot para el dueño. """
    @owner
    def on_stats(self, _, update, args):
        chat_id = update.message.chat_id

        self.cursor.execute('SELECT COUNT(DISTINCT(chat_id)), COUNT(DISTINCT(summoner_id)) FROM chats_summoners;')
        r = self.cursor.fetchone()
        n_chats = r[0]
        n_summoners = r[1]

        self.cursor.execute('SELECT COUNT(*) FROM summoners;')
        t_summoners = self.cursor.fetchone()[0]

        msg = 'Se hace seguimiento a {} invocadores en {} chats.\n' \
              'Invocadores totales almacenados: {}.'.format(n_summoners, n_chats, t_summoners)

        if len(args) == 1 and 'extended' in args:

            for _, chat in self.chats.items():
                summoners = chat.get_summoners()
                summoners = [summoner.name for _, summoner in summoners.items()]
                msg += "\n{}: {}".format(chat.name, ', '.join(summoners))

        self.__send_message(chat_id, msg)

    """ Reiniciar el bot """
    @owner
    def on_restart(self, _, update):
        chat_id = update.message.chat_id
        self.__send_message(chat_id, "Bot is restarting...")
        time.sleep(0.2)

        os.execl(sys.executable, sys.executable, *sys.argv)

    """ Manejador para distintas funciones de callback. """
    def on_callback(self, bot, update):
        data = json.loads(update.callback_query.data, encoding='utf-8')
        if 'action' in data and data['action'] in self.cbs:
            self.cbs[data['action']](bot, update)

    """ Función callback que se encarga de enviar el mensaje de 'Espera' al chat del LoL. """
    def cb_send_wait(self, bot, update):
        query = update.callback_query
        chat_id = query.message.chat_id

        data = json.loads(query.data, encoding='utf-8')
        summoner_id = data['data']['id']

        summoner = self.chats[chat_id].get_summoners([summoner_id])
        summoner = summoner[summoner_id]

        jid = 'sum{}@pvp.net'.format(summoner.id)

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

    """ Método que maneja el inline mode del bot. Se encarga de enviar la lista invocadores de un chat específico
    o de generar un comando para llamar a la función de envío de mensajes /say <mensaje> to <invocador>. Se la invoca
    poniendo @nombre_del_bot en el chat. """
    def on_inlinequery(self, _, update):
        user_id = update.inline_query.from_user.id

        query = update.inline_query.query

        if user_id in self.chats and query:
            summoners = self.chats[user_id].get_summoners()

            results = [InlineQueryResultArticle(
                id=uuid4(),
                title=summoner.name,
                input_message_content=InputTextMessageContent('/say ' + query + ' to ' + summoner.slug())
            ) for _, summoner in summoners.items()]

            update.inline_query.answer(results, cache_time=0)

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
        summoner_id = int(p_from[3:p_from.index('@')])

        for chat_id, chat in self.chats.items():
            summoner = chat.get_summoners([summoner_id])
            if summoner:
                summoner = summoner[summoner_id]

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

                    if soup.body.gamestatus and soup.body.gamestatus.text == 'inQueue':
                        # Guardamos su estado en su summoner correspondiente
                        # summoner.gamequeuetype = soup.body.gamequeuetype.text
                        summoner.timestamp = soup.body.timestamp

                        # Si se puede notificar sobre este invocador
                        # Preparamos la notificación y el botón para avisar por el chat
                        if summoner.noticeable:
                            keyboard = [[InlineKeyboardButton(
                                '¡Espérame que juego!',
                                callback_data=json.dumps(
                                    {'action': "send_wait", 'data': {'id': summoner.id}},
                                    sort_keys=True
                                )
                            )]]
                            markup = InlineKeyboardMarkup(keyboard)

                            self.__send_message(
                                chat_id,
                                '{} ha entrado en cola. '.format(summoner.name),
                                reply_markup=markup
                            )

                    elif soup.body.gamestatus.text == 'championSelect':
                        # Delete message send in 'inQueue' state
                        pass

                    elif soup.body.gamestatus.text == 'inGame' and (soup.body.championid or soup.body.skinname):
                        # Los clientes antiguos no tienen un campo "championID" solo se puede deducir el campeón
                        # a partir de otro campo: skinname
                        try:
                            summoner.champion = self.champions.get(int(soup.body.championid.text), None)
                        except AttributeError:
                            summoner.champion = soup.body.skinname.text

if __name__ == '__main__':
    lt = LoLTracker(token=TG_TOKEN)

    lt.connect()
