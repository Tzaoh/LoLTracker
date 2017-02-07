TrackerBot
---
Bot de Telegram para hacer seguimiento del estado de invocadores de League of Legends.
Se conecta tanto al chat del cliente del League of Legends como a un chat de Telegram, enviando
información sobre el primero al segundo cuando se le requiera.

Adicionalmente, informará cuando uno de los invocadores a los que se le haga el seguimiento entre
en cola, dando la opción a la gente de Telegram a enviarle un mensaje al chat de LoL para que
les espere para jugar.

Requirements:
---
```bash
# python -m pip install telegram
# python -m pip install bs4
# python -m pip install riotwatcher
# python -m pip install sleekxmpp
# python -m pip install dnspython
```
League of Legends account.
Telegram Bot details.
    
TODOs:
---
* Mostrar campeón que se está jugando
* El campo del nombre de la conversación no se guarda bien
* Quizás estaría un poco mejor la parte de los invocadores cacheados (self.summoners) en el método __load_settings().
* Alguna forma para notificar automaticamente en todos los canales cuando la nueva versión y sus cambios.
* Mutear/desmutear varios invocadores, pero no todos.
* Metodo para saber información de en cuantos canales está invocadores y caracteristicas
* Funcionalidad de Borrar mensaje de aviso de en cola cuando lo implementen en la API BOT de telegram. L(392)
* Modo admin (?)
* SPAM(?)
* Al añadir un nuevo invocador, no busca su estado, solo cuando cambia
