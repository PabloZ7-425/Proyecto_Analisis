# UI/ventas_ui.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QGroupBox, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox,
                             QMessageBox, QHeaderView, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.conexion import DatabaseConnection


class DialogoSeleccionCliente(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.cliente_seleccionado = None
        self.clientes_data = []
        self.init_ui()
        self.cargar_clientes()

    def init_ui(self):
        self.setWindowTitle("Seleccionar Cliente")
        self.setFixedSize(550, 450)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Seleccione un Cliente")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar cliente...")
        self.search_input.setStyleSheet("padding: 10px; border-radius: 6px; border: 1px solid #E5E7EB;")
        self.search_input.textChanged.connect(self.buscar_clientes)
        layout.addWidget(self.search_input)

        layout.addSpacing(10)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Telefono"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.doubleClicked.connect(self.seleccionar_cliente)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.table)

        layout.addSpacing(10)

        btn_nuevo = QPushButton("+ Nuevo Cliente")
        btn_nuevo.setStyleSheet("""
            QPushButton {
                background-color: #F5C800;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        btn_nuevo.clicked.connect(self.nuevo_cliente)
        layout.addWidget(btn_nuevo)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.seleccionar_cliente)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def cargar_clientes(self):
        query = "SELECT id_cliente, nombre, apellido, telefono FROM cliente ORDER BY nombre"
        self.clientes_data = self.db.fetch_all(query)
        self.actualizar_tabla(self.clientes_data)

    def actualizar_tabla(self, clientes):
        self.table.setRowCount(len(clientes))
        for i, c in enumerate(clientes):
            nombre = f"{c['nombre']} {c['apellido']}" if c.get('apellido') else c['nombre']
            self.table.setItem(i, 0, QTableWidgetItem(str(c['id_cliente'])))
            self.table.setItem(i, 1, QTableWidgetItem(nombre))
            self.table.setItem(i, 2, QTableWidgetItem(c.get('telefono') or ''))

    def buscar_clientes(self):
        texto = self.search_input.text().lower()
        if not texto:
            self.actualizar_tabla(self.clientes_data)
            return
        filtrados = []
        for c in self.clientes_data:
            nombre_completo = f"{c['nombre']} {c['apellido']}" if c.get('apellido') else c['nombre']
            if texto in c['nombre'].lower() or texto in nombre_completo.lower():
                filtrados.append(c)
        self.actualizar_tabla(filtrados)

    def nuevo_cliente(self):
        from UI.clientes_ui import DialogoCliente
        dialog = DialogoCliente(self)
        if dialog.exec_():
            self.cargar_clientes()

    def seleccionar_cliente(self):
        row = self.table.currentRow()
        if row >= 0:
            cliente_id = int(self.table.item(row, 0).text())
            for c in self.clientes_data:
                if c['id_cliente'] == cliente_id:
                    self.cliente_seleccionado = c
                    break
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Seleccione un cliente")


class VentanasVentas(QWidget):
    def __init__(self, usuario_data, id_caja_actual=None):
        super().__init__()
        self.usuario_data = usuario_data
        self.id_caja_actual = id_caja_actual
        self.db = DatabaseConnection()
        self.cliente_actual = None
        self.cart_items = []
        self.init_ui()
        self.cargar_productos()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        header = QLabel("Nueva Venta")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(header)

        # Cliente section
        cliente_frame = QGroupBox("Datos del Cliente")
        cliente_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 10px;
            }
        """)
        cliente_layout = QHBoxLayout()

        self.cliente_label = QLabel("No hay cliente seleccionado")
        self.cliente_label.setStyleSheet("color: #6B7280; padding: 8px;")
        cliente_layout.addWidget(self.cliente_label)

        self.seleccionar_cliente_btn = QPushButton("Seleccionar Cliente")
        self.seleccionar_cliente_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5C800;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
        """)
        self.seleccionar_cliente_btn.clicked.connect(self.seleccionar_cliente)
        cliente_layout.addWidget(self.seleccionar_cliente_btn)

        cliente_frame.setLayout(cliente_layout)
        layout.addWidget(cliente_frame)

        # Contenido principal
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.crear_seleccion_producto(), 1)
        content_layout.addWidget(self.crear_carrito(), 2)
        layout.addLayout(content_layout)

        self.setLayout(layout)

    def seleccionar_cliente(self):
        dialog = DialogoSeleccionCliente(self)
        if dialog.exec_() and dialog.cliente_seleccionado:
            self.cliente_actual = dialog.cliente_seleccionado
            nombre = f"{self.cliente_actual['nombre']} {self.cliente_actual.get('apellido', '')}"
            self.cliente_label.setText(f"Cliente: {nombre} | Telefono: {self.cliente_actual.get('telefono', 'N/A')}")
            self.cliente_label.setStyleSheet("color: #10B981; padding: 8px; font-weight: bold;")

    def crear_seleccion_producto(self):
        widget = QWidget()
        layout = QVBoxLayout()

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
        self.product_search.setPlaceholderText("Buscar producto...")
        self.product_search.setStyleSheet("padding: 10px; border-radius: 6px; border: 1px solid #E5E7EB;")
        self.product_search.textChanged.connect(self.buscar_productos)
        search_layout.addWidget(self.product_search)

        self.product_combo = QComboBox()
        self.product_combo.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        search_layout.addWidget(self.product_combo)

        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

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
        cart_layout.addRow("Precio:", self.precio_spin)

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
        add_btn.clicked.connect(self.agregar_al_carrito)
        cart_layout.addRow(add_btn)

        cart_group.setLayout(cart_layout)
        layout.addWidget(cart_group)
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def crear_carrito(self):
        widget = QWidget()
        layout = QVBoxLayout()

        cart_label = QLabel("Carrito")
        cart_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(cart_label)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Producto", "Cantidad", "Precio", "Subtotal", "Accion"])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cart_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: white;
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

        buttons_layout = QHBoxLayout()

        clear_btn = QPushButton("Limpiar")
        clear_btn.setStyleSheet("padding: 10px; background-color: #F3F4F6; border-radius: 8px;")
        clear_btn.clicked.connect(self.limpiar_carrito)
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
        checkout_btn.clicked.connect(self.finalizar_venta)
        buttons_layout.addWidget(checkout_btn)

        layout.addLayout(buttons_layout)
        widget.setLayout(layout)
        return widget

    def cargar_productos(self):
        query = "SELECT id_producto, nombre, marca FROM producto ORDER BY nombre"
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

    def buscar_productos(self):
        texto = self.product_search.text().strip()
        if not texto:
            self.cargar_productos()
            return

        query = """
            SELECT id_producto, nombre, marca 
            FROM producto 
            WHERE LOWER(nombre) LIKE %s
            ORDER BY nombre
        """
        productos = self.db.fetch_all(query, (f'%{texto.lower()}%',))

        self.product_combo.clear()
        if productos:
            for p in productos:
                texto = p['nombre']
                if p.get('marca'):
                    texto += f" - {p['marca']}"
                self.product_combo.addItem(texto, p['id_producto'])
        else:
            self.product_combo.addItem("No encontrado", None)

    def agregar_al_carrito(self):
        if not self.cliente_actual:
            QMessageBox.warning(self, "Error", "Primero seleccione un cliente")
            return

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
        self.cargar_productos()

    def actualizar_tabla_carrito(self):
        self.cart_table.setRowCount(len(self.cart_items))

        for i, item in enumerate(self.cart_items):
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['producto_nombre']))
            self.cart_table.setItem(i, 1, QTableWidgetItem(str(item['cantidad'])))
            self.cart_table.setItem(i, 2, QTableWidgetItem(f"Q{item['precio']:.2f}"))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"Q{item['subtotal']:.2f}"))

            remove_btn = QPushButton("Eliminar")
            remove_btn.clicked.connect(lambda checked, row=i: self.remover_del_carrito(row))
            self.cart_table.setCellWidget(i, 4, remove_btn)

    def remover_del_carrito(self, row):
        self.cart_items.pop(row)
        self.actualizar_tabla_carrito()
        self.actualizar_total()

    def limpiar_carrito(self):
        self.cart_items = []
        self.actualizar_tabla_carrito()
        self.actualizar_total()

    def actualizar_total(self):
        total = sum(item['subtotal'] for item in self.cart_items)
        self.total_label.setText(f"Q{total:.2f}")

    def finalizar_venta(self):
        if not self.cliente_actual:
            QMessageBox.warning(self, "Error", "Seleccione un cliente")
            return

        if not self.cart_items:
            QMessageBox.warning(self, "Error", "Agregue productos al carrito")
            return

        if not self.id_caja_actual:
            QMessageBox.warning(self, "Error", "No hay caja abierta")
            return

        total = sum(item['subtotal'] for item in self.cart_items)
        forma_pago = self.cart_items[0]['forma_pago']

        # Crear movimiento
        query_mov = """
            INSERT INTO movimiento_caja (id_caja_fk, tipo_movimiento, descripcion, monto, fecha_hora)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id_movimiento
        """
        mov_result = self.db.fetch_one(query_mov, (self.id_caja_actual, "INGRESO", f"Venta", total))

        if not mov_result:
            QMessageBox.critical(self, "Error", "Error al crear movimiento")
            return

        id_movimiento = mov_result['id_movimiento']

        # Crear venta
        query_venta = """
            INSERT INTO venta (id_movimiento_fk, id_cliente_fk, numero_documento, forma_pago, total, es_envio)
            VALUES (%s, %s, %s, %s, %s, false)
            RETURNING id_venta
        """
        num_doc = f"FACT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        venta_result = self.db.fetch_one(query_venta,
                                         (id_movimiento, self.cliente_actual['id_cliente'], num_doc, forma_pago, total))

        if not venta_result:
            QMessageBox.critical(self, "Error", "Error al crear venta")
            return

        id_venta = venta_result['id_venta']

        # Detalles
        for item in self.cart_items:
            query_detalle = """
                INSERT INTO detalle_venta (id_venta_fk, id_producto_fk, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.db.execute_query(query_detalle,
                                  (id_venta, item['producto_id'], item['cantidad'], item['precio'], item['subtotal']))

        QMessageBox.information(self, "Exito", f"Venta completada. Total: Q{total:.2f}")

        self.limpiar_carrito()
        self.cliente_actual = None
        self.cliente_label.setText("No hay cliente seleccionado")
        self.cliente_label.setStyleSheet("color: #6B7280; padding: 8px;")