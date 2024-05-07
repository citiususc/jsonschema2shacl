import json
def leer_json_schema(ruta_archivo: str) -> dict:
    try:
        with open(ruta_archivo, 'r') as archivo:
            schema = json.load(archivo)
        return schema
    except FileNotFoundError:
        print(f"El archivo '{ruta_archivo}' no fue encontrado.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error al decodificar el archivo JSON: {e}")
        return None