# Clase Cliente
class Cliente:
    def __init__(self, nombres, apellidos):
        self.__nombres = nombres
        self.__apellidos = apellidos

    # Getters
    def get_nombres(self):
        return self.__nombres

    def get_apellidos(self):
        return self.__apellidos

    # Setters
    def set_nombres(self, nombres):
        self.__nombres = nombres

    def set_apellidos(self, apellidos):
        self.__apellidos = apellidos

    # Mostrar datos
    def mostrar_cliente(self):
        print("\n--- DATOS DEL CLIENTE ---")
        print("Nombres:", self.__nombres)
        print("Apellidos:", self.__apellidos)


# Clase Producto
class Producto:
    def __init__(self, marca, modelo, nombre_producto, descripcion):
        self.__marca = marca
        self.__modelo = modelo
        self.__nombre_producto = nombre_producto
        self.__descripcion = descripcion

    # Getters
    def get_marca(self):
        return self.__marca

    def get_modelo(self):
        return self.__modelo

    def get_nombre_producto(self):
        return self.__nombre_producto

    def get_descripcion(self):
        return self.__descripcion

    # Setters
    def set_marca(self, marca):
        self.__marca = marca

    def set_modelo(self, modelo):
        self.__modelo = modelo

    def set_nombre_producto(self, nombre_producto):
        self.__nombre_producto = nombre_producto

    def set_descripcion(self, descripcion):
        self.__descripcion = descripcion

    # Mostrar datos
    def mostrar_producto(self):
        print("\n--- DATOS DEL PRODUCTO ---")
        print("Marca:", self.__marca)
        print("Modelo:", self.__modelo)
        print("Nombre del producto:", self.__nombre_producto)
        print("Descripción:", self.__descripcion)


# Registro Cliente
print("REGISTRO DE CLIENTE ")
nombres = input("Ingrese nombres: ")
apellidos = input("Ingrese apellidos: ")

cliente1 = Cliente(nombres, apellidos)

# Registro Producto
print("\nREGISTRO DE PRODUCTO ")
marca = input("Ingrese marca: ")
modelo = input("Ingrese modelo: ")
nombre_producto = input("Ingrese nombre del producto: ")
descripcion = input("Ingrese descripción: ")

producto1 = Producto(marca, modelo, nombre_producto, descripcion)

# Mostrar nuevamente al finalizar

print("      DATOS INGRESADOS")

cliente1.mostrar_cliente()
producto1.mostrar_producto()