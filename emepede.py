import os
import requests
from datetime import datetime, timedelta
import time

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    raise ValueError("No se encontró el GITHUB_TOKEN...")

OUTPUT_FILE = "trocalaoca.txt"
API_URL = "https://api.github.com/search/code"

def handle_rate_limit(response):
    if response.status_code == 429:
        print("⚠️ Límite de peticiones alcanzado. Esperando 60 segundos...")
        time.sleep(60)
        return True
    return False

def search_github(query):
    print(f"Ejecutando la consulta en GitHub: '{query}'")
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    params = {"q": query, "per_page": 100}
    
    try:
        response = requests.get(API_URL, headers=headers, params=params)
        if handle_rate_limit(response):
            response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        print(f"Error al contactar la API de GitHub: {e}")
        return []

def main():
    open(OUTPUT_FILE, 'a').close()
    
    if not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0:
        days_to_search = 15
        print(f"Primera ejecución: buscando en los últimos {days_to_search} días.")
    else:
        days_to_search = 1
        print(f"Ejecución diaria: buscando en las últimas 24 horas.")
    
    since_date = (datetime.now() - timedelta(days=days_to_search)).strftime('%Y-%m-%d')

    # --- LISTA DE CONSULTAS ESPECIALIZADAS ---
    # En lugar de una búsqueda, hacemos varias más pequeñas y precisas.
    queries = [
        f'http ".mpd" path:*.md pushed:>{since_date}',
        f'http ".mpd" path:*.txt pushed:>{since_date}',
        f'http ".mpd" path:*.json pushed:>{since_date}',
        f'http ".mpd" path:*.html pushed:>{since_date}',
        f'http ".mpd" path:*.m3u pushed:>{since_date}',
        f'http ".mpd" path:*.m3u8 pushed:>{since_date}',
    ]

    all_files_found = []
    # Ejecutamos cada consulta de la lista
    for query in queries:
        results = search_github(query)
        if results:
            all_files_found.extend(results)
        time.sleep(10) # Pausa entre diferentes búsquedas para proteger la API

    if not all_files_found:
        print("No se encontraron archivos que cumplan los criterios en ninguna de las búsquedas.")
        return

    # Eliminamos duplicados por si un archivo aparece en varias búsquedas
    unique_files = {item['html_url']: item for item in all_files_found}.values()

    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        existing_links = set(line.split(',')[0].replace('Enlace: ', '').strip() for line in f if line.startswith("Enlace: "))

    new_links_found = 0
    print(f"Se encontraron {len(unique_files)} archivos únicos para procesar...")

    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        for file_item in unique_files:
            repo_url = file_item['repository']['html_url']
            raw_url = file_item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            
            try:
                time.sleep(2)
                content_response = requests.get(raw_url, timeout=10)
                if content_response.status_code != 200: continue

                for line in content_response.text.splitlines():
                    clean_line = line.strip().strip('\'"')
                    if clean_line.startswith('http') and clean_line.endswith('.mpd') and clean_line not in existing_links:
                        output = f"Enlace: {clean_line}, Repositorio: {repo_url}\n"
                        f.write(output)
                        existing_links.add(clean_line)
                        new_links_found += 1
            except requests.exceptions.RequestException as e:
                print(f"No se pudo procesar el archivo {raw_url}: {e}")
                continue

    print(f"Proceso completado. Se añadieron {new_links_found} nuevos enlaces a {OUTPUT_FILE}.")

if __name__ == "__main__":
    main()
