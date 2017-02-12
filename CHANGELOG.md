v0.2.3
---
* Descripción corregida.
* Añadido soporte para funciones administrativas. Para utilizarlas tan sólo hay que añadir el decorador @owner al principio del método.
* Aplicados estilos de convención PEP 8 en parte del código.
* Ahora se muestra el campeón que se está jugando.
* Un campo interno de la base de datos (titulo de conversacion) no se guardaba correctamente al iniciar el bot (/start). Esto era debido a que no consideraba que algunos campos pudieran ser opcionales.
* El diccionario de invocadores de cada chat tendra dos entradas por cada invocador, una con su ID de invocador y otra con su nombre normalizado (lowercase sin espacios). Puesto que su valor es un puntero a la misma clase, los cambios de una estarán sincronizados con la otra
* Las operaciones sobre todos los invocadores todos se pueden hacer con los comodines 'all' y '*'
* Mover la lógica de mutear, desmutear y borrar invocadores de un chat a la clase Chat.py
* Mas genéricas las funciones de Chat.py de get_summoner (quitar get_summoner_by_name y by id)
* Dejar de mostrar el IDs de invocador, ya que al hacer las operaciones basándonos en el nombre ya no debería ser necesario.
* Poder Mutear/desmutear varios invocadores, pero no todos.
* Combinar get_tracked_summoners y get_summoners.
* Se ha cambiado la ayuda del bot para reflejar los cambios en los argumentos realizados (* all etc).

v0.2.2
---
* Intentar ahorrarnos la peticion a riot si existe el ID de invocador en la tabla summoners, al agregar un nuevo summoner.	
* Se han cambiado los iconos de mute y unmute para que sean mas ilustrativos.
* Creamos settings.orig.py.
* Creamos README.md para el repositorio de github.
* Añadida constante con el número de versión.

v0.2.1
---
* FIX: Si un invocador se desconectaba seguía apareciendo en la lista de seguimiento.
* Ahora se puede agregar a varios invocadores de una sola vez. "/add name1, name2 ...".
* Ahora se pueden borrar varios invocadores de una sola vez.
* Ahora se pueden borrar todos los invocadores con la utilizando "/del all".
* Se ha mejorado el rendimiento general. Menos bucles empleando conjuntos e intersecciones.
* En las operaciones /add, /del, /mute, /unmute se mostrará la lista de invocadores con los cambios en vez de una confirmación genérica.
* Se ha añadido un nuevo comando (/last_changes) para mostrar los cambios de la última versión.
* Se ha separado los ajustes de conexión a un archivo aparte para poder ignorarlos en el git.
* Se ha actualizado los comandos de ayuda (/help) en el propio @LoLTrackerBot y con @FatherBot.
* Se ha actualizado la descripción en (/description) y con @FatherBot.

v0.2.0
---
* Version reconstruida desde cero
* Se ha eliminado la función anti-spam por no poder afinarse adecuadamente por falta de datos.
	  Ahora se pueden silenciar las notificaciones por invocador o para todos los invocadores del
	  canal especifco desde el que se envie la orden /mute <summoner ID> o /mute all
* Se guardan los ajustes de cada canal en una tabla SQLite para cargarse al iniciar el script
	  de nuevo.

v0.1.1
---
* Añadido función anti-spam para que no mande mensajes de "<Summoner> en cola" continuamente.
* Parametrizadas unas constantes para hacer mas rapido el despliegue entre entorno de desarrollo y producción
	  
v0.1.0
---
* Release inicial

	
