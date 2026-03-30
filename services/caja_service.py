# Servicio para manejar operaciones de caja y autenticación
# Por ahora sin conexión a BD

from models.usuario import Usuario


class CajaService:
    """Servicio para manejar la caja y autenticación"""

    def __init__(self):
        # Datos de prueba (simulando base de datos)
        self.usuarios_prueba = [
            {
                'id_usuario': 1,
                'nombre': 'Administrador',
                'usuario': 'admin',
                'password': 'admin123',
                'rol': 'ADMIN',
                'estado': True
            },
            {
                'id_usuario': 2,
                'nombre': 'Cajero Principal',
                'usuario': 'cajero1',
                'password': 'caja123',
                'rol': 'CAJERO',
                'estado': True
            },
            {
                'id_usuario': 3,
                'nombre': 'Cajero Secundario',
                'usuario': 'cajero2',
                'password': 'caja456',
                'rol': 'CAJERO',
                'estado': True
            },
            {
                'id_usuario': 4,
                'nombre': 'Usuario Inactivo',
                'usuario': 'inactivo',
                'password': 'test123',
                'rol': 'CAJERO',
                'estado': False
            }
        ]

    def obtener_usuarios_activos(self):
        """Obtiene la lista de usuarios activos"""
        usuarios_activos = []
        for user_data in self.usuarios_prueba:
            if user_data['estado']:
                usuario = Usuario.from_dict(user_data)
                usuarios_activos.append({
                    'id_usuario': usuario.id_usuario,
                    'nombre': usuario.nombre,
                    'usuario': usuario.usuario,
                    'rol': usuario.rol
                })
        return usuarios_activos

    def autenticar_usuario(self, id_usuario, password):
        """
        Autentica un usuario por ID y contraseña
        Retorna: (success, mensaje, usuario_dict)
        """
        # Buscar usuario por ID
        user_data = None
        for user in self.usuarios_prueba:
            if user['id_usuario'] == id_usuario:
                user_data = user
                break

        if not user_data:
            return False, "Usuario no encontrado", None

        # Verificar estado
        if not user_data['estado']:
            return False, "Usuario desactivado, contacte al administrador", None

        # Crear objeto usuario y verificar contraseña
        usuario = Usuario.from_dict(user_data)

        if not usuario.verificar_password(password):
            return False, "Contraseña incorrecta", None

        # Autenticación exitosa
        return True, "Bienvenido", usuario.to_dict()

    def registrar_apertura_caja(self, id_usuario, monto_inicial):
        """
        Registra la apertura de caja cuando un usuario inicia sesión
        """
        # Placeholder para cuando implementemos la BD
        # Esto creará un registro en apertura_cierre
        print(f"Apertura de caja para usuario {id_usuario} con monto {monto_inicial}")
        return True