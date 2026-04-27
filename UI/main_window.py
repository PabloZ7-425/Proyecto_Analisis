# UI/main_window.py
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.conexion import DatabaseConnection
from UI.ventas_ui import VentanasVentas
from UI.clientes_ui import VentanaClientes
from UI.productos_ui import VentanaProductos
from UI.caja_ui import VentanaCaja
from UI.apartados_ui import VentanaApartados


class MainWindow(QMainWindow):
    def __init__(self, usuario_data):
        super().__init__()
        self.usuario_data = usuario_data
        self.db = DatabaseConnection()
        self.id_caja_actual = None
        self.init_ui()
        self.verificar_caja_abierta()

    def init_ui(self):
        self.setWindowTitle(f"TechShop - {self.usuario_data['nombre']}")
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(1000, 600)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        central.setLayout(main_layout)

        sidebar = self.crear_sidebar()
        main_layout.addWidget(sidebar)

        self.content_area = QWidget()
        self.content_area.setStyleSheet("background-color: #F9FAFB;")
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_area.setLayout(self.content_layout)
        main_layout.addWidget(self.content_area, 1)

        self.show_dashboard()

    def crear_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("background-color: white; border-right: 1px solid #E5E7EB;")

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 30, 15, 30)

        logo = QLabel("TECH SHOP")
        logo.setFont(QFont("Arial", 18, QFont.Bold))
        logo.setStyleSheet("padding-bottom: 20px; padding-left: 15px;")
        layout.addWidget(logo)

        botones = [
            ("Dashboard", self.show_dashboard),
            ("Ventas", self.show_ventas),
            ("Clientes", self.show_clientes),
            ("Productos", self.show_productos),
            ("Caja", self.show_caja),
            ("Apartados", self.show_apartados),
        ]

        if self.usuario_data['rol'].lower() in ['gerente', 'supervisor', 'admin', 'administrador']:
            botones.append(("Reportes", self.show_reportes))

        for texto, callback in botones:
            btn = QPushButton(texto)
            btn.setFixedHeight(45)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #4B5563;
                    border: none;
                    text-align: left;
                    padding: 10px 20px;
                    font-size: 13px;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #F3F4F6;
                }
                QPushButton:pressed {
                    background-color: #F5C800;
                }
            """)
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        layout.addStretch()

        user_frame = QFrame()
        user_frame.setStyleSheet("background-color: #F9FAFB; border-radius: 12px; padding: 12px;")
        user_layout = QVBoxLayout()

        user_name = QLabel(self.usuario_data['nombre'])
        user_name.setFont(QFont("Segoe UI", 12, QFont.Bold))
        user_layout.addWidget(user_name)

        user_rol = QLabel(f"Rol: {self.usuario_data['rol']}")
        user_rol.setFont(QFont("Segoe UI", 10))
        user_rol.setStyleSheet("color: #6B7280;")
        user_layout.addWidget(user_rol)

        logout_btn = QPushButton("Cerrar Sesion")
        logout_btn.setFixedHeight(35)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #EF4444;
                border: 1px solid #FEE2E2;
                border-radius: 8px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
            }
        """)
        logout_btn.clicked.connect(self.cerrar_sesion)
        user_layout.addWidget(logout_btn)

        user_frame.setLayout(user_layout)
        layout.addWidget(user_frame)

        sidebar.setLayout(layout)
        return sidebar

    def verificar_caja_abierta(self):
        query = """
            SELECT ac.id_caja_fk
            FROM apertura_cierre ac
            WHERE ac.fecha_hora_cierre IS NULL
            ORDER BY ac.fecha_hora_apertura DESC
            LIMIT 1
        """
        resultado = self.db.fetch_one(query)
        if resultado:
            self.id_caja_actual = resultado['id_caja_fk']

    def limpiar_contenido(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_dashboard(self):
        self.limpiar_contenido()

        title = QLabel(f"Bienvenido, {self.usuario_data['nombre']}")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.content_layout.addWidget(title)

        rol_label = QLabel(f"Rol: {self.usuario_data['rol']}")
        rol_label.setFont(QFont("Segoe UI", 12))
        rol_label.setStyleSheet("color: #6B7280; margin-bottom: 20px;")
        self.content_layout.addWidget(rol_label)

        info = QLabel(
            "Sistema de Control de Caja - TechShop\n\n"
            "Seleccione una opcion del menu lateral para comenzar."
        )
        info.setFont(QFont("Segoe UI", 12))
        info.setStyleSheet("background-color: #F3F4F6; padding: 40px; border-radius: 16px;")
        info.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(info)
        self.content_layout.addStretch()

    def show_ventas(self):
        self.limpiar_contenido()
        widget = VentanasVentas(self.usuario_data, self.id_caja_actual)
        self.content_layout.addWidget(widget)

    def show_clientes(self):
        self.limpiar_contenido()
        widget = VentanaClientes()
        self.content_layout.addWidget(widget)

    def show_productos(self):
        self.limpiar_contenido()
        widget = VentanaProductos()
        self.content_layout.addWidget(widget)

    def show_caja(self):
        self.limpiar_contenido()
        widget = VentanaCaja(self.usuario_data)
        self.content_layout.addWidget(widget)
        widget.caja_abierta_signal.connect(self.actualizar_id_caja)

    def show_apartados(self):
        self.limpiar_contenido()
        widget = VentanaApartados(self.id_caja_actual)
        self.content_layout.addWidget(widget)

    def show_reportes(self):
        self.limpiar_contenido()
        from UI.reportes_ui import VentanaReportes
        widget = VentanaReportes()
        self.content_layout.addWidget(widget)

    def actualizar_id_caja(self, id_caja):
        self.id_caja_actual = id_caja

    def cerrar_sesion(self):
        reply = QMessageBox.question(self, 'Cerrar Sesion', 'Esta seguro?',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.close()
            from UI.login_ui import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()