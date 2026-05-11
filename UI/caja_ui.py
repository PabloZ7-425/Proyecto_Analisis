# UI/caja_ui.py

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QDoubleSpinBox,
    QComboBox,
    QMessageBox,
    QHeaderView,
    QTabWidget,
    QGridLayout
)

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIntValidator

import sys
import os

# =========================================================
# RUTAS
# =========================================================
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

# =========================================================
# IMPORTS
# =========================================================
from database.conexion import DatabaseConnection
from services.gasto_service import GastoService


# =========================================================
# VENTANA CAJA
# =========================================================
class VentanaCaja(QWidget):

    caja_abierta_signal = pyqtSignal(int)

    def __init__(self, usuario_data):

        super().__init__()

        self.usuario_data = usuario_data

        self.db = DatabaseConnection()

        # =================================================
        # SERVICE GASTOS
        # =================================================
        self.gasto_service = GastoService(self.db)

        self.id_caja_actual = None
        self.id_apertura_actual = None

        # =================================================
        # DENOMINACIONES
        # =================================================
        self.denominaciones = [200, 100, 50, 20, 10, 5, 1]

        self.inputs_efectivo = {}

        self.init_ui()

        self.verificar_estado_caja()

    # =====================================================
    # UI
    # =====================================================
    def init_ui(self):

        layout = QVBoxLayout()

        layout.setSpacing(20)

        # =================================================
        # HEADER
        # =================================================
        header = QLabel("Control de Caja")

        header.setFont(
            QFont("Segoe UI", 18, QFont.Bold)
        )

        layout.addWidget(header)

        # =================================================
        # ESTADO
        # =================================================
        self.estado_frame = QLabel()

        self.estado_frame.setStyleSheet("""
            border-radius: 10px;
            padding: 15px;
            font-weight: bold;
        """)

        layout.addWidget(self.estado_frame)

        # =================================================
        # TABS
        # =================================================
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
                font-weight: bold;
            }
        """)

        self.tabs.addTab(
            self.crear_tab_apertura(),
            "Apertura / Cierre"
        )

        self.tabs.addTab(
            self.crear_tab_movimientos(),
            "Movimientos"
        )

        self.tabs.addTab(
            self.crear_tab_historial(),
            "Historial"
        )

        layout.addWidget(self.tabs)

        self.setLayout(layout)

    # =====================================================
    # TAB APERTURA
    # =====================================================
    def crear_tab_apertura(self):

        tab = QWidget()

        layout_principal = QHBoxLayout()

        layout_principal.setSpacing(25)

        layout_principal.setContentsMargins(
            15,
            15,
            15,
            15
        )

        # =================================================
        # DESGLOSE EFECTIVO
        # =================================================
        grupo_desglose = QGroupBox(
            "Conteo para Apertura"
        )

        grupo_desglose.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 15px;
            }
        """)

        ly_desglose = QVBoxLayout()

        grid = QGridLayout()

        validador = QIntValidator(0, 9999)

        for i, den in enumerate(self.denominaciones):

            lbl = QLabel(f"Q {den}.00")

            lbl.setFixedWidth(60)

            h_controles = QHBoxLayout()

            btn_menos = QPushButton("-")

            btn_menos.setFixedSize(30, 30)

            btn_menos.clicked.connect(
                lambda ch, d=den:
                self.ajustar_conteo(d, -1)
            )

            edit = QLineEdit("0")

            edit.setFixedWidth(55)

            edit.setFixedHeight(30)

            edit.setAlignment(Qt.AlignCenter)

            edit.setValidator(validador)

            edit.textChanged.connect(
                self.actualizar_monto_inicial_desde_conteo
            )

            self.inputs_efectivo[den] = edit

            btn_mas = QPushButton("+")

            btn_mas.setFixedSize(30, 30)

            btn_mas.clicked.connect(
                lambda ch, d=den:
                self.ajustar_conteo(d, 1)
            )

            h_controles.addWidget(btn_menos)

            h_controles.addWidget(edit)

            h_controles.addWidget(btn_mas)

            grid.addWidget(lbl, i, 0)

            grid.addLayout(h_controles, i, 1)

        ly_desglose.addLayout(grid)

        self.lbl_total_conteo = QLabel(
            "TOTAL CONTEO: Q 0.00"
        )

        self.lbl_total_conteo.setStyleSheet("""
            font-size: 14px;
            font-weight: 800;
            color: #111827;
            margin-top: 10px;
            border-top: 1px solid #EEE;
            padding-top: 10px;
        """)

        ly_desglose.addWidget(
            self.lbl_total_conteo,
            alignment=Qt.AlignRight
        )

        grupo_desglose.setLayout(ly_desglose)

        # =================================================
        # DERECHO
        # =================================================
        ly_derecho = QVBoxLayout()

        ly_derecho.setSpacing(15)

        # =================================================
        # APERTURA
        # =================================================
        apertura_group = QGroupBox(
            "Apertura de Caja"
        )

        apertura_group.setStyleSheet(
            grupo_desglose.styleSheet()
        )

        apertura_layout = QFormLayout()

        self.monto_inicial = QDoubleSpinBox()

        self.monto_inicial.setMinimum(0)

        self.monto_inicial.setMaximum(100000)

        self.monto_inicial.setPrefix("Q")

        self.monto_inicial.setFixedHeight(35)

        apertura_layout.addRow(
            "Monto Inicial:",
            self.monto_inicial
        )

        self.apertura_btn = QPushButton(
            "Abrir Caja"
        )

        self.apertura_btn.setStyleSheet("""
            background-color: #10B981;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-weight: bold;
        """)

        self.apertura_btn.clicked.connect(
            self.abrir_caja
        )

        apertura_layout.addRow(
            self.apertura_btn
        )

        apertura_group.setLayout(apertura_layout)

        # =================================================
        # CIERRE
        # =================================================
        cierre_group = QGroupBox(
            "Cierre de Caja"
        )

        cierre_group.setStyleSheet(
            grupo_desglose.styleSheet()
        )

        cierre_layout = QFormLayout()

        self.monto_final = QDoubleSpinBox()

        self.monto_final.setMinimum(0)

        self.monto_final.setMaximum(1000000)

        self.monto_final.setPrefix("Q")

        self.monto_final.setFixedHeight(35)

        cierre_layout.addRow(
            "Monto Final:",
            self.monto_final
        )

        self.cierre_btn = QPushButton(
            "Cerrar Caja"
        )

        self.cierre_btn.setStyleSheet("""
            background-color: #EF4444;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-weight: bold;
        """)

        self.cierre_btn.clicked.connect(
            self.cerrar_caja
        )

        cierre_layout.addRow(self.cierre_btn)

        cierre_group.setLayout(cierre_layout)

        ly_derecho.addWidget(apertura_group)

        ly_derecho.addWidget(cierre_group)

        ly_derecho.addStretch()

        layout_principal.addWidget(
            grupo_desglose,
            2
        )

        layout_principal.addLayout(
            ly_derecho,
            1
        )

        tab.setLayout(layout_principal)

        return tab

    # =====================================================
    # TAB MOVIMIENTOS
    # =====================================================
    def crear_tab_movimientos(self):

        tab = QWidget()

        layout = QVBoxLayout()

        form_group = QGroupBox(
            "Registrar Movimiento"
        )

        form_group.setStyleSheet("""
            font-weight: bold;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            margin-top: 12px;
            padding-top: 10px;
        """)

        form_layout = QFormLayout()

        # =================================================
        # TIPO MOVIMIENTO
        # =================================================
        self.tipo_movimiento = QComboBox()

        self.tipo_movimiento.addItems([
            "INGRESO",
            "EGRESO"
        ])

        form_layout.addRow(
            "Tipo:",
            self.tipo_movimiento
        )

        # =================================================
        # TIPO GASTO
        # =================================================
        self.tipo_gasto = QComboBox()

        self.tipo_gasto.addItems([
            "PROVEEDOR",
            "SUELDOS",
            "SERVICIOS",
            "INSUMOS",
            "DEVOLUCION",
            "OTRO"
        ])

        form_layout.addRow(
            "Tipo Gasto:",
            self.tipo_gasto
        )

        self.descripcion_mov = QLineEdit()

        self.descripcion_mov.setPlaceholderText(
            "Descripcion del movimiento"
        )

        form_layout.addRow(
            "Descripcion:",
            self.descripcion_mov
        )

        self.monto_mov = QDoubleSpinBox()

        self.monto_mov.setMinimum(0)

        self.monto_mov.setMaximum(100000)

        self.monto_mov.setPrefix("Q")

        form_layout.addRow(
            "Monto:",
            self.monto_mov
        )

        registrar_btn = QPushButton(
            "Registrar Movimiento"
        )

        registrar_btn.setStyleSheet("""
            background-color: #F5C800;
            border: none;
            border-radius: 8px;
            padding: 10px;
            font-weight: bold;
        """)

        registrar_btn.clicked.connect(
            self.registrar_movimiento
        )

        form_layout.addRow(registrar_btn)

        form_group.setLayout(form_layout)

        layout.addWidget(form_group)

        # =================================================
        # TABLA
        # =================================================
        self.movimientos_table = QTableWidget()

        self.movimientos_table.setColumnCount(5)

        self.movimientos_table.setHorizontalHeaderLabels([
            "Fecha",
            "Tipo",
            "Descripcion",
            "Monto",
            "Usuario"
        ])

        self.movimientos_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        layout.addWidget(self.movimientos_table)

        tab.setLayout(layout)

        return tab

    # =====================================================
    # TAB HISTORIAL
    # =====================================================
    def crear_tab_historial(self):

        tab = QWidget()

        layout = QVBoxLayout()

        self.historial_table = QTableWidget()

        self.historial_table.setColumnCount(6)

        self.historial_table.setHorizontalHeaderLabels([
            "Fecha Apertura",
            "Fecha Cierre",
            "Usuario",
            "Monto Inicial",
            "Monto Final",
            "Diferencia"
        ])

        self.historial_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        layout.addWidget(self.historial_table)

        refresh_btn = QPushButton("Actualizar")

        refresh_btn.clicked.connect(
            self.cargar_historial
        )

        layout.addWidget(
            refresh_btn,
            alignment=Qt.AlignRight
        )

        tab.setLayout(layout)

        return tab

    # =====================================================
    # AJUSTAR CONTEO
    # =====================================================
    def ajustar_conteo(self, den, delta):

        actual = int(
            self.inputs_efectivo[den].text() or 0
        )

        self.inputs_efectivo[den].setText(
            str(max(0, actual + delta))
        )

    # =====================================================
    # ACTUALIZAR MONTO
    # =====================================================
    def actualizar_monto_inicial_desde_conteo(self):

        total = sum(
            d * int(e.text() or 0)
            for d, e in self.inputs_efectivo.items()
        )

        self.lbl_total_conteo.setText(
            f"TOTAL CONTEO: Q {total:,.2f}"
        )

        self.monto_inicial.setValue(total)

    # =====================================================
    # VERIFICAR ESTADO
    # =====================================================
    def verificar_estado_caja(self):

        query = """
            SELECT
                ac.id_apertura,
                ac.id_caja_fk,
                ac.monto_inicial,
                ac.fecha_hora_apertura,
                u.nombre as usuario_nombre
            FROM apertura_cierre ac
            JOIN usuario u
                ON ac.id_usuario_fk = u.id_usuario
            WHERE ac.fecha_hora_cierre IS NULL
            ORDER BY ac.fecha_hora_apertura DESC
            LIMIT 1
        """

        resultado = self.db.fetch_one(query)

        if resultado:

            self.id_apertura_actual = resultado['id_apertura']

            self.id_caja_actual = resultado['id_caja_fk']

            self.caja_abierta_signal.emit(
                self.id_caja_actual
            )

            self.estado_frame.setText(
                f"CAJA ABIERTA - Usuario: "
                f"{resultado['usuario_nombre']} "
                f"| Monto: Q{resultado['monto_inicial']:.2f}"
            )

            self.estado_frame.setStyleSheet("""
                background-color: #D1FAE5;
                color: #059669;
                border-radius: 10px;
                padding: 15px;
            """)

            self.apertura_btn.setEnabled(False)

            self.cierre_btn.setEnabled(True)

            self.cargar_movimientos()

        else:

            self.id_apertura_actual = None

            self.id_caja_actual = None

            self.estado_frame.setText(
                "CAJA CERRADA"
            )

            self.estado_frame.setStyleSheet("""
                background-color: #FEE2E2;
                color: #DC2626;
                border-radius: 10px;
                padding: 15px;
            """)

            self.apertura_btn.setEnabled(True)

            self.cierre_btn.setEnabled(False)

        self.cargar_historial()

    # =====================================================
    # ABRIR CAJA
    # =====================================================
    def abrir_caja(self):

        monto = self.monto_inicial.value()

        if monto <= 0:

            QMessageBox.warning(
                self,
                "Error",
                "Ingrese un monto valido"
            )

            return

        caja_query = """
            INSERT INTO caja (fecha)
            VALUES (CURRENT_DATE)
            RETURNING id_caja
        """

        caja_result = self.db.fetch_one(caja_query)

        if not caja_result:

            QMessageBox.critical(
                self,
                "Error",
                "No se pudo abrir caja"
            )

            return

        id_caja = caja_result['id_caja']

        apertura_query = """
            INSERT INTO apertura_cierre
            (
                id_caja_fk,
                id_usuario_fk,
                fecha_hora_apertura,
                monto_inicial
            )
            VALUES
            (
                %s,
                %s,
                NOW(),
                %s
            )
            RETURNING id_apertura
        """

        apertura_result = self.db.fetch_one(
            apertura_query,
            (
                id_caja,
                self.usuario_data['id_usuario'],
                monto
            )
        )

        if apertura_result:

            QMessageBox.information(
                self,
                "Exito",
                "Caja abierta correctamente"
            )

            self.verificar_estado_caja()

    # =====================================================
    # CERRAR CAJA
    # =====================================================
    def cerrar_caja(self):

        monto_final = self.monto_final.value()

        query = """
            UPDATE apertura_cierre
            SET
                fecha_hora_cierre = NOW(),
                monto_final = %s
            WHERE id_apertura = %s
        """

        if self.db.execute_query(
            query,
            (
                monto_final,
                self.id_apertura_actual
            )
        ):

            QMessageBox.information(
                self,
                "Exito",
                "Caja cerrada"
            )

            self.verificar_estado_caja()

    # =====================================================
    # REGISTRAR MOVIMIENTO
    # =====================================================
    def registrar_movimiento(self):

        if not self.id_apertura_actual:

            QMessageBox.warning(
                self,
                "Error",
                "Debe abrir la caja primero"
            )

            return

        tipo = self.tipo_movimiento.currentText()

        tipo_gasto = self.tipo_gasto.currentText()

        descripcion = self.descripcion_mov.text().strip()

        monto = self.monto_mov.value()

        if not descripcion or monto <= 0:

            QMessageBox.warning(
                self,
                "Error",
                "Complete los campos correctamente"
            )

            return

        # =================================================
        # MOVIMIENTO CAJA
        # =================================================
        query = """
            INSERT INTO movimiento_caja
            (
                id_caja_fk,
                tipo_movimiento,
                descripcion,
                monto,
                fecha_hora
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                NOW()
            )
            RETURNING id_movimiento
        """

        movimiento = self.db.fetch_one(
            query,
            (
                self.id_caja_actual,
                tipo,
                descripcion,
                monto
            )
        )

        if not movimiento:

            QMessageBox.critical(
                self,
                "Error",
                "No se pudo registrar el movimiento"
            )

            return

        # =================================================
        # EGRESO -> GASTO
        # =================================================
        if tipo == "EGRESO":

            resultado_gasto = self.gasto_service.crear_gasto(
                movimiento['id_movimiento'],
                tipo_gasto,
                descripcion,
                monto
            )

            if not resultado_gasto:

                QMessageBox.critical(
                    self,
                    "Error",
                    "No se pudo registrar el gasto"
                )

                return

        QMessageBox.information(
            self,
            "Exito",
            "Movimiento registrado"
        )

        self.descripcion_mov.clear()

        self.monto_mov.setValue(0)

        self.cargar_movimientos()

    # =====================================================
    # CARGAR MOVIMIENTOS
    # =====================================================
    def cargar_movimientos(self):

        if not self.id_apertura_actual:
            return

        query = """
            SELECT
                mc.fecha_hora,
                mc.tipo_movimiento,
                mc.descripcion,
                mc.monto,
                u.nombre
            FROM movimiento_caja mc
            JOIN apertura_cierre ac
                ON mc.id_caja_fk = ac.id_caja_fk
            JOIN usuario u
                ON ac.id_usuario_fk = u.id_usuario
            WHERE ac.id_apertura = %s
            ORDER BY mc.fecha_hora DESC
        """

        movs = self.db.fetch_all(
            query,
            (self.id_apertura_actual,)
        )

        self.movimientos_table.setRowCount(
            len(movs)
        )

        for i, m in enumerate(movs):

            self.movimientos_table.setItem(
                i,
                0,
                QTableWidgetItem(
                    str(m['fecha_hora'])[:19]
                )
            )

            self.movimientos_table.setItem(
                i,
                1,
                QTableWidgetItem(
                    m['tipo_movimiento']
                )
            )

            self.movimientos_table.setItem(
                i,
                2,
                QTableWidgetItem(
                    m['descripcion']
                )
            )

            self.movimientos_table.setItem(
                i,
                3,
                QTableWidgetItem(
                    f"Q{m['monto']:.2f}"
                )
            )

            self.movimientos_table.setItem(
                i,
                4,
                QTableWidgetItem(
                    m['nombre']
                )
            )

    # =====================================================
    # CARGAR HISTORIAL
    # =====================================================
    def cargar_historial(self):

        query = """
            SELECT
                ac.fecha_hora_apertura,
                ac.fecha_hora_cierre,
                u.nombre,
                ac.monto_inicial,
                ac.monto_final
            FROM apertura_cierre ac
            JOIN usuario u
                ON ac.id_usuario_fk = u.id_usuario
            WHERE ac.fecha_hora_cierre IS NOT NULL
            ORDER BY ac.fecha_hora_apertura DESC
        """

        hist = self.db.fetch_all(query)

        self.historial_table.setRowCount(
            len(hist)
        )

        for i, h in enumerate(hist):

            self.historial_table.setItem(
                i,
                0,
                QTableWidgetItem(
                    str(h['fecha_hora_apertura'])[:19]
                )
            )

            self.historial_table.setItem(
                i,
                1,
                QTableWidgetItem(
                    str(h['fecha_hora_cierre'])[:19]
                )
            )

            self.historial_table.setItem(
                i,
                2,
                QTableWidgetItem(
                    h['nombre']
                )
            )

            self.historial_table.setItem(
                i,
                3,
                QTableWidgetItem(
                    f"Q{h['monto_inicial']:.2f}"
                )
            )

            self.historial_table.setItem(
                i,
                4,
                QTableWidgetItem(
                    f"Q{h['monto_final']:.2f}"
                )
            )

            diff = (
                h['monto_final']
                - h['monto_inicial']
            ) if h['monto_final'] else 0

            self.historial_table.setItem(
                i,
                5,
                QTableWidgetItem(
                    f"Q{diff:.2f}"
                )
            )