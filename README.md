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

# Optionals but will throw extra-warnings while connecting XMPP server
# python -m pip install pyasn1
# python -m pip install pyasn1-modules
```
* League of Legends account.
* Telegram Bot details.

Screenshots:
---
![List_Command](https://raw.githubusercontent.com/Tzaoh/LoLTracker/master/screenshots/list.png)
![Mute_Command](https://raw.githubusercontent.com/Tzaoh/LoLTracker/master/screenshots/mute.png)
![Tracked Command](https://raw.githubusercontent.com/Tzaoh/LoLTracker/master/screenshots/tracked.png)

TODOs:
---
* Algunas colas no se ven reflejadas porque su gamequeuetype es <gamequeuetype>NONE</gamequeuetype> (cola de entrenamiento)
* Separar el método decorador a una nueva clase
* Al añadir un nuevo invocador, no busca su estado, solo cuando cambia
* Argumento opcional en el método de stats para detalles extensos.
* Quizás estaría un poco mejor la parte de los invocadores cacheados (self.summoners) en el método __load_settings().
* Alguna forma para notificar automaticamente en todos los canales cuando la nueva versión y sus cambios.
* Funcionalidad de Borrar mensaje de aviso de en cola cuando lo implementen en la API BOT de telegram. L(392)
* SPAM(?)
* Como dar de baja conversaciones
