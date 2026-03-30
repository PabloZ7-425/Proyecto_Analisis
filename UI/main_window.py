from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""

    def __init__(self, usuario_data):
        super().__init__()
        self.usuario_data = usuario_data
        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz de la ventana principal"""
        self.setWindowTitle(f"TEC SHOP - Control de Caja - {self.usuario_data['nombre']}")
        self.setGeometry(100, 100, 800, 600)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Título de bienvenida
        welcome_label = QLabel(f"¡Bienvenido {self.usuario_data['nombre']}!")
        welcome_font = QFont("Arial", 18, QFont.Bold)
        welcome_label.setFont(welcome_font)
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)

        # Información del usuario
        info_label = QLabel(f"Rol: {self.usuario_data['rol']}")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)

        # Espacio
        layout.addSpacing(50)

        # Botones de navegación (placeholder)
        btn_ventas = QPushButton("Ventas")
        btn_ventas.clicked.connect(self.abrir_ventas)
        layout.addWidget(btn_ventas)

        btn_clientes = QPushButton("Clientes")
        btn_clientes.clicked.connect(self.abrir_clientes)
        layout.addWidget(btn_clientes)

        btn_caja = QPushButton("Caja")
        btn_caja.clicked.connect(self.abrir_caja)
        layout.addWidget(btn_caja)

        btn_apartados = QPushButton("Apartados")
        btn_apartados.clicked.connect(self.abrir_apartados)
        layout.addWidget(btn_apartados)

        btn_cerrar_sesion = QPushButton("Cerrar Sesión")
        btn_cerrar_sesion.clicked.connect(self.cerrar_sesion)
        layout.addWidget(btn_cerrar_sesion)

        layout.addStretch()

    def abrir_ventas(self):
        """Abre la ventana de ventas"""
        QMessageBox.information(self, "Info", "Módulo de Ventas (Próximamente)")

    def abrir_clientes(self):
        """Abre la ventana de clientes"""
        QMessageBox.information(self, "Info", "Módulo de Clientes (Próximamente)")

    def abrir_caja(self):
        """Abre la ventana de caja"""
        QMessageBox.information(self, "Info", "Módulo de Caja (Próximamente)")

    def abrir_apartados(self):
        """Abre la ventana de apartados"""
        QMessageBox.information(self, "Info", "Módulo de Apartados (Próximamente)")

    def cerrar_sesion(self):
        """Cierra la sesión actual"""
        reply = QMessageBox.question(self, 'Cerrar Sesión',
                                     '¿Está seguro de que desea cerrar sesión?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.close()
            # Volver a mostrar la ventana de login
            from UI.login_ui import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()