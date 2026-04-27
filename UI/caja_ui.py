# UI/caja_ui.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QGroupBox, QFormLayout, QLineEdit, QDoubleSpinBox,
                             QComboBox, QMessageBox, QHeaderView, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.conexion import DatabaseConnection


class VentanaCaja(QWidget):
    caja_abierta_signal = pyqtSignal(int)

    def __init__(self, usuario_data):
        super().__init__()
        self.usuario_data = usuario_data
        self.db = DatabaseConnection()
        self.id_caja_actual = None
        self.id_apertura_actual = None
        self.init_ui()
        self.verificar_estado_caja()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        header = QLabel("Control de Caja")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(header)

        self.estado_frame = QLabel()
        self.estado_frame.setStyleSheet("border-radius: 10px; padding: 15px; font-weight: bold;")
        layout.addWidget(self.estado_frame)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                background-color: white;
            }
            QTabBar::tab:selected {
                background-color: #F5C800;
                border-radius: 8px;
                padding: 10px 20px;
            }
        """)

        self.tabs.addTab(self.crear_tab_apertura(), "Apertura / Cierre")
        self.tabs.addTab(self.crear_tab_movimientos(), "Movimientos")
        self.tabs.addTab(self.crear_tab_historial(), "Historial")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def crear_tab_apertura(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        apertura_group = QGroupBox("Apertura de Caja")
        apertura_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 10px;
            }
        """)
        apertura_layout = QFormLayout()

        self.monto_inicial = QDoubleSpinBox()
        self.monto_inicial.setMinimum(0)
        self.monto_inicial.setMaximum(100000)
        self.monto_inicial.setPrefix("Q")
        self.monto_inicial.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        apertura_layout.addRow("Monto Inicial:", self.monto_inicial)

        self.apertura_btn = QPushButton("Abrir Caja")
        self.apertura_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        self.apertura_btn.clicked.connect(self.abrir_caja)
        apertura_layout.addRow(self.apertura_btn)

        apertura_group.setLayout(apertura_layout)
        layout.addWidget(apertura_group)

        cierre_group = QGroupBox("Cierre de Caja")
        cierre_group.setStyleSheet(apertura_group.styleSheet())
        cierre_layout = QFormLayout()

        self.monto_final = QDoubleSpinBox()
        self.monto_final.setMinimum(0)
        self.monto_final.setMaximum(1000000)
        self.monto_final.setPrefix("Q")
        self.monto_final.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        cierre_layout.addRow("Monto Final:", self.monto_final)

        self.cierre_btn = QPushButton("Cerrar Caja")
        self.cierre_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        self.cierre_btn.clicked.connect(self.cerrar_caja)
        cierre_layout.addRow(self.cierre_btn)

        cierre_group.setLayout(cierre_layout)
        layout.addWidget(cierre_group)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def crear_tab_movimientos(self):
        tab = QWidget()
        layout = QVBoxLayout()

        form_group = QGroupBox("Registrar Movimiento")
        form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 10px;
            }
        """)
        form_layout = QFormLayout()

        self.tipo_movimiento = QComboBox()
        self.tipo_movimiento.addItems(["INGRESO", "EGRESO"])
        self.tipo_movimiento.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Tipo:", self.tipo_movimiento)

        self.descripcion_mov = QLineEdit()
        self.descripcion_mov.setPlaceholderText("Descripcion del movimiento")
        self.descripcion_mov.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Descripcion:", self.descripcion_mov)

        self.monto_mov = QDoubleSpinBox()
        self.monto_mov.setMinimum(0)
        self.monto_mov.setMaximum(100000)
        self.monto_mov.setPrefix("Q")
        self.monto_mov.setStyleSheet("padding: 8px; border-radius: 6px; border: 1px solid #E5E7EB;")
        form_layout.addRow("Monto:", self.monto_mov)

        registrar_btn = QPushButton("Registrar Movimiento")
        registrar_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5C800;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        registrar_btn.clicked.connect(self.registrar_movimiento)
        form_layout.addRow(registrar_btn)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        layout.addSpacing(20)

        self.movimientos_table = QTableWidget()
        self.movimientos_table.setColumnCount(5)
        self.movimientos_table.setHorizontalHeaderLabels(["Fecha", "Tipo", "Descripcion", "Monto", "Usuario"])
        self.movimientos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.movimientos_table)

        tab.setLayout(layout)
        return tab

    def crear_tab_historial(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.historial_table = QTableWidget()
        self.historial_table.setColumnCount(6)
        self.historial_table.setHorizontalHeaderLabels(["Fecha Apertura", "Fecha Cierre", "Usuario", "Monto Inicial", "Monto Final", "Diferencia"])
        self.historial_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.historial_table)

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.setStyleSheet("padding: 8px; max-width: 120px; background-color: #F3F4F6; border-radius: 8px;")
        refresh_btn.clicked.connect(self.cargar_historial)
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)

        tab.setLayout(layout)
        return tab

    def verificar_estado_caja(self):
        query = """
            SELECT ac.id_apertura, ac.id_caja_fk, ac.monto_inicial, ac.fecha_hora_apertura,
                   u.nombre as usuario_nombre
            FROM apertura_cierre ac
            JOIN usuario u ON ac.id_usuario_fk = u.id_usuario
            WHERE ac.fecha_hora_cierre IS NULL
            ORDER BY ac.fecha_hora_apertura DESC
            LIMIT 1
        """
        resultado = self.db.fetch_one(query)

        if resultado:
            self.id_apertura_actual = resultado['id_apertura']
            self.id_caja_actual = resultado['id_caja_fk']
            self.caja_abierta_signal.emit(self.id_caja_actual)
            self.estado_frame.setText(f"CAJA ABIERTA - Apertura: {resultado['fecha_hora_apertura']} | Usuario: {resultado['usuario_nombre']} | Monto: Q{resultado['monto_inicial']:.2f}")
            self.estado_frame.setStyleSheet("background-color: #D1FAE5; color: #059669; border-radius: 10px; padding: 15px;")
            self.apertura_btn.setEnabled(False)
            self.cierre_btn.setEnabled(True)
            self.cargar_movimientos()
        else:
            self.id_apertura_actual = None
            self.id_caja_actual = None
            self.caja_abierta_signal.emit(0)
            self.estado_frame.setText("CAJA CERRADA - Realice la apertura para comenzar")
            self.estado_frame.setStyleSheet("background-color: #FEE2E2; color: #DC2626; border-radius: 10px; padding: 15px;")
            self.apertura_btn.setEnabled(True)
            self.cierre_btn.setEnabled(False)

        self.cargar_historial()

    def abrir_caja(self):
        monto = self.monto_inicial.value()

        if monto <= 0:
            QMessageBox.warning(self, "Error", "Ingrese un monto inicial valido")
            return

        caja_query = "INSERT INTO caja (fecha) VALUES (CURRENT_DATE) RETURNING id_caja"
        caja_result = self.db.fetch_one(caja_query)

        if not caja_result:
            QMessageBox.critical(self, "Error", "No se pudo crear registro de caja")
            return

        id_caja = caja_result['id_caja']

        apertura_query = """
            INSERT INTO apertura_cierre (id_caja_fk, id_usuario_fk, fecha_hora_apertura, monto_inicial)
            VALUES (%s, %s, NOW(), %s) RETURNING id_apertura
        """
        apertura_result = self.db.fetch_one(apertura_query, (id_caja, self.usuario_data['id_usuario'], monto))

        if apertura_result:
            self.id_apertura_actual = apertura_result['id_apertura']
            self.id_caja_actual = id_caja
            self.caja_abierta_signal.emit(id_caja)
            QMessageBox.information(self, "Exito", f"Caja abierta con Q{monto:.2f}")
            self.verificar_estado_caja()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar la apertura")

    def cerrar_caja(self):
        monto_final = self.monto_final.value()

        if monto_final < 0:
            QMessageBox.warning(self, "Error", "Ingrese un monto final valido")
            return

        reply = QMessageBox.question(self, "Confirmar", "Cerrar caja?", QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            query = """
                UPDATE apertura_cierre 
                SET fecha_hora_cierre = NOW(), monto_final = %s
                WHERE id_apertura = %s
            """
            if self.db.execute_query(query, (monto_final, self.id_apertura_actual)):
                self.id_caja_actual = None
                self.caja_abierta_signal.emit(0)
                QMessageBox.information(self, "Exito", "Caja cerrada")
                self.verificar_estado_caja()
            else:
                QMessageBox.critical(self, "Error", "No se pudo cerrar la caja")

    def registrar_movimiento(self):
        if not self.id_apertura_actual:
            QMessageBox.warning(self, "Error", "Debe abrir la caja primero")
            return

        tipo = self.tipo_movimiento.currentText()
        descripcion = self.descripcion_mov.text().strip()
        monto = self.monto_mov.value()

        if not descripcion:
            QMessageBox.warning(self, "Error", "Ingrese una descripcion")
            return

        if monto <= 0:
            QMessageBox.warning(self, "Error", "Ingrese un monto valido")
            return

        query = """
            INSERT INTO movimiento_caja (id_caja_fk, tipo_movimiento, descripcion, monto, fecha_hora)
            VALUES (%s, %s, %s, %s, NOW())
        """
        if self.db.execute_query(query, (self.id_caja_actual, tipo, descripcion, monto)):
            QMessageBox.information(self, "Exito", "Movimiento registrado")
            self.descripcion_mov.clear()
            self.monto_mov.setValue(0)
            self.cargar_movimientos()
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar")

    def cargar_movimientos(self):
        if not self.id_apertura_actual:
            return

        query = """
            SELECT mc.fecha_hora, mc.tipo_movimiento, mc.descripcion, mc.monto, u.nombre
            FROM movimiento_caja mc
            JOIN apertura_cierre ac ON mc.id_caja_fk = ac.id_caja_fk
            JOIN usuario u ON ac.id_usuario_fk = u.id_usuario
            WHERE ac.id_apertura = %s
            ORDER BY mc.fecha_hora DESC
        """
        movimientos = self.db.fetch_all(query, (self.id_apertura_actual,))

        self.movimientos_table.setRowCount(len(movimientos))

        for i, m in enumerate(movimientos):
            self.movimientos_table.setItem(i, 0, QTableWidgetItem(str(m['fecha_hora'])[:19]))
            self.movimientos_table.setItem(i, 1, QTableWidgetItem(m['tipo_movimiento']))
            self.movimientos_table.setItem(i, 2, QTableWidgetItem(m['descripcion']))
            self.movimientos_table.setItem(i, 3, QTableWidgetItem(f"Q{m['monto']:.2f}"))
            self.movimientos_table.setItem(i, 4, QTableWidgetItem(m['nombre']))

    def cargar_historial(self):
        query = """
            SELECT ac.fecha_hora_apertura, ac.fecha_hora_cierre, 
                   u.nombre, ac.monto_inicial, ac.monto_final
            FROM apertura_cierre ac
            JOIN usuario u ON ac.id_usuario_fk = u.id_usuario
            WHERE ac.fecha_hora_cierre IS NOT NULL
            ORDER BY ac.fecha_hora_apertura DESC
        """
        historial = self.db.fetch_all(query)

        self.historial_table.setRowCount(len(historial))

        for i, h in enumerate(historial):
            self.historial_table.setItem(i, 0, QTableWidgetItem(str(h['fecha_hora_apertura'])[:19]))
            cierre = str(h['fecha_hora_cierre'])[:19] if h['fecha_hora_cierre'] else "-"
            self.historial_table.setItem(i, 1, QTableWidgetItem(cierre))
            self.historial_table.setItem(i, 2, QTableWidgetItem(h['nombre']))
            self.historial_table.setItem(i, 3, QTableWidgetItem(f"Q{h['monto_inicial']:.2f}"))
            final = f"Q{h['monto_final']:.2f}" if h['monto_final'] else "-"
            self.historial_table.setItem(i, 4, QTableWidgetItem(final))
            diferencia = (h['monto_final'] - h['monto_inicial']) if h['monto_final'] else 0
            self.historial_table.setItem(i, 5, QTableWidgetItem(f"Q{diferencia:.2f}"))