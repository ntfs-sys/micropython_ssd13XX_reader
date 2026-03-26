#!/usr/bin/env python3
import json
import sys
import re
import os

RE_H1 = re.compile(r'^#\s+(.+)$')      # Глава
RE_H2 = re.compile(r'^##\s+(.+)$')     # Абзац
RE_H3 = re.compile(r'^###\s+(.+)$')    # Тема

def sanitize_filename(text):
    safe_chars = []
    for ch in text:
        if ch.isalnum() or ch in ' -_.':
            safe_chars.append(ch)
    result = ''.join(safe_chars).strip()
    result = result[:50].replace(' ', '_')
    return result

def split_topics(input_file, output_dir='.'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    chapter_num = 0
    chapter_title = None
    paragraph_num = 0
    paragraph_title = None

    topic_num = 0
    topic_title = None
    topic_lines = []

    topics = []
    created_files = []

    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            s = line.rstrip('\n')

            m1 = RE_H1.match(s)
            m2 = RE_H2.match(s)
            m3 = RE_H3.match(s)

            if m1:
                # новая глава
                chapter_num += 1
                chapter_title = m1.group(1).strip()
                paragraph_num = 0
                paragraph_title = None
                # главу в файл не пишем
                continue

            if m2:
                # новый абзац
                paragraph_num += 1
                paragraph_title = m2.group(1).strip()
                # абзац в файл не пишем
                continue

            if m3:
                # новая тема
                if topic_title is not None:
                    full_num = f"{chapter_num}.{paragraph_num}.{topic_num}"
                    fname = f"{full_num}_{sanitize_filename(topic_title)}.txt"
                    path = os.path.join(output_dir, fname)

                    with open(path, 'w', encoding='utf-8') as out:
                        out.writelines(topic_lines)

                    topics.append({
                        "chapter_num": chapter_num,
                        "chapter_title": chapter_title,
                        "paragraph_num": paragraph_num,
                        "paragraph_title": paragraph_title,
                        "topic_num": topic_num,
                        "topic_title": topic_title,
                        "full_num": full_num,
                        "file": fname,
                    })
                    created_files.append(path)
                    print(f"✓ {fname}")

                topic_num += 1
                topic_title = m3.group(1).strip()
                topic_lines = [line]
                continue

            if topic_title is not None:
                topic_lines.append(line)

    # последняя тема
    if topic_title is not None:
        full_num = f"{chapter_num}.{paragraph_num}.{topic_num}"
        fname = f"{full_num}_{sanitize_filename(topic_title)}.txt"
        path = os.path.join(output_dir, fname)

        with open(path, 'w', encoding='utf-8') as out:
            out.writelines(topic_lines)

        topics.append({
            "chapter_num": chapter_num,
            "chapter_title": chapter_title,
            "paragraph_num": paragraph_num,
            "paragraph_title": paragraph_title,
            "topic_num": topic_num,
            "topic_title": topic_title,
            "full_num": full_num,
            "file": fname,
        })
        created_files.append(path)
        print(f"✓ {fname}")

    return topics, created_files

def create_index(topics, output_file):
    index = {
        "total_topics": len(topics),
        "topics": topics
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Index saved to: {output_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python split_topics.py input.txt [output_dir]")
        return

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found")
        return

    print(f"Splitting '{input_file}' into topic files...\n")
    topics, files = split_topics(input_file, output_dir)

    if not topics:
        print("No topics found!")
        return

    index_file = os.path.join(output_dir, "topics_index.json")
    create_index(topics, index_file)

    print(f"\n✓ Created {len(topics)} topic files")

if __name__ == "__main__":
    main()
