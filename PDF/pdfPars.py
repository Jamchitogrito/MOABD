import fitz
import pandas as pd
import io
import glob
import re
from IPython.display import display

all_pdf = glob.glob(r'pdfFiles/*.pdf')
print(len(all_pdf))
print(all_pdf)


pdf_document = r"pdfFiles/Объектно ориентированное програмирование в графических языках _ Хабр.pdf"
doc = fitz.open(pdf_document)
print("Исходный документ: ", doc)
print("\nКоличество страниц: %i\n\n------------------\n\n" % doc.page_count)
for current_page in range(2):
    page = doc.load_page(current_page)
    page_text = page.get_text("text")
    print("Стр. ", current_page+1, "\n")
    print(page_text)
    


def parse_habr_article(text):
    """Парсит статью с Хабра по структуре внизу страницы"""
    lines = text.split('\n')
    result = {
        'author': '',
        'date': '',
        'title': '',
        'read_time': '',
        'views': '',
        'tags': ''
    }
    
    for i, line in enumerate(lines):
        if re.match(r'^[a-z0-9\-]+$', line.strip(), re.I):
            result['author'] = line.strip()
            
            # Следующая строка дата
            if i + 1 < len(lines):
                result['date'] = lines[i + 1].strip()
            
            # Через 1-2 строки заголовок
            if i + 2 < len(lines):
                result['title'] = lines[i + 2].strip()
            
            # Ещё через 1-2 строки время чтения
            if i + 3 < len(lines):
                time_match = re.search(r'(\d+\s*мин)', lines[i + 3])
                if time_match:
                    result['read_time'] = time_match.group(1)
            
            # Просмотры через строку после времени
            if i + 4 < len(lines):
                views_match = re.search(r'(\d+(?:\.\d+)?[KМ])', lines[i + 4])
                if views_match:
                    result['views'] = views_match.group(1)
            
            # Теги в следующей строке с символами * 
            if i + 5 < len(lines) and '*' in lines[i + 5]:
                result['tags'] = lines[i + 5].strip()
            
            break
    
    return result

for pdf_path in all_pdf:
    doc = fitz.open(pdf_path)
    first_page = doc[0].get_text("text")
    data = parse_habr_article(first_page)
    print(f"\n=== {pdf_path.split('/')[-1]} ===")
    print(f"Автор: {data['author']}")
    print(f"Дата: {data['date']}")
    print(f"Заголовок: {data['title']}")
    print(f"Время: {data['read_time']}")
    print(f"Просмотры: {data['views']}")
    doc.close()
    
def extract_text_from_pdf(pdf_path):
    """Извлекает весь текст из PDF постранично"""
    doc = fitz.open(pdf_path)
    text_pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_pages.append(page.get_text("text"))
    doc.close()
    return text_pages

def has_author(text_content):
    """Проверяет, есть ли в тексте автор (никнейм)"""
    
    author_pattern = r'^[a-z0-9\-]+(?:\s+\d+\s+(?:час|мин|сек))?$'
    
    first_page = text_content[0] if text_content else ""
    lines = first_page.split('\n')
    
    for line in lines:
        line = line.strip()
        if re.match(author_pattern, line, re.IGNORECASE):
            if len(line) < 50 and not any(c in line for c in [' ', '.', ',', '!', '?']):
                return True
    return False

def has_minimal_content(text_content, min_chars=500):
    """Проверяет, что в PDF есть минимальный текст"""
    full_text = ' '.join(text_content)
    return len(full_text) > min_chars


# Очищенные списки
clean_pdfs = []
clean_names = []

filtered_NameCompany = []
filtered_Raiting = []
filtered_DataPublish = []
filtered_Activity = []
filtered_TextArticle = []

for pdf_path in all_pdf:
    try:
        text_content = extract_text_from_pdf(pdf_path)
        filename = pdf_path.split('/')[-1]
        
        # Проверяем наличие автора (через parse_habr_article)
        first_page = text_content[0] if text_content else ""
        parsed = parse_habr_article(first_page)
        
        # Автор считается найденным, если строка не пустая и не похожа на мусор
        has_valid_author = (
            parsed['author'] and 
            len(parsed['author']) > 1 and
            not parsed['author'].replace('.', '').isdigit() and
            parsed['author'] not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        )
        
        # Проверяем минимальное содержимое
        full_text = ' '.join(text_content)
        has_content = len(full_text) > 500
        
        if has_valid_author and has_content:
            print(f"ПОЛНЫЙ: {filename}")
            print(f"Автор: {parsed['author']}, Заголовок: {parsed['title'][:50]}...")
            
            # Сохраняем данные
            filtered_NameCompany.append(parsed['author'])
            filtered_Raiting.append(parsed['views'])
            filtered_DataPublish.append(parsed['date'])
            filtered_Activity.append(parsed['tags'])
            filtered_TextArticle.append(full_text)
            clean_pdfs.append(pdf_path)
            clean_names.append(filename)
        else:
            if not has_valid_author:
                print(f"НЕТ АВТОРА: {filename} (найдено: '{parsed['author']}')")
            elif not has_content:
                print(f"ПУСТОЙ/КОРОТКИЙ: {filename}")
                
    except Exception as e:
        print(f"ОШИБКА при чтении {pdf_path}: {e}")

print(f"\n\nИтого: {len(clean_pdfs)} полных PDF из {len(all_pdf)}")
print("Отфильтрованные файлы:", clean_names)


if len(clean_names) > 0:
    clean_df = pd.DataFrame({
        'Author': filtered_NameCompany,
        'Views': filtered_Raiting,
        'Date': filtered_DataPublish,
        'Tags': filtered_Activity,
        'Text': filtered_TextArticle,
        'Filename': clean_names,
        'Path': clean_pdfs
    })
    
    print(f"\nСоздан датафрейм с {len(clean_df)} записями")
    display(clean_df.head())
    
    clean_df.to_csv(r"clean_habr_articles.csv", index=False)
    print("Сохранено в clean_habr_articles.csv")
else:
    print("Нет полных PDF для сохранения")
    
    
df = pd.DataFrame({
    'NameCompany': [],
    'Description': [],
    'Raiting': [],
    'DataPublish': [],
    'Activity': [],
    'TextArticle': [] 
})

for pdf_path in clean_pdfs:
    try:
        text_content = extract_text_from_pdf(pdf_path)
        first_page = text_content[0] if text_content else ""
        
        parsed = parse_habr_article(first_page)
        
        full_text = ' '.join(text_content).replace('\n', ' ').strip()
        
        new_row = pd.DataFrame({
            'NameCompany': [parsed['author']],
            'Description': [parsed['title']],
            'Raiting': [parsed['views']],
            'DataPublish': [parsed['date']],
            'Activity': [parsed['tags']],
            'TextArticle': [full_text]
        })
        
        df = pd.concat([df, new_row], ignore_index=True)
        
    except Exception as e:
        print(f"Ошибка при обработке {pdf_path}: {e}")

print(f"Создан дф с {len(df)} записями")
df = df.dropna()
df.head(30)