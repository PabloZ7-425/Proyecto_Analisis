import sys
import os
import sys
import os

ruta_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ruta_raiz)
import psycopg2
from config.db_config import DatabaseConfig

class DatabaseConnection:

    def __init__(self):
        params = DatabaseConfig.get_connection_params()
        self.conn = psycopg2.connect(**params)
        self.conn.set_client_encoding('UTF8')

    def execute_query(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        cursor.close()

    def fetch_all(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        data = cursor.fetchall()
        cursor.close()
        return data

class Producto:
    def __init__(self, id_producto=None, nombre="", marca="", modelo="", descripcion=""):
        self.id_producto = id_producto
        self.nombre = nombre
        self.marca = marca
        self.modelo = modelo
        self.descripcion = descripcion

    @staticmethod
    def from_db(row):
        return Producto(row[0], row[1], row[2], row[3], row[4])

class ProductoDAO:

    def __init__(self, db):
        self.db = db

    def crear(self, producto):
        query = """
        INSERT INTO producto (nombre, marca, modelo, descripcion)
        VALUES (%s, %s, %s, %s)
        """
        self.db.execute_query(
            query,
            (producto.nombre, producto.marca, producto.modelo, producto.descripcion)
        )

    def listar(self):
        datos = self.db.fetch_all("SELECT * FROM producto")
        return [Producto.from_db(d) for d in datos]

    def eliminar(self, id_producto):
        self.db.execute_query(
            "DELETE FROM producto WHERE id_producto = %s",
            (id_producto,)
        )

    def actualizar(self, producto):
        query = """
        UPDATE producto 
        SET nombre=%s, marca=%s, modelo=%s, descripcion=%s
        WHERE id_producto=%s
        """
        self.db.execute_query(
            query,
            (producto.nombre, producto.marca, producto.modelo, producto.descripcion, producto.id_producto)
        )

class ProductoService:

    def __init__(self):
        self.db = DatabaseConnection()
        self.dao = ProductoDAO(self.db)

    def crear(self, nombre, marca, modelo, descripcion):
        self.dao.crear(Producto(nombre=nombre, marca=marca, modelo=modelo, descripcion=descripcion))

    def listar(self):
        return self.dao.listar()

    def eliminar(self, id_producto):
        self.dao.eliminar(id_producto)

    def actualizar(self, id_producto, nombre, marca, modelo, descripcion):
        self.dao.actualizar(Producto(id_producto, nombre, marca, modelo, descripcion))

if __name__ == "__main__":
    service = ProductoService()

    while True:
        print("\n--- PRODUCTOS ---")
        print("1. Crear")
        print("2. Listar")
        print("3. Editar")
        print("4. Eliminar")
        print("5. Salir")

        op = input("Opción: ")

        if op == "1":
            n = input("Nombre: ")
            m = input("Marca: ")
            mo = input("Modelo: ")
            d = input("Descripción: ")
            service.crear(n, m, mo, d)

        elif op == "2":
            for p in service.listar():
                print(p.id_producto, p.nombre, p.marca, p.modelo, p.descripcion)

        elif op == "3":
            idp = input("ID: ")
            n = input("Nombre: ")
            m = input("Marca: ")
            mo = input("Modelo: ")
            d = input("Descripción: ")
            service.actualizar(idp, n, m, mo, d)

        elif op == "4":
            idp = input("ID: ")
            service.eliminar(idp)

        elif op == "5":
            break