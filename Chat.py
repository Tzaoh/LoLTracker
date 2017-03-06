#!/usr/bin/python
# -*- coding: utf-8 -*-

from Summoner import Summoner


class Chat:
    
    def __init__(self, id, name):        
        # Id del chat
        self.id = id
        
        # Nombre del chat
        self.name = name
        
        # Diccionario con los invocadores que hace seguimiento para este canal
        self.__tracked_summoners = {}
        
    def add_summoner(self, summoner_id, summoner_name, noticeable=True):
        try:
            key = summoner_name.replace(' ', '').lower()
            summoner_id = int(summoner_id)
            summoner = Summoner(summoner_id, summoner_name, noticeable)

            self.__tracked_summoners[summoner_id] = summoner
            self.__tracked_summoners[key] = summoner

            return True
        
        except ValueError:
            return False

    def del_summoners(self, summoner_names):
        summoner_names = [name.replace(' ', '').lower() for name in summoner_names]

        if summoner_names[0] in ['*', 'all']:
            summoners_deleted = {key: summoner for key, summoner in self.__tracked_summoners.items()
                                 if isinstance(key, int)}
            self.__tracked_summoners = {}
        else:
            summoners_deleted = self.get_summoners(summoner_names)
            for _, summoner in summoners_deleted.items():
                del self.__tracked_summoners[summoner.id]
                del self.__tracked_summoners[summoner.name.replace(' ', '').lower()]

        return summoners_deleted

    def get_summoners(self, keys=None):
        result = {summoner.id: summoner for key, summoner in self.__tracked_summoners.items() if not bool(keys) or
                  key in keys}

        return result

    """ Devuelve la lista de invocadores en un chat especifico. """
    def list_summoners(self):
        result = ''

        summoners = self.get_summoners()

        for key, summoner in summoners.items():
            result += "{}\n".format(summoner)

        if not result:
            result = '-'

        return result

    def has_summoner(self, key):
        return key in self.__tracked_summoners

    def mute_summoners(self, summoner_names):
        summoner_names = [name.replace(' ', '').lower() for name in summoner_names]

        if summoner_names[0] in ['*', 'all']:
            # summoners_muted = self.get_tracked_summoners()
            summoners_muted = self.get_summoners()
        else:
            summoners_muted = self.get_summoners(summoner_names)

        for _, summoner in summoners_muted.items():
            summoner.noticeable = False

        return summoners_muted

    def unmute_summoners(self, summoner_names):
        summoner_names = [name.replace(' ', '').lower() for name in summoner_names]

        if summoner_names[0] in ['*', 'all']:
            summoners_unmuted = self.get_summoners()
        else:
            summoners_unmuted = self.get_summoners(summoner_names)

        for _, summoner in summoners_unmuted.items():
            summoner.noticeable = True

        return summoners_unmuted
