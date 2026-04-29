#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import sys

DB_CONFIG = {
    'dbname': 'vuz_lab5',
    'user': 'uliavladimirovna',
    'password': '',
    'host': 'localhost'
}

def get_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print(f"Ошибка подключения: {e}")
        sys.exit(1)

def print_header(col_widths, headers):
    print('┌' + '┬'.join('─' * (w + 2) for w in col_widths) + '┐')
    row = '│'
    for i, h in enumerate(headers):
        row += f' {h:<{col_widths[i]}} │'
    print(row)
    print('├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤')

def print_row(cells, col_widths):
    row = '│'
    for i, cell in enumerate(cells):
        row += f' {str(cell):<{col_widths[i]}} │'
    print(row)

def print_footer(col_widths):
    print('└' + '┴'.join('─' * (w + 2) for w in col_widths) + '┘')

def task1_report(group_param=None, subject_param=None):
    conn = get_connection()
    cur = conn.cursor()
    
    sql = """
    SELECT 
        группа,
        дисциплина,
        средний_балл,
        количество_оценок
    FROM v_report_data
    WHERE (LOWER(группа) LIKE LOWER(%s) OR %s IS NULL)
      AND (LOWER(дисциплина) LIKE LOWER(%s) OR %s IS NULL)
    ORDER BY группа, дисциплина
    """
    
    group_pattern = f"%{group_param}%" if group_param else None
    subject_pattern = f"%{subject_param}%" if subject_param else None
    
    cur.execute(sql, (group_pattern, group_pattern, subject_pattern, subject_pattern))
    rows = cur.fetchall()
    
    print()
    print('=' * 80)
    print('  ОТЧЁТ: СРЕДНИЙ БАЛЛ ПО ГРУППАМ И ДИСЦИПЛИНАМ')
    print('=' * 80)
    if group_param:
        print(f'  Группа: {group_param}')
    if subject_param:
        print(f'  Дисциплина: {subject_param}')
    print('-' * 80)
    
    if not rows:
        print("  Данные не найдены")
        cur.close()
        conn.close()
        return
    
    col_widths = [4, 14, 28, 10, 8]
    headers = ['№', 'Группа', 'Дисциплина', 'Ср.балл', 'Оценок']
    
    print_header(col_widths, headers)
    
    current_group = None
    group_total = 0
    group_count = 0
    grand_total = 0
    grand_count = 0
    row_num = 1
    first_in_group = True
    
    for group, subject, avg_grade, count in rows:
        if current_group != group:
            if current_group is not None:
                avg_total = group_total / group_count if group_count > 0 else 0
                print_row(['', current_group[:12], 'ИТОГО:', f'{avg_total:.2f}', str(int(group_total))], col_widths)
                print('├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤')
                row_num = 1
            
            current_group = group
            group_total = 0
            group_count = 0
            first_in_group = True
        
        group_display = group if first_in_group else ''
        subject_short = subject[:26] + '..' if len(subject) > 26 else subject
        print_row([row_num if first_in_group else '', group_display[:12], subject_short, f'{avg_grade:.2f}', str(int(count))], col_widths)
        
        group_total += avg_grade * count
        group_count += count
        grand_total += avg_grade * count
        grand_count += count
        row_num += 1
        first_in_group = False
    
    if current_group is not None:
        avg_total = group_total / group_count if group_count > 0 else 0
        print_row(['', current_group[:12], 'ИТОГО:', f'{avg_total:.2f}', str(int(group_total))], col_widths)
        print('├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤')
    
    if grand_count > 0:
        grand_avg = grand_total / grand_count
        print_row(['', 'ВСЕГО', '', f'{grand_avg:.2f}', str(int(grand_total))], col_widths)
    print_footer(col_widths)
    
    cur.close()
    conn.close()

def task2_pivot_table(group_param=None):
    conn = get_connection()
    cur = conn.cursor()
    
    sql = """
    SELECT 
        группа,
        дисциплина,
        средний_балл
    FROM v_report_data
    WHERE (LOWER(группа) LIKE LOWER(%s) OR %s IS NULL)
    ORDER BY группа, дисциплина
    """
    group_pattern = f"%{group_param}%" if group_param else None
    cur.execute(sql, (group_pattern, group_pattern))
    rows = cur.fetchall()
    
    fixed_subjects = ['Web-дизайн', 'Базы данных', 'Бухучет', 'Высшая математика', 'Информатика', 'Английский язык']
    
    data = {}
    groups_set = set()
    
    for group, subject, avg_grade in rows:
        if group not in data:
            data[group] = {}
        data[group][subject] = avg_grade
        groups_set.add(group)
    
    groups = sorted(groups_set)
    
    short_names = {
        'Web-дизайн': 'Web',
        'Базы данных': 'БД',
        'Бухучет': 'Бух',
        'Высшая математика': 'Матем',
        'Информатика': 'Инф',
        'Английский язык': 'Англ'
    }
    headers_short = [short_names.get(s, s[:6]) for s in fixed_subjects]
    
    print()
    print('=' * 70)
    print('  СВОДНАЯ ТАБЛИЦА: СРЕДНИЙ БАЛЛ ПО ГРУППАМ')
    print('=' * 70)
    if group_param:
        print(f'  Фильтр: группа содержит "{group_param}"')
    print('-' * 70)
    
    col_widths = [4, 10] + [7] * len(fixed_subjects) + [8]
    headers = ['№', 'Группа'] + headers_short + ['Итого']
    
    print_header(col_widths, headers)
    
    for i, group in enumerate(groups, 1):
        row = [i, group[:8]]
        group_total = 0
        for subject in fixed_subjects:
            val = data.get(group, {}).get(subject, 0)
            row.append(f'{val:.2f}' if val > 0 else '─')
            if val > 0:
                group_total += val
        row.append(f'{group_total:.2f}')
        print_row(row, col_widths)
    
    print_footer(col_widths)
    
    cur.close()
    conn.close()

def show_help():
    print("=" * 60)
    print("  ОТЧЁТЫ ПО БАЗЕ ДАННЫХ ВУЗ")
    print("=" * 60)
    print()
    print("Использование:")
    print("  python lab8_report_fixed.py task1 [группа] [дисциплина]")
    print("  python lab8_report_fixed.py task2 [группа]")
    print()
    print("Примеры:")
    print("  python lab8_report_fixed.py task1")
    print("  python lab8_report_fixed.py task1 ИНФ-101")
    print("  python lab8_report_fixed.py task2")
    print("  python lab8_report_fixed.py task2 ИНФ")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "task1":
        group_param = sys.argv[2] if len(sys.argv) > 2 else None
        subject_param = sys.argv[3] if len(sys.argv) > 3 else None
        task1_report(group_param, subject_param)
    elif command == "task2":
        group_param = sys.argv[2] if len(sys.argv) > 2 else None
        task2_pivot_table(group_param)
    else:
        show_help()
