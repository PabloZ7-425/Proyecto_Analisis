import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from UI.login_ui import LoginWindow


def main():

    app = QApplication(sys.argv)


    app.setStyle('Fusion')

    # Crear y mostrar ventana de login
    login_window = LoginWindow()
    login_window.show()


    sys.exit(app.exec_())


if __name__ == '__main__':
    main()