"""Compilador del pseudolenguaje descrito en la especificacion a PostgreSQL."""

import sys

from lark import Lark, Transformer, UnexpectedInput, v_args
from lark.exceptions import VisitError


GRAMMAR = r"""
    start: instruction ";"?

    ?instruction: make_stmt
                | get_stmt
                | put_stmt
                | drop_stmt

    make_stmt: "MAKE"i IDENTIFIER "(" field_def ("," field_def)* ")"
    field_def: IDENTIFIER TYPE

    get_stmt: "GET"i projection "FROM"i IDENTIFIER where_clause? sort_clause? top_clause?
    projection: select_item ("," select_item)*
    ?select_item: IDENTIFIER -> selected_field
                | "*"        -> all_fields
    sort_clause: "SORT"i sort_expression
    sort_expression: IDENTIFIER direction?
    direction: "ASC"i  -> ascending
             | "DESC"i -> descending
    top_clause: "TOP"i INTEGER

    put_stmt: "PUT"i IDENTIFIER "(" assignment ("," assignment)* ")" where_clause?
    assignment: IDENTIFIER "=" expression

    drop_stmt: "DROP"i IDENTIFIER where_clause?
    where_clause: "WHERE"i expression

    expression: expression_item+
    ?expression_item: STRING                  -> literal
                    | RAW                     -> raw
                    | "(" expression_arguments? ")" -> parenthesized
    expression_arguments: expression ("," expression)*

    TYPE.5: /(?i:(?:id|num|text|bool|time)!?)/
    IDENTIFIER: /[A-Za-z_][A-Za-z0-9_]*/
    INTEGER: /[0-9]+/
    STRING: /'(?:''|[^'])*'|"(?:\"\"|[^"])*"/
    RAW: /[^\s(),]+/

    %import common.WS
    %ignore WS
"""

_PARSER = Lark(GRAMMAR, parser="lalr", lexer="contextual")


def _check_identifier(identifier):
    if not identifier.replace("_", "a").isalnum() or not (
        identifier[0].isalpha() or identifier[0] == "_"
    ):
        raise ValueError(f"Identificador no valido: {identifier!r}")
    return identifier


@v_args(inline=True)
class _SQLCompiler(Transformer):
    def start(self, statement):
        return statement

    def field_def(self, name, type_name):
        return str(name), str(type_name).lower()

    def make_stmt(self, table, *fields):
        table = _check_identifier(str(table))
        names = [name for name, _ in fields]
        if len(names) != len(set(names)):
            raise ValueError("No se permiten campos repetidos en MAKE.")

        type_sql = {
            "id": "BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY",
            "num": "NUMERIC",
            "text": "TEXT",
            "bool": "BOOLEAN DEFAULT FALSE",
            "time": "TIMESTAMPTZ DEFAULT NOW()",
        }
        definitions = []
        for name, type_name in fields:
            _check_identifier(name)
            required = type_name.endswith("!")
            base_type = type_name[:-1] if required else type_name
            sql_type = type_sql.get(base_type)
            if sql_type is None:
                raise ValueError(f"Tipo no reconocido: {type_name!r}")
            if required:
                sql_type += " NOT NULL"
            definitions.append(f"{name} {sql_type}")
        return f"CREATE TABLE {table} ({', '.join(definitions)});"

    def selected_field(self, name):
        return str(name)

    def all_fields(self):
        return "*"

    def projection(self, *fields):
        if len(fields) == 1 and fields[0] == "ALL":
            return "*"
        return ", ".join(fields)

    def ascending(self):
        return "ASC"

    def descending(self):
        return "DESC"

    def sort_expression(self, field, direction=None):
        return f"{field} {direction}" if direction else str(field)

    def top_clause(self, count):
        return int(str(count))

    def literal(self, value):
        return str(value)

    def raw(self, value):
        return str(value)

    def expression_arguments(self, *values):
        return ", ".join(values)

    def parenthesized(self, value=""):
        return f"( {value} )" if value else "()"

    def expression(self, *parts):
        return " ".join(parts)

    def where_clause(self, condition):
        return ("WHERE", condition)

    def assignment(self, field, value):
        return _check_identifier(str(field)), value

    def get_stmt(self, fields, table, *clauses):
        table = _check_identifier(str(table))
        where = next((value for kind, value in clauses if kind == "WHERE"), None)
        sort = next((value for kind, value in clauses if kind == "SORT"), None)
        limit = next((value for kind, value in clauses if kind == "TOP"), None)
        sql = f"SELECT {fields} FROM {table}"
        if where is not None:
            sql += f" WHERE {where}"
        if sort is not None:
            sql += f" ORDER BY {sort}"
        if limit is not None:
            sql += f" LIMIT {limit}"
        return sql + ";"

    def sort_clause(self, expression):
        return "SORT", expression

    def top_clause(self, count):
        return "TOP", int(str(count))

    def put_stmt(self, table, *parts):
        table = _check_identifier(str(table))
        where = None
        assignments = parts
        if parts and isinstance(parts[-1], tuple) and parts[-1][0] == "WHERE":
            where = parts[-1][1]
            assignments = parts[:-1]
        if len({field for field, _ in assignments}) != len(assignments):
            raise ValueError("No se permiten campos repetidos en PUT.")

        if where is None:
            fields = ", ".join(field for field, _ in assignments)
            values = ", ".join(value for _, value in assignments)
            return f"INSERT INTO {table} ({fields}) VALUES ({values});"
        values = ", ".join(f"{field} = {value}" for field, value in assignments)
        return f"UPDATE {table} SET {values} WHERE {where};"

    def drop_stmt(self, table, *clauses):
        table = _check_identifier(str(table))
        if not clauses:
            return f"DROP TABLE {table};"
        return f"DELETE FROM {table} WHERE {clauses[0][1]};"


_COMPILER = _SQLCompiler()


def compile_line(line):
    """Compila una instruccion del pseudolenguaje en una sentencia PostgreSQL."""
    source = line.strip()
    if not source:
        return ""
    try:
        return _COMPILER.transform(_PARSER.parse(source))
    except UnexpectedInput as error:
        raise ValueError(
            f"Sintaxis no valida en columna {error.column}: {error.get_context(source).strip()}"
        ) from error
    except VisitError as error:
        if isinstance(error.orig_exc, ValueError):
            raise error.orig_exc from error
        raise


def main():
    if len(sys.argv) > 1:
        lines = [" ".join(sys.argv[1:])]
    else:
        lines = sys.stdin

    failed = False
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            print(compile_line(line))
        except (ValueError, TypeError) as error:
            print(f"Linea {line_number}: {error}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
