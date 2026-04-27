# main.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QSplashScreen, QStyleFactory
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
from UI.login_ui import LoginWindow


def setup_application(app):
    """Configura la aplicacion con estilos profesionales"""

    # Fusion style para mejor apariencia
    app.setStyle(QStyleFactory.create('Fusion'))

    # Paleta de colores
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.WindowText, QColor(26, 26, 26))
    palette.setColor(QPalette.Base, QColor(249, 250, 251))
    palette.setColor(QPalette.AlternateBase, QColor(243, 244, 246))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(26, 26, 26))
    palette.setColor(QPalette.Text, QColor(26, 26, 26))
    palette.setColor(QPalette.Button, QColor(243, 244, 246))
    palette.setColor(QPalette.ButtonText, QColor(26, 26, 26))
    palette.setColor(QPalette.BrightText, QColor(245, 200, 0))
    palette.setColor(QPalette.Link, QColor(245, 200, 0))
    palette.setColor(QPalette.Highlight, QColor(245, 200, 0))
    palette.setColor(QPalette.HighlightedText, QColor(26, 26, 26))
    app.setPalette(palette)

    # Fuente por defecto
    font = QFont("Segoe UI", 9)
    app.setFont(font)


def main():
    app = QApplication(sys.argv)
    setup_application(app)

    # Splash screen opcional
    splash = QSplashScreen()
    splash.setStyleSheet("""
        QSplashScreen {
            background-color: #FFFFFF;
            color: #1A1A1A;
        }
    """)
    splash.showMessage("Cargando TechShop...", Qt.AlignCenter, QColor(26, 26, 26))
    splash.show()

    # Crear y mostrar ventana de login
    login_window = LoginWindow()

    # Pequeña demora para mostrar splash
    QTimer.singleShot(1500, lambda: [splash.finish(login_window), login_window.show()])

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()