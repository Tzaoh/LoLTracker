#!/usr/bin/python
# -*- coding: utf-8 -*-

import time

class Summoner():
    
    def __init__(self, id, name, noticeable):
        # Estos se graban en base de datos
        self.id = id
        self.name = name
        self.noticeable = noticeable
        
        # Estos no
        self.gamestatus = None
        self.gamequeuetype = None
        self.timestamp = None

    def get_status(self):
        status = ''
        if self.gamestatus:
            status = '{} {}'.format('✅' if self.noticeable else '❌', self.name)
            
            if self.gamestatus == 'inGame' and self.gamequeuetype and self.timestamp:
                t = time.time() - int(self.timestamp) / 1000
                m, s = divmod(t, 60)
                status += ": {} ({:.0f}m {:.0f}s)\n".format(self.gamequeuetype, m, s)
            else:
                status += ": {}\n".format(self.gamestatus)
            
        return status
        
    def __str__(self):
        return '{} {} ({})'.format('✅' if self.noticeable else '❌', self.name, self.id)
        