from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from ezFBfont import ezFBfont
import ezFBfont_micro_full_05 as fnt
import time, os

# ---------- кнопки и встроенный светодиод ----------
BTN_LEFT = Pin(11, Pin.IN, Pin.PULL_DOWN)   # к 3.3V
BTN_RIGHT = Pin(9,  Pin.IN, Pin.PULL_DOWN)  # к 3.3V
LED = Pin(25, Pin.OUT)

# ---------- дисплей и шрифт ----------
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

BRIGHT_LEVELS = [30, 60, 100]
bright_idx = 1

def set_brightness(idx):
    global bright_idx
    bright_idx = idx % len(BRIGHT_LEVELS)
    lvl = BRIGHT_LEVELS[bright_idx]
    try:
        oled.contrast(lvl)
    except AttributeError:
        pass

set_brightness(bright_idx)

font = ezFBfont(oled, fnt)

char_w = fnt.max_width()
char_h = fnt.height()
line_gap = 1
line_h = char_h + line_gap

cols = 128 // char_w
rows = 64 // line_h
content_rows = rows - 3

# ---------- translit + cleaning ----------

_RU_MAP = {
    # Основной русский алфавит (твой оригинал)
    "а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"yo","ж":"zh","з":"z","и":"i","й":"y",
    "к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f",
    "х":"h","ц":"c","ч":"ch","ш":"sh","щ":"sch","ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya",
    "А":"A","Б":"B","В":"V","Г":"G","Д":"D","Е":"E","Ё":"Yo","Ж":"Zh","З":"Z","И":"I","Й":"Y",
    "К":"K","Л":"L","М":"M","Н":"N","О":"O","П":"P","Р":"R","С":"S","Т":"T","У":"U","Ф":"F",
    "Х":"H","Ц":"C","Ч":"Ch","Ш":"Sh","Щ":"Sch","Ъ":"","Ы":"Y","Ь":"","Э":"E","Ю":"Yu","Я":"Ya",
    
    # Специальные символы из твоего запроса
    "¬":"not",    # Отрицание (логическое НЕ)
    "⊕":"oplus",  # Круглый плюс (XOR, симметричная разность)
    "∨":"or",     # Логическое ИЛИ
    "∧":"and",    # Логическое И
    "α":"alpha",  # Альфа (греческая)
    
    # Символы степени и суперскрипты
    "²":"^2", "³":"^3", "⁴":"^4", "⁵":"^5", "⁶":"^6", "⁷":"^7", "⁸":"^8", "⁹":"^9",
    "¹":"^1", "⁰":"^0",
    
    # Другие полезные математические символы
    "×":"x", "÷":"/", "±":"+-", "√":"sqrt", "∞":"inf",
    "∑":"sum", "∏":"prod", "∂":"d", "∆":"delta", "∇":"grad",
    "≠":"!=", "≤":"<=", "≥":">=", "≈":"~", "≡":"==", 
    "→":"->", "←":"<=", "↑":"^", "↓":"v",
    
    # Валюты и пунктуация
    "€":"euro", "£":"pound", "¢":"cent", "¥":"yen", "₽":"rub",
    "№":"no", "§":"par", "°":"deg",
    
    # Стрелки и указатели
    "►":"->", "◄":"<-", "▲":"^", "▼":"v",
    
    # Заглавные греческие (если нужны)
    "Α":"Alpha", "Β":"Beta", "Γ":"Gamma", "Δ":"Delta", "Θ":"Theta",
}


def translit_ru(s: str) -> str:
    out = []
    for ch in s:
        if ch in _RU_MAP:
            out.append(_RU_MAP[ch])
        else:
            out.append(ch)
    return "".join(out)

def clean_text(s: str) -> str:
    s = translit_ru(s)
    out = []
    for ch in s:
        code = ord(ch)
        if ch == "\t":
            continue
        if ch == "\n" or ch == "\r":
            out.append("\\n")
            continue
        if 32 <= code <= 126:
            out.append(ch)
    return "".join(out)

def get_display_name(filename: str) -> str:
    """Транслитерирует имя файла для отображения на экране."""
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
        display = translit_ru(name) + "." + ext
    else:
        display = translit_ru(filename)
    return display

# ---------- виртуальный пейджер с offsets ----------

MAX_PAGE_BYTES = 2048  # макс ~2 КБ на страницу

class VirtualPager:
    """Читает файл по страницам, используя offsets. Не грузит весь файл."""
    def __init__(self, filename, cols_width, content_rows):
        self.filename = filename
        self.cols = cols_width
        self.content_rows = content_rows
        self.page_offsets = []
        self.total_pages = 0
        self._build_page_index()
    
    def _build_page_index(self):
        """Один раз прокручиваем файл, запоминаем offsets для каждой страницы."""
        try:
            f = open(self.filename, "r")
        except OSError:
            self.total_pages = 0
            return

        self.page_offsets = [0]
        line_count = 0
        
        try:
            while True:
                offset = f.tell()
                line = f.readline()
                if not line:
                    break
                
                clean_line = clean_text(line)
                screen_lines = (len(clean_line) + self.cols - 1) // self.cols
                if screen_lines == 0:
                    screen_lines = 1
                
                line_count += screen_lines
                
                if line_count > self.content_rows:
                    self.page_offsets.append(offset)
                    line_count = screen_lines
        finally:
            f.close()
        
        self.total_pages = len(self.page_offsets)
        if self.total_pages == 0:
            self.total_pages = 1
    
    def get_page(self, page_idx):
        """Читает одну страницу по индексу."""
        if page_idx < 0 or page_idx >= self.total_pages:
            return []
        
        try:
            f = open(self.filename, "r")
            f.seek(self.page_offsets[page_idx])
            
            page_lines = []
            line_count = 0
            total_bytes = 0
            
            while True:
                if total_bytes > MAX_PAGE_BYTES:
                    break
                
                line = f.readline()
                if not line:
                    break
                
                clean_line = clean_text(line)
                total_bytes += len(clean_line)
                
                for i in range(0, max(1, len(clean_line)), self.cols):
                    chunk = clean_line[i:i+self.cols]
                    page_lines.append(chunk)
                    line_count += 1
                    if line_count >= self.content_rows:
                        f.close()
                        return page_lines
            
            f.close()
            return page_lines
        except OSError:
            return []

# ---------- состояние кнопок ----------
class ButtonState:
    def __init__(self):
        self.prev_left = 0
        self.prev_right = 0

btn_state = ButtonState()

# ---------- система команд с кнопками (неблокирующая) ----------

def get_command_nonblocking():
    """Проверяет кнопки без блокировки. Возвращает команду или None."""
    left = BTN_LEFT.value()
    right = BTN_RIGHT.value()
    
    cmd = None
    
    # нажатие левой кнопки
    if left == 1 and btn_state.prev_left == 0:
        if right == 1:
            cmd = 'select'
        else:
            cmd = 'up'
    
    # нажатие правой кнопки
    if right == 1 and btn_state.prev_right == 0:
        if left == 1:
            cmd = 'select'
        else:
            cmd = 'down'
    
    btn_state.prev_left = left
    btn_state.prev_right = right
    
    return cmd

# ---------- утилиты файлов ----------

def is_text_file(filename):
    text_extensions = {
        '.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm',
        '.py', '.c', '.cpp', '.h', '.hpp', '.js', '.css', '.yaml', '.yml',
        '.sh', '.bash', '.ini', '.conf', '.log', '.cfg'
    }
    for ext in text_extensions:
        if filename.lower().endswith(ext):
            return True
    if '.' not in filename or filename.startswith('.'):
        return True
    return False

def make_menu_pages(items):
    pages = []
    for i in range(0, len(items), content_rows):
        pages.append(items[i:i+content_rows])
    return pages or [[]]

# ---------- бегущая строка для меню ----------

class ScrollingText:
    def __init__(self, text, display_width, delay=100):
        self.text = text
        self.display_width = display_width
        self.delay = delay
        self.pos = 0
        self.last_time = time.ticks_ms()
    
    def get_frame(self):
        """Возвращает текущий фрейм бегущей строки."""
        now = time.ticks_ms()
        if now - self.last_time >= self.delay:
            # смещаемся на 1 символ, циклим в пределах длины строки
            self.pos = (self.pos + 1) % len(self.text)
            self.last_time = now
        
        if len(self.text) <= self.display_width:
            return self.text
        
        # берем display_width символов начиная с pos, зацикливаем
        result = ""
        for i in range(self.display_width):
            idx = (self.pos + i) % len(self.text)
            result = result + self.text[idx]
        
        return result

# ---------- отрисовка ----------

def draw_header(title="", subtitle="", info=""):
    oled.fill(0)
    font.write(title[:cols], 0, 0)
    font.write((subtitle + " " + info)[:cols], 0, line_h)

def draw_menu_page(items, selected_idx, page_idx, total_pages, title="Menu", all_count=0, scrollers=None):
    draw_header(title, "(" + str(page_idx+1) + "/" + str(total_pages) + ")", str(all_count) + " items")
    start_y = line_h * 3
    for i, item in enumerate(items):
        actual_global_idx = page_idx * (rows - 3) + i
        y = start_y + i * line_h
        prefix = "> " if actual_global_idx == selected_idx else "  "
        
        # если назв более cols-3 символов, используем бегущую строку
        if len(item) > cols - 3:
            if scrollers and i in scrollers:
                text = prefix + scrollers[i].get_frame()
            else:
                text = prefix + item[:cols-3]
        else:
            text = prefix + item
        
        font.write(text, 0, y)
    oled.show()

def draw_text_page(page_lines, filename="", page_idx=0, total_pages=1):
    fname = filename[-cols+2:] if len(filename) > cols-2 else filename
    draw_header(fname, "Page " + str(page_idx+1) + "/" + str(total_pages), "")
    start_y = line_h * 3
    for r, line in enumerate(page_lines):
        y = start_y + r * line_h
        if y < 64:
            font.write(line, 0, y)
    oled.show()

# ---------- режим меню выбора файла ----------

def file_select_menu():
    base_dir = "/chapters"
    try:
        try:
            all_files = os.listdir(base_dir)
        except:
            all_files = []
        
        files = [f for f in all_files if is_text_file(f)]
        
        if not files:
            oled.fill(0)
            font.write("No text files", 0, 0)
            font.write("in /chapters", 0, line_h)
            oled.show()
            time.sleep(2)
            return None
    except Exception as e:
        print("Error listing files:", e)
        return None

    selected = 0
    menu_pages = make_menu_pages(files)
    
    display_files = [get_display_name(f) for f in files]
    display_menu_pages = make_menu_pages(display_files)
    
    # создаём скроллеры для каждого элемента
    scrollers_by_page = {}
    for page_idx, page_items in enumerate(display_menu_pages):
        scrollers_by_page[page_idx] = {}
        for i, item in enumerate(page_items):
            if len(item) > cols - 3:
                scrollers_by_page[page_idx][i] = ScrollingText(item, cols - 3, delay=100)

    while True:
        page_idx = selected // (rows - 3)
        items_on_page = display_menu_pages[page_idx]
        page_scrollers = scrollers_by_page.get(page_idx, {})
        draw_menu_page(items_on_page, selected, page_idx, len(display_menu_pages), "Select file", len(files), page_scrollers)
        
        # неблокирующая проверка кнопок
        cmd = get_command_nonblocking()
        if cmd == 'up':
            selected = (selected - 1) % len(files)
        elif cmd == 'down':
            selected = (selected + 1) % len(files)
        elif cmd == 'select':
            return base_dir + "/" + files[selected]
        
        # небольшая задержка для плавности анимации
        time.sleep(0.1)

# ---------- режим просмотра текста ----------

def text_viewer(filename):
    """Режим чтения с виртуальным пейджером."""
    oled.fill(0)
    font.write("Loading...", 0, 0)
    oled.show()
    
    try:
        pager = VirtualPager(filename, cols, content_rows)
    except Exception as e:
        print("Error:", e)
        oled.fill(0)
        font.write("Error loading", 0, 0)
        font.write(filename[:cols], 0, line_h)
        oled.show()
        time.sleep(2)
        return

    if pager.total_pages == 0:
        oled.fill(0)
        font.write("Empty file", 0, 0)
        oled.show()
        time.sleep(2)
        return

    page_idx = 0
    page_lines = pager.get_page(page_idx)
    draw_text_page(page_lines, filename, page_idx, pager.total_pages)

    while True:
        cmd = get_command_nonblocking()
        if cmd == 'up':
            page_idx = max(0, page_idx - 1)
            page_lines = pager.get_page(page_idx)
            draw_text_page(page_lines, filename, page_idx, pager.total_pages)
        elif cmd == 'down':
            page_idx = min(pager.total_pages - 1, page_idx + 1)
            page_lines = pager.get_page(page_idx)
            draw_text_page(page_lines, filename, page_idx, pager.total_pages)
        elif cmd == 'select':
            return
        
        # небольшая задержка
        time.sleep(0.1)

# ---------- главный цикл ----------

def main_loop():
    print("=== Text Viewer (Virtual Pager) ===")
    while True:
        filename = file_select_menu()
        if filename is None:
            break
        print("Opening:", filename)
        text_viewer(filename)

# ---------- запуск ----------

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nExit")
    except Exception as e:
        print("Error:", e)

