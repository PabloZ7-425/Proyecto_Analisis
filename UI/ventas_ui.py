# UI/ventas_ui.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QGroupBox, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox,
                             QMessageBox, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.conexion import DatabaseConnection


class VentanasVentas(QWidget):
    def __init__(self, usuario_data, id_caja_actual=None):
        super().__init__()
        self.usuario_data = usuario_data
        self.id_caja_actual = id_caja_actual
        self.db = DatabaseConnection()
        self.cart_items = []
        self.init_ui()
        self.load_products()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        header = QLabel("Nueva Venta")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(header)

        content_layout = QHBoxLayout()
        content_layout.addWidget(self.crear_seleccion_producto(), 1)
        content_layout.addWidget(self.crear_carrito(), 2)

        layout.addLayout(content_layout)
        self.setLayout(layout)

    def crear_seleccion_producto(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Buscar producto
        search_group = QGroupBox("Buscar Producto")
        search_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 10px;
            }
        """)
        search_layout = QVBoxLayout()

        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Nombre del producto")
        self.product_search.setStyleSheet("padding: 10px; border-radius: 6px; border: 1px solid #E5E7EB;")
        self.product_search.textChanged.connect(self.search_product)
        search_layout.addWidget(self.product_search)

        self.product_combo = QComboBox()
        self.product_combo.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        search_layout.addWidget(self.product_combo)

        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # Agregar al carrito
        cart_group = QGroupBox("Agregar al Carrito")
        cart_group.setStyleSheet(search_group.styleSheet())
        cart_layout = QFormLayout()

        self.cantidad_spin = QSpinBox()
        self.cantidad_spin.setMinimum(1)
        self.cantidad_spin.setMaximum(999)
        self.cantidad_spin.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        cart_layout.addRow("Cantidad:", self.cantidad_spin)

        self.precio_spin = QDoubleSpinBox()
        self.precio_spin.setMinimum(0)
        self.precio_spin.setMaximum(999999)
        self.precio_spin.setPrefix("Q")
        self.precio_spin.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        cart_layout.addRow("Precio Unitario:", self.precio_spin)

        add_btn = QPushButton("+ Agregar Producto")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5C800;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        add_btn.clicked.connect(self.add_to_cart)
        cart_layout.addRow(add_btn)

        cart_group.setLayout(cart_layout)
        layout.addWidget(cart_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def crear_carrito(self):
        widget = QWidget()
        layout = QVBoxLayout()

        cart_label = QLabel("Carrito de Compras")
        cart_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(cart_label)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(
            ["Producto", "Cantidad", "Precio", "Subtotal", "Forma Pago", "Accion"])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cart_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #F9FAFB;
                padding: 10px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.cart_table)

        # Forma de pago
        pago_layout = QHBoxLayout()
        pago_layout.addWidget(QLabel("Forma de Pago:"))
        self.forma_pago = QComboBox()
        self.forma_pago.addItems(["EFECTIVO", "TARJETA", "TRANSFERENCIA", "DEPOSITO"])
        self.forma_pago.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        pago_layout.addWidget(self.forma_pago)
        pago_layout.addStretch()
        layout.addLayout(pago_layout)

        # Total
        total_widget = QWidget()
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_layout.addWidget(QLabel("Total:"))
        self.total_label = QLabel("Q0.00")
        self.total_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.total_label.setStyleSheet("color: #F5C800;")
        total_layout.addWidget(self.total_label)
        total_widget.setLayout(total_layout)
        layout.addWidget(total_widget)

        # Botones
        buttons_layout = QHBoxLayout()

        clear_btn = QPushButton("Limpiar Carrito")
        clear_btn.setStyleSheet("padding: 10px; background-color: #F3F4F6; border-radius: 8px;")
        clear_btn.clicked.connect(self.clear_cart)
        buttons_layout.addWidget(clear_btn)

        checkout_btn = QPushButton("Finalizar Venta")
        checkout_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        checkout_btn.clicked.connect(self.finalize_sale)
        buttons_layout.addWidget(checkout_btn)

        layout.addLayout(buttons_layout)
        widget.setLayout(layout)
        return widget

    def load_products(self):
        query = "SELECT id_producto, nombre, marca FROM producto ORDER BY nombre LIMIT 50"
        productos = self.db.fetch_all(query)

        self.product_combo.clear()
        if productos:
            for p in productos:
                texto = p['nombre']
                if p.get('marca'):
                    texto += f" - {p['marca']}"
                self.product_combo.addItem(texto, p['id_producto'])
        else:
            self.product_combo.addItem("No hay productos", None)

    def search_product(self):
        search_text = self.product_search.text().strip()
        if not search_text:
            self.load_products()
            return

        query = """
            SELECT id_producto, nombre, marca 
            FROM producto 
            WHERE LOWER(nombre) LIKE %s
            ORDER BY nombre
            LIMIT 20
        """
        productos = self.db.fetch_all(query, (f'%{search_text.lower()}%',))

        self.product_combo.clear()
        if productos:
            for p in productos:
                texto = p['nombre']
                if p.get('marca'):
                    texto += f" - {p['marca']}"
                self.product_combo.addItem(texto, p['id_producto'])
        else:
            self.product_combo.addItem("No se encontraron", None)

    def add_to_cart(self):
        product_id = self.product_combo.currentData()
        product_name = self.product_combo.currentText()
        cantidad = self.cantidad_spin.value()
        precio = self.precio_spin.value()

        if not product_id:
            QMessageBox.warning(self, "Error", "Seleccione un producto")
            return

        if cantidad <= 0:
            QMessageBox.warning(self, "Error", "Cantidad invalida")
            return

        if precio <= 0:
            QMessageBox.warning(self, "Error", "Precio invalido")
            return

        subtotal = cantidad * precio

        self.cart_items.append({
            'producto_id': product_id,
            'producto_nombre': product_name,
            'cantidad': cantidad,
            'precio': precio,
            'subtotal': subtotal,
            'forma_pago': self.forma_pago.currentText()
        })

        self.actualizar_tabla_carrito()
        self.actualizar_total()

        self.cantidad_spin.setValue(1)
        self.precio_spin.setValue(0)
        self.product_search.clear()
        self.load_products()

    def actualizar_tabla_carrito(self):
        self.cart_table.setRowCount(len(self.cart_items))

        for i, item in enumerate(self.cart_items):
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['producto_nombre']))
            self.cart_table.setItem(i, 1, QTableWidgetItem(str(item['cantidad'])))
            self.cart_table.setItem(i, 2, QTableWidgetItem(f"Q{item['precio']:.2f}"))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"Q{item['subtotal']:.2f}"))
            self.cart_table.setItem(i, 4, QTableWidgetItem(item['forma_pago']))

            remove_btn = QPushButton("Eliminar")
            remove_btn.setStyleSheet("padding: 4px 8px; background-color: #FEE2E2; color: #EF4444; border-radius: 4px;")
            remove_btn.clicked.connect(lambda checked, row=i: self.remover_del_carrito(row))
            self.cart_table.setCellWidget(i, 5, remove_btn)

    def remover_del_carrito(self, row):
        self.cart_items.pop(row)
        self.actualizar_tabla_carrito()
        self.actualizar_total()

    def clear_cart(self):
        self.cart_items = []
        self.actualizar_tabla_carrito()
        self.actualizar_total()

    def actualizar_total(self):
        total = sum(item['subtotal'] for item in self.cart_items)
        self.total_label.setText(f"Q{total:.2f}")

    def finalize_sale(self):
        if not self.cart_items:
            QMessageBox.warning(self, "Error", "El carrito esta vacio")
            return

        if not self.id_caja_actual:
            QMessageBox.warning(self, "Error", "No hay caja abierta")
            return

        total_venta = sum(item['subtotal'] for item in self.cart_items)
        forma_pago = self.cart_items[0]['forma_pago']

        # Crear movimiento en caja
        mov_query = """
            INSERT INTO movimiento_caja (id_caja_fk, tipo_movimiento, descripcion, monto, fecha_hora)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id_movimiento
        """
        mov_result = self.db.fetch_one(mov_query, (
        self.id_caja_actual, "INGRESO", f"Venta - {len(self.cart_items)} productos", total_venta))

        if not mov_result:
            QMessageBox.critical(self, "Error", "No se pudo registrar movimiento")
            return

        id_movimiento = mov_result['id_movimiento']

        # Crear venta
        venta_query = """
            INSERT INTO venta (id_movimiento_fk, id_cliente_fk, numero_documento, forma_pago, total, es_envio)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_venta
        """
        numero_doc = f"FACT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        venta_result = self.db.fetch_one(venta_query, (id_movimiento, 1, numero_doc, forma_pago, total_venta, False))

        if not venta_result:
            QMessageBox.critical(self, "Error", "No se pudo registrar venta")
            return

        id_venta = venta_result['id_venta']

        # Detalles de venta
        for item in self.cart_items:
            detalle_query = """
                INSERT INTO detalle_venta (id_venta_fk, id_producto_fk, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.db.execute_query(detalle_query,
                                  (id_venta, item['producto_id'], item['cantidad'], item['precio'], item['subtotal']))

        QMessageBox.information(self, "Exito", f"Venta registrada. Total: Q{total_venta:.2f}")
        self.clear_cart()