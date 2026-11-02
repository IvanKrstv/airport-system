"""Страница с универсален CRUD (Streamlit): преглед, добавяне, редакция, изтриване.

Добавянето, редакцията и изтриването се показват в изскачащи прозорци (st.dialog).
Кой прозорец е отворен пазим в session_state['crud_dialog'] като
(таблица, действие, ID на записа); при всяко изпълнение на скрипта, ако има
такова състояние, извикваме съответната dialog функция.
"""
from datetime import datetime
from decimal import Decimal

import psycopg
import streamlit as st

from airport_system.db import crud, procedures
from airport_system.db.tables import TABLES, Column, Table


DIALOG_KEY = 'crud_dialog'


# ---------------------------------------------------------------- съобщения

def _flash(kind: str, text: str) -> None:
    """Запомня съобщение, което се показва след st.rerun()."""
    st.session_state['flash'] = (kind, text)


def _show_flash() -> None:
    if 'flash' in st.session_state:
        kind, text = st.session_state.pop('flash')
        getattr(st, kind)(text)


def _error_text(error: psycopg.Error) -> str:
    diag = error.diag
    primary = diag.message_primary or str(error)
    detail = diag.message_detail

    if isinstance(error, psycopg.errors.RaiseException):
        return primary  # съобщение от RAISE EXCEPTION в процедурата
    if isinstance(error, psycopg.errors.ForeignKeyViolation):
        text = 'The record is linked to other records and cannot be deleted (or it points to a non-existent record).'
    elif isinstance(error, psycopg.errors.UniqueViolation):
        text = 'A record with this value already exists.'
    elif isinstance(error, psycopg.errors.CheckViolation):
        return f'The value violates a constraint ({diag.constraint_name}).'
    else:
        text = primary
    return f'{text} {detail}' if detail else text


# ---------------------------------------------------------------- отваряне и затваряне на прозорците

def _open_dialog(table: Table, action: str, pk: int | None = None) -> None:
    st.session_state[DIALOG_KEY] = (table.name, action, pk)


def _clear_dialog() -> None:
    st.session_state.pop(DIALOG_KEY, None)


def _close_dialog() -> None:
    """Затваря прозореца: st.rerun() пуска целия скрипт, а той вече не вика dialog функцията."""
    _clear_dialog()
    st.rerun()


def _on_row_button(table: Table, action: str, rows: list[dict]) -> None:
    """Callback на бутоните в таблицата: отваря прозореца за натиснатия ред."""
    click = st.session_state[f'crud_click_{action}_{table.name}']
    _open_dialog(table, action, rows[click['row']]['_pk'])


def _attempt(action, success_message: str) -> None:
    """Изпълнява действие; при грешка я показва в прозореца, при успех го затваря."""
    try:
        action()
    except ValueError as error:
        st.error(str(error))
        return
    except psycopg.Error as error:
        st.error(_error_text(error))
        return
    _flash('success', success_message)
    _close_dialog()


# ---------------------------------------------------------------- полета на формите

def _field(col: Column, default, key: str):
    if col.type == 'text':
        return st.text_input(col.label, value=default or '', max_chars=col.max_len, key=key)

    if col.type == 'int':
        minimum = int(col.min_value) if col.min_value is not None else None
        start = int(default) if default is not None else (minimum if minimum is not None else 0)
        return st.number_input(col.label, min_value=minimum, value=start, step=1, key=key)

    if col.type == 'decimal':
        minimum = float(col.min_value) if col.min_value is not None else 0.0
        start = float(default) if default is not None else minimum
        value = st.number_input(col.label, min_value=minimum, value=start,
                                step=0.01, format='%.2f', key=key)
        return Decimal(str(round(value, 2)))

    if col.type == 'datetime':
        start = default or datetime.now().replace(second=0, microsecond=0)
        day = st.date_input(f'{col.label} – date', value=start.date(), key=f'{key}_d')
        hour = st.time_input(f'{col.label} – time', value=start.time(), step=60, key=f'{key}_t')
        return datetime.combine(day, hour)

    if col.type == 'fk':
        options = crud.list_options(col.ref)
        if not options:
            st.warning(f'First add records to "{TABLES[col.ref].label}".')
            return None
        ids = [pk for pk, _ in options]
        index = ids.index(default) if default in ids else 0
        return st.selectbox(col.label, ids, index=index,
                            format_func=dict(options).get, key=key)

    raise ValueError(f'Unknown field type: {col.type}')


def _form_fields(table: Table, defaults: dict | None, prefix: str) -> dict:
    return {col.name: _field(col, defaults.get(col.name) if defaults else None,
                             f'{prefix}_{col.name}')
            for col in table.columns}


def _form_buttons(submit_label: str) -> tuple[bool, bool]:
    """Бутоните „потвърди“ и „Отказ“ в края на форма."""
    left, right = st.columns(2)
    submitted = left.form_submit_button(submit_label, type='primary', width='stretch')
    cancelled = right.form_submit_button('Cancel', width='stretch')
    return submitted, cancelled


# ---------------------------------------------------------------- таблицата с бутони

def _table_view(table: Table, rows: list[dict]) -> None:
    st.caption(f'Records: {len(rows)} · click a column header to sort')
    if not rows:
        st.info('No records.')
        return

    # Колоните с бутони: стойността в клетката е надписът на бутона.
    # click['row'] е позицията в подадените данни, дори таблицата да е сортирана в браузъра.
    column_config = {'_pk': None}           # служебната колона с ID не се показва
    actions = [(action, icon, help_text)
               for action, icon, help_text, allowed in (
                   ('edit', ':material/edit:', 'Edit', table.can_edit),
                   ('delete', ':material/delete:', 'Delete', table.can_delete))
               if allowed]
    data = [{**row, **{f'_{action}': icon for action, icon, _ in actions}} for row in rows]
    for action, _, help_text in actions:
        column_config[f'_{action}'] = st.column_config.ButtonColumn(
            '', help=help_text, type='tertiary', width=40,
            key=f'crud_click_{action}_{table.name}',
            on_click=_on_row_button, args=(table, action, rows))

    st.dataframe(data, hide_index=True, column_config=column_config,
                 key=f'crud_grid_{table.name}')


# ---------------------------------------------------------------- съдържание на прозорците

def _add_body(table: Table) -> None:
    if table.name == 'passenger':
        st.caption('Adding goes through the sp_insert_update_passenger procedure (with validation).')

    with st.form(f'add_form_{table.name}', border=False):
        values = _form_fields(table, None, f'add_{table.name}')
        submitted, cancelled = _form_buttons('Add')
    if cancelled:
        _close_dialog()
    if submitted:
        _attempt(lambda: crud.add(table.name, values), 'Record added.')


def _edit_body(table: Table, pk: int) -> None:
    current = crud.get_row(table.name, pk)
    if current is None:
        st.warning('The record no longer exists.')
        return

    with st.form(f'edit_form_{table.name}_{pk}', border=False):
        values = _form_fields(table, current, f'edit_{table.name}_{pk}')
        submitted, cancelled = _form_buttons('Save')
    if cancelled:
        _close_dialog()
    if submitted:
        _attempt(lambda: crud.edit(table.name, pk, values), 'Record updated.')


def _delete_body(table: Table, pk: int, rows: list[dict]) -> None:
    row = next((r for r in rows if r['_pk'] == pk), None)
    if row is None:
        st.warning('The record no longer exists.')
        return

    # Показваме реда с четимите стойности (имена вместо ID-та на външните ключове)
    for label, value in row.items():
        if label != '_pk':
            st.markdown(f'**{label}:** {value if value is not None else "—"}')

    force = False
    if table.name == 'flight':
        force = st.checkbox('Also delete the tickets sold for this flight (irreversible)',
                            key=f'force_{table.name}_{pk}')
    confirmed = st.checkbox('Confirm that you want to delete this record',
                            key=f'confirm_{table.name}_{pk}')

    left, right = st.columns(2)
    if left.button('Delete', type='primary', disabled=not confirmed, width='stretch',
                   key=f'delete_btn_{table.name}_{pk}'):
        _attempt(lambda: crud.remove(table.name, pk, force), 'Record deleted.')
    if right.button('Cancel', width='stretch', key=f'cancel_del_{table.name}_{pk}'):
        _close_dialog()


def _sell_ticket_body() -> None:
    """Билетите се добавят само през процедурата sell_ticket."""
    flights = crud.list_options('flight')
    employees = crud.list_options('employee')
    if not flights or not employees:
        st.info('Selling a ticket requires at least one flight and one employee.')
        return

    st.caption('The sale goes through the sell_ticket procedure (transaction: passenger + ticket). '
               'The price is calculated automatically.')
    flight_labels = dict(flights)
    # Полето е извън формата, за да се опреснява списъкът с места при смяна на полета
    flight_id = st.selectbox('Flight', list(flight_labels),
                             format_func=flight_labels.get, key='sell_flight')
    seats = crud.seat_names_for_flight(flight_id)
    country_labels = {None: '— (existing passenger) —', **dict(crud.list_options('country'))}
    employee_labels = dict(employees)

    with st.form('sell_ticket_form', border=False):
        seat = st.selectbox('Seat', seats)
        passport = st.text_input('Passport', max_chars=20)
        name = st.text_input('Name (new passenger only)', max_chars=50)
        country_id = st.selectbox('Country (new passenger only)', list(country_labels),
                                  format_func=country_labels.get)
        employee_id = st.selectbox('Employee', list(employee_labels),
                                   format_func=employee_labels.get)
        submitted, cancelled = _form_buttons('Sell ticket')

    if cancelled:
        _close_dialog()
    if submitted:
        _attempt(
            lambda: procedures.sell_ticket(
                flight_id, seat, passport,
                name.strip() or None,
                crud.country_name(country_id) if country_id else None,
                employee_id),
            'Ticket sold.')


# ---------------------------------------------------------------- dialog функции
#
# Само един прозорец може да е отворен наведнъж. При затваряне с X / ESC / клик
# извън него on_dismiss изчиства състоянието, за да не се отвори отново.

@st.dialog('Add', width='medium', on_dismiss=_clear_dialog)
def _add_dialog(table: Table) -> None:
    st.caption(table.label)
    _add_body(table)


@st.dialog('Sell ticket', width='medium', on_dismiss=_clear_dialog)
def _sell_dialog() -> None:
    _sell_ticket_body()


@st.dialog('Edit', width='medium', on_dismiss=_clear_dialog)
def _edit_dialog(table: Table, pk: int) -> None:
    st.caption(f'{table.label} · record #{pk}')
    _edit_body(table, pk)


@st.dialog('Delete', width='medium', on_dismiss=_clear_dialog)
def _delete_dialog(table: Table, pk: int, rows: list[dict]) -> None:
    st.caption(f'{table.label} · record #{pk}')
    _delete_body(table, pk, rows)


def _show_open_dialog(table: Table, rows: list[dict]) -> None:
    state = st.session_state.get(DIALOG_KEY)
    if state is None:
        return
    table_name, action, pk = state
    if table_name != table.name:            # остатък от друга таблица
        _clear_dialog()
        return

    if action == 'add':
        if table.name == 'ticket':
            _sell_dialog()
        else:
            _add_dialog(table)
    elif action == 'edit':
        _edit_dialog(table, pk)
    elif action == 'delete':
        _delete_dialog(table, pk, rows)


# ---------------------------------------------------------------- страницата

def render() -> None:
    _show_flash()

    left, right = st.columns([4, 1], vertical_alignment='bottom')
    table_key = left.selectbox('Table', list(TABLES),
                               format_func=lambda key: TABLES[key].label, key='crud_table')
    table = TABLES[table_key]
    add_label = 'Sell ticket' if table.name == 'ticket' else 'Add'
    right.button(add_label, icon=':material/add:', type='primary', width='stretch',
                 key=f'add_btn_{table.name}', on_click=_open_dialog, args=(table, 'add'))

    if table.name == 'ticket':
        st.caption('Tickets are a junction table: view and sell only, '
                   'no editing or deleting.')

    rows = crud.list_rows(table.name)
    _table_view(table, rows)
    _show_open_dialog(table, rows)
