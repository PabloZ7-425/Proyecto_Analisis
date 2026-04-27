# UI/apartados_ui.py - Versión CORREGIDA
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QDialog, QFormLayout, QComboBox, QDoubleSpinBox,
                             QDateEdit, QMessageBox, QHeaderView, QInputDialog)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.conexion import DatabaseConnection


class DialogoApartado(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.init_ui()
        self.cargar_clientes()
        self.cargar_productos()

    def init_ui(self):
        self.setWindowTitle("Nuevo Apartado")
        self.setFixedSize(450, 400)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Registro de Apartado")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(20)

        form_layout = QFormLayout()

        self.cliente_combo = QComboBox()
        self.cliente_combo.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Cliente:", self.cliente_combo)

        self.producto_combo = QComboBox()
        self.producto_combo.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Producto:", self.producto_combo)

        self.total_producto = QDoubleSpinBox()
        self.total_producto.setMinimum(0)
        self.total_producto.setMaximum(999999)
        self.total_producto.setPrefix("Q")
        self.total_producto.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Total Producto:", self.total_producto)

        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(QDate.currentDate())
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Fecha Inicio:", self.fecha_inicio)

        layout.addLayout(form_layout)
        layout.addSpacing(30)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Guardar")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5C800;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        save_btn.clicked.connect(self.guardar)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def cargar_clientes(self):
        query = "SELECT id_cliente, nombre, apellido FROM cliente ORDER BY nombre"
        clientes = self.db.fetch_all(query)
        self.cliente_combo.clear()
        for cliente in clientes:
            nombre = f"{cliente['nombre']} {cliente['apellido']}" if cliente['apellido'] else cliente['nombre']
            self.cliente_combo.addItem(nombre, cliente['id_cliente'])

    def cargar_productos(self):
        query = "SELECT id_producto, nombre, marca, modelo FROM producto ORDER BY nombre"
        productos = self.db.fetch_all(query)
        self.producto_combo.clear()
        for producto in productos:
            texto = producto['nombre']
            if producto.get('marca'):
                texto += f" - {producto['marca']}"
            self.producto_combo.addItem(texto, producto['id_producto'])

    def guardar(self):
        cliente_id = self.cliente_combo.currentData()
        producto_id = self.producto_combo.currentData()
        total = self.total_producto.value()
        fecha = self.fecha_inicio.date().toString("yyyy-MM-dd")

        if not cliente_id or not producto_id:
            QMessageBox.warning(self, "Error", "Seleccione cliente y producto")
            return

        if total <= 0:
            QMessageBox.warning(self, "Error", "El total debe ser mayor a 0")
            return

        query = """
            INSERT INTO apartado (id_cliente_fk, id_producto_fk, total_producto, fecha_inicio, estado)
            VALUES (%s, %s, %s, %s, 'ACTIVO')
        """
        if self.db.execute_query(query, (cliente_id, producto_id, total, fecha)):
            QMessageBox.information(self, "Exito", "Apartado registrado")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar")


class VentanaApartados(QWidget):
    def __init__(self, id_caja_actual=None):
        super().__init__()
        self.db = DatabaseConnection()
        self.id_caja_actual = id_caja_actual
        self.init_ui()
        self.cargar_apartados()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        header = QHBoxLayout()
        title = QLabel("Gestion de Apartados")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("+ Nuevo Apartado")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5C800;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
        """)
        add_btn.clicked.connect(self.agregar_apartado)
        header.addWidget(add_btn)

        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Cliente", "Producto", "Total", "Fecha", "Estado", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #F9FAFB;
                padding: 12px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def cargar_apartados(self):
        query = """
            SELECT a.id_apartado, a.total_producto, a.fecha_inicio, a.estado,
                   c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                   p.nombre as producto_nombre, p.marca,
                   COALESCE(SUM(da.monto), 0) as total_pagado
            FROM apartado a
            JOIN cliente c ON a.id_cliente_fk = c.id_cliente
            JOIN producto p ON a.id_producto_fk = p.id_producto
            LEFT JOIN detalle_apartado da ON a.id_apartado = da.id_apartado_fk
            GROUP BY a.id_apartado, c.nombre, c.apellido, p.nombre, p.marca
            ORDER BY a.fecha_inicio DESC
        """
        apartados = self.db.fetch_all(query)

        self.table.setRowCount(len(apartados))

        for row, apartado in enumerate(apartados):
            self.table.setItem(row, 0, QTableWidgetItem(str(apartado['id_apartado'])))

            cliente = f"{apartado['cliente_nombre']} {apartado['cliente_apellido']}" if apartado[
                'cliente_apellido'] else apartado['cliente_nombre']
            self.table.setItem(row, 1, QTableWidgetItem(cliente))

            producto = apartado['producto_nombre']
            if apartado['marca']:
                producto += f" - {apartado['marca']}"
            self.table.setItem(row, 2, QTableWidgetItem(producto))

            self.table.setItem(row, 3, QTableWidgetItem(f"Q{apartado['total_producto']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(str(apartado['fecha_inicio'])))

            # Estado
            estado = apartado['estado']
            estado_label = QLabel(estado)
            if estado == 'ACTIVO':
                estado_label.setStyleSheet("color: #F5C800; font-weight: bold;")
            elif estado == 'COMPLETADO':
                estado_label.setStyleSheet("color: #10B981; font-weight: bold;")
            else:
                estado_label.setStyleSheet("color: #EF4444; font-weight: bold;")
            self.table.setCellWidget(row, 5, estado_label)

            # Acciones
            acciones = QWidget()
            acciones_layout = QHBoxLayout()
            acciones_layout.setContentsMargins(4, 4, 4, 4)

            saldo = apartado['total_producto'] - apartado['total_pagado']

            if saldo > 0 and self.id_caja_actual:
                pago_btn = QPushButton("Pagar")
                pago_btn.setStyleSheet("padding: 4px 12px; background-color: #F5C800; border-radius: 4px;")
                pago_btn.clicked.connect(lambda checked, a=apartado: self.registrar_pago(a))
                acciones_layout.addWidget(pago_btn)

            if apartado['estado'] == 'ACTIVO':
                cancel_btn = QPushButton("Cancelar")
                cancel_btn.setStyleSheet(
                    "padding: 4px 12px; background-color: #FEE2E2; color: #EF4444; border-radius: 4px;")
                cancel_btn.clicked.connect(lambda checked, a=apartado: self.cancelar_apartado(a))
                acciones_layout.addWidget(cancel_btn)

            acciones.setLayout(acciones_layout)
            self.table.setCellWidget(row, 6, acciones)

    def agregar_apartado(self):
        dialog = DialogoApartado(self)
        if dialog.exec_():
            self.cargar_apartados()

    def registrar_pago(self, apartado):
        if not self.id_caja_actual:
            QMessageBox.warning(self, "Error", "Debe abrir caja primero")
            return

        saldo_pendiente = apartado['total_producto'] - apartado['total_pagado']

        monto, ok = QInputDialog.getDouble(
            self,
            "Registrar Pago",
            f"Saldo pendiente: Q{saldo_pendiente:.2f}\nMonto a pagar:",
            0, 0, saldo_pendiente, 2
        )

        if not ok or monto <= 0:
            return

        # Registrar movimiento en caja
        mov_query = """
            INSERT INTO movimiento_caja (id_caja_fk, tipo_movimiento, descripcion, monto, fecha_hora)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id_movimiento
        """
        mov_result = self.db.fetch_one(mov_query, (
            self.id_caja_actual,
            "INGRESO",
            f"Pago apartado #{apartado['id_apartado']}",
            monto
        ))

        if mov_result:
            detalle_query = """
                INSERT INTO detalle_apartado (id_apartado_fk, id_movimiento_fk, fecha_pago, monto)
                VALUES (%s, %s, CURRENT_DATE, %s)
            """
            nuevo_total_pagado = apartado['total_pagado'] + monto
            nuevo_estado = 'COMPLETADO' if nuevo_total_pagado >= apartado['total_producto'] else 'ACTIVO'

            if self.db.execute_query(detalle_query, (apartado['id_apartado'], mov_result['id_movimiento'], monto)):
                self.db.execute_query(
                    "UPDATE apartado SET estado = %s WHERE id_apartado = %s",
                    (nuevo_estado, apartado['id_apartado'])
                )
                QMessageBox.information(self, "Exito", f"Pago de Q{monto:.2f} registrado")
                self.cargar_apartados()
            else:
                QMessageBox.critical(self, "Error", "No se pudo registrar el detalle")
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar el movimiento")

    def cancelar_apartado(self, apartado):
        reply = QMessageBox.question(
            self,
            "Confirmar",
            f"Cancelar apartado #{apartado['id_apartado']}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            query = "UPDATE apartado SET estado = 'CANCELADO' WHERE id_apartado = %s"
            if self.db.execute_query(query, (apartado['id_apartado'],)):
                QMessageBox.information(self, "Exito", "Apartado cancelado")
                self.cargar_apartados()
            else:
                QMessageBox.critical(self, "Error", "No se pudo cancelar")