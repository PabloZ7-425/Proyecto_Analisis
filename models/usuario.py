class Usuario:
    """Modelo de Usuario"""

    def __init__(self, id_usuario=None, nombre=None, usuario=None,
                 password=None, rol=None, estado=True, fecha_creacion=None):
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.usuario = usuario
        self.password = password
        self.rol = rol
        self.estado = estado
        self.fecha_creacion = fecha_creacion

    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id_usuario': self.id_usuario,
            'nombre': self.nombre,
            'usuario': self.usuario,
            'rol': self.rol,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion
        }

    @staticmethod
    def from_dict(data):
        """Crea un objeto Usuario desde un diccionario"""
        return Usuario(
            id_usuario=data.get('id_usuario'),
            nombre=data.get('nombre'),
            usuario=data.get('usuario'),
            password=data.get('password'),
            rol=data.get('rol'),
            estado=data.get('estado', True),
            fecha_creacion=data.get('fecha_creacion')
        )

    def verificar_password(self, password_input):
        """Verifica si la contraseña ingresada es correcta"""
        # Por ahora comparación directa, después se usará hash
        return self.password == password_input

    def __str__(self):
        return f"{self.nombre} ({self.rol})"