# UI/reportes_ui.py - Solo para gerente/supervisor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QDateEdit, QComboBox, QHeaderView, QTabWidget)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.conexion import DatabaseConnection


class VentanaReportes(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseConnection()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        header = QLabel("Reportes Gerenciales")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(header)

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

        self.tabs.addTab(self.crear_tab_ventas(), "Reporte de Ventas")
        self.tabs.addTab(self.crear_tab_caja(), "Historial de Caja")
        self.tabs.addTab(self.crear_tab_apartados(), "Reporte de Apartados")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def crear_tab_ventas(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Filtros
        filter_layout = QHBoxLayout()

        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(QDate.currentDate().addDays(-30))
        self.fecha_inicio.setCalendarPopup(True)
        filter_layout.addWidget(QLabel("Desde:"))
        filter_layout.addWidget(self.fecha_inicio)

        self.fecha_fin = QDateEdit()
        self.fecha_fin.setDate(QDate.currentDate())
        self.fecha_fin.setCalendarPopup(True)
        filter_layout.addWidget(QLabel("Hasta:"))
        filter_layout.addWidget(self.fecha_fin)

        filter_layout.addStretch()

        buscar_btn = QPushButton("Generar")
        buscar_btn.clicked.connect(self.cargar_ventas)
        buscar_btn.setStyleSheet("padding: 8px 16px; background-color: #F5C800; border-radius: 8px; font-weight: bold;")
        filter_layout.addWidget(buscar_btn)

        layout.addLayout(filter_layout)

        # Tabla
        self.ventas_table = QTableWidget()
        self.ventas_table.setColumnCount(6)
        self.ventas_table.setHorizontalHeaderLabels(["Fecha", "Factura", "Cliente", "Total", "Forma Pago", "Envio"])
        self.ventas_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ventas_table.setStyleSheet("border: 1px solid #E5E7EB; border-radius: 12px;")
        layout.addWidget(self.ventas_table)

        tab.setLayout(layout)
        self.cargar_ventas()
        return tab

    def crear_tab_caja(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.caja_table = QTableWidget()
        self.caja_table.setColumnCount(6)
        self.caja_table.setHorizontalHeaderLabels(["Apertura", "Cierre", "Usuario", "Monto Inicial", "Monto Final", "Diferencia"])
        self.caja_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.caja_table.setStyleSheet("border: 1px solid #E5E7EB; border-radius: 12px;")
        layout.addWidget(self.caja_table)

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.cargar_caja)
        refresh_btn.setStyleSheet("padding: 8px; max-width: 120px; background-color: #F3F4F6; border-radius: 8px;")
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)

        tab.setLayout(layout)
        self.cargar_caja()
        return tab

    def crear_tab_apartados(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.apartados_table = QTableWidget()
        self.apartados_table.setColumnCount(7)
        self.apartados_table.setHorizontalHeaderLabels(["Cliente", "Producto", "Total", "Pagado", "Saldo", "Fecha", "Estado"])
        self.apartados_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.apartados_table.setStyleSheet("border: 1px solid #E5E7EB; border-radius: 12px;")
        layout.addWidget(self.apartados_table)

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.cargar_apartados)
        refresh_btn.setStyleSheet("padding: 8px; max-width: 120px; background-color: #F3F4F6; border-radius: 8px;")
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)

        tab.setLayout(layout)
        self.cargar_apartados()
        return tab

    def cargar_ventas(self):
        desde = self.fecha_inicio.date().toString("yyyy-MM-dd")
        hasta = self.fecha_fin.date().toString("yyyy-MM-dd")

        query = """
            SELECT v.fecha_hora, v.numero_documento, v.total, v.forma_pago, v.es_envio,
                   c.nombre as cliente_nombre, c.apellido as cliente_apellido
            FROM venta v
            LEFT JOIN cliente c ON v.id_cliente_fk = c.id_cliente
            WHERE DATE(v.fecha_hora) BETWEEN %s AND %s
            ORDER BY v.fecha_hora DESC
        """
        ventas = self.db.fetch_all(query, (desde, hasta))

        self.ventas_table.setRowCount(len(ventas))

        for i, v in enumerate(ventas):
            self.ventas_table.setItem(i, 0, QTableWidgetItem(str(v['fecha_hora'])[:19]))
            self.ventas_table.setItem(i, 1, QTableWidgetItem(v['numero_documento']))
            cliente = f"{v['cliente_nombre']} {v['cliente_apellido']}" if v['cliente_nombre'] else "Consumidor Final"
            self.ventas_table.setItem(i, 2, QTableWidgetItem(cliente))
            self.ventas_table.setItem(i, 3, QTableWidgetItem(f"Q{v['total']:.2f}"))
            self.ventas_table.setItem(i, 4, QTableWidgetItem(v['forma_pago']))
            envio = "Si" if v['es_envio'] else "No"
            self.ventas_table.setItem(i, 5, QTableWidgetItem(envio))

    def cargar_caja(self):
        query = """
            SELECT ac.fecha_hora_apertura, ac.fecha_hora_cierre, 
                   u.nombre, ac.monto_inicial, ac.monto_final
            FROM apertura_cierre ac
            JOIN usuario u ON ac.id_usuario_fk = u.id_usuario
            ORDER BY ac.fecha_hora_apertura DESC
        """
        historial = self.db.fetch_all(query)

        self.caja_table.setRowCount(len(historial))

        for i, h in enumerate(historial):
            self.caja_table.setItem(i, 0, QTableWidgetItem(str(h['fecha_hora_apertura'])[:19]))
            cierre = str(h['fecha_hora_cierre'])[:19] if h['fecha_hora_cierre'] else "-"
            self.caja_table.setItem(i, 1, QTableWidgetItem(cierre))
            self.caja_table.setItem(i, 2, QTableWidgetItem(h['nombre']))
            self.caja_table.setItem(i, 3, QTableWidgetItem(f"Q{h['monto_inicial']:.2f}"))
            final = f"Q{h['monto_final']:.2f}" if h['monto_final'] else "-"
            self.caja_table.setItem(i, 4, QTableWidgetItem(final))
            diferencia = (h['monto_final'] - h['monto_inicial']) if h['monto_final'] else 0
            self.caja_table.setItem(i, 5, QTableWidgetItem(f"Q{diferencia:.2f}"))

    def cargar_apartados(self):
        query = """
            SELECT a.id_apartado, a.total_producto, a.fecha_inicio, a.estado,
                   c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                   p.nombre as producto_nombre,
                   COALESCE(SUM(da.monto), 0) as total_pagado
            FROM apartado a
            JOIN cliente c ON a.id_cliente_fk = c.id_cliente
            JOIN producto p ON a.id_producto_fk = p.id_producto
            LEFT JOIN detalle_apartado da ON a.id_apartado = da.id_apartado_fk
            GROUP BY a.id_apartado, c.nombre, c.apellido, p.nombre
            ORDER BY a.fecha_inicio DESC
        """
        apartados = self.db.fetch_all(query)

        self.apartados_table.setRowCount(len(apartados))

        for i, a in enumerate(apartados):
            cliente = f"{a['cliente_nombre']} {a['cliente_apellido']}" if a['cliente_apellido'] else a['cliente_nombre']
            self.apartados_table.setItem(i, 0, QTableWidgetItem(cliente))
            self.apartados_table.setItem(i, 1, QTableWidgetItem(a['producto_nombre']))
            self.apartados_table.setItem(i, 2, QTableWidgetItem(f"Q{a['total_producto']:.2f}"))
            self.apartados_table.setItem(i, 3, QTableWidgetItem(f"Q{a['total_pagado']:.2f}"))
            saldo = a['total_producto'] - a['total_pagado']
            self.apartados_table.setItem(i, 4, QTableWidgetItem(f"Q{saldo:.2f}"))
            self.apartados_table.setItem(i, 5, QTableWidgetItem(str(a['fecha_inicio'])))

            estado = a['estado']
            if estado == 'ACTIVO':
                estado = "ACTIVO"
            elif estado == 'COMPLETADO':
                estado = "COMPLETADO"
            else:
                estado = "CANCELADO"
            self.apartados_table.setItem(i, 6, QTableWidgetItem(estado))