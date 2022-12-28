Este módulo agrega un nuevo campo que indica el estado de un contacto con respecto al SAT. Los estados son los siguientes:

* ``Desconocido``: El contacto no figura en la lista de "vigilados" por el sat (Es lo más común)
* ``Desvirtuado``: El SAT reconoce que no teníá por qué vigilar al contacto
* ``Favorable``: El contacto apeló ante el SAT y recibió una sentencia favorable
* ``Presunto``: ⚠ El SAT sospecha que el contacto factura operaciones simuladas
* ``Definitivo``: 🛑 El SAT identifica el contacto como un EFOS

Se identifica como ``Peligro`` si el contacto está en el estado de ``Presunto`` o ``Definitvo``.

Se agrega el campo de Estado en SAT en la vista de lista (opcional), adicionalmente existe u nuevo filtro ``EFOS`` que muestra aquellos contactos en los estados de ``Peligro``.

En las facturas, si el contacto relacionado está en ``Peligro``, se muestra un icono a lado del mismo.

En la vista de lista de las facturas, las que estén relacionadas a un contacto en ``Peligro``, se muestra un mensaje de advertencia.

Existe una tarea programada que (por defecto) es ejecutada cada día el cual descarga la lista de EFOS directamente del SAT y revisa los contactos existentens para determinar su estado.
