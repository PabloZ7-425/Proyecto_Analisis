import psycopg2
from config.db_config import DatabaseConfig
# Clase de configuración incluida para evitar el error 'not defined'


def getConexion():
    try:
        params = DatabaseConfig.get_connection_params()
        conexion = psycopg2.connect(**params)
        conexion.set_client_encoding('UTF8')
        return conexion
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

# Resto de tus clases (Cliente y Producto) con el método guardar() integrado:
class Cliente:
    def __init__(self, nombres, apellidos):
        self.__nombres = nombres
        self.__apellidos = apellidos

    def guardar(self):
        conexion = getConexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                # Asegúrate que el nombre de la tabla sea exactamente igual al de tu BD
                # Verifica si la tabla es 'clientes' o 'cliente'
                sql = "INSERT INTO cliente (nombre, apellido) VALUES (%s, %s)"
                cursor.execute(sql, (self.__nombres, self.__apellidos))
                conexion.commit()
                print("✅ Cliente guardado.")
                cursor.close()
                conexion.close()
            except Exception as e:
                print(f"❌ Error al guardar cliente: {e}")
class Producto:
    def __init__(self, marca, modelo, nombre_producto, descripcion):
        self.__marca = marca
        self.__modelo = modelo
        self.__nombre_producto = nombre_producto
        self.__descripcion = descripcion

    def guardar(self):
        conexion = getConexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                # Según tus imágenes, las columnas son: nombre, marca, modelo, descripcion
                sql = "INSERT INTO producto (nombre, marca, modelo, descripcion) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (self.__nombre_producto, self.__marca, self.__modelo, self.__descripcion))
                conexion.commit()
                print("✅ Producto guardado.")
                cursor.close()
                conexion.close()
            except Exception as e:
                print(f"❌ Error al guardar producto: {e}")

# Ejecución
print("--- REGISTRO ---")
nombre = input("Ingrese nombre: ")
apellido = input("Ingrese apellido: ")
cli = Cliente(nombre, apellido)
cli.guardar()

marca = input("Ingrese marca: ")
modelo = input("Ingrese modelo: ")
prod_nombre = input("Ingrese nombre del producto: ")
desc = input("Ingrese descripción: ")
prod = Producto(marca, modelo, prod_nombre, desc)
prod.guardar()