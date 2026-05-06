import sys
import os
from datetime import datetime

# Configuración de rutas para encontrar la conexión (estilo CajaService)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.conexion import DatabaseConnection

class ServiceApartado:
    def __init__(self):
        self.db = DatabaseConnection()

    def crear_apartado(self, id_cliente, id_producto, monto_original, descuento=0, primer_abono=0):
        """Registra el apartado inicial en la tabla 'apartado'."""
        monto_final = monto_original - descuento
        fecha_inicio = datetime.now().date()
        
        # El estado nace como 'pagado' si el abono inicial cubre el total, sino 'pendiente'
        estado = "pagado" if primer_abono >= monto_final else "pendiente"

        query_apartado = """
            INSERT INTO apartado 
                (id_cliente_fk, id_producto_fk, total_producto, fecha_inicio, estado, 
                 monto_original, descuento_pactado, monto_final)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_apartado
        """
        params = (id_cliente, id_producto, monto_original, fecha_inicio, estado, 
                  monto_original, descuento, monto_final)
        
        try:
            res = self.db.fetch_one(query_apartado, params)
            if not res:
                return None

            id_apartado = res['id_apartado']
            print(f"✅ Apartado principal creado (ID: {id_apartado})")

            if primer_abono > 0:
                self.registrar_abono(id_apartado, primer_abono)
            
            return id_apartado
            
        except Exception as e:
            print(f"❌ Error al insertar en tabla 'apartado': {e}")
            return None

    def registrar_abono(self, id_apartado, monto):
        """Registra un pago y verifica si el apartado se liquida."""
        try:
            # Asegúrate de que el nombre de la tabla sea 'detalle_apartado'
            query_detalle = """
                INSERT INTO detalle_apartado (id_apartado_fk, id_movimiento_fk, fecha_pago, monto)
                VALUES (%s, 1, CURRENT_DATE, %s)
                RETURNING id_detalle
            """
            res = self.db.fetch_one(query_detalle, (id_apartado, monto))
            
            if res:
                print(f"✅ Abono de {monto} registrado exitosamente")
                # Al registrar abono, revisamos si ya terminó de pagar todo
                self.verificar_liquidacion(id_apartado)
                return res['id_detalle']
                
        except Exception as e:
            print(f"❌ ERROR EN DETALLE: {e}")
            print("💡 Tip: Verifica que el Movimiento ID 1 exista en tu base de datos.")

    def verificar_liquidacion(self, id_apartado):
        """Compara el total pagado contra el monto final y actualiza el estado."""
        # 1. Obtener datos del apartado
        apartado = self.db.fetch_one("SELECT monto_final, estado FROM apartado WHERE id_apartado = %s", (id_apartado,))
        
        # 2. Sumar todos los abonos realizados en la tabla de detalles
        res_sum = self.db.fetch_one("SELECT SUM(monto) as total FROM detalle_apartado WHERE id_apartado_fk = %s", (id_apartado,))
        
        total_pagado = res_sum['total'] if res_sum['total'] else 0
        monto_objetivo = apartado['monto_final']
        faltante = monto_objetivo - total_pagado

        print(f"📊 Resumen de Cuenta: Pagado {total_pagado} | Faltan {max(0, faltante)}")

        # 3. Si ya pagó todo y el estado era pendiente, lo pasamos a pagado
        if total_pagado >= monto_objetivo and apartado['estado'] == 'pendiente':
            ok = self.db.execute_query(
                "UPDATE apartado SET estado = 'pagado' WHERE id_apartado = %s", 
                (id_apartado,)
            )
            if ok:
                print(f"🎊 ¡APARTADO #{id_apartado} LIQUIDADO COMPLETAMENTE!")

# ──────────────────────────────────────────────────────────────
# BLOQUE DE PRUEBA PARA VARIOS ABONOS
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    servicio = ServiceApartado()
    print("\n--- 🛒 PRUEBA DE ABONOS MÚLTIPLES ---")

    try:
        # 1. Crear un nuevo apartado para la prueba
        print("Primero, creemos un apartado rápido:")
        id_p = int(input("ID del producto (ej. 1): "))
        id_c = int(input("ID del cliente (ej. 1): "))
        m_o  = float(input("Precio del producto: "))
        
        id_a = servicio.crear_apartado(id_c, id_p, m_o, descuento=0, primer_abono=0)

        # 2. Bucle para hacer abonos seguidos
        if id_a:
            print(f"\n--- Iniciando ciclo de abonos para Apartado #{id_a} ---")
            
            while True:
                continuar = input("\n¿Desea realizar un abono? (s/n): ").lower()
                if continuar != 's':
                    break
                
                monto_abono = float(input("Monto a abonar: "))
                servicio.registrar_abono(id_a, monto_abono)
                
                # Consultar si ya se pagó para sugerir salir
                estado_actual = servicio.db.fetch_one("SELECT estado FROM apartado WHERE id_apartado = %s", (id_a,))
                if estado_actual['estado'] == 'pagado':
                    print("El apartado ya está totalmente pagado. Saliendo...")
                    break

        print("\n🚀 Prueba finalizada. Revisa tu historial en Supabase.")

    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")