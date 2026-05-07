import sys
import os
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.conexion import DatabaseConnection


class ServiceVenta:
    """Servicio para gestionar ventas"""

    def __init__(self, id_usuario_actual: int = None):
        self.db = DatabaseConnection()
        self.id_usuario_actual = id_usuario_actual or self._obtener_usuario_por_defecto()

    def _obtener_usuario_por_defecto(self) -> int:
        try:
            query = "SELECT id_usuario FROM public.usuario WHERE estado = true LIMIT 1"
            result = self.db.fetch_one(query)
            return result['id_usuario'] if result else 1
        except:
            return 1

    def _obtener_caja_del_dia(self) -> int | None:
        query = "SELECT id_caja FROM public.caja WHERE fecha = CURRENT_DATE"
        resultado = self.db.fetch_one(query)
        return resultado['id_caja'] if resultado else None

    def _obtener_apertura_activa(self) -> dict | None:
        query = """
            SELECT id_apertura, id_caja_fk, monto_inicial, monto_final
            FROM public.apertura_cierre
            WHERE id_usuario_fk = %s AND fecha_hora_cierre IS NULL
            ORDER BY fecha_hora_apertura DESC LIMIT 1
        """
        return self.db.fetch_one(query, (self.id_usuario_actual,))

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

    def _generar_numero_documento(self) -> str:
        fecha = datetime.now().strftime('%Y%m%d')
        query = """
            SELECT COUNT(*) as total 
            FROM public.venta v
            JOIN public.movimiento_caja m ON v.id_movimiento_fk = m.id_movimiento
            WHERE DATE(m.fecha_hora) = CURRENT_DATE
        """
        resultado = self.db.fetch_one(query)
        consecutivo = (resultado['total'] + 1) if resultado else 1
        return f"F{fecha}-{consecutivo:04d}"

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

    def registrar_venta(self, id_cliente: int, forma_pago: str,
                        es_envio: bool = False,
                        id_empresa_fk: int = None,
                        numero_guia: str = None,
                        productos: list = None) -> dict:
        """
        productos: lista de dict con id_producto, cantidad, precio_unitario, descuento
        """
        try:
            # Verificar caja abierta
            caja_verificada = self.verificar_caja_abierta()
            if not caja_verificada['success']:
                return caja_verificada

            id_caja = caja_verificada['id_caja']
            id_apertura = caja_verificada['id_apertura']

            # Verificar cliente
            cliente = self.obtener_cliente(id_cliente)
            if not cliente:
                return {'success': False, 'message': f'Cliente ID {id_cliente} no encontrado'}

            if not productos:
                return {'success': False, 'message': 'Debe agregar al menos un producto'}

            # Calcular total (cantidad * precio_costo)
            total = 0.0
            for item in productos:
                # precio_unitario debe venir del producto (precio_costo)
                subtotal = float(item['cantidad']) * float(item['precio_unitario']) - float(item.get('descuento', 0))
                total += subtotal

            # Generar número de documento
            numero_documento = self._generar_numero_documento()
            nombre_cliente = f"{cliente.get('nombre', '')} {cliente.get('apellido', '')}".strip()

            # Crear movimiento de caja
            query_movimiento = """
                INSERT INTO public.movimiento_caja 
                    (id_caja_fk, tipo_movimiento, descripcion, monto, id_usuario_fk, fecha_hora)
                VALUES (%s, %s, %s, %s, %s, NOW()) RETURNING id_movimiento
            """
            resultado_mov = self.db.fetch_one(query_movimiento, (
                id_caja, 'INGRESO', f"Venta {numero_documento} - {nombre_cliente}",
                total, self.id_usuario_actual
            ))

            if not resultado_mov:
                return {'success': False, 'message': 'Error al crear movimiento de caja'}

            id_movimiento = resultado_mov['id_movimiento']

            # Crear venta
            query_venta = """
                INSERT INTO public.venta 
                    (id_movimiento_fk, id_cliente_fk, numero_documento, forma_pago, total, 
                     es_envio, id_empresa_fk, numero_guia)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_venta
            """
            resultado_venta = self.db.fetch_one(query_venta, (
                id_movimiento, id_cliente, numero_documento, forma_pago, total,
                es_envio, id_empresa_fk, numero_guia
            ))

            if not resultado_venta:
                return {'success': False, 'message': 'Error al registrar venta'}

            id_venta = resultado_venta['id_venta']

            # Registrar detalles
            for item in productos:
                subtotal = float(item['cantidad']) * float(item['precio_unitario']) - float(item.get('descuento', 0))
                query_detalle = """
                    INSERT INTO public.detalle_venta 
                        (id_venta_fk, id_producto_fk, cantidad, precio_unitario, subtotal, descuento)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                self.db.execute_query(query_detalle, (
                    id_venta, item['id_producto'], item['cantidad'],
                    item['precio_unitario'], subtotal, item.get('descuento', 0)
                ))

            # Actualizar monto final en apertura_cierre
            query_update_apertura = """
                UPDATE public.apertura_cierre 
                SET monto_final = COALESCE(monto_final, monto_inicial) + %s
                WHERE id_apertura = %s
            """
            self.db.execute_query(query_update_apertura, (total, id_apertura))

            # Si es envío, crear cuenta por cobrar
            if es_envio:
                query_cuenta = """
                    INSERT INTO public.cuenta_por_cobrar 
                        (id_movimiento_fk, numero_documento, monto, id_venta_fk, pagado)
                    VALUES (%s, %s, %s, %s, false)
                """
                self.db.execute_query(query_cuenta, (
                    id_movimiento, numero_documento, total, id_venta
                ))

            return {
                'success': True,
                'message': 'Venta registrada exitosamente',
                'id_venta': id_venta,
                'numero_documento': numero_documento,
                'total': float(total)
            }

        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}

    def registrar_venta_rapida(self, id_cliente: int, id_producto: int,
                               cantidad: int = 1, forma_pago: str = 'EF',
                               descuento: float = 0) -> dict:
        """
        Registra una venta rápida de un solo producto.
        Usa el precio_costo de la tabla producto.
        """
        producto = self.obtener_producto(id_producto)
        if not producto:
            return {'success': False, 'message': 'Producto no encontrado'}

        # Usar precio_costo directamente
        precio_costo = producto.get('precio_costo')
        if precio_costo is None or float(precio_costo) <= 0:
            return {'success': False, 'message': f'Producto {producto["nombre"]} no tiene precio_costo configurado'}

        productos = [{
            'id_producto': id_producto,
            'cantidad': cantidad,
            'precio_unitario': float(precio_costo),
            'descuento': descuento
        }]

        return self.registrar_venta(id_cliente, forma_pago, False, None, None, productos)

    def registrar_venta_envio(self, id_cliente: int, id_empresa_fk: int,
                              numero_guia: str, productos: list,
                              forma_pago: str = 'COD') -> dict:
        return self.registrar_venta(
            id_cliente=id_cliente,
            forma_pago=forma_pago,
            es_envio=True,
            id_empresa_fk=id_empresa_fk,
            numero_guia=numero_guia,
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

        # Calcular desglose por forma de pago
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

if __name__ == "__main__":
    from services.caja_service import CajaService

    print("=" * 50)
    print("   SISTEMA DE VENTAS - TECH SHOP")
    print("=" * 50)

    id_usuario = 1

    # Abrir caja si es necesario
    caja = CajaService()
    service = ServiceVenta(id_usuario_actual=id_usuario)

    verificacion = service.verificar_caja_abierta()
    if not verificacion['success']:
        print("\nAbriendo caja...")
        resultado_apertura = caja.registrar_apertura_caja(id_usuario, 500.00)
        if resultado_apertura:
            print(f"✅ Caja abierta! ID: {resultado_apertura}")
        else:
            print("❌ No se pudo abrir la caja")
            exit()
    else:
        print("✅ Caja ya está abierta")

    while True:
        print("\n" + "=" * 50)
        print("   SISTEMA DE VENTAS - TECH SHOP")
        print("=" * 50)
        print("1. Registrar venta completa")
        print("2. Registrar venta rápida")
        print("3. Registrar venta por envío")
        print("4. Ver ventas del día")
        print("5. Buscar venta por ID")
        print("6. Reporte de ventas del día")
        print("7. Reporte de ventas mensual")
        print("8. Listar cuentas por cobrar")
        print("9. Listar empresas de envío")
        print("10. Listar clientes")
        print("11. Listar productos")
        print("12. Salir")
        print("-" * 50)

        opcion = input("Opción: ")

        if opcion == "1":
            print("\n--- NUEVA VENTA ---")
            try:
                # Mostrar clientes disponibles
                clientes = service.listar_clientes()
                print("\nClientes disponibles:")
                for c in clientes[:5]:
                    print(f"  ID: {c['id_cliente']} - {c.get('nombre', '')} {c.get('apellido', '')}")

                id_cliente = int(input("\nID cliente: "))

                print("\nFormas de pago: EF, TC/TD, TF, DP, COD")
                forma_pago = input("Forma de pago: ").upper()
                es_envio = input("¿Es envío? (s/n): ").lower() == 's'

                id_empresa = None
                num_guia = None
                if es_envio:
                    empresas = service.listar_empresas_envio()
                    print("\nEmpresas de envío:")
                    for e in empresas:
                        print(f"  ID: {e['id_empresa']} - {e['nombre']}")
                    id_empresa = int(input("ID empresa envío: "))
                    num_guia = input("Número de guía: ")

                productos = []
                while True:
                    print(f"\n--- Producto {len(productos) + 1} ---")

                    prods = service.listar_productos()
                    print("\nProductos disponibles:")
                    for p in prods[:5]:
                        print(
                            f"  ID: {p['id_producto']} - {p['nombre']} {p.get('marca', '')} (Q{p.get('precio_costo', 0):.2f})")

                    id_prod = int(input("\nID producto: "))
                    cantidad = int(input("Cantidad: "))
                    # EL PRECIO SE USA EL DE LA TABLA, NO SE PIDE AL USUARIO
                    precio = float(service.obtener_producto(id_prod)['precio_costo'])
                    descuento = float(input("Descuento (0 si no): "))

                    productos.append({
                        'id_producto': id_prod,
                        'cantidad': cantidad,
                        'precio_unitario': precio,
                        'descuento': descuento
                    })

                    if input("¿Agregar otro producto? (s/n): ").lower() != 's':
                        break

                resultado = service.registrar_venta(
                    id_cliente, forma_pago, es_envio,
                    id_empresa, num_guia, productos
                )
                print(f"\n✅ {resultado['message']}")
                if resultado.get('success'):
                    print(f"   Documento: {resultado['numero_documento']}")
                    print(f"   Total: Q{resultado['total']:.2f}")

            except ValueError as e:
                print(f"❌ Error: {e}")

        elif opcion == "2":
            print("\n--- VENTA RÁPIDA ---")
            try:
                clientes = service.listar_clientes()
                print("\nClientes:")
                for c in clientes[:5]:
                    print(f"  ID: {c['id_cliente']} - {c.get('nombre', '')} {c.get('apellido', '')}")
                id_cliente = int(input("\nID cliente: "))

                productos_disponibles = service.listar_productos()
                print("\nProductos:")
                for p in productos_disponibles[:5]:
                    print(f"  ID: {p['id_producto']} - {p['nombre']} (Q{p.get('precio_costo', 0):.2f})")
                id_producto = int(input("ID producto: "))

                cantidad = int(input("Cantidad: "))
                # 🔴 ELIMINADO: ya no se pide precio al usuario
                # precio = float(input("Precio unitario: ") or 0)
                forma_pago = input("Forma de pago (EF/TC/TD/TF): ").upper()
                descuento = float(input("Descuento (0 si no): "))

                resultado = service.registrar_venta_rapida(
                    id_cliente, id_producto, cantidad, forma_pago, descuento
                )
                print(f"\n✅ {resultado['message']}")

            except ValueError:
                print("❌ Error: Ingrese valores válidos")

        elif opcion == "3":
            print("\n--- VENTA POR ENVÍO ---")
            try:
                clientes = service.listar_clientes()
                print("\nClientes:")
                for c in clientes[:5]:
                    print(f"  ID: {c['id_cliente']} - {c.get('nombre', '')} {c.get('apellido', '')}")
                id_cliente = int(input("\nID cliente: "))

                empresas = service.listar_empresas_envio()
                print("\nEmpresas de envío:")
                for e in empresas:
                    print(f"  ID: {e['id_empresa']} - {e['nombre']}")
                id_empresa = int(input("ID empresa envío: "))
                num_guia = input("Número de guía: ")

                productos = []
                while True:
                    print(f"\n--- Producto {len(productos) + 1} ---")
                    prods = service.listar_productos()
                    for p in prods[:5]:
                        print(f"  ID: {p['id_producto']} - {p['nombre']} (Q{p.get('precio_costo', 0):.2f})")
                    id_prod = int(input("ID producto: "))
                    cantidad = int(input("Cantidad: "))
                    # EL PRECIO SE USA EL DE LA TABLA
                    precio = float(service.obtener_producto(id_prod)['precio_costo'])
                    descuento = float(input("Descuento: "))

                    productos.append({
                        'id_producto': id_prod,
                        'cantidad': cantidad,
                        'precio_unitario': precio,
                        'descuento': descuento
                    })

                    if input("¿Agregar otro? (s/n): ").lower() != 's':
                        break

                resultado = service.registrar_venta_envio(id_cliente, id_empresa, num_guia, productos)
                print(f"\n✅ {resultado['message']}")

            except ValueError:
                print("❌ Error: Ingrese valores válidos")

        elif opcion == "4":
            print("\n--- VENTAS DEL DÍA ---")
            ventas = service.listar_ventas_dia()
            if ventas:
                print(f"\n{'ID':<6} {'Documento':<15} {'Cliente':<25} {'Total':<12} {'Forma':<8}")
                print("-" * 70)
                for v in ventas:
                    nombre = f"{v.get('nombre', '')} {v.get('apellido', '')}"
                    print(
                        f"{v['id_venta']:<6} {v['numero_documento']:<15} {nombre[:25]:<25} Q{float(v['total']):<11.2f} {v['forma_pago']:<8}")
            else:
                print("No hay ventas hoy")

        elif opcion == "5":
            print("\n--- BUSCAR VENTA ---")
            try:
                id_venta = int(input("ID venta: "))
                venta = service.obtener_venta(id_venta)
                if venta:
                    print(f"\n📄 VENTA #{venta['id_venta']}")
                    print(f"   Documento: {venta['numero_documento']}")
                    print(f"   Cliente: {venta.get('nombre', '')} {venta.get('apellido', '')}")
                    print(f"   Fecha: {venta.get('fecha_venta', 'N/A')}")
                    print(f"   Forma de pago: {venta['forma_pago']}")
                    print(f"   Total: Q{float(venta['total']):.2f}")
                    if venta.get('es_envio'):
                        print(f"   Envío - Empresa: {venta.get('empresa_envio', 'N/A')}")
                        print(f"   Guía: {venta.get('numero_guia', 'N/A')}")
                    if venta.get('productos'):
                        print("\n   Productos:")
                        for p in venta['productos']:
                            print(
                                f"      - {p['cantidad']}x {p['nombre']} @ Q{float(p['precio_unitario']):.2f} = Q{float(p['subtotal']):.2f}")
                else:
                    print("Venta no encontrada")
            except ValueError:
                print("ID inválido")

        elif opcion == "6":
            reporte = service.reporte_ventas_diario()
            print(f"\n📊 REPORTE DEL DÍA {reporte['fecha']}")
            print(f"   Total ventas: Q{reporte['total_ventas']:.2f}")
            print(f"   Cantidad de ventas: {reporte['cantidad']}")
            print("\n   Por forma de pago:")
            for forma, monto in reporte['desglose'].items():
                if monto > 0:
                    print(f"      - {forma}: Q{monto:.2f}")

        elif opcion == "7":
            print("\n--- REPORTE MENSUAL ---")
            try:
                anio = int(input("Año (ej. 2026): "))
                mes = int(input("Mes (1-12): "))
                ventas = service.reporte_ventas_mensual(anio, mes)
                if ventas:
                    total = sum(float(v['total']) for v in ventas)
                    print(f"\n📊 {anio}-{mes:02d}: {len(ventas)} ventas, Total: Q{total:.2f}")
                    for v in ventas[:10]:
                        print(f"   {v['fecha_hora'][:10]} - {v['numero_documento']} - Q{float(v['total']):.2f}")
                else:
                    print("No hay ventas en ese período")
            except ValueError:
                print("Año/mes inválido")

        elif opcion == "8":
            print("\n--- CUENTAS POR COBRAR PENDIENTES ---")
            cuentas = service.listar_cuentas_pendientes()
            if cuentas:
                for c in cuentas:
                    print(
                        f"ID: {c['id_cuenta']} | Documento: {c['numero_documento']} | Monto: Q{float(c['monto']):.2f}")
                marcar = input("\n¿Marcar alguna como pagada? (s/n): ").lower()
                if marcar == 's':
                    id_cuenta = int(input("ID de cuenta: "))
                    resultado = service.marcar_cuenta_pagada(id_cuenta)
                    print(f"✅ {resultado['message']}")
            else:
                print("No hay cuentas pendientes")

        elif opcion == "9":
            print("\n--- EMPRESAS DE ENVÍO ---")
            empresas = service.listar_empresas_envio()
            for e in empresas:
                print(f"ID: {e['id_empresa']} | {e['nombre']} | Tel: {e.get('telefono', 'N/A')}")

        elif opcion == "10":
            print("\n--- CLIENTES ---")
            clientes = service.listar_clientes()
            for c in clientes:
                print(
                    f"ID: {c['id_cliente']} | {c.get('nombre', '')} {c.get('apellido', '')} | Tel: {c.get('telefono', 'N/A')}")

        elif opcion == "11":
            print("\n--- PRODUCTOS ---")
            productos = service.listar_productos()
            for p in productos:
                print(
                    f"ID: {p['id_producto']} | {p['nombre']} {p.get('marca', '')} {p.get('modelo', '')} | Costo: Q{float(p.get('precio_costo', 0)):.2f}")

        elif opcion == "12":
            print("\n👋 ¡Hasta luego!")
            break

        else:
            print("Opción inválida")

        input("\nPresione Enter para continuar...")