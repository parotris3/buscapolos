import os
import requests
from datetime import datetime, timedelta

# Token de autenticación de GitHub (proporcionado por GitHub Actions)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    raise ValueError("No se encontró el GITHUB_TOKEN. Asegúrate de que se está ejecutando en un entorno de GitHub Actions.")

# Nombre del archivo donde se guardarán los enlaces
OUTPUT_FILE = "todas.txt"
# URL de la API de búsqueda de código de GitHub
API_URL = "https://api.github.com/search/code"

def get_search_date():
    """Determina la fecha de búsqueda: 7 días si el archivo no existe, 24 horas si ya existe."""
    if not os.path.exists(OUTPUT_FILE):
        print("Primera ejecución: buscando en los últimos 7 días.")
        return (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    else:
        print("Ejecución diaria: buscando en las últimas 24 horas.")
        return (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d')

def search_github(since_date):
    """Busca en GitHub archivos .m3u creados o modificados después de la fecha indicada."""
    query = f'extension:m3u created:>{since_date}'
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    params = {
        "q": query,
        "per_page": 100  # Máximo permitido por la API
    }
    
    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()  # Lanza un error si la petición falla (e.g., 4xx o 5xx)
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        print(f"Error al contactar la API de GitHub: {e}")
        return []

def get_existing_links():
    """Lee los enlaces que ya existen en el archivo para evitar duplicados."""
    if not os.path.exists(OUTPUT_FILE):
        return set()
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def main():
    """Función principal del script."""
    since_date = get_search_date()
    results = search_github(since_date)
    
    if not results:
        print("No se encontraron nuevos enlaces.")
        return

    existing_links = get_existing_links()
    new_links_found = 0
    
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        for item in results:
            # La URL 'html_url' te lleva a la vista del archivo en GitHub.
            # Para el enlace directo al contenido (raw), hacemos una pequeña transformación.
            raw_url = item['html_url'].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            
            if raw_url not in existing_links:
                f.write(raw_url + '\n')
                existing_links.add(raw_url)
                new_links_found += 1
    
    print(f"Proceso completado. Se añadieron {new_links_found} nuevos enlaces a {OUTPUT_FILE}.")

if __name__ == "__main__":
    main()
