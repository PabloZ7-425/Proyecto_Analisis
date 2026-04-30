from datetime import date, timedelta


class Apartado:
    ESTADO_ACTIVO = 'ACTIVO'
    ESTADO_COMPLETADO = 'COMPLETADO'
    ESTADO_CANCELADO = 'CANCELADO'

    def __init__(self, id_apartado=None, id_cliente_fk=None, id_producto_fk=None,
                 total_producto=0, fecha_inicio=None, estado=ESTADO_ACTIVO):
        self.id_apartado = id_apartado
        self.id_cliente_fk = id_cliente_fk
        self.id_producto_fk = id_producto_fk
        self.total_producto = total_producto
        self.fecha_inicio = fecha_inicio or date.today()
        self.estado = estado

    def to_dict(self):
        return {
            'id_apartado': self.id_apartado,
            'id_cliente_fk': self.id_cliente_fk,
            'id_producto_fk': self.id_producto_fk,
            'total_producto': self.total_producto,
            'fecha_inicio': self.fecha_inicio,
            'estado': self.estado
        }

    @staticmethod
    def from_dict(data):
        return Apartado(
            id_apartado=data.get('id_apartado'),
            id_cliente_fk=data.get('id_cliente_fk'),
            id_producto_fk=data.get('id_producto_fk'),
            total_producto=data.get('total_producto', 0),
            fecha_inicio=data.get('fecha_inicio'),
            estado=data.get('estado', Apartado.ESTADO_ACTIVO)
        )

    def monto_inicial(self):
        return self.total_producto * 0.1

    def fecha_limite(self):
        return self.fecha_inicio + timedelta(days=90)

    def completar(self):
        self.estado = self.ESTADO_COMPLETADO

    def cancelar(self):
        self.estado = self.ESTADO_CANCELADO

    def __str__(self):
        return f"Apartado {self.id_apartado} - {self.estado} - Q{self.total_producto}"