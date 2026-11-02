"""Страница с универсален CRUD (Streamlit): преглед, добавяне, редакция, изтриване."""
from datetime import datetime
from decimal import Decimal

import psycopg
import streamlit as st

from airport_system.db import crud, procedures
from airport_system.db.tables import TABLES, Column, Table


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
        return primary                      # съобщение от RAISE EXCEPTION в процедурата
    if isinstance(error, psycopg.errors.ForeignKeyViolation):
        text = 'Записът е свързан с други записи и не може да бъде изтрит (или сочи към несъществуващ запис).'
    elif isinstance(error, psycopg.errors.UniqueViolation):
        text = 'Вече съществува запис с такава стойност.'
    elif isinstance(error, psycopg.errors.CheckViolation):
        return f'Стойността нарушава ограничение ({diag.constraint_name}).'
    else:
        text = primary
    return f'{text} {detail}' if detail else text


def _attempt(action, success_message: str) -> None:
    """Изпълнява действие; показва грешката или съобщение за успех и опреснява страницата."""
    try:
        action()
    except ValueError as error:
        st.error(str(error))
        return
    except psycopg.Error as error:
        st.error(_error_text(error))
        return
    _flash('success', success_message)
    st.rerun()


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
        day = st.date_input(f'{col.label} – дата', value=start.date(), key=f'{key}_d')
        hour = st.time_input(f'{col.label} – час', value=start.time(), step=60, key=f'{key}_t')
        return datetime.combine(day, hour)

    if col.type == 'fk':
        options = crud.list_options(col.ref)
        if not options:
            st.warning(f'Първо добавете записи в „{TABLES[col.ref].label}“.')
            return None
        ids = [pk for pk, _ in options]
        index = ids.index(default) if default in ids else 0
        return st.selectbox(col.label, ids, index=index,
                            format_func=dict(options).get, key=key)

    raise ValueError(f'Непознат тип поле: {col.type}')


def _form_fields(table: Table, defaults: dict | None, prefix: str) -> dict:
    return {col.name: _field(col, defaults.get(col.name) if defaults else None,
                             f'{prefix}_{col.name}')
            for col in table.columns}


def _pick_record(table: Table, key: str):
    """Падащо меню за избор на запис; връща първичния му ключ (или None)."""
    options = crud.list_options(table.name)
    if not options:
        st.info('Няма записи.')
        return None
    return st.selectbox('Запис', [pk for pk, _ in options],
                        format_func=dict(options).get, key=key)


# ---------------------------------------------------------------- табове

def _view_tab(table: Table) -> None:
    # sort_options = [(table.pk, 'ID')] + [(c.name, c.label) for c in table.columns]
    # left, right = st.columns([3, 2])
    # order_by = left.selectbox('Сортирай по', [name for name, _ in sort_options],
    #                           format_func=dict(sort_options).get, key=f'sort_{table.name}')
    # direction = right.radio('Ред', ['Възходящо', 'Низходящо'], horizontal=True,
    #                         key=f'dir_{table.name}')

    # rows = crud.list_rows(table.name, order_by, direction == 'Низходящо')
    rows = crud.list_rows(table.name)
    st.caption(f'Записи: {len(rows)}')
    st.dataframe(rows, hide_index=True)


def _add_tab(table: Table) -> None:
    if table.name == 'ticket':
        _sell_ticket_form()
        return
    if table.name == 'passenger':
        st.caption('Добавянето минава през процедурата sp_insert_update_passenger (с валидации).')

    with st.form(f'add_form_{table.name}'):
        values = _form_fields(table, None, f'add_{table.name}')
        submitted = st.form_submit_button('Добави', type='primary')
    if submitted:
        _attempt(lambda: crud.add(table.name, values), 'Записът е добавен.')


def _edit_tab(table: Table) -> None:
    pk = _pick_record(table, f'edit_pick_{table.name}')
    if pk is None:
        return
    current = crud.get_row(table.name, pk)
    if current is None:
        st.warning('Записът вече не съществува.')
        return

    with st.form(f'edit_form_{table.name}_{pk}'):
        values = _form_fields(table, current, f'edit_{table.name}_{pk}')
        submitted = st.form_submit_button('Запази промените')
    if submitted:
        _attempt(lambda: crud.edit(table.name, pk, values), 'Записът е обновен.')


def _delete_tab(table: Table) -> None:
    pk = _pick_record(table, f'delete_pick_{table.name}')
    if pk is None:
        return

    force = False
    if table.name == 'flight':
        force = st.checkbox('Изтрий и продадените билети за този полет (необратимо)',
                            key=f'force_{pk}')
    confirmed = st.checkbox('Потвърждавам, че искам да изтрия записа',
                            key=f'confirm_{table.name}_{pk}')
    if st.button('Изтрий', type='primary', disabled=not confirmed,
                 key=f'delete_btn_{table.name}'):
        _attempt(lambda: crud.remove(table.name, pk, force), 'Записът е изтрит.')


def _sell_ticket_form() -> None:
    """Билетите се добавят само през процедурата sell_ticket."""
    flights = crud.list_options('flight')
    employees = crud.list_options('employee')
    if not flights or not employees:
        st.info('За продажба са нужни поне един полет и един служител.')
        return

    st.caption('Продажбата минава през процедурата sell_ticket (транзакция: пътник + билет). '
               'Цената се изчислява автоматично.')
    flight_labels = dict(flights)
    # Полето е извън формата, за да се опреснява списъкът с места при смяна на полета
    flight_id = st.selectbox('Полет', list(flight_labels),
                             format_func=flight_labels.get, key='sell_flight')
    seats = crud.seat_names_for_flight(flight_id)
    country_labels = {None: '— (пътникът вече съществува) —', **dict(crud.list_options('country'))}
    employee_labels = dict(employees)

    with st.form('sell_ticket_form'):
        seat = st.selectbox('Място', seats)
        passport = st.text_input('Паспорт', max_chars=20)
        name = st.text_input('Име (само за нов пътник)', max_chars=50)
        country_id = st.selectbox('Държава (само за нов пътник)', list(country_labels),
                                  format_func=country_labels.get)
        employee_id = st.selectbox('Служител', list(employee_labels),
                                   format_func=employee_labels.get)
        submitted = st.form_submit_button('Продай билет')

    if submitted:
        _attempt(
            lambda: procedures.sell_ticket(
                flight_id, seat, passport,
                name.strip() or None,
                crud.country_name(country_id) if country_id else None,
                employee_id),
            'Билетът е продаден.')


# ---------------------------------------------------------------- страницата

def render() -> None:
    _show_flash()

    table_key = st.selectbox('Таблица', list(TABLES),
                             format_func=lambda key: TABLES[key].label, key='crud_table')
    table = TABLES[table_key]

    if table.name == 'ticket':
        st.caption('Билетите са междинна таблица: само преглед и продажба, '
                   'без редакция и изтриване.')

    names = ['Преглед', 'Добавяне']
    if table.can_edit:
        names.append('Редакция')
    if table.can_delete:
        names.append('Изтриване')
    tabs = st.tabs(names)

    with tabs[0]:
        _view_tab(table)
    with tabs[1]:
        _add_tab(table)

    index = 2
    if table.can_edit:
        with tabs[index]:
            _edit_tab(table)
        index += 1
    if table.can_delete:
        with tabs[index]:
            _delete_tab(table)