# Biblioteca Personal

Catálogo personal de libros físicos: se identifican por ISBN, se guardan en una colección y se anotan con estado de lectura, valoración y opinión. Aparte, se apuntan los libros que el usuario quiere comprar.

## Language

### Colección

**Colección**:
El conjunto de libros que el usuario posee y ha guardado en su biblioteca personal. No incluye las Futuras compras.
_Avoid_: Biblioteca (como sinónimo de los datos), lista

**Futuras compras**:
Los libros que el usuario aún no posee pero quiere comprar. Se consultan en su propia sección, separados de la Colección, y no tienen estado de lectura.
_Avoid_: Lista de deseos, wishlist, pendientes (Pendiente es un estado de lectura)

**Compra**:
El paso de un libro de Futuras compras a la Colección. A partir de ese momento cuenta como añadido a la Colección. Un libro solo pasa de Futuras compras a la Colección, nunca al revés.
_Avoid_: Adquisición, mover

**Fecha de entrada**:
Cuándo el libro entró en la Colección. Para un libro que se guardó primero en Futuras compras, es el momento de la Compra, no cuando se apuntó. Mientras está en Futuras compras, es cuándo se apuntó.
_Avoid_: Fecha de creación

**Autor principal**:
El primer autor que figura en la lista de autores de un libro, tal como está escrito.
_Avoid_: Autor (a secas, cuando hay varios), primer autor

### Orden de la colección

Los dos órdenes se aplican igual a la colección y a futuras compras.

**Orden por defecto**:
Los libros del más reciente al más antiguo según su fecha de entrada.
_Avoid_: Orden cronológico, recientes

**Orden por autor**:
Los libros de la A a la Z por el nombre del autor principal, tal como está escrito (sin separar nombre y apellido), sin distinguir mayúsculas ni acentos. Dentro de un mismo autor, por fecha de publicación (los que no tienen fecha, detrás); los libros sin autor van al final.
_Avoid_: Orden alfabético, orden por apellido

**Orden por saga**:
Los libros de la colección agrupados por saga, con las sagas de la A a la Z por su nombre sin distinguir mayúsculas ni acentos. Dentro de una saga, por número de tomo de menor a mayor (los que no tienen tomo, detrás); a igual tomo, por fecha de publicación y después por título. Una saga sale como grupo aunque solo tenga un libro. Los libros sin saga van al final, en su propio grupo, siguiendo el orden por autor. Solo existe en la Colección, no en las Futuras compras.
_Avoid_: Agrupar por serie, vista de sagas

### Sagas

**Saga**:
Grupo de libros que el autor o la editorial publican como una misma obra o secuencia (p. ej. El Señor de los Anillos). Un libro pertenece como mucho a una saga y las sagas no se anidan. Una saga solo existe mientras tiene al menos un libro en la colección.
_Avoid_: Serie, colección, trilogía

**Nombre de saga**:
Dos nombres designan la misma saga si coinciden sin distinguir mayúsculas, acentos ni espacios al principio o al final; se conserva el nombre tal como se escribió la primera vez.

**Número de tomo**:
La posición opcional de un libro dentro de su saga (p. ej. Las dos torres es el tomo 2 de El Señor de los Anillos). Puede ser 0 o fraccionario para precuelas y novelas intermedias (p. ej. 3.5), y dos libros de la misma saga pueden compartirlo (p. ej. dos ediciones). Solo tiene sentido si el libro pertenece a una saga.
_Avoid_: Volumen, entrega, número de serie
