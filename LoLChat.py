#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import sleekxmpp
import dns
import threading
import sys


class LoLChat:
    
    def __init__(self, server, port, user, pwd, debug_level=logging.INFO):
        # Configuración de logueo
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=debug_level
        )
        
        # Instancia del logger para guardar cosas
        self.logger = logging.getLogger(__name__)
        
        self.server = server
        self.port = port
        self.user = user
        self.pwd = pwd
        
        self.xmpp = sleekxmpp.ClientXMPP(
            self.user + '@pvp.net/xiff2',
            'AIR_' + self.pwd
        )

        # Seteamos el evento de session start.
        self.xmpp.add_event_handler('session_start', self.on_session_start, threaded=True)

        # Si nos envian petición de amistad auto-aceptamos.
        self.xmpp.auto_authorize = True
        self.xmpp.auto_subscribe = True
    
        # Para esperar que se actualice el roster
        self.presences_received = threading.Event()
        self.roster_ids = []

    """ Añadir eventos. """
    def add_handler(self, event, handler):
        self.xmpp.add_event_handler(event, handler)
    
    """ Eliminar eventos. """
    def del_handler(self, event, handler):
        self.xmpp.del_event_handler(event, handler)
        
    """ Conectar al chat con los parámetros especificados """
    def connect(self):
        server_ip = dns.resolver.query(self.server)
        if server_ip:
            if self.xmpp.connect((str(server_ip[0]), self.port), use_ssl=True):
                self.xmpp.process(block=False)
                self.xmpp.register_plugin("xep_0199")  # XMPP Ping
                
                self.logger.debug("Connection with the server established.")
                return True
            else:
                self.logger.critical(
                    "Couldn't resolve the server's A record.\nAn update may be required to continue using this."
                )
                sys.exit(-1)
        else:
            self.logger.critical(
                "Couldn't resolve the server's A record.\nAn update may be required to continue using this."
            )
            sys.exit(-1)
    
    """ Envía un mensaje a JID (sum1234567@pvp.net) especificado. """
    def send_message(self, mto, mbody, mtype='chat'):
        self.xmpp.send_message(mto=mto, mbody=mbody, mtype=mtype)

    """ Envía una petición de amistad a un JID especificado. """
    def add_friend(self, jid):
        self.xmpp.send_presence(pto=jid, ptype='subscribe')

    """ Cuando nos conectamos al chat enviamos nuestro estado y recuperamos el roster. """
    def on_session_start(self, _):
        self.xmpp.get_roster()
        self.xmpp.send_presence(ptype="chat", pstatus="<body></body>")
        # self.logger.info("Successfully logged in")
        
        self.presences_received.wait(1)

        # diccionario tipo {'nombre de grupo': ['sum123123123@pvp.net', ''], '': [], ... }
        groups = self.xmpp.client_roster.groups()

        self.roster_ids = [int(item[3:item.index('@')]) for sublist in groups.values() for item in sublist if '@'
                           in item]
