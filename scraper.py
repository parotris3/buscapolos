import os
import requests
from datetime import datetime, timedelta
import time # Importamos la librería time para añadir pausas

# Token de autenticación de GitHub (proporcionado por GitHub Actions)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    raise ValueError("No se encontró el GITHUB_TOKEN...")

OUTPUT_FILE = "todas.txt"
API_URL = "https://api.github.com/search/code"

def get_search_date():
    """Determina la fecha de búsqueda."""
    if not os.path.exists(OUTPUT_FILE):
        print("Primera ejecución: buscando en los últimos 7 días.")
        return (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    else:
        print("Ejecución diaria: buscando en las últimas 24 horas.")
        return (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d')

def search_github(query):
    """Busca en GitHub usando la consulta y recorriendo las páginas de resultados."""
    print(f"Ejecutando la consulta en GitHub: '{query}'")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    all_results = []
    # La API de GitHub devuelve un máximo de 10 páginas (1000 resultados)
    for page in range(1, 11): 
        params = {
            "q": query,
            "per_page": 100,
            "page": page
        }
        
        try:
            response = requests.get(API_URL, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            page_results = data.get('items', [])
            all_results.extend(page_results)
            
            # Si la página actual tiene menos de 100 resultados, es la última página.
            if len(page_results) < 100:
                print(f"Se encontró la última página ({page}). Terminando búsqueda.")
                break
            
            print(f"Página {page} procesada, {len(page_results)} resultados. Continuando...")
            # Pausa para no sobrecargar la API de GitHub y evitar errores de rate limit
            time.sleep(2)

        except requests.exceptions.RequestException as e:
            print(f"Error en la página {page}: {e}")
            # Si una página falla, es mejor parar para no obtener resultados incompletos.
            break
            
    return all_results

def get_existing_links():
    """Lee los enlaces que ya existen en el archivo para evitar duplicados."""
    if not os.path.exists(OUTPUT_FILE):
        return set()
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def main():
    """Función principal del script."""
    # Para la búsqueda de M3U, es mejor una consulta más simple y sin fecha
    # para maximizar los resultados hasta el límite de 1000.
    query = 'extension:m3u' 
    
    results = search_github(query)
    
    if not results:
        print("No se encontraron nuevos enlaces.")
        return

    existing_links = get_existing_links()
    new_links_found = 0
    
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        for item in results:
            raw_url = item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            if raw_url not in existing_links:
                f.write(raw_url + '\n')
                existing_links.add(raw_url)
                new_links_found += 1
    
    print(f"Proceso completado. Se encontraron un total de {len(results)} resultados.")
    print(f"Se añadieron {new_links_found} nuevos enlaces a {OUTPUT_FILE}.")

if __name__ == "__main__":
    main()
