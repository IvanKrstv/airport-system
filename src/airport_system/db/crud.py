"""Универсален CRUD слой.

SQL се сглобява само от описанието в tables.py (имена на таблици и колони, които
пишем ние), а всички СТОЙНОСТИ винаги минават като параметри (%(име)s).
Така потребителският вход никога не влиза в текста на заявката.

Три таблици минават през съхранени процедури:
  - passenger: добавяне и редакция -> sp_insert_update_passenger (с валидации)
  - flight:    изтриване            -> sp_delete_flight
  - ticket:    добавяне             -> sell_ticket (вика се от интерфейса)
"""
from airport_system.db import procedures
from airport_system.db.connection import get_connection, query
from airport_system.db.tables import TABLES, Table


# ---------------------------------------------------------------- четене

def list_rows(table_key: str, order_by: str | None = None,
              descending: bool = False) -> list[dict]:
    table = TABLES[table_key]
    select_parts = [f't."{table.pk}" AS "_pk"']
    joins = []
    order_exprs = {table.pk: f't."{table.pk}"'}

    for col in table.columns:
        if col.type == 'fk':
            ref = TABLES[col.ref]
            alias = f'r_{col.name}'
            joins.append(f'LEFT JOIN "{ref.name}" {alias} '
                         f'ON {alias}."{ref.pk}" = t."{col.name}"')
            expr = ref.label_sql.format(a=alias)
        else:
            expr = f't."{col.name}"'
        select_parts.append(f'{expr} AS "{col.label}"')
        order_exprs[col.name] = expr

    # order_by се търси в речника, т.е. се приема само име на колона от описанието
    order_expr = order_exprs.get(order_by, order_exprs[table.pk])
    direction = 'DESC' if descending else 'ASC'

    statement = (f'SELECT {", ".join(select_parts)} FROM "{table.name}" t '
                 f'{" ".join(joins)} '
                 f'ORDER BY {order_expr} {direction}, t."{table.pk}"')
    return query(statement)


def list_options(table_key: str) -> list[tuple[int, str]]:
    """(id, четим текст) за падащи менюта."""
    table = TABLES[table_key]
    label = table.label_sql.format(a='t')
    rows = query(f'SELECT t."{table.pk}" AS id, {label} AS label '
                 f'FROM "{table.name}" t ORDER BY label')
    return [(row['id'], row['label']) for row in rows]


def get_row(table_key: str, pk_value: int) -> dict | None:
    """Един ред със сурови стойности (id-та), за формата за редакция."""
    table = TABLES[table_key]
    columns = ', '.join(f'"{c.name}"' for c in table.columns)
    rows = query(f'SELECT {columns} FROM "{table.name}" WHERE "{table.pk}" = %(pk)s',
                 {'pk': pk_value})
    return rows[0] if rows else None


#noinspection SqlResolve
def seat_names_for_flight(flight_id: int) -> list[str]:
    """Местата на самолета, който изпълнява полета (по ред и буква)."""
    rows = query(
        r"""
        SELECT s.seat_name
        FROM Seat s
        JOIN Flight f ON f.plane_id = s.plane_id
        WHERE f.flight_id = %(flight_id)s
        ORDER BY NULLIF(regexp_replace(s.seat_name, '\D', '', 'g'), '')::int, s.seat_name
        """,
        {'flight_id': flight_id})
    return [row['seat_name'] for row in rows]

# noinspection SqlResolve
def locked_columns(table_key: str, pk_value: int) -> dict[str, str]:
    """Колони, които не може да се редактират за този запис -> причина."""
    if table_key == 'flight':
        sql = 'SELECT COUNT(*) AS n FROM Ticket WHERE flight_id = %(pk)s'
        reason = 'The plane cannot be changed - this flight has {n} sold ticket(s).'
    elif table_key == 'seat':
        sql = 'SELECT COUNT(*) AS n FROM Ticket WHERE seat_id = %(pk)s'
        reason = 'The plane cannot be changed - this seat has been sold {n} time(s).'
    else:
        return {}
    n = query(sql, {'pk': pk_value})[0]['n']
    return {'plane_id': reason.format(n=n)} if n else {}


# noinspection SqlResolve
def country_name(country_id: int) -> str:
    rows = query('SELECT country_name FROM Country WHERE country_id = %(id)s',
                 {'id': country_id})
    return rows[0]['country_name']


def add(table_key: str, values: dict) -> None:
    table = TABLES[table_key]
    if table_key == 'ticket':
        raise ValueError('Tickets are sold through the sell_ticket procedure.')
    values = _clean_values(table, values)

    if table_key == 'passenger':
        procedures.add_passenger(values['passport_id'], values['passenger_name'],
                                 country_name(values['country_id']))
    else:
        _insert(table, values)


def edit(table_key: str, pk_value: int, values: dict) -> None:
    table = TABLES[table_key]
    if not table.can_edit:
        raise ValueError('This table does not allow editing.')
    values = _clean_values(table, values)

    if table_key == 'passenger':
        procedures.update_passenger(pk_value, values['passport_id'],
                                    values['passenger_name'],
                                    country_name(values['country_id']))
    else:
        _update(table, pk_value, values)


def remove(table_key: str, pk_value: int, force: bool = False) -> None:
    table = TABLES[table_key]
    if not table.can_delete:
        raise ValueError('This table does not allow deleting.')

    if table_key == 'flight':
        procedures.delete_flight(pk_value, force)
    else:
        _execute(f'DELETE FROM "{table.name}" WHERE "{table.pk}" = %(pk)s',
                 {'pk': pk_value})


# ---------------------------------------------------------------- вътрешни

def _clean_values(table: Table, values: dict) -> dict:
    """Взима само колоните от описанието и проверява задължителните полета."""
    cleaned = {}
    for col in table.columns:
        value = values.get(col.name)
        if col.type == 'text':
            value = (value or '').strip()
            if not value:
                if not col.nullable:
                    raise ValueError(f'The field "{col.label}" is required.')
                value = None
        elif value is None:
            raise ValueError(f'The field "{col.label}" is required.')
        cleaned[col.name] = value
    return cleaned


def _insert(table: Table, values: dict) -> None:
    names = ', '.join(f'"{c.name}"' for c in table.columns)
    marks = ', '.join(f'%({c.name})s' for c in table.columns)
    _execute(f'INSERT INTO "{table.name}" ({names}) VALUES ({marks})', values)


def _update(table: Table, pk_value: int, values: dict) -> None:
    assignments = ', '.join(f'"{c.name}" = %({c.name})s' for c in table.columns)
    _execute(f'UPDATE "{table.name}" SET {assignments} WHERE "{table.pk}" = %(_pk)s',
             {**values, '_pk': pk_value})


def _execute(statement: str, params: dict) -> None:
    with get_connection() as connection:
        connection.execute(statement, params)