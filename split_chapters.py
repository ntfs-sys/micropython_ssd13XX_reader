#!/usr/bin/env python3
"""
Разбивает файл вида inform.txt на отдельные файлы глав.
Имена файлов: 1_Информация.txt, 2_Измерение.txt и т.д.
Создаёт также chapters_index.json для быстрого доступа к спискам.

Использует те же ## N. ... заголовки как маркеры.
"""

import json
import sys
import re
import os

HEAD_RE = re.compile(r'^##\s+([1-9]\d?)\.\s+(.+)$')

CHAPTER_MIN = 1
CHAPTER_MAX = 39

def parse_head(line: str):
    """Парсит заголовок ## N. Текст"""
    m = HEAD_RE.match(line.strip())
    if not m:
        return None
    num_str, title_rest = m.groups()
    num = int(num_str)
    if not (CHAPTER_MIN <= num <= CHAPTER_MAX):
        return None
    return int(num), title_rest.strip()

def sanitize_filename(text):
    """Делает имя файла безопасным из текста заголовка"""
    # Удаляем опасные символы для имён файлов
    safe_chars = []
    for ch in text:
        if ch.isalnum() or ch in ' -_.':
            safe_chars.append(ch)
    result = ''.join(safe_chars).strip()
    # Обрезаем до 50 символов и заменяем пробелы на подчеркивание
    result = result[:50].replace(' ', '_')
    return result

def split_file_into_chapters(input_file, output_dir=None):
    """
    Разбивает файл на главы.
    Имена файлов: 1_Информация.txt, 2_Измерение.txt и т.д.
    
    Возвращает:
    - chapters: список (номер, название, имя_файла)
    - files: созданные файлы
    """
    if output_dir is None:
        output_dir = '.'
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    chapters = []
    current_chapter_num = None
    current_chapter_title = None
    current_chapter_lines = []
    
    created_files = []
    
    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parsed = parse_head(line)
            
            if parsed is not None:
                # Это заголовок новой главы
                new_num, new_title = parsed
                
                # Сохраняем предыдущую главу если она была
                if current_chapter_num is not None:
                    # Имя файла: "1_Информация.txt"
                    safe_title = sanitize_filename(current_chapter_title)
                    filename = f"{current_chapter_num}_{safe_title}.txt"
                    filepath = os.path.join(output_dir, filename)
                    
                    # Записываем содержимое главы
                    with open(filepath, "w", encoding="utf-8") as out:
                        out.writelines(current_chapter_lines)
                    
                    chapters.append({
                        "num": current_chapter_num,
                        "title": current_chapter_title,
                        "file": filename
                    })
                    created_files.append(filepath)
                    
                    print(f"✓ {filename}")
                
                # Начинаем новую главу
                current_chapter_num = new_num
                current_chapter_title = new_title
                current_chapter_lines = [line]  # С самого заголовка
            else:
                # Обычная строка, добавляем в текущую главу
                if current_chapter_num is not None:
                    current_chapter_lines.append(line)
    
    # Сохраняем последнюю главу
    if current_chapter_num is not None:
        safe_title = sanitize_filename(current_chapter_title)
        filename = f"{current_chapter_num}_{safe_title}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as out:
            out.writelines(current_chapter_lines)
        
        chapters.append({
            "num": current_chapter_num,
            "title": current_chapter_title,
            "file": filename
        })
        created_files.append(filepath)
        
        print(f"✓ {filename}")
    
    return chapters, created_files

def create_index(chapters, output_file):
    """Создаёт index JSON для быстрого доступа к главам"""
    index = {
        "total": len(chapters),
        "chapters": chapters
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Index saved to: {output_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python split_chapters.py input.txt [output_dir]")
        print("Example: python split_chapters.py inform.txt ./chapters")
        return

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found")
        return

    print(f"Splitting '{input_file}' into chapters...\n")
    
    chapters, created_files = split_file_into_chapters(input_file, output_dir)
    
    if not chapters:
        print("No chapters found!")
        return
    
    # Создаём index
    index_file = os.path.join(output_dir, "chapters_index.json")
    create_index(chapters, index_file)
    
    print(f"\n✓ Created {len(chapters)} chapter files")
    print(f"✓ Total files created: {len(created_files)}")
    print(f"\nChapters:")
    for ch in chapters:
        print(f"  {ch['num']:2d}. {ch['title'][:60]}")

if __name__ == "__main__":
    main()