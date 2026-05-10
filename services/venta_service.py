import sys
import os
from datetime import  date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.conexion import DatabaseConnection
from services.cuentas_por_cobrar_service import CuentaPorCobrarService



class ServiceVenta:
    """Servicio para gestionar ventas"""

    def __init__(self, id_usuario_actual: int = None):
        self.db = DatabaseConnection()
        self.id_usuario_actual = id_usuario_actual or self._obtener_usuario_por_defecto()
        self.cuentas_service = CuentaPorCobrarService()

    def _obtener_usuario_por_defecto(self) -> int:
        try:
            query = "SELECT id_usuario FROM public.usuario WHERE estado = true LIMIT 1"
            result = self.db.fetch_one(query)
            return result['id_usuario'] if result else 1
        except:
            return 1

    def _obtener_caja_del_dia(self) -> int | None:
        query = "SELECT id_caja FROM public.caja WHERE fecha = CURRENT_DATE"
        resultado = self.db.fetch_one(query, None)
        return resultado['id_caja'] if resultado else None

    def _obtener_apertura_activa(self) -> dict | None:
        query = """
            SELECT id_apertura, id_caja_fk, monto_inicial, monto_final
            FROM public.apertura_cierre
            WHERE fecha_hora_cierre IS NULL
            ORDER BY fecha_hora_apertura DESC LIMIT 1
        """
        return self.db.fetch_one(query, None)

    def verificar_caja_abierta(self) -> dict:
        apertura = self._obtener_apertura_activa()
        if not apertura:
            return {
                'success': False,
                'message': 'No hay una caja abierta. Debe abrir caja primero.'
            }
        caja = self._obtener_caja_del_dia()
        if not caja:
            return {
                'success': False,
                'message': 'No hay caja registrada para hoy.'
            }
        return {
            'success': True,
            'id_apertura': apertura['id_apertura'],
            'id_caja': caja
        }
    def obtener_cliente(self, id_cliente: int) -> dict | None:
        query = "SELECT id_cliente, nombre, apellido, telefono FROM public.cliente WHERE id_cliente = %s"
        return self.db.fetch_one(query, (id_cliente,))

    def obtener_producto(self, id_producto: int) -> dict | None:
        """Obtiene producto con su precio_costo"""
        query = """
            SELECT id_producto, nombre, marca, modelo, precio_costo 
            FROM public.producto WHERE id_producto = %s
        """
        return self.db.fetch_one(query, (id_producto,))

    # =========================================================
    # registrar_venta
    # =========================================================

    def registrar_venta(
            self,
            id_cliente: int,
            forma_pago: str,
            tipo_documento: str,
            numero_documento_manual: str,
            es_envio: bool = False,
            id_empresa_fk: int = None,
            numero_guia: str = None,
            precio_envio: float = 0,
            producto_pagado: bool = True,
            productos: list = None
    ) -> dict:

        try:

            # ==========================================
            # VERIFICAR TIPO Y NUMERO DE DOCUMENTO
            # ==========================================

            if not tipo_documento or tipo_documento not in ('FAC', 'REC'):
                return {
                    'success': False,
                    'message': 'Tipo de documento inválido. Use FAC (Factura) o REC (Recibo).'
                }

            if not numero_documento_manual or not str(numero_documento_manual).strip():
                return {
                    'success': False,
                    'message': 'Debe ingresar el número de documento.'
                }

            numero_documento = f"{tipo_documento}-{str(numero_documento_manual).strip()}"

            # ==========================================
            # VERIFICAR CAJA
            # ==========================================

            caja_verificada = self.verificar_caja_abierta()

            if not caja_verificada['success']:
                return caja_verificada

            id_caja = caja_verificada['id_caja']
            id_apertura = caja_verificada['id_apertura']

            # ==========================================
            # VERIFICAR CLIENTE
            # ==========================================

            cliente = self.obtener_cliente(id_cliente)

            if not cliente:
                return {
                    'success': False,
                    'message': f'Cliente ID {id_cliente} no encontrado'
                }

            if not productos:
                return {
                    'success': False,
                    'message': 'Debe agregar al menos un producto'
                }

            # ==========================================
            # CALCULAR TOTAL
            # ==========================================

            total = 0.0

            for item in productos:
                subtotal = (
                                   float(item['cantidad'])
                                   * float(item['precio_unitario'])
                           ) - float(item.get('descuento', 0))

                total += subtotal

            # ==========================================
            # SUMAR PRECIO DE ENVÍO
            # ==========================================

            total += float(precio_envio or 0)

            # ==========================================
            # NOMBRE CLIENTE
            # ==========================================

            nombre_cliente = (
                f"{cliente.get('nombre', '')} "
                f"{cliente.get('apellido', '')}"
            ).strip()

            # ==========================================
            # DETERMINAR TIPO DE MOVIMIENTO
            # ==========================================

            tipo_movimiento = (
                'INGRESO'
                if producto_pagado
                else 'CUENTA_POR_COBRAR'
            )

            descripcion_movimiento = (
                f"Venta {numero_documento} - {nombre_cliente}"
                if producto_pagado
                else f"Cuenta por cobrar {numero_documento} - {nombre_cliente}"
            )

            # ==========================================
            # CREAR MOVIMIENTO
            # ==========================================

            query_movimiento = """
                INSERT INTO public.movimiento_caja
                (
                    id_caja_fk,
                    tipo_movimiento,
                    descripcion,
                    monto,
                    id_usuario_fk,
                    fecha_hora
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    NOW()
                )
                RETURNING id_movimiento
            """

            resultado_mov = self.db.fetch_one(
                query_movimiento,
                (
                    id_caja,
                    tipo_movimiento,
                    descripcion_movimiento,
                    total,
                    self.id_usuario_actual
                )
            )

            if not resultado_mov:
                return {
                    'success': False,
                    'message': 'Error al crear movimiento'
                }

            id_movimiento = resultado_mov['id_movimiento']

            # ==========================================
            # CREAR VENTA
            # ==========================================

            query_venta = """
                INSERT INTO public.venta
                (
                    id_movimiento_fk,
                    id_cliente_fk,
                    numero_documento,
                    forma_pago,
                    total,
                    es_envio,
                    id_empresa_fk,
                    numero_guia,
                    producto_pagado
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id_venta
            """

            resultado_venta = self.db.fetch_one(
                query_venta,
                (
                    id_movimiento,
                    id_cliente,
                    numero_documento,
                    forma_pago,
                    total,
                    es_envio,
                    id_empresa_fk,
                    numero_guia,
                    producto_pagado
                )
            )

            if not resultado_venta:
                return {
                    'success': False,
                    'message': 'Error al registrar venta'
                }

            id_venta = resultado_venta['id_venta']

            # ==========================================
            # REGISTRAR DETALLES
            # ==========================================

            for item in productos:
                subtotal = (
                                   float(item['cantidad'])
                                   * float(item['precio_unitario'])
                           ) - float(item.get('descuento', 0))

                query_detalle = """
                    INSERT INTO public.detalle_venta
                    (
                        id_venta_fk,
                        id_producto_fk,
                        cantidad,
                        precio_unitario,
                        subtotal,
                        descuento
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """

                self.db.execute_query(
                    query_detalle,
                    (
                        id_venta,
                        item['id_producto'],
                        item['cantidad'],
                        item['precio_unitario'],
                        subtotal,
                        item.get('descuento', 0)
                    )
                )

            # ==========================================
            # SOLO SUMAR A CAJA SI YA FUE PAGADO
            # ==========================================

            if producto_pagado:
                query_update_apertura = """
                    UPDATE public.apertura_cierre
                    SET monto_final =
                        COALESCE(monto_final, monto_inicial) + %s
                    WHERE id_apertura = %s
                """

                self.db.execute_query(
                    query_update_apertura,
                    (
                        total,
                        id_apertura
                    )
                )

            # ==========================================
            # CREAR CUENTA POR COBRAR
            # ==========================================

            if not producto_pagado:
                self.cuentas_service.registrar_cuenta(
                    id_caja_fk=id_caja,
                    id_usuario_fk=self.id_usuario_actual,
                    numero_documento=numero_documento,
                    monto=total,
                    id_venta_fk=id_venta
                )

            return {
                'success': True,
                'message': 'Venta registrada exitosamente',
                'id_venta': id_venta,
                'numero_documento': numero_documento,
                'total': float(total)
            }

        except Exception as e:

            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }

    def registrar_venta_rapida(
            self,
            id_cliente: int,
            id_producto: int,
            tipo_documento: str,
            numero_documento_manual: str,
            cantidad: int = 1,
            forma_pago: str = 'EF',
            descuento: float = 0
    ) -> dict:

        producto = self.obtener_producto(id_producto)

        if not producto:
            return {
                'success': False,
                'message': 'Producto no encontrado'
            }

        precio_costo = producto.get('precio_costo')

        if precio_costo is None or float(precio_costo) <= 0:
            return {
                'success': False,
                'message': f'Producto {producto["nombre"]} no tiene precio_costo configurado'
            }

        productos = [
            {
                'id_producto': id_producto,
                'cantidad': cantidad,
                'precio_unitario': float(precio_costo),
                'descuento': descuento
            }
        ]

        return self.registrar_venta(
            id_cliente=id_cliente,
            forma_pago=forma_pago,
            tipo_documento=tipo_documento,
            numero_documento_manual=numero_documento_manual,
            es_envio=False,
            id_empresa_fk=None,
            numero_guia=None,
            precio_envio=0,
            producto_pagado=True,
            productos=productos
        )

    # =========================================================
    # registrar_venta_envio
    # =========================================================

    def registrar_venta_envio(
            self,
            id_cliente: int,
            id_empresa_fk: int,
            numero_guia: str,
            productos: list,
            tipo_documento: str,
            numero_documento_manual: str,
            forma_pago: str = 'COD',
            precio_envio: float = 0,
            producto_pagado: bool = False
    ) -> dict:

        return self.registrar_venta(
            id_cliente=id_cliente,
            forma_pago=forma_pago,
            tipo_documento=tipo_documento,
            numero_documento_manual=numero_documento_manual,
            es_envio=True,
            id_empresa_fk=id_empresa_fk,
            numero_guia=numero_guia,
            precio_envio=precio_envio,
            producto_pagado=producto_pagado,
            productos=productos
        )

    def obtener_venta(self, id_venta: int) -> dict:
        query = """
            SELECT v.id_venta, v.numero_documento, v.forma_pago, v.total,
                   v.es_envio, v.numero_guia, m.fecha_hora as fecha_venta,
                   c.id_cliente, c.nombre, c.apellido, c.telefono,
                   e.id_empresa, e.nombre as empresa_envio
            FROM public.venta v
            JOIN public.movimiento_caja m ON v.id_movimiento_fk = m.id_movimiento
            JOIN public.cliente c ON v.id_cliente_fk = c.id_cliente
            LEFT JOIN public.empresa_envio e ON v.id_empresa_fk = e.id_empresa
            WHERE v.id_venta = %s
        """
        venta = self.db.fetch_one(query, (id_venta,))

        if venta:
            if venta.get('total'):
                venta['total'] = float(venta['total'])

            query_detalles = """
                SELECT dv.cantidad, dv.precio_unitario, dv.subtotal, dv.descuento,
                       p.id_producto, p.nombre, p.marca, p.modelo, p.precio_costo
                FROM public.detalle_venta dv
                JOIN public.producto p ON dv.id_producto_fk = p.id_producto
                WHERE dv.id_venta_fk = %s
            """
            detalles = self.db.fetch_all(query_detalles, (id_venta,))
            for d in detalles:
                if d.get('precio_unitario'):
                    d['precio_unitario'] = float(d['precio_unitario'])
                if d.get('subtotal'):
                    d['subtotal'] = float(d['subtotal'])
                if d.get('precio_costo'):
                    d['precio_costo'] = float(d['precio_costo'])
            venta['productos'] = detalles

        return venta

    def listar_ventas_dia(self) -> list:
        query = """
            SELECT v.id_venta, v.numero_documento, v.forma_pago, v.total,
                   v.es_envio, v.numero_guia, m.fecha_hora,
                   c.id_cliente, c.nombre, c.apellido
            FROM public.venta v
            JOIN public.movimiento_caja m ON v.id_movimiento_fk = m.id_movimiento
            JOIN public.cliente c ON v.id_cliente_fk = c.id_cliente
            WHERE DATE(m.fecha_hora) = CURRENT_DATE
            ORDER BY m.fecha_hora DESC
        """
        ventas = self.db.fetch_all(query) or []
        for v in ventas:
            if v.get('total'):
                v['total'] = float(v['total'])
        return ventas

    def reporte_ventas_diario(self) -> dict:
        ventas = self.listar_ventas_dia()
        total_ventas = sum(float(v['total']) for v in ventas) if ventas else 0

        ventas_efectivo = sum(float(v['total']) for v in ventas if v['forma_pago'] == 'EF')
        ventas_tarjeta = sum(float(v['total']) for v in ventas if v['forma_pago'] == 'TC/TD')
        ventas_transferencia = sum(float(v['total']) for v in ventas if v['forma_pago'] == 'TF')
        ventas_envio = sum(float(v['total']) for v in ventas if v['es_envio'] == True)

        return {
            'fecha': date.today(),
            'total_ventas': total_ventas,
            'cantidad': len(ventas),
            'desglose': {
                'efectivo': ventas_efectivo,
                'tarjeta': ventas_tarjeta,
                'transferencia': ventas_transferencia,
                'envio': ventas_envio
            },
            'ventas': ventas
        }

    def reporte_ventas_mensual(self, anio: int, mes: int) -> list:
        """Reporte de ventas mensual"""
        query = """
            SELECT v.id_venta, v.numero_documento, v.forma_pago, v.total,
                   v.es_envio, m.fecha_hora,
                   c.nombre, c.apellido
            FROM public.venta v
            JOIN public.movimiento_caja m ON v.id_movimiento_fk = m.id_movimiento
            JOIN public.cliente c ON v.id_cliente_fk = c.id_cliente
            WHERE EXTRACT(YEAR FROM m.fecha_hora) = %s 
              AND EXTRACT(MONTH FROM m.fecha_hora) = %s
            ORDER BY m.fecha_hora
        """
        ventas = self.db.fetch_all(query, (anio, mes)) or []
        for v in ventas:
            if v.get('total'):
                v['total'] = float(v['total'])
        return ventas

    def listar_cuentas_pendientes(self) -> list:
        """Lista cuentas por cobrar pendientes"""
        query = """
            SELECT id_cuenta, numero_documento, monto, id_venta_fk
            FROM public.cuenta_por_cobrar 
            WHERE pagado = false
            ORDER BY id_cuenta
        """
        cuentas = self.db.fetch_all(query) or []
        for c in cuentas:
            if c.get('monto'):
                c['monto'] = float(c['monto'])
        return cuentas

    def marcar_cuenta_pagada(self, id_cuenta: int) -> dict:
        """Marca cuenta como pagada"""
        try:
            query = "UPDATE public.cuenta_por_cobrar SET pagado = true WHERE id_cuenta = %s"
            self.db.execute_query(query, (id_cuenta,))
            return {'success': True, 'message': 'Cuenta marcada como pagada'}
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}

    def listar_empresas_envio(self) -> list:
        query = "SELECT id_empresa, nombre, telefono FROM public.empresa_envio ORDER BY nombre"
        return self.db.fetch_all(query) or []

    def listar_clientes(self) -> list:
        query = "SELECT id_cliente, nombre, apellido, telefono FROM public.cliente ORDER BY nombre"
        return self.db.fetch_all(query) or []

    def listar_productos(self) -> list:
        query = """
            SELECT id_producto, nombre, marca, modelo, precio_costo 
            FROM public.producto ORDER BY nombre
        """
        productos = self.db.fetch_all(query) or []
        for p in productos:
            if p.get('precio_costo'):
                p['precio_costo'] = float(p['precio_costo'])
        return productos


# ==================== MENÚ DE PRUEBA ====================
"""
if __name__ == "__main__":

    from services.caja_service import CajaService

    print("=" * 50)
    print("   SISTEMA DE VENTAS - TECH SHOP")
    print("=" * 50)

    id_usuario = 1

    # =====================================================
    # ABRIR CAJA SI NO EXISTE
    # =====================================================

    caja = CajaService()
    service = ServiceVenta(id_usuario_actual=id_usuario)

    verificacion = service.verificar_caja_abierta()

    if not verificacion['success']:

        print("\nAbriendo caja...")

        resultado_apertura = caja.registrar_apertura_caja(
            id_usuario,
            500.00
        )

        if resultado_apertura:

            print(f" Caja abierta! ID: {resultado_apertura}")

        else:

            print(" No se pudo abrir la caja")
            exit()

    else:

        print(" Caja ya está abierta")

    # =====================================================
    # MENÚ
    # =====================================================

    while True:

        print("\n" + "=" * 50)
        print("   SISTEMA DE VENTAS - TECH SHOP")
        print("=" * 50)

        print("1. Registrar venta completa")
        print("2. Registrar venta rápida")
        print("3. Registrar venta por envío")
        print("4. Ver ventas del día")
        print("5. Buscar venta por ID")
        print("6. Reporte ventas del día")
        print("7. Reporte ventas mensual")
        print("8. Listar cuentas por cobrar")
        print("9. Listar empresas envío")
        print("10. Listar clientes")
        print("11. Listar productos")
        print("12. Salir")

        print("-" * 50)

        opcion = input("Opción: ")

        # =================================================
        # HELPER: PEDIR TIPO Y NÚMERO DE DOCUMENTO
        # =================================================

        def pedir_documento() -> tuple[str, str]:
            print("\nTipo de documento:")
            print("FAC = Factura")
            print("REC = Recibo")
            tipo = input("Tipo (FAC/REC): ").upper().strip()
            numero = input("Número de documento: ").strip()
            return tipo, numero

        # =================================================
        # VENTA COMPLETA
        # =================================================

        if opcion == "1":

            print("\n--- NUEVA VENTA ---")

            try:

                # =========================================
                # TIPO Y NÚMERO DE DOCUMENTO
                # =========================================

                tipo_documento, numero_documento_manual = pedir_documento()

                # =========================================
                # CLIENTES
                # =========================================

                clientes = service.listar_clientes()

                print("\nClientes disponibles:\n")

                for c in clientes[:10]:

                    nombre = (
                        f"{c.get('nombre', '')} "
                        f"{c.get('apellido', '')}"
                    ).strip()

                    print(
                        f"ID: {c['id_cliente']:<3} "
                        f"| {nombre}"
                    )

                id_cliente = int(
                    input("\nID cliente: ")
                )

                # =========================================
                # FORMA PAGO
                # =========================================

                print("\nFormas de pago:")
                print("EF = Efectivo")
                print("TC/TD = Tarjeta")
                print("TF = Transferencia")
                print("DP = Depósito")
                print("COD = Contra entrega")

                forma_pago = input(
                    "\nForma de pago: "
                ).upper()

                # =========================================
                # ENVÍO
                # =========================================

                es_envio = input(
                    "\n¿Es envío? (s/n): "
                ).lower() == 's'

                id_empresa = None
                num_guia = None
                precio_envio = 0

                if es_envio:

                    empresas = service.listar_empresas_envio()

                    print("\nEmpresas de envío:\n")

                    for e in empresas:

                        print(
                            f"ID: {e['id_empresa']:<3} "
                            f"| {e['nombre']}"
                        )

                    id_empresa = int(
                        input("\nID empresa: ")
                    )

                    num_guia = input(
                        "Número guía (opcional): "
                    ).strip()

                    precio_envio = float(
                        input(
                            "Costo envío (0 si no): "
                        ) or 0
                    )

                # =========================================
                # ¿YA PAGÓ?
                # =========================================

                producto_pagado = input(
                    "\n¿El cliente ya pagó? (s/n): "
                ).lower() == 's'

                # =========================================
                # PRODUCTOS
                # =========================================

                productos = []

                while True:

                    print(
                        f"\n--- PRODUCTO {len(productos)+1} ---"
                    )

                    prods = service.listar_productos()

                    print("\nProductos disponibles:\n")

                    for p in prods[:10]:

                        print(
                            f"ID: {p['id_producto']:<3} "
                            f"| {p['nombre']:<25} "
                            f"| Q{float(p.get('precio_costo', 0)):.2f}"
                        )

                    id_prod = int(
                        input("\nID producto: ")
                    )

                    cantidad = int(
                        input("Cantidad: ")
                    )

                    producto = service.obtener_producto(
                        id_prod
                    )

                    precio = float(
                        producto['precio_costo']
                    )

                    descuento = float(
                        input(
                            "Descuento (0 si no): "
                        ) or 0
                    )

                    productos.append({

                        'id_producto': id_prod,
                        'cantidad': cantidad,
                        'precio_unitario': precio,
                        'descuento': descuento

                    })

                    otro = input(
                        "\n¿Agregar otro producto? (s/n): "
                    ).lower()

                    if otro != 's':
                        break

                # =========================================
                # REGISTRAR VENTA
                # =========================================

                resultado = service.registrar_venta(

                    id_cliente=id_cliente,
                    forma_pago=forma_pago,
                    tipo_documento=tipo_documento,
                    numero_documento_manual=numero_documento_manual,
                    es_envio=es_envio,
                    id_empresa_fk=id_empresa,
                    numero_guia=num_guia,
                    precio_envio=precio_envio,
                    producto_pagado=producto_pagado,
                    productos=productos

                )

                # =========================================
                # RESPUESTA
                # =========================================

                if resultado.get('success'):

                    print("\n✅ VENTA REGISTRADA")

                    print(
                        f"\nDocumento: "
                        f"{resultado['numero_documento']}"
                    )

                    print(
                        f"Total: "
                        f"Q{resultado['total']:.2f}"
                    )

                    if not producto_pagado:

                        print(
                            "⚠️ Venta enviada a cuentas por cobrar"
                        )

                else:

                    print(
                        f"\n❌ {resultado['message']}"
                    )

            except ValueError:

                print(
                    "\n❌ Error: datos inválidos"
                )

        # =================================================
        # VENTA RÁPIDA
        # =================================================

        elif opcion == "2":

            print("\n--- VENTA RÁPIDA ---")

            try:

                tipo_documento, numero_documento_manual = pedir_documento()

                clientes = service.listar_clientes()

                print("\nClientes:\n")

                for c in clientes[:10]:

                    nombre = (
                        f"{c.get('nombre', '')} "
                        f"{c.get('apellido', '')}"
                    ).strip()

                    print(
                        f"ID: {c['id_cliente']:<3} "
                        f"| {nombre}"
                    )

                id_cliente = int(
                    input("\nID cliente: ")
                )

                productos = service.listar_productos()

                print("\nProductos:\n")

                for p in productos[:10]:

                    print(
                        f"ID: {p['id_producto']:<3} "
                        f"| {p['nombre']:<25} "
                        f"| Q{float(p.get('precio_costo', 0)):.2f}"
                    )

                id_producto = int(
                    input("\nID producto: ")
                )

                cantidad = int(
                    input("Cantidad: ")
                )

                forma_pago = input(
                    "Forma pago: "
                ).upper()

                descuento = float(
                    input(
                        "Descuento (0 si no): "
                    ) or 0
                )

                resultado = service.registrar_venta_rapida(

                    id_cliente=id_cliente,
                    id_producto=id_producto,
                    tipo_documento=tipo_documento,
                    numero_documento_manual=numero_documento_manual,
                    cantidad=cantidad,
                    forma_pago=forma_pago,
                    descuento=descuento

                )

                if resultado.get('success'):

                    print(
                        f"\n✅ {resultado['message']}"
                    )

                else:

                    print(
                        f"\n❌ {resultado['message']}"
                    )

            except ValueError:

                print("\n❌ Datos inválidos")

        # =================================================
        # VENTA ENVÍO
        # =================================================

        elif opcion == "3":

            print("\n--- VENTA POR ENVÍO ---")

            try:

                tipo_documento, numero_documento_manual = pedir_documento()

                clientes = service.listar_clientes()

                print("\nClientes:\n")

                for c in clientes[:10]:

                    nombre = (
                        f"{c.get('nombre', '')} "
                        f"{c.get('apellido', '')}"
                    ).strip()

                    print(
                        f"ID: {c['id_cliente']:<3} "
                        f"| {nombre}"
                    )

                id_cliente = int(
                    input("\nID cliente: ")
                )

                empresas = service.listar_empresas_envio()

                print("\nEmpresas:\n")

                for e in empresas:

                    print(
                        f"ID: {e['id_empresa']:<3} "
                        f"| {e['nombre']}"
                    )

                id_empresa = int(
                    input("\nID empresa: ")
                )

                numero_guia = input(
                    "Número guía: "
                ).strip()

                precio_envio = float(
                    input(
                        "Costo envío (0 si no): "
                    ) or 0
                )

                producto_pagado = input(
                    "¿Cliente ya pagó? (s/n): "
                ).lower() == 's'

                productos = []

                while True:

                    prods = service.listar_productos()

                    print("\nProductos:\n")

                    for p in prods[:10]:

                        print(
                            f"ID: {p['id_producto']:<3} "
                            f"| {p['nombre']:<25} "
                            f"| Q{float(p.get('precio_costo', 0)):.2f}"
                        )

                    id_prod = int(
                        input("\nID producto: ")
                    )

                    cantidad = int(
                        input("Cantidad: ")
                    )

                    producto = service.obtener_producto(
                        id_prod
                    )

                    precio = float(
                        producto['precio_costo']
                    )

                    descuento = float(
                        input(
                            "Descuento (0 si no): "
                        ) or 0
                    )

                    productos.append({

                        'id_producto': id_prod,
                        'cantidad': cantidad,
                        'precio_unitario': precio,
                        'descuento': descuento

                    })

                    otro = input(
                        "\n¿Agregar otro producto? (s/n): "
                    ).lower()

                    if otro != 's':
                        break

                resultado = service.registrar_venta_envio(

                    id_cliente=id_cliente,
                    id_empresa_fk=id_empresa,
                    numero_guia=numero_guia,
                    productos=productos,
                    tipo_documento=tipo_documento,
                    numero_documento_manual=numero_documento_manual,
                    precio_envio=precio_envio,
                    producto_pagado=producto_pagado

                )

                if resultado.get('success'):

                    print(
                        f"\n✅ {resultado['message']}"
                    )

                    print(
                        f"Documento: "
                        f"{resultado['numero_documento']}"
                    )

                    print(
                        f"Total: "
                        f"Q{resultado['total']:.2f}"
                    )

                    if not producto_pagado:

                        print(
                            "⚠️ Venta enviada a cuentas por cobrar"
                        )

                else:

                    print(
                        f"\n❌ {resultado['message']}"
                    )

            except ValueError:

                print("\n❌ Datos inválidos")

        # =================================================
        # SALIR
        # =================================================

        elif opcion == "12":

            print("\n👋 ¡Hasta luego!")
            break

        else:

            print("\n❌ Opción inválida")

        input("\nPresione ENTER para continuar...")
        """
