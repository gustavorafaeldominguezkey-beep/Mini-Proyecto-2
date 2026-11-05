
Mini Proyecto 2


Especificación del Pseudolenguaje PostgreSQL
1. Visión General y Filosofía
Esta especificación define un pseudolenguaje minimalista y orientado a líneas que se compila directamente en PostgreSQL estándar. Las instrucciones y palabras clave del pseudolenguaje (MAKE, GET, PUT, DROP), así como el código SQL resultante, se mantienen en inglés, mientras que todas las explicaciones, reglas gramaticales y notas técnicas se presentan en español.
2. Reglas Sintácticas Fundamentales
Ejecución por Líneas: Cada instrucción se define en una única línea. No se requieren delimitadores de bloque (como BEGIN/END) ni punto y coma al final de las sentencias del pseudocódigo.
Palabras Clave: Las instrucciones del lenguaje se escriben en inglés (MAKE, GET, PUT, DROP, WHERE, SORT, TOP).
Separadores: Los argumentos y campos se separan mediante comas.
Condicionales: Las cláusulas de filtrado utilizan la palabra clave WHERE.
3. Mapeo de Tipos de Datos
El pseudolenguaje utiliza identificadores de tipos simplificados que se traducen directamente a tipos de PostgreSQL:


Tipo en Pseudolenguaje
Descripción
Tipo en PostgreSQL
id
Clave primaria autoincremental
BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY
num
Valor numérico / decimal
NUMERIC
text
Cadena de texto UTF-8
TEXT
text!
Texto obligatorio (no nulo)
TEXT NOT NULL
bool
Valor booleano (falso por defecto)
BOOLEAN DEFAULT FALSE
time
Marca de tiempo con zona horaria
TIMESTAMPTZ DEFAULT NOW()


Agregar un signo de exclamación (!) al final de cualquier tipo añade la restricción NOT NULL en PostgreSQL.
4. Instrucciones y Operaciones 
4.1 MAKE (Definición de Tablas / DDL)
Propósito: Crea una nueva tabla.
Sintaxis: MAKE <table_name> (<field1> <type>, <field2> <type>, ...)
Equivalente en PostgreSQL: CREATE TABLE <table_name> (...)
4.2 GET (Consultas / DQL)
Propósito: Obtiene registros de una tabla.
Sintaxis: GET <fields> FROM <table_name> [WHERE <condition>] [SORT <field>] [TOP <n>]
Equivalente en PostgreSQL: SELECT <fields> FROM <table_name> [WHERE <condition>] [ORDER BY <field>] [LIMIT <n>]
4.3 PUT (Inserción y Modificación / DML)
Propósito: Inserta o actualiza registros según la presencia de la cláusula WHERE.
Inserción (sin WHERE): PUT <table_name> (<field1> = <value1>, <field2> = <value2>)
PostgreSQL Equivalent: INSERT INTO  (, ) VALUES (, )
Actualización (con WHERE): PUT <table_name> (<field1> = <value1>) WHERE <condition>
PostgreSQL Equivalent: UPDATE  SET  =  WHERE <condición>
4.4 DROP (Eliminación de Datos y Tablas / DML y DDL)
Propósito: Elimina filas específicas o borra la tabla por completo.
Borrar Registros (con WHERE): DROP <table_name> WHERE <condition>
PostgreSQL Equivalent: DELETE FROM  WHERE <condición>
Eliminar Tabla (sin WHERE): DROP <table_name>
PostgreSQL Equivalent: DROP TABLE 
5. Ejemplos Completos de Compilación
Ejemplo 1: Creación de Tabla
Instrucción (Pseudolenguaje):
MAKE users (id id, name text, email text!, created time)

Resultado PostgreSQL:


CREATE TABLE users (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name TEXT,
  email TEXT NOT NULL,
  created TIMESTAMPTZ DEFAULT NOW()
);
Ejemplo 2: Inserción de Datos
Instrucción (Pseudolenguaje):
PUT users (name = 'Alex', email = 'alex@test.com')

Resultado PostgreSQL:


INSERT INTO users (name, email)
VALUES ('Alex', 'alex@test.com');
Ejemplo 3: Consulta de Datos
Instrucción (Pseudolenguaje):
GET name, email FROM users WHERE name = 'Alex' SORT created TOP 5

Resultado PostgreSQL:


SELECT name, email
FROM users
WHERE name = 'Alex'
ORDER BY created
LIMIT 5;
Ejemplo 4: Modificación de Registros
Instrucción (Pseudolenguaje):
PUT users (name = 'Alexander') WHERE email = 'alex@test.com'

Resultado PostgreSQL:


UPDATE users
SET name = 'Alexander'
WHERE email = 'alex@test.com';
Ejemplo 5: Eliminación de Registros y Tabla
Instrucciones (Pseudolenguaje):
DROP users WHERE name = 'Alex'
DROP users

Resultado PostgreSQL:


DELETE FROM users WHERE name = 'Alex';
DROP TABLE users;
