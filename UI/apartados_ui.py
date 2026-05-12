# UI/apartados_ui.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QComboBox, QDoubleSpinBox, QDateEdit, QMessageBox,
    QHeaderView, QInputDialog, QCheckBox, QGroupBox,
    QScrollArea
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor
import sys
import os
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.conexion import DatabaseConnection
from services.apartado_service import ApartadoService


class DialogoApartado(QDialog):
    """Diálogo para crear un nuevo apartado con todos los campos."""

    def __init__(self, service: ApartadoService, parent=None):
        super().__init__(parent)
        self.service = service
        self.db = service.db
        self.init_ui()
        self.cargar_clientes()
        self.cargar_productos()
        self.cargar_empresas()

    def init_ui(self):
        self.setWindowTitle("Nuevo Apartado")
        self.setFixedSize(550, 700)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Registro de Apartado")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(20)

        # Scroll area para campos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Cliente
        self.cliente_combo = QComboBox()
        self.cliente_combo.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Cliente:", self.cliente_combo)

        # Producto
        self.producto_combo = QComboBox()
        self.producto_combo.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Producto:", self.producto_combo)

        # Precio del producto
        self.lbl_precio = QLabel("Q 0.00")
        self.lbl_precio.setStyleSheet("color: #10B981; font-weight: bold;")
        form_layout.addRow("Precio producto:", self.lbl_precio)
        
        self.producto_combo.currentIndexChanged.connect(self.actualizar_precio)

        # Monto original
        self.monto_original = QDoubleSpinBox()
        self.monto_original.setMinimum(0)
        self.monto_original.setMaximum(999999)
        self.monto_original.setPrefix("Q ")
        self.monto_original.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Precio original:", self.monto_original)

        # Descuento (cantidad en quetzales)
        self.descuento_input = QDoubleSpinBox()
        self.descuento_input.setMinimum(0)
        self.descuento_input.setMaximum(999999)
        self.descuento_input.setPrefix("Q ")
        self.descuento_input.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        self.descuento_input.valueChanged.connect(self.calcular_total_con_descuento)
        form_layout.addRow("Descuento (Q):", self.descuento_input)

        # Total a pagar (se calcula automáticamente)
        self.total_producto = QDoubleSpinBox()
        self.total_producto.setMinimum(0)
        self.total_producto.setMaximum(999999)
        self.total_producto.setPrefix("Q ")
        self.total_producto.setReadOnly(True)
        self.total_producto.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB; background-color: #F3F4F6;")
        form_layout.addRow("Total a pagar:", self.total_producto)

        # Fecha inicio
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(QDate.currentDate())
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Fecha Inicio:", self.fecha_inicio)

        # Es envío?
        self.check_envio = QCheckBox("Este apartado es por envío")
        self.check_envio.toggled.connect(self.toggle_envio)
        form_layout.addRow("", self.check_envio)

        # Empresa de envío
        self.empresa_combo = QComboBox()
        self.empresa_combo.setEnabled(False)
        self.empresa_combo.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Empresa envío:", self.empresa_combo)

        scroll_layout.addLayout(form_layout)
        scroll_area.setWidget(scroll_widget)
        
        layout.addWidget(scroll_area)
        layout.addSpacing(20)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet("padding: 10px; background-color: #F3F4F6; border-radius: 8px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Guardar Apartado")
        save_btn.setStyleSheet("padding: 10px; background-color: #F5C800; border-radius: 8px; font-weight: bold;")
        save_btn.clicked.connect(self.guardar)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def actualizar_precio(self):
        """Actualiza el precio del producto seleccionado."""
        producto_data = self.producto_combo.currentData()
        if producto_data and isinstance(producto_data, dict):
            precio = float(producto_data.get('precio_costo', 0))
            if precio:
                self.lbl_precio.setText(f"Q {precio:.2f}")
                self.monto_original.setValue(precio)
                self.calcular_total_con_descuento()

    def calcular_total_con_descuento(self):
        """Calcula el total a pagar aplicando el descuento."""
        original = self.monto_original.value()
        descuento = self.descuento_input.value()
        total = max(original - descuento, 0)
        self.total_producto.setValue(total)

    def toggle_envio(self, checked):
        """Habilita/deshabilita campos de envío."""
        self.empresa_combo.setEnabled(checked)

    def cargar_clientes(self):
        query = "SELECT id_cliente, nombre, apellido FROM cliente ORDER BY nombre"
        clientes = self.db.fetch_all(query)
        self.cliente_combo.clear()
        for cliente in clientes:
            nombre = f"{cliente['nombre']} {cliente['apellido']}" if cliente['apellido'] else cliente['nombre']
            self.cliente_combo.addItem(nombre, cliente['id_cliente'])

    def cargar_productos(self):
        query = "SELECT id_producto, nombre, marca, modelo, precio_costo FROM producto ORDER BY nombre"
        productos = self.db.fetch_all(query)
        self.producto_combo.clear()
        for producto in productos:
            texto = f"{producto['nombre']}"
            if producto.get('marca'):
                texto += f" - {producto['marca']}"
            if producto.get('modelo'):
                texto += f" ({producto['modelo']})"
            self.producto_combo.addItem(texto, producto)

    def cargar_empresas(self):
        query = "SELECT id_empresa, nombre FROM empresa_envio ORDER BY nombre"
        empresas = self.db.fetch_all(query)
        self.empresa_combo.clear()
        self.empresa_combo.addItem("Seleccionar empresa", None)
        for empresa in empresas:
            self.empresa_combo.addItem(empresa['nombre'], empresa['id_empresa'])

    def guardar(self):
        cliente_id = self.cliente_combo.currentData()
        producto_data = self.producto_combo.currentData()
        
        if not producto_data or not isinstance(producto_data, dict):
            QMessageBox.warning(self, "Error", "Seleccione un producto válido")
            return
            
        producto_id = producto_data['id_producto']
        
        total = self.total_producto.value()
        monto_original = self.monto_original.value()
        descuento = self.descuento_input.value()
        fecha = self.fecha_inicio.date().toPyDate()
        es_envio = self.check_envio.isChecked()
        id_empresa = self.empresa_combo.currentData() if es_envio else None

        if not cliente_id:
            QMessageBox.warning(self, "Error", "Seleccione un cliente")
            return

        if total <= 0:
            QMessageBox.warning(self, "Error", "El total debe ser mayor a 0")
            return

        data = {
            'id_cliente_fk': cliente_id,
            'id_producto_fk': producto_id,
            'total_producto': total,
            'monto_original': monto_original,
            'descuento_pactado': descuento,
            'monto_final': total,
            'fecha_inicio': fecha,
            'es_envio': es_envio,
            'id_empresa_fk': id_empresa
        }

        id_apartado = self.service.crear_apartado(data)
        if id_apartado:
            QMessageBox.information(self, "Éxito", f"Apartado #{id_apartado} registrado correctamente")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar el apartado")


class VentanaApartados(QWidget):
    """Ventana principal de gestión de apartados - SOLO MUESTRA PENDIENTES."""

    def __init__(self, id_usuario_actual: int, id_caja_actual: int = None):
        super().__init__()
        self.db = DatabaseConnection()
        self.apartado_service = ApartadoService(self.db)
        self.id_usuario_actual = id_usuario_actual
        self.id_caja_actual = id_caja_actual
        self.init_ui()
        self.cargar_apartados()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QHBoxLayout()
        title = QLabel("Apartados Pendientes")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.addWidget(title)
        header.addStretch()

        # Indicador de estado de caja
        self.caja_status_label = QLabel()
        self.actualizar_estado_caja()
        header.addWidget(self.caja_status_label)

        add_btn = QPushButton("+ Nuevo Apartado")
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
        add_btn.clicked.connect(self.agregar_apartado)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Tabla de apartados pendientes
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Cliente", "Producto", "Total", 
            "Pagado", "Saldo", "% Pagado", "Acciones"
        ])
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
                border: none;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def actualizar_estado_caja(self):
        """Actualiza el indicador visual del estado de la caja."""
        estado = self.apartado_service.obtener_estado_caja()
        if estado['abierta']:
            self.caja_status_label.setText("✅ Caja Abierta")
            self.caja_status_label.setStyleSheet("color: #10B981; font-weight: bold; padding: 5px 10px; background-color: #D1FAE5; border-radius: 15px;")
            if not self.id_caja_actual:
                self.id_caja_actual = estado['id_caja']
        else:
            self.caja_status_label.setText("❌ Caja Cerrada")
            self.caja_status_label.setStyleSheet("color: #EF4444; font-weight: bold; padding: 5px 10px; background-color: #FEE2E2; border-radius: 15px;")

    def cargar_apartados(self):
        """Carga SOLO los apartados con saldo pendiente."""
        apartados = self.apartado_service.obtener_apartados_pendientes()

        self.table.setRowCount(len(apartados))

        for row, apartado in enumerate(apartados):
            self.table.setRowHeight(row, 50)
            
            # Cliente
            cliente = f"{apartado['cliente_nombre']} {apartado['cliente_apellido']}" if apartado['cliente_apellido'] else apartado['cliente_nombre']
            self.table.setItem(row, 0, QTableWidgetItem(cliente))

            # Producto
            producto = apartado['producto_nombre']
            if apartado['marca']:
                producto += f" - {apartado['marca']}"
            self.table.setItem(row, 1, QTableWidgetItem(producto))

            # Total - Convertir Decimal a float
            total = float(apartado['total_producto']) if apartado['total_producto'] else 0
            total_item = QTableWidgetItem(f"Q{total:.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, total_item)

            # Pagado - Convertir Decimal a float
            pagado = float(apartado['total_pagado']) if apartado['total_pagado'] else 0
            pagado_item = QTableWidgetItem(f"Q{pagado:.2f}")
            pagado_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            pagado_item.setForeground(QColor("#059669"))
            self.table.setItem(row, 3, pagado_item)

            # Saldo pendiente - Convertir Decimal a float
            saldo = float(apartado['saldo_pendiente']) if apartado['saldo_pendiente'] else 0
            saldo_item = QTableWidgetItem(f"Q{saldo:.2f}")
            saldo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if saldo > 0:
                saldo_item.setForeground(QColor("#DC2626"))
                saldo_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table.setItem(row, 4, saldo_item)

            # Porcentaje pagado - Convertir Decimal a float
            porcentaje = float(apartado['porcentaje_pagado']) if apartado['porcentaje_pagado'] else 0
            porcentaje_item = QTableWidgetItem(f"{porcentaje:.1f}%")
            porcentaje_item.setTextAlignment(Qt.AlignCenter)
            if porcentaje >= 75:
                porcentaje_item.setForeground(QColor("#059669"))
            elif porcentaje >= 50:
                porcentaje_item.setForeground(QColor("#F59E0B"))
            else:
                porcentaje_item.setForeground(QColor("#DC2626"))
            self.table.setItem(row, 5, porcentaje_item)

            # Acciones
            acciones_widget = QWidget()
            acciones_layout = QHBoxLayout()
            acciones_layout.setContentsMargins(4, 4, 4, 4)
            acciones_layout.setSpacing(5)

            if saldo > 0 and self.id_caja_actual:
                pago_btn = QPushButton("💰 Pagar")
                pago_btn.setStyleSheet("padding: 5px 10px; background-color: #F5C800; border-radius: 5px; font-weight: bold;")
                # Pasar los valores ya convertidos a float
                apartado_con_floats = {
                    'id_apartado': apartado['id_apartado'],
                    'cliente_nombre': apartado['cliente_nombre'],
                    'cliente_apellido': apartado['cliente_apellido'],
                    'producto_nombre': apartado['producto_nombre'],
                    'total_producto': total,
                    'total_pagado': pagado,
                    'saldo_pendiente': saldo
                }
                pago_btn.clicked.connect(lambda checked, a=apartado_con_floats: self.registrar_pago(a))
                acciones_layout.addWidget(pago_btn)

            detalle_btn = QPushButton("📋 Ver")
            detalle_btn.setStyleSheet("padding: 5px 10px; background-color: #3B82F6; color: white; border-radius: 5px;")
            detalle_btn.clicked.connect(lambda checked, a=apartado: self.ver_detalle(a))
            acciones_layout.addWidget(detalle_btn)

            cancel_btn = QPushButton("❌ Cancelar")
            cancel_btn.setStyleSheet("padding: 5px 10px; background-color: #FEE2E2; color: #EF4444; border-radius: 5px;")
            cancel_btn.clicked.connect(lambda checked, a=apartado: self.cancelar_apartado(a))
            acciones_layout.addWidget(cancel_btn)

            acciones_widget.setLayout(acciones_layout)
            self.table.setCellWidget(row, 6, acciones_widget)

        self.table.resizeRowsToContents()

    def agregar_apartado(self):
        """Abre el diálogo para crear un nuevo apartado."""
        dialog = DialogoApartado(self.apartado_service, self)
        if dialog.exec_():
            self.cargar_apartados()

    def registrar_pago(self, apartado: dict):
        """Registra un pago/abono para un apartado."""
        if not self.id_caja_actual:
            QMessageBox.warning(self, "Caja Cerrada", "Debe abrir la caja antes de registrar un pago.")
            return

        # Ya tenemos los valores como float
        saldo_pendiente = apartado['saldo_pendiente']
        total_producto = apartado['total_producto']
        total_pagado = apartado['total_pagado']

        monto, ok = QInputDialog.getDouble(
            self,
            "Registrar Pago",
            f"📋 APARTADO #{apartado['id_apartado']}\n\n"
            f"Cliente: {apartado['cliente_nombre']} {apartado['cliente_apellido']}\n"
            f"Producto: {apartado['producto_nombre']}\n"
            f"Total del producto: Q{total_producto:.2f}\n"
            f"Pagado hasta ahora: Q{total_pagado:.2f}\n"
            f"Saldo pendiente: Q{saldo_pendiente:.2f}\n\n"
            f"💰 Monto a pagar:",
            0, 0, saldo_pendiente, 2
        )

        if not ok or monto <= 0:
            return

        confirmar = QMessageBox.question(
            self,
            "Confirmar Pago",
            f"¿Registrar pago de Q{monto:.2f} para el apartado #{apartado['id_apartado']}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmar != QMessageBox.Yes:
            return

        exito = self.apartado_service.registrar_abono(
            apartado['id_apartado'],
            monto,
            self.id_caja_actual,
            self.id_usuario_actual
        )

        if exito:
            nuevo_total_pagado = total_pagado + monto
            if nuevo_total_pagado >= total_producto:
                QMessageBox.information(self, "✅ Apartado Completado", f"¡El apartado #{apartado['id_apartado']} ha sido pagado en su totalidad!")
            else:
                QMessageBox.information(self, "Pago Registrado", f"Se ha registrado un pago de Q{monto:.2f}.\nSaldo restante: Q{total_producto - nuevo_total_pagado:.2f}")
            self.cargar_apartados()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar el pago.")

    def ver_detalle(self, apartado: dict):
        """Muestra el detalle completo del apartado y su historial de pagos."""
        detalle = self.apartado_service.obtener_detalle_apartado(apartado['id_apartado'])
        historial = self.apartado_service.obtener_historial_pagos(apartado['id_apartado'])
        
        if not detalle:
            QMessageBox.warning(self, "Error", "No se pudo obtener el detalle del apartado")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Detalle Apartado #{apartado['id_apartado']}")
        dialog.setMinimumSize(650, 550)
        dialog.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Información del apartado
        info_group = QGroupBox("Información del Apartado")
        info_layout = QFormLayout()
        info_layout.setSpacing(10)
        
        # Convertir Decimal a float para mostrar
        total_producto = float(detalle['total_producto']) if detalle['total_producto'] else 0
        monto_original = float(detalle.get('monto_original', 0)) if detalle.get('monto_original') else 0
        descuento = float(detalle.get('descuento_pactado', 0)) if detalle.get('descuento_pactado') else 0
        total_pagado = float(detalle['total_pagado']) if detalle['total_pagado'] else 0
        saldo = total_producto - total_pagado
        
        info_layout.addRow("Cliente:", QLabel(f"{detalle['cliente_nombre']} {detalle['cliente_apellido'] or ''}"))
        info_layout.addRow("Teléfono:", QLabel(detalle.get('cliente_telefono') or 'N/A'))
        info_layout.addRow("Producto:", QLabel(f"{detalle['producto_nombre']} {detalle.get('marca', '')} {detalle.get('modelo', '')}"))
        info_layout.addRow("Precio original:", QLabel(f"Q{monto_original:.2f}"))
        info_layout.addRow("Descuento aplicado:", QLabel(f"Q{descuento:.2f}"))
        info_layout.addRow("Total a pagar:", QLabel(f"Q{total_producto:.2f}"))
        info_layout.addRow("Pagado:", QLabel(f"Q{total_pagado:.2f}"))
        info_layout.addRow("Saldo:", QLabel(f"Q{saldo:.2f}"))
        info_layout.addRow("Fecha Inicio:", QLabel(str(detalle['fecha_inicio'])))
        info_layout.addRow("Estado:", QLabel(detalle['estado']))
        info_layout.addRow("Es Envío:", QLabel("Sí" if detalle.get('es_envio') else "No"))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Historial de pagos
        if historial:
            history_group = QGroupBox(f"Historial de Pagos ({len(historial)} pagos)")
            history_layout = QVBoxLayout()
            
            history_table = QTableWidget()
            history_table.setColumnCount(4)
            history_table.setHorizontalHeaderLabels(["Fecha", "Monto", "Usuario", "Descripción"])
            history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            history_table.setRowCount(len(historial))
            
            for i, pago in enumerate(historial):
                history_table.setItem(i, 0, QTableWidgetItem(str(pago['fecha_pago'])))
                monto_pago = float(pago['monto']) if pago['monto'] else 0
                monto_item = QTableWidgetItem(f"Q{monto_pago:.2f}")
                monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                history_table.setItem(i, 1, monto_item)
                history_table.setItem(i, 2, QTableWidgetItem(pago.get('usuario_nombre', 'N/A')))
                history_table.setItem(i, 3, QTableWidgetItem(pago.get('descripcion', 'Abono a apartado')[:50]))
            
            history_layout.addWidget(history_table)
            history_group.setLayout(history_layout)
            layout.addWidget(history_group)
        else:
            layout.addWidget(QLabel("📭 No hay pagos registrados aún"))
        
        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.setStyleSheet("padding: 10px; background-color: #F5C800; border-radius: 8px; font-weight: bold;")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def cancelar_apartado(self, apartado: dict):
        """Cancela un apartado y registra la devolución correspondiente."""
        if not self.id_caja_actual:
            QMessageBox.warning(self, "Caja Cerrada", "Debe abrir la caja para procesar una cancelación/devolución.")
            return

        total_pagado = float(apartado['total_pagado']) if apartado['total_pagado'] else 0
        mensaje = f"⚠️ ¿Está seguro de CANCELAR el apartado #{apartado['id_apartado']}?\n\n"
        
        if total_pagado > 0:
            mensaje += f"💰 El cliente ha pagado Q{total_pagado:.2f}.\n"
            mensaje += f"🔄 Este monto será DEVUELTO y registrado como GASTO.\n\n"
            mensaje += f"¿Desea continuar con la cancelación?"
        else:
            mensaje += "❌ El cliente no ha realizado ningún pago.\n"
            mensaje += f"📝 Solo se cancelará el apartado.\n\n"
            mensaje += f"¿Desea continuar?"

        reply = QMessageBox.question(
            self,
            "Confirmar Cancelación",
            mensaje,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            exito = self.apartado_service.cancelar_apartado(
                apartado['id_apartado'],
                total_pagado,
                self.id_caja_actual,
                self.id_usuario_actual
            )

            if exito:
                QMessageBox.information(self, "Apartado Cancelado", f"✅ El apartado #{apartado['id_apartado']} ha sido cancelado.")
                self.cargar_apartados()
            else:
                QMessageBox.critical(self, "Error", "❌ No se pudo cancelar el apartado.")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    ventana = VentanaApartados(id_usuario_actual=1, id_caja_actual=1)
    ventana.resize(1300, 650)
    ventana.show()
    sys.exit(app.exec_())