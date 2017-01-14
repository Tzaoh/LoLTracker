#!/usr/bin/python
# -*- coding: utf-8 -*-


# 250219289:AAF-zuy5zDRt5Ukw8yA1bc7Qsf7ud7ASBEs
    
import logging

from Summoner import Summoner

class Chat():
    
    def __init__(self, id, name):        
        # Id del chat
        self.id = id
        
        # Nombre del chat
        self.name = name
        
        # Diccionario con los invocadores que hace seguimiento para este canal
        self.__tracked_summoners = {}
        
    def add_summoner(self, summoner_id, summoner_name, noticeable=True):
        try:
            summoner_id = int(summoner_id)
            self.__tracked_summoners[summoner_id] = Summoner(summoner_id, summoner_name, noticeable)            
            
            return True
        
        except ValueError:
            return False
        
    def del_summoner(self, summoner_id):
        item = self.__tracked_summoners.pop(summoner_id)
        return bool(item)
    
    def get_summoner(self, summoner_id):
        result = None
        if summoner_id in self.__tracked_summoners:
            result = self.__tracked_summoners[summoner_id]
            
        return result
    
    def has_summoner(self, summoner_id):
        return summoner_id in self.__tracked_summoners
        
    def get_tracked_summoners(self):
        return self.__tracked_summoners