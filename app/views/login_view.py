# app/views/login_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QPushButton, QMessageBox, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont, QIcon

class LoginView(QWidget):
    """Vista de inicio de sesión"""
    
    # Señal emitida cuando el inicio de sesión es exitoso
    login_successful = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Iniciar Sesión - Sistema POS")
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        
        # Configurar la interfaz
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Título
        title_label = QLabel("Sistema POS")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 24, QFont.Bold))
        
        # Logo (si existe)
        try:
            logo_pixmap = QPixmap("../resources/icons/logo.png")
            logo_label = QLabel()
            logo_label.setPixmap(logo_pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(logo_label)
        except:
            # Si no hay logo, mostrar un espacio adicional
            main_layout.addSpacing(20)
        
        main_layout.addWidget(title_label)
        main_layout.addSpacing(20)
        
        # Marco para el formulario
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.StyledPanel)
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                border: 1px solid #ddd;
            }
        """)
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        
        # Nombre de usuario
        username_label = QLabel("Usuario:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ingrese su nombre de usuario")
        
        # Contraseña
        password_label = QLabel("Contraseña:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Ingrese su contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        # Botón de inicio de sesión
        self.login_button = QPushButton("Iniciar Sesión")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        # Agregar widgets al layout del formulario
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.login_button)
        
        # Agregar formulario al layout principal
        main_layout.addWidget(form_frame)
        
        # Pie de página
        footer_label = QLabel("© 2025 - Sistema POS")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #888;")
        main_layout.addWidget(footer_label)
        
        # Conectar señales
        self.login_button.clicked.connect(self.on_login_clicked)
        self.password_input.returnPressed.connect(self.on_login_clicked)
    
    def on_login_clicked(self):
        """Manejar clic en el botón de inicio de sesión"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(
                self,
                "Campos vacíos",
                "Por favor, ingrese su nombre de usuario y contraseña."
            )
            return
        
        # Aquí normalmente llamaríamos al controlador para autenticar,
        # pero como este es solo el diseño de la vista, simulemos un inicio de sesión exitoso
        # En la implementación real, esto sería reemplazado por una llamada al controlador
        
        # Simular un usuario para pruebas
        if username == "admin" and password == "admin":
            # Usuario administrador
            user_data = {
                'user_id': 1,
                'username': 'admin',
                'full_name': 'Administrador',
                'role': 'admin'
            }
            self.login_successful.emit(user_data)
        elif username == "cajero" and password == "cajero":
            # Usuario cajero
            user_data = {
                'user_id': 2,
                'username': 'cajero',
                'full_name': 'Juan Pérez',
                'role': 'cashier'
            }
            self.login_successful.emit(user_data)
        else:
            # Credenciales incorrectas
            QMessageBox.warning(
                self,
                "Error de inicio de sesión",
                "Nombre de usuario o contraseña incorrectos."
            )
    
    def keyPressEvent(self, event):
        """Manejar teclas presionadas"""
        # Salir de la aplicación con Escape
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)