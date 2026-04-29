#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import matplotlib.pyplot as plt
import sys
import os

DB_CONFIG = {
    'dbname': 'vuz_lab5',
    'user': 'uliavladimirovna',
    'password': '',
    'host': 'localhost'
}

# Создаём папку для скриншотов, если её нет
os.makedirs('docs', exist_ok=True)

def file_exists(filename, force=False):
    """Проверка существования файла"""
    if not force and os.path.exists(filename):
        response = input(f"Файл {filename} уже существует. Перезаписать? (y/N): ")
        return response.lower() != 'y'
    return False

def task3_chart(save_img=False, force=False):
    """Задача 3: Графики количества оценок и среднего балла"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    sql = """
    SELECT 
        DATE_TRUNC('month', дата) as месяц,
        COUNT(*) as количество,
        ROUND(AVG(оценка), 2) as средний_балл
    FROM УСПЕВАЕМОСТЬ
    WHERE дата IS NOT NULL
    GROUP BY DATE_TRUNC('month', дата)
    ORDER BY месяц
    """
    
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        print("Нет данных для построения графика")
        return
    
    months = [row[0] for row in rows]
    counts = [row[1] for row in rows]
    avg_grades = [row[2] for row in rows]
    
    fig, ax1 = plt.subplots(figsize=(12, 5))
    
    ax1.set_xlabel('Дата')
    ax1.set_ylabel('Количество оценок', color='blue')
    ax1.plot(months, counts, color='blue', marker='o', linewidth=2, label='Количество')
    ax1.tick_params(axis='y', labelcolor='blue')
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Средний балл', color='red')
    ax2.plot(months, avg_grades, color='red', marker='s', linewidth=2, label='Средний балл')
    ax2.tick_params(axis='y', labelcolor='red')
    
    plt.title('Динамика успеваемости по месяцам')
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    
    if save_img:
        filename = 'docs/task3_chart.png'
        if file_exists(filename, force):
            print("Сохранение отменено")
        else:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"График сохранён в {filename}")
    
    plt.show()

def task4_chart(group_param=None, save_img=False, force=False):
    """Задача 4: Круговая диаграмма распределения по группам"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    if group_param:
        sql = """
        SELECT ГР.название, COUNT(*) 
        FROM УСПЕВАЕМОСТЬ У
        JOIN ГРУППЫ ГР ON ГР.код = У.группа
        WHERE ГР.название LIKE %s
        GROUP BY ГР.название
        ORDER BY COUNT(*) DESC
        """
        cur.execute(sql, (f"%{group_param}%",))
        filename = f'docs/task4_chart_{group_param}.png'
    else:
        sql = """
        SELECT ГР.название, COUNT(*) 
        FROM УСПЕВАЕМОСТЬ У
        JOIN ГРУППЫ ГР ON ГР.код = У.группа
        GROUP BY ГР.название
        ORDER BY COUNT(*) DESC
        """
        cur.execute(sql)
        filename = 'docs/task4_chart.png'
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        print("Нет данных для построения диаграммы")
        return
    
    labels = [row[0] for row in rows]
    sizes = [row[1] for row in rows]
    
    plt.figure(figsize=(10, 8))
    
    def autopct_format(pct):
        return f'{pct:.1f}%'
    
    plt.pie(sizes, labels=labels, autopct=autopct_format, startangle=90)
    title = 'Распределение оценок по группам'
    if group_param:
        title += f'\n(фильтр: {group_param})'
    plt.title(title)
    plt.axis('equal')
    
    if save_img:
        if file_exists(filename, force):
            print("Сохранение отменено")
        else:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"Диаграмма сохранена в {filename}")
    
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python lab8_chart.py task3 [--save] [--force]")
        print("  python lab8_chart.py task4 [группа] [--save] [--force]")
        print("  python lab8_chart.py save-all [--force]")
        sys.exit(0)
    
    save = '--save' in sys.argv
    force = '--force' in sys.argv
    
    if sys.argv[1] == "task3":
        task3_chart(save, force)
    elif sys.argv[1] == "task4":
        group = None
        for arg in sys.argv[2:]:
            if arg not in ['--save', '--force']:
                group = arg
        task4_chart(group, save, force)
    elif sys.argv[1] == "save-all":
        print("Сохранение всех графиков...")
        task3_chart(True, force)
        task4_chart(None, True, force)
        task4_chart("ИНФ", True, force)
        print("Все графики сохранены в папку docs/")
    else:
        print("Неизвестная команда")
