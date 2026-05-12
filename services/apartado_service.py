# services/apartado_service.py
import sys
import os
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.conexion import DatabaseConnection
from models.dao import ApartadoDAO, MovimientoCajaDAO
from models.apartado import Apartado
from models.movimiento import MovimientoCaja


class ApartadoService:
    """Servicio para gestionar la lógica de negocio de apartados."""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.apartado_dao = ApartadoDAO(self.db)
        self.movimiento_dao = MovimientoCajaDAO(self.db)

    def obtener_apartados_pendientes(self) -> list[dict]:
        """
        Obtiene SOLO los apartados ACTIVOS con saldo pendiente por pagar.
        Retorna una lista de diccionarios con toda la información necesaria.
        """
        query = """
            SELECT a.id_apartado, 
                   a.total_producto, 
                   a.monto_original,
                   a.descuento_pactado,
                   a.monto_final,
                   a.fecha_inicio, 
                   a.estado,
                   a.es_envio,
                   a.id_empresa_fk,
                   c.id_cliente,
                   c.nombre as cliente_nombre, 
                   c.apellido as cliente_apellido,
                   c.telefono as cliente_telefono,
                   p.id_producto,
                   p.nombre as producto_nombre, 
                   p.marca,
                   p.modelo,
                   p.precio_costo,
                   ee.nombre as empresa_envio_nombre,
                   COALESCE(SUM(da.monto), 0) as total_pagado
            FROM apartado a
            JOIN cliente c ON a.id_cliente_fk = c.id_cliente
            JOIN producto p ON a.id_producto_fk = p.id_producto
            LEFT JOIN detalle_apartado da ON a.id_apartado = da.id_apartado_fk
            LEFT JOIN empresa_envio ee ON a.id_empresa_fk = ee.id_empresa
            WHERE a.estado = 'ACTIVO'
            GROUP BY a.id_apartado, c.id_cliente, c.nombre, c.apellido, c.telefono,
                     p.id_producto, p.nombre, p.marca, p.modelo, p.precio_costo,
                     ee.nombre
            HAVING COALESCE(SUM(da.monto), 0) < a.total_producto
            ORDER BY a.fecha_inicio ASC
        """
        resultados = self.db.fetch_all(query)
        
        # Calcular saldo pendiente para cada uno
        for r in resultados:
            r['saldo_pendiente'] = float(r['total_producto']) - float(r['total_pagado'])
            r['porcentaje_pagado'] = (float(r['total_pagado']) / float(r['total_producto'])) * 100 if r['total_producto'] > 0 else 0
            
        return resultados

    def obtener_todos_apartados(self) -> list[dict]:
        """
        Obtiene TODOS los apartados (activos, completados, cancelados).
        Útil para reportes y administración.
        """
        query = """
            SELECT a.id_apartado, 
                   a.total_producto, 
                   a.monto_original,
                   a.descuento_pactado,
                   a.monto_final,
                   a.fecha_inicio, 
                   a.estado,
                   a.es_envio,
                   c.nombre as cliente_nombre, 
                   c.apellido as cliente_apellido,
                   p.nombre as producto_nombre, 
                   p.marca,
                   COALESCE(SUM(da.monto), 0) as total_pagado
            FROM apartado a
            JOIN cliente c ON a.id_cliente_fk = c.id_cliente
            JOIN producto p ON a.id_producto_fk = p.id_producto
            LEFT JOIN detalle_apartado da ON a.id_apartado = da.id_apartado_fk
            GROUP BY a.id_apartado, c.nombre, c.apellido, p.nombre, p.marca
            ORDER BY a.fecha_inicio DESC
        """
        return self.db.fetch_all(query)

    def crear_apartado(self, data: dict) -> int | None:
        """
        Crea un nuevo apartado con todos los campos de la tabla.
        data debe contener: id_cliente_fk, id_producto_fk, total_producto,
                           fecha_inicio, monto_original, descuento_pactado,
                           monto_final, es_envio, id_empresa_fk (opcional)
        """
        query = """
            INSERT INTO apartado (
                id_cliente_fk, id_producto_fk, total_producto, 
                fecha_inicio, estado, monto_original, 
                descuento_pactado, monto_final, es_envio, id_empresa_fk
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_apartado
        """
        params = (
            data['id_cliente_fk'],
            data['id_producto_fk'],
            data['total_producto'],
            data['fecha_inicio'],
            'ACTIVO',
            data.get('monto_original', data['total_producto']),
            data.get('descuento_pactado', 0),
            data.get('monto_final', data['total_producto']),
            data.get('es_envio', False),
            data.get('id_empresa_fk')
        )
        resultado = self.db.fetch_one(query, params)
        return resultado['id_apartado'] if resultado else None

    def registrar_abono(self, id_apartado: int, monto: float, id_caja_fk: int, id_usuario_fk: int) -> bool:
        """Registra un abono a un apartado existente."""
        return self.apartado_dao.registrar_abono(id_apartado, monto, id_caja_fk, id_usuario_fk)

    def cancelar_apartado(self, id_apartado: int, total_pagado: float, id_caja_fk: int, id_usuario_fk: int) -> bool:
        """Cancela un apartado y registra la devolución correspondiente."""
        return self.apartado_dao.cancelar_apartado(id_apartado, total_pagado, id_caja_fk, id_usuario_fk)

    def obtener_estado_caja(self) -> dict:
        """Verifica si hay una caja abierta y devuelve su ID."""
        query = """
            SELECT ac.id_apertura, ac.id_caja_fk
            FROM apertura_cierre ac
            WHERE ac.fecha_hora_cierre IS NULL
            ORDER BY ac.fecha_hora_apertura DESC
            LIMIT 1
        """
        resultado = self.db.fetch_one(query)
        if resultado:
            return {'abierta': True, 'id_caja': resultado['id_caja_fk']}
        return {'abierta': False, 'id_caja': None}
    
    def obtener_detalle_apartado(self, id_apartado: int) -> dict | None:
        """Obtiene el detalle completo de un apartado específico."""
        query = """
            SELECT a.*, 
                   c.nombre as cliente_nombre, 
                   c.apellido as cliente_apellido,
                   c.telefono as cliente_telefono,
                   p.nombre as producto_nombre,
                   p.marca, p.modelo,
                   COALESCE(SUM(da.monto), 0) as total_pagado,
                   COUNT(da.id_detalle) as num_pagos
            FROM apartado a
            JOIN cliente c ON a.id_cliente_fk = c.id_cliente
            JOIN producto p ON a.id_producto_fk = p.id_producto
            LEFT JOIN detalle_apartado da ON a.id_apartado = da.id_apartado_fk
            WHERE a.id_apartado = %s
            GROUP BY a.id_apartado, c.nombre, c.apellido, c.telefono, p.nombre, p.marca, p.modelo
        """
        return self.db.fetch_one(query, (id_apartado,))
    
    def obtener_historial_pagos(self, id_apartado: int) -> list[dict]:
        """Obtiene el historial de pagos de un apartado."""
        query = """
            SELECT da.id_detalle, da.fecha_pago, da.monto,
                   mc.tipo_movimiento, mc.descripcion, mc.fecha_hora,
                   u.nombre as usuario_nombre
            FROM detalle_apartado da
            JOIN movimiento_caja mc ON da.id_movimiento_fk = mc.id_movimiento
            JOIN usuario u ON mc.id_usuario_fk = u.id_usuario
            WHERE da.id_apartado_fk = %s
            ORDER BY da.fecha_pago DESC
        """
        return self.db.fetch_all(query, (id_apartado,))
    
    # services/apartado_service.py - AGREGAR ESTOS MÉTODOS

    def crear_cuenta_por_cobrar_apartado(self, id_apartado: int, id_caja_fk: int, id_usuario_fk: int) -> bool:
        """
        Crea una cuenta por cobrar para un apartado que es por envío.
        Esto permite rastrear el cobro del envío.
        """
        # Obtener datos del apartado
        apartado = self.obtener_detalle_apartado(id_apartado)
        if not apartado:
            return False
        
        # Crear movimiento de caja como CUENTA_POR_COBRAR
        query_movimiento = """
            INSERT INTO movimiento_caja (
                id_caja_fk, tipo_movimiento, descripcion, monto, fecha_hora, id_usuario_fk
            ) VALUES (%s, %s, %s, %s, NOW(), %s)
            RETURNING id_movimiento
        """
        
        descripcion = f"Apartado por envío #{id_apartado} - {apartado['cliente_nombre']}"
        resultado_mov = self.db.fetch_one(
            query_movimiento,
            (id_caja_fk, 'CUENTA_POR_COBRAR', descripcion, apartado['total_producto'], id_usuario_fk)
        )
        
        if not resultado_mov:
            return False
        
        id_movimiento = resultado_mov['id_movimiento']
        
        # Crear cuenta por cobrar
        query_cuenta = """
            INSERT INTO cuenta_por_cobrar (
                id_movimiento_fk, numero_documento, monto, id_venta_fk, pagado
            ) VALUES (%s, %s, %s, %s, false)
        """
        
        numero_documento = f"APARTADO-{id_apartado}"
        
        return self.db.execute_query(
            query_cuenta,
            (id_movimiento, numero_documento, apartado['total_producto'], None)
        )
    
    def registrar_abono(self, id_apartado: int, monto: float, id_caja_fk: int, id_usuario_fk: int) -> bool:
        """Registra un abono a un apartado existente."""
        # Primero verificar si el apartado es por envío y crear cuenta por cobrar si no existe
        apartado = self.obtener_detalle_apartado(id_apartado)
        if apartado and apartado.get('es_envio'):
            # Verificar si ya existe cuenta por cobrar para este apartado
            query_verificar = """
                SELECT id_cuenta FROM cuenta_por_cobrar 
                WHERE numero_documento = %s
            """
            existe = self.db.fetch_one(query_verificar, (f"APARTADO-{id_apartado}",))
            if not existe:
                self.crear_cuenta_por_cobrar_apartado(id_apartado, id_caja_fk, id_usuario_fk)
        
        # Registrar el abono normalmente
        return self.apartado_dao.registrar_abono(id_apartado, monto, id_caja_fk, id_usuario_fk)