import psycopg2
import secrets
import string
from config.db_config import DatabaseConfig 

# =========================
# CONEXIÓN A BD
# =========================
def getConexion():
    try:
        params = DatabaseConfig.get_connection_params()
        conexion = psycopg2.connect(**params)
        conexion.set_client_encoding('UTF8')
        return conexion
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

# =========================
# GENERADOR DE CONTRASEÑA
# =========================
def generarPassword(longitud=12):
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

# =========================
# CREAR USUARIO
# =========================
def crearUsuario():
    nombre = input("Nombre completo: ")
    usuario = input("Nombre de usuario: ")
    
    print("\n¿Desea generar una contraseña automática?")
    op_pass = input("1. Sí / 2. No: ")
    password = generarPassword() if op_pass == "1" else input("Ingrese contraseña: ")
    if op_pass == "1": print(f"🔑 Generada: {password}")

    rol = input("Rol: ")

    conexion = getConexion()
    if conexion:
        try:
            cursor = conexion.cursor()
            # Por defecto se crea en TRUE (Habilitado)
            cursor.execute("""
                INSERT INTO usuario (nombre, usuario, password, rol, estado)
                VALUES (%s, %s, %s, %s, true)
            """, (nombre, usuario, password, rol))
            conexion.commit()
            print(f"\n✅ Usuario '{usuario}' creado y HABILITADO.")
            cursor.close()
            conexion.close()
        except Exception as e:
            print("❌ Error:", e)

# =========================
# ACTIVAR / DESACTIVAR USUARIO
# =========================
def gestionarEstadoUsuario():
    usuario = input("Ingrese el nombre de usuario a gestionar: ")
    
    print(f"\n¿Qué desea hacer con el usuario '{usuario}'?")
    print("1. Habilitar (Set True)")
    print("2. Deshabilitar (Set False)")
    op = input("Seleccione: ")

    nuevo_estado = True if op == "1" else False
    estado_texto = "HABILITADO" if nuevo_estado else "DESHABILITADO"

    conexion = getConexion()
    if conexion:
        try:
            cursor = conexion.cursor()
            # Ejecutamos el UPDATE para cambiar solo el estado
            cursor.execute("""
                UPDATE usuario 
                SET estado = %s 
                WHERE usuario = %s
            """, (nuevo_estado, usuario))
            
            if cursor.rowcount > 0:
                conexion.commit()
                print(f"\n🔄 El usuario '{usuario}' ahora está {estado_texto}.")
            else:
                print(f"\n❌ No se encontró el usuario '{usuario}'.")
            
            cursor.close()
            conexion.close()
        except Exception as e:
            print("❌ Error al actualizar estado:", e)

# =========================
# MENÚ PRINCIPAL
# =========================
if __name__ == "__main__":
    while True:
        print("\n=== GESTIÓN DE USUARIOS SUPABASE ===")
        print("1. Crear nuevo usuario")
        print("2. Habilitar/Deshabilitar usuario")
        print("3. Salir")

        op = input("Seleccione una opción: ")

        if op == "1":
            crearUsuario()
        elif op == "2":
            gestionarEstadoUsuario()
        elif op == "3":
            print("Saliendo...")
            break
        else:
            print("❌ Opción inválida.")