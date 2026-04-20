import random
import string

class Usuario:
    def __init__(self, nombre, usuario, rol, contraseña):
        self._nombre = nombre
        self._usuario = usuario
        self._rol = rol
        self._contraseña = contraseña

    @property
    def usuario(self):
        return self._usuario

    @property
    def rol(self):
        return self._rol

    def validarPassword(self, password):
        return self._contraseña == password

    def mostrar(self):
        print(f"Nombre: {self._nombre}")
        print(f"Usuario: {self._usuario}")
        print(f"Rol: {self._rol}")
        print("----------------------")


usuarios_db = []

# admin por defecto
usuarios_db.append(Usuario("Admin", "admin", "administrador", "1234"))


def generarPassword(longitud=8):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longitud))


def crearUsuario():
    nombre = input("Ingrese nombre: ")
    usuario = input("Ingrese usuario: ")

    # validar usuario único
    for u in usuarios_db:
        if u.usuario == usuario:
            print("Ese usuario ya existe")
            return

    rol = input("Ingrese rol (administrador/vendedor): ").lower()
    if rol not in ["administrador", "vendedor"]:
        print("Rol inválido")
        return

    opcion = input("¿Generar contraseña automática? (s/n): ").lower()

    if opcion == "s":
        contraseña = generarPassword()
    else:
        contraseña = input("Ingrese contraseña: ")

    nuevo = Usuario(nombre, usuario, rol, contraseña)
    usuarios_db.append(nuevo)

    print("\n✅ Usuario creado correctamente")
    print("⚠️ GUARDA ESTA CONTRASEÑA Y ENTRÉGALA AL USUARIO:")
    print(f"👉 Usuario: {usuario}")
    print(f"👉 Contraseña: {contraseña}")
    print("----------------------")


def login():
    usuario = input("Usuario: ")
    password = input("Contraseña: ")

    for u in usuarios_db:
        if u.usuario == usuario and u.validarPassword(password):
            print(f"Bienvenido {usuario} ({u.rol})")
            return u

    print("Credenciales incorrectas")
    return None


def mostrarUsuarios():
    print("\n--- LISTA DE USUARIOS ---")
    for u in usuarios_db:
        u.mostrar()


def menuAdmin():
    while True:
        print("\n--- MENÚ ADMIN ---")
        print("1. Crear usuario")
        print("2. Mostrar usuarios")
        print("3. Cerrar sesión")

        op = input("Seleccione: ")

        if op == "1":
            crearUsuario()
        elif op == "2":
            mostrarUsuarios()
        elif op == "3":
            break


def menuVendedor():
    while True:
        print("\n--- MENÚ VENDEDOR ---")
        print("1. Ver usuarios")
        print("2. Cerrar sesión")

        op = input("Seleccione: ")

        if op == "1":
            mostrarUsuarios()
        elif op == "2":
            break


# PROGRAMA PRINCIPAL
while True:
    print("\n=== SISTEMA ===")
    print("1. Iniciar sesión")
    print("2. Salir")

    op = input("Seleccione: ")

    if op == "1":
        usuarioLogueado = login()

        if usuarioLogueado:
            if usuarioLogueado.rol == "administrador":
                menuAdmin()
            else:
                menuVendedor()

    elif op == "2":
        print("Saliendo...")
        break