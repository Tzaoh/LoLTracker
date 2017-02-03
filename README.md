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
	- FIX: Si un invocador se desconectaba seguía apareciendo en la lista de seguimiento.
	- Ahora se puede agregar a varios invocadores de una sola vez. "/add name1, name2 ...".
	- Ahora se pueden borrar varios invocadores de una sola vez.
	- Ahora se pueden borrar todos los invocadores con la utilizando "/del all".
	- Se ha mejorado el rendimiento general. Menos bucles empleando conjuntos e intersecciones.
	- En las operaciones /add, /del, /mute, /unmute se mostrará la lista de invocadores con los cambios en vez de una confirmación genérica.
	- Se ha añadido un nuevo comando (/last_changes) para mostrar los cambios de la última versión.
	- Se ha separado los ajustes de conexión a un archivo aparte para poder ignorarlos en el git.
	- Se ha actualizado los comandos de ayuda (/help) en el propio @LoLTrackerBot y con @FatherBot.
	- Se ha actualizado la descripción en (/description) y con @FatherBot.
v0.2.2
	- Intentar ahorrarnos la peticion a riot si existe el ID de invocador en la tabla summoners, al agregar un nuevo summoner.
	- Se han cambiado los iconos de mute y unmute para que sean mas ilustrativos.
	- Creamos settings.orig.py.
	- Creamos README.md para el repositorio de github.
	- Añadida constante con el número de versión.

Requirements:
	python -m pip install telegram
	python -m pip install bs4
	python -m pip install riotwatcher
	python -m pip install sleekxmpp
	python -m pip install dnspython

    League of Legends account.
    Telegram Bot details.
    
TODOs:
    - Rellenar README.md
    - Quizás estaría un poco mejor la parte de los invocadores cacheados (self.summoners) en el método __load_settings().
    - Alguna forma para notificar automaticamente en todos los canales cuando la nueva versión y sus cambios.
    - Probar markdown de lista de puntos con el changelog.
    - Mutear/desmutear varios invocadores, pero no todos.
    - Metodo para saber información de en cuantos canales está invocadores y caracteristicas
    - Modo admin
    - Investigar los subscribed y unsuscribed events en clientxmpp de LoLChat (Podríamos liberar recursos y actualizar el "update_roster"). https://github.com/fritzy/SleekXMPP/wiki/Roster-Management
    - Funcionalidad de Borrar mensaje de aviso de en cola cuando lo implementen en la API BOT de telegram. L(392)
    - SPAM(?)
    
    - Al añadir un nuevo invocador, no busca su estado, solo cuando cambia
    - Que salga el tiempo que se esta en cola (?)
