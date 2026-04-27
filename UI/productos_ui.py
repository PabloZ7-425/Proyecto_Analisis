# UI/productos_ui.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QDialog, QFormLayout, QLineEdit, QMessageBox,
                             QHeaderView, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.conexion import DatabaseConnection


class DialogoProducto(QDialog):
    def __init__(self, producto=None, parent=None):
        super().__init__(parent)
        self.producto = producto
        self.db = DatabaseConnection()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Nuevo Producto" if not self.producto else "Editar Producto")
        self.setFixedSize(450, 450)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Datos del Producto")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(20)

        form_layout = QFormLayout()

        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Nombre del producto")
        self.nombre_input.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Nombre:", self.nombre_input)

        self.marca_input = QLineEdit()
        self.marca_input.setPlaceholderText("Marca")
        self.marca_input.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Marca:", self.marca_input)

        self.modelo_input = QLineEdit()
        self.modelo_input.setPlaceholderText("Modelo")
        self.modelo_input.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Modelo:", self.modelo_input)

        self.descripcion_input = QTextEdit()
        self.descripcion_input.setPlaceholderText("Descripción del producto")
        self.descripcion_input.setMaximumHeight(100)
        self.descripcion_input.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Descripción:", self.descripcion_input)

        layout.addLayout(form_layout)
        layout.addSpacing(30)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 10px; 
                background-color: #F3F4F6; 
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Guardar")
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 10px; 
                background-color: #F5C800; 
                border-radius: 8px; 
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E5B800;
            }
        """)
        save_btn.clicked.connect(self.guardar)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        if self.producto:
            self.cargar_datos()

    def cargar_datos(self):
        self.nombre_input.setText(self.producto.get('nombre', ''))
        self.marca_input.setText(self.producto.get('marca', ''))
        self.modelo_input.setText(self.producto.get('modelo', ''))
        self.descripcion_input.setText(self.producto.get('descripcion', ''))

    def guardar(self):
        nombre = self.nombre_input.text().strip()
        marca = self.marca_input.text().strip()
        modelo = self.modelo_input.text().strip()
        descripcion = self.descripcion_input.toPlainText().strip()

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre del producto es requerido")
            return

        if self.producto:
            # Actualizar producto existente
            query = """
                UPDATE producto 
                SET nombre=%s, marca=%s, modelo=%s, descripcion=%s 
                WHERE id_producto=%s
            """
            params = (nombre, marca, modelo, descripcion, self.producto['id_producto'])
            success = self.db.execute_query(query, params)
        else:
            # Insertar nuevo producto
            query = """
                INSERT INTO producto (nombre, marca, modelo, descripcion)
                VALUES (%s, %s, %s, %s)
            """
            params = (nombre, marca, modelo, descripcion)
            success = self.db.execute_query(query, params)

        if success:
            QMessageBox.information(self, "Éxito", "Producto guardado correctamente")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo guardar el producto")


class VentanaProductos(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseConnection()
        self.init_ui()
        self.cargar_productos()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QHBoxLayout()
        title = QLabel("Gestión de Productos")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("+ Nuevo Producto")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5C800;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E5B800;
            }
        """)
        add_btn.clicked.connect(self.agregar_producto)
        header.addWidget(add_btn)

        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Marca", "Modelo", "Descripción", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
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
                border: none;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def cargar_productos(self):
        query = "SELECT id_producto, nombre, marca, modelo, descripcion FROM producto ORDER BY id_producto"
        productos = self.db.fetch_all(query)

        self.table.setRowCount(len(productos))

        for row_idx, producto in enumerate(productos):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(producto['id_producto'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(producto['nombre']))
            self.table.setItem(row_idx, 2, QTableWidgetItem(producto.get('marca') or ''))
            self.table.setItem(row_idx, 3, QTableWidgetItem(producto.get('modelo') or ''))
            self.table.setItem(row_idx, 4, QTableWidgetItem(producto.get('descripcion') or ''))

            acciones_widget = QWidget()
            acciones_layout = QHBoxLayout()
            acciones_layout.setContentsMargins(4, 4, 4, 4)
            acciones_layout.setSpacing(5)

            edit_btn = QPushButton("Editar")
            edit_btn.setStyleSheet("""
                QPushButton {
                    padding: 5px 12px;
                    background-color: #3B82F6;
                    color: white;
                    border-radius: 4px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
            """)
            edit_btn.clicked.connect(lambda checked, p=producto.copy(): self.editar_producto(p))
            acciones_layout.addWidget(edit_btn)

            delete_btn = QPushButton("Eliminar")
            delete_btn.setStyleSheet("""
                QPushButton {
                    padding: 5px 12px;
                    background-color: #EF4444;
                    color: white;
                    border-radius: 4px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                }
            """)
            delete_btn.clicked.connect(lambda checked, p=producto.copy(): self.eliminar_producto(p))
            acciones_layout.addWidget(delete_btn)

            acciones_widget.setLayout(acciones_layout)
            self.table.setCellWidget(row_idx, 5, acciones_widget)

        self.table.resizeRowsToContents()

    def agregar_producto(self):
        dialog = DialogoProducto(self)
        if dialog.exec_():
            self.cargar_productos()

    def editar_producto(self, producto):
        dialog = DialogoProducto(producto, self)
        if dialog.exec_():
            self.cargar_productos()

    def eliminar_producto(self, producto):
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar el producto '{producto['nombre']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            query = "DELETE FROM producto WHERE id_producto = %s"
            if self.db.execute_query(query, (producto['id_producto'],)):
                QMessageBox.information(self, "Éxito", "Producto eliminado correctamente")
                self.cargar_productos()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el producto")