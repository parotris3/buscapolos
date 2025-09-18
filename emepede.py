import os
import requests
from datetime import datetime, timedelta
import time

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    raise ValueError("No se encontró el GITHUB_TOKEN...")

OUTPUT_FILE = "trocalaoca.txt"
API_URL = "https://api.github.com/search/code"

# La función handle_rate_limit no cambia
def handle_rate_limit(response):
    if response.status_code == 429:
        print("⚠️ Límite de peticiones alcanzado. Esperando 60 segundos...")
        time.sleep(60)
        return True
    return False

# La función search_github no cambia
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
        print(f"Primera ejecución para {OUTPUT_FILE}: buscando en los últimos 300 días.")
        since_date = (datetime.now() - timedelta(days=300)).strftime('%Y-%m-%d')
    else:
        print(f"Ejecución diaria para {OUTPUT_FILE}: buscando en las últimas 24 horas.")
        since_date = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d')

    # --- CONSULTA FINAL Y CORRECTA ---
    # Buscamos archivos que contengan la palabra "http" Y la cadena exacta ".mpd".
    # Esto es un indicador muy fuerte de que el archivo contiene un enlace completo.
    #query = f'http ".mpd" pushed:>{since_date}'
    query = 'http ".mpd"' # Deja solo esta, sin el filtro de fecha
    
    files_containing_mpd = search_github(query)
    
    if not files_containing_mpd:
        print("No se encontraron archivos que cumplan los criterios de búsqueda.")
        return

    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        existing_links = set(line.split(',')[0].replace('Enlace: ', '').strip() for line in f if line.startswith("Enlace: "))

    new_links_found = 0
    print(f"Se encontraron {len(files_containing_mpd)} archivos. Procesando contenido...")

    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        for file_item in files_containing_mpd:
            repo_url = file_item['repository']['html_url']
            raw_url = file_item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            
            try:
                time.sleep(2) # Pausa entre descargas de archivos
                content_response = requests.get(raw_url, timeout=10)
                if content_response.status_code != 200:
                    continue

                for line in content_response.text.splitlines():
                    # --- LÓGICA DE FILTRADO MEJORADA ---
                    # Limpiamos la línea de espacios y comillas comunes
                    clean_line = line.strip().strip('\'"')
                    
                    # Verificamos que la línea COMIENCE con http y TERMINE con .mpd
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
