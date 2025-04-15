# app/views/main_window.py
from PySide6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QLabel, QStatusBar,
                              QMessageBox, QMenuBar, QMenu, QAction, QToolBar,
                              QDialog, QDialogButtonBox, QLineEdit, QComboBox,
                              QCheckBox, QFrame, QSplitter, QApplication)
from PySide6.QtCore import Qt, Signal, QSize, QSettings, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QFont, QAction

import sys
import os
import logging
from datetime import datetime

# Importar vistas
from .pos_view import POSView
from .admin_view import AdminView
from .inventory_view import InventoryView
from .reports_view import ReportsView

class MainWindow(QMainWindow):
    """Ventana principal del sistema"""
    
    # Señales
    logout_requested = Signal()
    backup_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración básica
        self.setWindowTitle("Sistema POS")
        self.setMinimumSize(1024, 768)
        
        # Inicializar logger
        self.logger = logging.getLogger('pos.views.main')
        
        # Datos del usuario actual
        self.current_user = None
        
        # Inicializar la interfaz
        self.setup_ui()
        
        # Cargar configuración guardada
        self.load_settings()
        
        # Inicializar temporizador para actualizar hora
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_time)
        self.update_timer.start(1000)  # Actualizar cada segundo
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Widget central con pestañas
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)
        
        # Crear barra de menú
        self.create_menu_bar()
        
        # Crear barra de herramientas
        self.create_toolbar()
        
        # Crear barra de estado
        self.create_status_bar()
        
        # Agregar pestañas (serán habilitadas según el rol del usuario)
        self.create_tabs()
        
        # Inicialmente deshabilitar pestañas hasta que inicie sesión
        self.disable_tabs()
    
    def create_menu_bar(self):
        """Crear barra de menú"""
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        
        # Menú archivo
        file_menu = QMenu("&Archivo", self)
        menu_bar.addMenu(file_menu)
        
        # Acciones del menú archivo
        backup_action = QAction("Crear &Copia de Seguridad", self)
        backup_action.setShortcut(QKeySequence("Ctrl+B"))
        backup_action.triggered.connect(self.backup_requested)
        
        logout_action = QAction("&Cerrar Sesión", self)
        logout_action.setShortcut(QKeySequence("Ctrl+L"))
        logout_action.triggered.connect(self.confirm_logout)
        
        exit_action = QAction("&Salir", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        
        file_menu.addAction(backup_action)
        file_menu.addSeparator()
        file_menu.addAction(logout_action)
        file_menu.addAction(exit_action)
        
        # Menú ayuda
        help_menu = QMenu("A&yuda", self)
        menu_bar.addMenu(help_menu)
        
        # Acciones del menú ayuda
        about_action = QAction("&Acerca de", self)
        about_action.triggered.connect(self.show_about_dialog)
        
        help_action = QAction("&Ayuda", self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self.show_help_dialog)
        
        help_menu.addAction(help_action)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Crear barra de herramientas"""
        toolbar = QToolBar("Barra de Herramientas Principal", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        
        # Botones de la barra de herramientas
        # Usar íconos de sistema o agregar los propios
        icons_dir = os.path.join(os.path.dirname(__file__), "../../resources/icons")
        
        # Ventas
        sales_action = QAction("Ventas", self)
        sales_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        try:
            sales_action.setIcon(QIcon(os.path.join(icons_dir, "sales.png")))
        except:
            pass
        toolbar.addAction(sales_action)
        
        # Inventario
        inventory_action = QAction("Inventario", self)
        inventory_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        try:
            inventory_action.setIcon(QIcon(os.path.join(icons_dir, "inventory.png")))
        except:
            pass
        toolbar.addAction(inventory_action)
        
        # Reportes
        reports_action = QAction("Reportes", self)
        reports_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        try:
            reports_action.setIcon(QIcon(os.path.join(icons_dir, "reports.png")))
        except:
            pass
        toolbar.addAction(reports_action)
        
        # Separador
        toolbar.addSeparator()
        
        # Administración
        admin_action = QAction("Administración", self)
        admin_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        try:
            admin_action.setIcon(QIcon(os.path.join(icons_dir, "admin.png")))
        except:
            pass
        toolbar.addAction(admin_action)
        
        # Separador
        toolbar.addSeparator()
        
        # Cerrar sesión
        logout_action = QAction("Cerrar Sesión", self)
        logout_action.triggered.connect(self.confirm_logout)
        try:
            logout_action.setIcon(QIcon(os.path.join(icons_dir, "logout.png")))
        except:
            pass
        toolbar.addAction(logout_action)
    
    def create_status_bar(self):
        """Crear barra de estado"""
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        
        # Información del usuario actual
        self.user_label = QLabel("No ha iniciado sesión")
        status_bar.addWidget(self.user_label)
        
        # Separador
        status_bar.addPermanentWidget(QLabel(" | "))
        
        # Fecha y hora actual
        self.datetime_label = QLabel(datetime.now().strftime("%d/%m/%Y %H:%M"))
        self.datetime_label.setAlignment(Qt.AlignRight)
        status_bar.addPermanentWidget(self.datetime_label)
    
    def create_tabs(self):
        """Crear las pestañas del sistema"""
        # Pestaña de ventas (POS)
        self.pos_view = POSView(self)
        self.tab_widget.addTab(self.pos_view, "Ventas")
        
        # Pestaña de inventario
        self.inventory_view = InventoryView(self)
        self.tab_widget.addTab(self.inventory_view, "Inventario")
        
        # Pestaña de reportes
        self.reports_view = ReportsView(self)
        self.tab_widget.addTab(self.reports_view, "Reportes")
        
        # Pestaña de administración
        self.admin_view = AdminView(self)
        self.tab_widget.addTab(self.admin_view, "Administración")
    
    def set_user(self, user_data):
        """
        Establecer el usuario actual y configurar la interfaz según su rol
        
        Args:
            user_data: Diccionario con datos del usuario
        """
        self.current_user = user_data
        
        # Actualizar etiqueta de usuario
        self.user_label.setText(f"Usuario: {user_data['full_name']} ({user_data['role']})")
        
        # Habilitar pestañas según el rol
        if user_data['role'] == 'admin':
            # Administrador tiene acceso a todo
            self.enable_tabs([0, 1, 2, 3])
        elif user_data['role'] == 'manager':
            # Gerente tiene acceso a todo excepto administración
            self.enable_tabs([0, 1, 2])
            self.disable_tabs([3])
        else:
            # Cajero solo tiene acceso a ventas
            self.enable_tabs([0])
            self.disable_tabs([1, 2, 3])
        
        # Ir a la pestaña principal según el rol
        if user_data['role'] == 'admin' or user_data['role'] == 'manager':
            self.tab_widget.setCurrentIndex(0)
        else:
            self.tab_widget.setCurrentIndex(0)
        
        # Registrar en el log
        self.logger.info(f"Usuario {user_data['username']} ha iniciado sesión")
        
        # Mostrar mensaje de bienvenida
        self.statusBar().showMessage(f"Bienvenido, {user_data['full_name']}", 5000)
    
    def enable_tabs(self, indices):
        """
        Habilitar pestañas específicas
        
        Args:
            indices: Lista de índices de pestañas a habilitar
        """
        for i in range(self.tab_widget.count()):
            self.tab_widget.setTabEnabled(i, i in indices)
    
    def disable_tabs(self, indices=None):
        """
        Deshabilitar pestañas específicas
        
        Args:
            indices: Lista de índices de pestañas a deshabilitar (None para todas)
        """
        if indices is None:
            indices = range(self.tab_widget.count())
            
        for i in indices:
            self.tab_widget.setTabEnabled(i, False)
    
    def load_settings(self):
        """Cargar configuración guardada"""
        settings = QSettings("Sistema POS", "POS")
        
        # Restaurar geometría de la ventana
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Establecer tamaño por defecto
            self.resize(1200, 800)
        
        # Restaurar posición
        pos = settings.value("pos")
        if pos:
            self.move(pos)
    
    def save_settings(self):
        """Guardar configuración actual"""
        settings = QSettings("Sistema POS", "POS")
        
        # Guardar geometría de la ventana
        settings.setValue("geometry", self.saveGeometry())
        
        # Guardar posición
        settings.setValue("pos", self.pos())
    
    def update_time(self):
        """Actualizar hora en la barra de estado"""
        self.datetime_label.setText(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    
    def confirm_logout(self):
        """Confirmar cierre de sesión"""
        reply = QMessageBox.question(
            self,
            "Cerrar Sesión",
            "¿Está seguro de que desea cerrar sesión?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.do_logout()
    
    def do_logout(self):
        """Realizar cierre de sesión"""
        if self.current_user:
            self.logger.info(f"Usuario {self.current_user['username']} ha cerrado sesión")
            
        # Limpiar usuario actual
        self.current_user = None
        
        # Actualizar etiqueta de usuario
        self.user_label.setText("No ha iniciado sesión")
        
        # Deshabilitar pestañas
        self.disable_tabs()
        
        # Emitir señal de cierre de sesión
        self.logout_requested.emit()
    
    def show_about_dialog(self):
        """Mostrar cuadro de diálogo Acerca de"""
        about_text = """
        <h2>Sistema POS</h2>
        <p>Versión 1.0.0</p>
        <p>Sistema de Punto de Venta (POS) completo para negocios minoristas.</p>
        <p>&copy; 2025 - Todos los derechos reservados</p>
        """
        
        QMessageBox.about(self, "Acerca de Sistema POS", about_text)
    
    def show_help_dialog(self):
        """Mostrar cuadro de diálogo de ayuda"""
        help_text = """
        <h2>Ayuda del Sistema POS</h2>
        
        <h3>Atajos de teclado:</h3>
        <ul>
            <li><b>F1</b> - Mostrar esta ayuda</li>
            <li><b>Ctrl+L</b> - Cerrar sesión</li>
            <li><b>Ctrl+B</b> - Crear copia de seguridad</li>
            <li><b>Ctrl+Q</b> - Salir del sistema</li>
        </ul>
        
        <h3>Módulos:</h3>
        <ul>
            <li><b>Ventas</b> - Realizar ventas, gestionar carrito, cobrar</li>
            <li><b>Inventario</b> - Administrar productos, categorías y stock</li>
            <li><b>Reportes</b> - Generar y visualizar reportes del sistema</li>
            <li><b>Administración</b> - Gestionar usuarios, configuración y respaldos</li>
        </ul>
        
        <p>Para obtener más ayuda, consulte la documentación completa.</p>
        """
        
        QMessageBox.information(self, "Ayuda", help_text)
    
    def closeEvent(self, event):
        """
        Manejar evento de cierre de la ventana
        
        Args:
            event: Evento de cierre
        """
        # Guardar configuración actual
        self.save_settings()
        
        # Confirmar cierre si hay un usuario activo
        if self.current_user:
            reply = QMessageBox.question(
                self,
                "Confirmar Salida",
                "¿Está seguro de que desea salir del sistema?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Realizar cierre de sesión
                self.do_logout()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()