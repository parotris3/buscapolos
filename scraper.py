import os
import requests
from datetime import datetime, timedelta
import time

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    raise ValueError("No se encontró el GITHUB_TOKEN...")

OUTPUT_FILE = "todas.txt"
API_URL = "https://api.github.com/search/code"

def handle_rate_limit(response):
    """Detecta un error de límite de peticiones y espera."""
    if response.status_code == 429:
        print("⚠️ Límite de peticiones alcanzado. Esperando 60 segundos...")
        time.sleep(60)
        return True # Indica que se debe reintentar
    return False

def search_github(query):
    """Busca en GitHub con reintentos automáticos en caso de error 429."""
    print(f"Ejecutando la consulta en GitHub: '{query}'")
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    all_results = []

    # Se ha aumentado a 15 páginas por si hay muchos resultados pequeños
    for page in range(1, 15):
        params = {"q": query, "per_page": 100, "page": page}
        
        while True: # Bucle de reintento
            try:
                response = requests.get(API_URL, headers=headers, params=params)
                if handle_rate_limit(response):
                    continue # Vuelve a intentarlo si hubo un error de rate limit
                
                response.raise_for_status() # Lanza error para otros códigos (404, 500, etc.)
                
                data = response.json()
                page_results = data.get('items', [])
                all_results.extend(page_results)
                
                print(f"Página {page} procesada, {len(page_results)} resultados.")
                
                if len(page_results) < 100:
                    print("Se encontró la última página. Terminando búsqueda.")
                    return all_results
                
                # Pausa para ser respetuosos con la API
                time.sleep(10)
                break # Sale del bucle de reintento y va a la siguiente página

            except requests.exceptions.RequestException as e:
                print(f"Error en la página {page}: {e}")
                return all_results # Devuelve lo que ha conseguido hasta ahora
    return all_results

def main():
    """Función principal del script."""
    open(OUTPUT_FILE, 'a').close()

    # --- CAMBIO PRINCIPAL AQUÍ ---
    # 1. Calculamos la fecha de hace 7 días
    since_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    # 2. Añadimos el filtro de fecha a la consulta
    query = f'extension:m3u pushed:>{since_date}'
    
    results = search_github(query)
    
    if not results:
        print("No se encontraron nuevos enlaces en los últimos 7 días.")
        return

    # Leemos los enlaces que ya existen para no añadir duplicados
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        existing_links = set(line.strip() for line in f)

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
