import psycopg2
from config.db_config import DatabaseConfig

def getConexion():
    try:
        params = DatabaseConfig.get_connection_params()
        conexion = psycopg2.connect(**params)
        conexion.set_client_encoding('UTF8')
        return conexion
    except Exception as e:
        print(f"Error de conexion: {e}")
        return None

class Producto:
    # CORREGIDO: El orden ahora es (nombre, marca, modelo, descripcion)
    def __init__(self, nombre, marca, modelo, descripcion):
        self.__nombre = nombre
        self.__marca = marca
        self.__modelo = modelo
        self.__descripcion = descripcion

    def guardar(self):
        conexion = getConexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                sql = "INSERT INTO producto (nombre, marca, modelo, descripcion) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (self.__nombre, self.__marca, self.__modelo, self.__descripcion))
                conexion.commit()
                print("Producto guardado.")
                cursor.close()
                conexion.close()
                return True
            except Exception as e:
                print(f"Error al guardar producto: {e}")
                conexion.rollback()
                return False
        return False



