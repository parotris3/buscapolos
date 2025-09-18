import os
import requests
from datetime import datetime, timedelta

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    raise ValueError("No se encontró el GITHUB_TOKEN...")

OUTPUT_FILE = "trocalaoca.txt"
API_URL = "https://api.github.com/search/code"

# ... (Las funciones get_search_date, search_github, y get_existing_mpd_links no cambian) ...

def main():
    """Función principal del script."""
    # --- LÍNEA AÑADIDA ---
    # Aseguramos que el archivo de salida exista, solucionando el error del commit.
    open(OUTPUT_FILE, 'a').close()

    since_date = get_search_date()
    # --- CONSULTA MEJORADA ---
    # Buscamos archivos de texto, markdown o json que contengan "mpd" y también
    # las palabras "manifest" o "DASH", que suelen acompañar a estos enlaces.
    # Esto es mucho más efectivo que buscar solo ".mpd".
    query = f'(manifest OR DASH) AND mpd extension:txt extension:md extension:json pushed:>{since_date}'
    
    files_containing_mpd = search_github(query)
    
    if not files_containing_mpd:
        print("No se encontraron archivos nuevos que contengan enlaces .mpd.")
        return

    # ... (El resto del código de procesamiento no cambia) ...
    existing_links = get_existing_mpd_links()
    new_links_found = 0
    print(f"Se encontraron {len(files_containing_mpd)} archivos. Procesando contenido...")

    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        for file_item in files_containing_mpd:
            repo_url = file_item['repository']['html_url']
            raw_url = file_item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            try:
                content_response = requests.get(raw_url, timeout=10)
                if content_response.status_code != 200:
                    continue
                for line in content_response.text.splitlines():
                    clean_line = line.strip()
                    if '.mpd' in clean_line and 'http' in clean_line and clean_line not in existing_links:
                        output = f"Enlace: {clean_line}, Repositorio: {repo_url}\n"
                        f.write(output)
                        existing_links.add(clean_line)
                        new_links_found += 1
            except requests.exceptions.RequestException as e:
                print(f"No se pudo procesar el archivo {raw_url}: {e}")
                continue

    print(f"Proceso completado. Se añadieron {new_links_found} nuevos enlaces a {OUTPUT_FILE}.")

if __name__ == "__main__":
    # Definiciones de funciones auxiliares para main
    def get_search_date():
        if not os.path.exists(OUTPUT_FILE):
            print(f"Primera ejecución para {OUTPUT_FILE}: buscando en los últimos 60 días.")
            return (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        else:
            print(f"Ejecución diaria para {OUTPUT_FILE}: buscando en las últimas 24 horas.")
            return (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d')

    def search_github(query):
        print(f"Ejecutando la consulta en GitHub: '{query}'")
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        params = {"q": query, "per_page": 100}
        try:
            response = requests.get(API_URL, headers=headers, params=params)
            response.raise_for_status()
            return response.json().get('items', [])
        except requests.exceptions.RequestException as e:
            print(f"Error al contactar la API de GitHub: {e}")
            return []

    def get_existing_mpd_links():
        links = set()
        if not os.path.exists(OUTPUT_FILE):
            return links
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("Enlace: "):
                    try:
                        link = line.split(',')[0].replace('Enlace: ', '').strip()
                        links.add(link)
                    except IndexError:
                        continue
        return links

    main()
