# app/views/admin_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                              QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                              QMessageBox, QDialog, QDialogButtonBox, QLineEdit,
                              QComboBox, QFormLayout, QCheckBox, QHeaderView,
                              QSpinBox, QDoubleSpinBox, QGroupBox, QSplitter,
                              QTextEdit, QFileDialog, QInputDialog)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QIcon, QFont

import os
import logging
from datetime import datetime

class AdminView(QWidget):
    """Vista para la administración del sistema"""
    
    # Señales
    user_created = Signal(dict)
    user_updated = Signal(int, dict)
    user_deleted = Signal(int)
    backup_requested = Signal(str)
    restore_requested = Signal(str)
    settings_updated = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración básica
        self.logger = logging.getLogger('pos.views.admin')
        
        # Inicializar la interfaz
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Pestañas de administración
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Pestaña de usuarios
        users_tab = self.create_users_tab()
        tab_widget.addTab(users_tab, "Usuarios")
        
        # Pestaña de configuración
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "Configuración")
        
        # Pestaña de copias de seguridad
        backup_tab = self.create_backup_tab()
        tab_widget.addTab(backup_tab, "Copias de Seguridad")
        
        # Pestaña de registro (log)
        log_tab = self.create_log_tab()
        tab_widget.addTab(log_tab, "Registro")
    
    def create_users_tab(self):
        """Crear pestaña de gestión de usuarios"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Encabezado
        header_layout = QHBoxLayout()
        header_label = QLabel("Gestión de Usuarios")
        header_label.setFont(QFont('Arial', 14, QFont.Bold))
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Botones
        new_button = QPushButton("Nuevo Usuario")
        new_button.clicked.connect(self.show_new_user_dialog)
        header_layout.addWidget(new_button)
        
        layout.addLayout(header_layout)
        
        # Tabla de usuarios
        self.users_table = QTableWidget(0, 5)  # Filas, Columnas
        self.users_table.setHorizontalHeaderLabels(["ID", "Usuario", "Nombre Completo", "Rol", "Acciones"])
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.users_table)
        
        # Cargar datos de usuarios (simulado)
        self.load_sample_users()
        
        return tab
    
    def create_settings_tab(self):
        """Crear pestaña de configuración del sistema"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Encabezado
        header_label = QLabel("Configuración del Sistema")
        header_label.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(header_label)
        
        # Formulario de configuración
        form_layout = QFormLayout()
        
        # Información de la tienda
        store_group = QGroupBox("Información de la Tienda")
        store_layout = QFormLayout(store_group)
        
        self.store_name_input = QLineEdit()
        self.store_address_input = QLineEdit()
        self.store_phone_input = QLineEdit()
        
        store_layout.addRow("Nombre de la Tienda:", self.store_name_input)
        store_layout.addRow("Dirección:", self.store_address_input)
        store_layout.addRow("Teléfono:", self.store_phone_input)
        
        form_layout.addWidget(store_group)
        
        # Configuración fiscal
        fiscal_group = QGroupBox("Configuración Fiscal")
        fiscal_layout = QFormLayout(fiscal_group)
        
        self.tax_rate_input = QDoubleSpinBox()
        self.tax_rate_input.setRange(0, 100)
        self.tax_rate_input.setDecimals(2)
        self.tax_rate_input.setSuffix("%")
        self.tax_rate_input.setValue(16.0)  # IVA por defecto
        
        self.currency_symbol_input = QLineEdit()
        self.currency_symbol_input.setText("$")
        self.currency_symbol_input.setMaxLength(3)
        
        fiscal_layout.addRow("Tasa de Impuesto (IVA):", self.tax_rate_input)
        fiscal_layout.addRow("Símbolo de Moneda:", self.currency_symbol_input)
        
        form_layout.addWidget(fiscal_group)
        
        # Configuración de impresión
        printer_group = QGroupBox("Configuración de Impresión")
        printer_layout = QFormLayout(printer_group)
        
        self.receipt_header_input = QTextEdit()
        self.receipt_header_input.setMaximumHeight(80)
        self.receipt_footer_input = QTextEdit()
        self.receipt_footer_input.setMaximumHeight(80)
        
        printer_layout.addRow("Encabezado del Recibo:", self.receipt_header_input)
        printer_layout.addRow("Pie del Recibo:", self.receipt_footer_input)
        
        form_layout.addWidget(printer_group)
        
        # Otras configuraciones
        other_group = QGroupBox("Otras Configuraciones")
        other_layout = QFormLayout(other_group)
        
        self.auto_backup_checkbox = QCheckBox("Realizar copias de seguridad automáticas")
        self.auto_backup_checkbox.setChecked(True)
        
        self.backup_frequency_combo = QComboBox()
        self.backup_frequency_combo.addItems(["Diariamente", "Semanalmente", "Mensualmente"])
        
        other_layout.addRow(self.auto_backup_checkbox)
        other_layout.addRow("Frecuencia de copias:", self.backup_frequency_combo)
        
        form_layout.addWidget(other_group)
        
        layout.addLayout(form_layout)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Guardar Configuración")
        save_button.clicked.connect(self.save_settings)
        
        restore_defaults_button = QPushButton("Restaurar Valores por Defecto")
        restore_defaults_button.clicked.connect(self.restore_default_settings)
        
        button_layout.addStretch()
        button_layout.addWidget(restore_defaults_button)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        # Cargar configuración actual (simulada)
        self.load_sample_settings()
        
        return tab
    
    def create_backup_tab(self):
        """Crear pestaña de copias de seguridad"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Encabezado
        header_label = QLabel("Copias de Seguridad")
        header_label.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(header_label)
        
        # Acciones de copia de seguridad
        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout(actions_group)
        
        backup_button = QPushButton("Crear Copia de Seguridad")
        backup_button.clicked.connect(self.create_backup)
        
        restore_button = QPushButton("Restaurar Copia de Seguridad")
        restore_button.clicked.connect(self.restore_backup)
        
        actions_layout.addWidget(backup_button)
        actions_layout.addWidget(restore_button)
        
        layout.addWidget(actions_group)
        
        # Lista de copias de seguridad
        list_group = QGroupBox("Copias de Seguridad Disponibles")
        list_layout = QVBoxLayout(list_group)
        
        self.backups_table = QTableWidget(0, 4)  # Filas, Columnas
        self.backups_table.setHorizontalHeaderLabels(["Nombre", "Fecha", "Tamaño", "Acciones"])
        self.backups_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.backups_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.backups_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        list_layout.addWidget(self.backups_table)
        
        layout.addWidget(list_group)
        
        # Cargar copias de seguridad (simuladas)
        self.load_sample_backups()
        
        return tab
    
    def create_log_tab(self):
        """Crear pestaña de registro (log)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Encabezado
        header_layout = QHBoxLayout()
        header_label = QLabel("Registro del Sistema")
        header_label.setFont(QFont('Arial', 14, QFont.Bold))
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Botones
        refresh_button = QPushButton("Actualizar")
        refresh_button.clicked.connect(self.refresh_log)
        
        export_button = QPushButton("Exportar")
        export_button.clicked.connect(self.export_log)
        
        header_layout.addWidget(refresh_button)
        header_layout.addWidget(export_button)
        
        layout.addLayout(header_layout)
        
        # Visor de log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 10))
        
        layout.addWidget(self.log_text)
        
        # Cargar log (simulado)
        self.load_sample_log()
        
        return tab
    
    def load_sample_users(self):
        """Cargar datos de ejemplo de usuarios (para demostración)"""
        # Limpiar tabla
        self.users_table.setRowCount(0)
        
        # Datos de ejemplo
        users = [
            {"user_id": 1, "username": "admin", "full_name": "Administrador", "role": "admin"},
            {"user_id": 2, "username": "cajero1", "full_name": "Juan Pérez", "role": "cashier"},
            {"user_id": 3, "username": "cajero2", "full_name": "María López", "role": "cashier"},
            {"user_id": 4, "username": "gerente", "full_name": "Carlos Rodríguez", "role": "manager"}
        ]
        
        # Agregar datos a la tabla
        for user in users:
            row_position = self.users_table.rowCount()
            self.users_table.insertRow(row_position)
            
            # ID
            id_item = QTableWidgetItem(str(user["user_id"]))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.users_table.setItem(row_position, 0, id_item)
            
            # Usuario
            username_item = QTableWidgetItem(user["username"])
            self.users_table.setItem(row_position, 1, username_item)
            
            # Nombre completo
            fullname_item = QTableWidgetItem(user["full_name"])
            self.users_table.setItem(row_position, 2, fullname_item)
            
            # Rol
            role_item = QTableWidgetItem(user["role"])
            role_item.setTextAlignment(Qt.AlignCenter)
            self.users_table.setItem(row_position, 3, role_item)
            
            # Botones de acción
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_button = QPushButton("Editar")
            edit_button.setProperty("user_id", user["user_id"])
            edit_button.clicked.connect(lambda checked, user_id=user["user_id"]: self.show_edit_user_dialog(user_id))
            
            delete_button = QPushButton("Eliminar")
            delete_button.setProperty("user_id", user["user_id"])
            delete_button.clicked.connect(lambda checked, user_id=user["user_id"]: self.confirm_delete_user(user_id))
            
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            
            self.users_table.setCellWidget(row_position, 4, actions_widget)
    
    def load_sample_settings(self):
        """Cargar configuración de ejemplo (para demostración)"""
        # Información de la tienda
        self.store_name_input.setText("Mi Tienda")
        self.store_address_input.setText("Calle Principal #123")
        self.store_phone_input.setText("123-456-7890")
        
        # Configuración fiscal
        self.tax_rate_input.setValue(16.0)
        self.currency_symbol_input.setText("$")
        
        # Configuración de impresión
        self.receipt_header_input.setText("MI TIENDA\nCalle Principal #123\nTel: 123-456-7890")
        self.receipt_footer_input.setText("¡Gracias por su compra!\nVuelva pronto")
        
        # Otras configuraciones
        self.auto_backup_checkbox.setChecked(True)
        self.backup_frequency_combo.setCurrentIndex(0)  # Diariamente
    
    def load_sample_backups(self):
        """Cargar copias de seguridad de ejemplo (para demostración)"""
        # Limpiar tabla
        self.backups_table.setRowCount(0)
        
        # Datos de ejemplo
        backups = [
            {"name": "backup_20250410_120000.bak", "date": "10/04/2025 12:00:00", "size": "2.5 MB"},
            {"name": "backup_20250409_120000.bak", "date": "09/04/2025 12:00:00", "size": "2.4 MB"},
            {"name": "backup_20250408_120000.bak", "date": "08/04/2025 12:00:00", "size": "2.3 MB"}
        ]
        
        # Agregar datos a la tabla
        for backup in backups:
            row_position = self.backups_table.rowCount()
            self.backups_table.insertRow(row_position)
            
            # Nombre
            name_item = QTableWidgetItem(backup["name"])
            self.backups_table.setItem(row_position, 0, name_item)
            
            # Fecha
            date_item = QTableWidgetItem(backup["date"])
            date_item.setTextAlignment(Qt.AlignCenter)
            self.backups_table.setItem(row_position, 1, date_item)
            
            # Tamaño
            size_item = QTableWidgetItem(backup["size"])
            size_item.setTextAlignment(Qt.AlignCenter)
            self.backups_table.setItem(row_position, 2, size_item)
            
            # Botones de acción
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            restore_button = QPushButton("Restaurar")
            restore_button.setProperty("backup_name", backup["name"])
            restore_button.clicked.connect(lambda checked, name=backup["name"]: self.confirm_restore_backup(name))
            
            delete_button = QPushButton("Eliminar")
            delete_button.setProperty("backup_name", backup["name"])
            delete_button.clicked.connect(lambda checked, name=backup["name"]: self.confirm_delete_backup(name))
            
            actions_layout.addWidget(restore_button)
            actions_layout.addWidget(delete_button)
            
            self.backups_table.setCellWidget(row_position, 3, actions_widget)
    
    def load_sample_log(self):
        """Cargar log de ejemplo (para demostración)"""
        log_content = """2025-04-14 08:00:00 INFO - Sistema iniciado
2025-04-14 08:05:23 INFO - Usuario admin ha iniciado sesión
2025-04-14 08:10:45 INFO - Venta #1001 registrada por admin, total: $150.75
2025-04-14 08:15:32 INFO - Venta #1002 registrada por admin, total: $75.50
2025-04-14 08:20:18 WARNING - Producto con ID 56 tiene stock bajo (2 unidades)
2025-04-14 08:25:41 INFO - Usuario cajero1 ha iniciado sesión
2025-04-14 08:30:12 INFO - Venta #1003 registrada por cajero1, total: $210.25
2025-04-14 08:35:04 ERROR - Error al conectar con la impresora
2025-04-14 08:40:37 INFO - Impresora reconectada
2025-04-14 08:45:22 INFO - Venta #1004 registrada por cajero1, total: $45.00
2025-04-14 08:50:15 INFO - Usuario cajero1 ha cerrado sesión
2025-04-14 08:55:30 INFO - Copia de seguridad realizada: backup_20250414_085530.bak"""
        
        self.log_text.setText(log_content)
    
    def show_new_user_dialog(self):
        """Mostrar diálogo para crear un nuevo usuario"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Usuario")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Formulario
        form_layout = QFormLayout()
        
        username_input = QLineEdit()
        username_input.setPlaceholderText("Nombre de usuario")
        
        password_input = QLineEdit()
        password_input.setPlaceholderText("Contraseña")
        password_input.setEchoMode(QLineEdit.Password)
        
        confirm_password_input = QLineEdit()
        confirm_password_input.setPlaceholderText("Confirmar contraseña")
        confirm_password_input.setEchoMode(QLineEdit.Password)
        
        fullname_input = QLineEdit()
        fullname_input.setPlaceholderText("Nombre completo")
        
        role_combo = QComboBox()
        role_combo.addItems(["admin", "manager", "cashier"])
        
        active_checkbox = QCheckBox("Usuario activo")
        active_checkbox.setChecked(True)
        
        form_layout.addRow("Nombre de usuario:", username_input)
        form_layout.addRow("Contraseña:", password_input)
        form_layout.addRow("Confirmar contraseña:", confirm_password_input)
        form_layout.addRow("Nombre completo:", fullname_input)
        form_layout.addRow("Rol:", role_combo)
        form_layout.addRow("", active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        
        # Mostrar diálogo
        if dialog.exec() == QDialog.Accepted:
            # Verificar contraseñas
            if password_input.text() != confirm_password_input.text():
                QMessageBox.warning(self, "Error", "Las contraseñas no coinciden")
                return
                
            # Verificar campos obligatorios
            if not username_input.text() or not password_input.text() or not fullname_input.text():
                QMessageBox.warning(self, "Error", "Todos los campos son obligatorios")
                return
                
            # Crear usuario
            user_data = {
                "username": username_input.text(),
                "password": password_input.text(),
                "full_name": fullname_input.text(),
                "role": role_combo.currentText(),
                "is_active": active_checkbox.isChecked()
            }
            
            # Emitir señal (en un sistema real, esto invocaría al controlador)
            self.user_created.emit(user_data)
            
            # Para demostración, recargar los usuarios
            self.load_sample_users()
            
            QMessageBox.information(self, "Usuario Creado", f"Usuario '{user_data['username']}' creado correctamente")
    
    def show_edit_user_dialog(self, user_id):
        """
        Mostrar diálogo para editar un usuario existente
        
        Args:
            user_id: ID del usuario a editar
        """
        # En un sistema real, obtendríamos los datos del usuario desde el controlador
        # Para demostración, usamos datos de ejemplo
        user_data = None
        for row in range(self.users_table.rowCount()):
            if self.users_table.item(row, 0).text() == str(user_id):
                user_data = {
                    "user_id": user_id,
                    "username": self.users_table.item(row, 1).text(),
                    "full_name": self.users_table.item(row, 2).text(),
                    "role": self.users_table.item(row, 3).text(),
                    "is_active": True
                }
                break
                
        if not user_data:
            QMessageBox.warning(self, "Error", f"Usuario con ID {user_id} no encontrado")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Editar Usuario: {user_data['username']}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Formulario
        form_layout = QFormLayout()
        
        username_input = QLineEdit(user_data["username"])
        username_input.setReadOnly(True)  # No permitir cambiar el nombre de usuario
        
        password_input = QLineEdit()
        password_input.setPlaceholderText("Nueva contraseña (dejar en blanco para mantener)")
        password_input.setEchoMode(QLineEdit.Password)
        
        confirm_password_input = QLineEdit()
        confirm_password_input.setPlaceholderText("Confirmar nueva contraseña")
        confirm_password_input.setEchoMode(QLineEdit.Password)
        
        fullname_input = QLineEdit(user_data["full_name"])
        
        role_combo = QComboBox()
        role_combo.addItems(["admin", "manager", "cashier"])
        role_combo.setCurrentText(user_data["role"])
        
        active_checkbox = QCheckBox("Usuario activo")
        active_checkbox.setChecked(user_data["is_active"])
        
        form_layout.addRow("Nombre de usuario:", username_input)
        form_layout.addRow("Nueva contraseña:", password_input)
        form_layout.addRow("Confirmar contraseña:", confirm_password_input)
        form_layout.addRow("Nombre completo:", fullname_input)
        form_layout.addRow("Rol:", role_combo)
        form_layout.addRow("", active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        
        # Mostrar diálogo
        if dialog.exec() == QDialog.Accepted:
            # Verificar contraseñas si se van a cambiar
            if password_input.text():
                if password_input.text() != confirm_password_input.text():
                    QMessageBox.warning(self, "Error", "Las contraseñas no coinciden")
                    return
                    
            # Verificar campos obligatorios
            if not fullname_input.text():
                QMessageBox.warning(self, "Error", "El nombre completo es obligatorio")
                return
                
            # Actualizar usuario
            updated_data = {
                "full_name": fullname_input.text(),
                "role": role_combo.currentText(),
                "is_active": active_checkbox.isChecked()
            }
            
            # Agregar contraseña si se va a cambiar
            if password_input.text():
                updated_data["password"] = password_input.text()
                
            # Emitir señal (en un sistema real, esto invocaría al controlador)
            self.user_updated.emit(user_id, updated_data)
            
            # Para demostración, recargar los usuarios
            self.load_sample_users()
            
            QMessageBox.information(self, "Usuario Actualizado", f"Usuario '{user_data['username']}' actualizado correctamente")
    
    def confirm_delete_user(self, user_id):
        """
        Confirmar eliminación de un usuario
        
        Args:
            user_id: ID del usuario a eliminar
        """
        # Obtener nombre de usuario
        username = ""
        for row in range(self.users_table.rowCount()):
            if self.users_table.item(row, 0).text() == str(user_id):
                username = self.users_table.item(row, 1).text()
                break
                
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el usuario '{username}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Emitir señal (en un sistema real, esto invocaría al controlador)
            self.user_deleted.emit(user_id)
            
            # Para demostración, recargar los usuarios
            self.load_sample_users()
            
            QMessageBox.information(self, "Usuario Eliminado", f"Usuario '{username}' eliminado correctamente")
    
    def save_settings(self):
        """Guardar configuración del sistema"""
        # Recopilar datos de configuración
        settings_data = {
            "store_name": self.store_name_input.text(),
            "store_address": self.store_address_input.text(),
            "store_phone": self.store_phone_input.text(),
            "tax_rate": self.tax_rate_input.value() / 100,  # Convertir a decimal
            "currency_symbol": self.currency_symbol_input.text(),
            "receipt_header": self.receipt_header_input.toPlainText(),
            "receipt_footer": self.receipt_footer_input.toPlainText(),
            "auto_backup": self.auto_backup_checkbox.isChecked(),
            "backup_frequency": self.backup_frequency_combo.currentText().lower()
        }
        
        # Validar datos
        if not settings_data["store_name"]:
            QMessageBox.warning(self, "Error", "El nombre de la tienda es obligatorio")
            return
            
        # Emitir señal (en un sistema real, esto invocaría al controlador)
        self.settings_updated.emit(settings_data)
        
        QMessageBox.information(self, "Configuración Guardada", "La configuración se ha guardado correctamente")
    
    def restore_default_settings(self):
        """Restaurar configuración por defecto"""
        reply = QMessageBox.question(
            self,
            "Confirmar Restauración",
            "¿Está seguro de que desea restaurar la configuración a los valores por defecto?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Cargar configuración por defecto
            self.load_sample_settings()
            
            QMessageBox.information(self, "Configuración Restaurada", "La configuración se ha restaurado a los valores por defecto")
    
    def create_backup(self):
        """Crear una copia de seguridad"""
        # Mostrar diálogo para seleccionar ubicación (opcional)
        backup_path = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar ubicación para la copia de seguridad",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        
        if not backup_path:
            return
            
        # Emitir señal (en un sistema real, esto invocaría al controlador)
        self.backup_requested.emit(backup_path)
        
        # Para demostración, recargar las copias de seguridad
        self.load_sample_backups()
        
        QMessageBox.information(self, "Copia de Seguridad", "Copia de seguridad creada correctamente")
    
    def restore_backup(self):
        """Restaurar una copia de seguridad"""
        # Mostrar diálogo para seleccionar archivo
        backup_file, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de copia de seguridad",
            os.path.expanduser("~"),
            "Archivos de copia de seguridad (*.bak)"
        )
        
        if not backup_file:
            return
            
        # Confirmar restauración
        reply = QMessageBox.warning(
            self,
            "Confirmar Restauración",
            "¡ADVERTENCIA! Restaurar una copia de seguridad sobrescribirá todos los datos actuales. "
            "Esta acción no se puede deshacer.\n\n"
            "¿Está seguro de que desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Emitir señal (en un sistema real, esto invocaría al controlador)
            self.restore_requested.emit(backup_file)
            
            QMessageBox.information(
                self,
                "Restauración Completada",
                "La copia de seguridad se ha restaurado correctamente.\n"
                "El sistema se reiniciará para aplicar los cambios."
            )
    
    def confirm_restore_backup(self, backup_name):
        """
        Confirmar restauración de una copia de seguridad específica
        
        Args:
            backup_name: Nombre del archivo de copia de seguridad
        """
        reply = QMessageBox.warning(
            self,
            "Confirmar Restauración",
            f"¡ADVERTENCIA! Restaurar la copia de seguridad '{backup_name}' sobrescribirá todos los datos actuales. "
            "Esta acción no se puede deshacer.\n\n"
            "¿Está seguro de que desea continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # En un sistema real, obtendríamos la ruta completa del archivo
            backup_path = f"/ruta/a/backups/{backup_name}"
            
            # Emitir señal (en un sistema real, esto invocaría al controlador)
            self.restore_requested.emit(backup_path)
            
            QMessageBox.information(
                self,
                "Restauración Completada",
                "La copia de seguridad se ha restaurado correctamente.\n"
                "El sistema se reiniciará para aplicar los cambios."
            )
    
    def confirm_delete_backup(self, backup_name):
        """
        Confirmar eliminación de una copia de seguridad
        
        Args:
            backup_name: Nombre del archivo de copia de seguridad
        """
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar la copia de seguridad '{backup_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # En un sistema real, eliminaríamos el archivo
            
            # Para demostración, recargar las copias de seguridad
            self.load_sample_backups()
            
            QMessageBox.information(self, "Copia Eliminada", f"Copia de seguridad '{backup_name}' eliminada correctamente")
    
    def refresh_log(self):
        """Actualizar contenido del log"""
        # En un sistema real, obtendríamos el contenido actualizado del archivo de log
        
        # Para demostración, simular una actualización
        current_log = self.log_text.toPlainText()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = f"\n{timestamp} INFO - Log actualizado manualmente"
        
        self.log_text.setText(current_log + new_entry)
    
    def export_log(self):
        """Exportar log a un archivo"""
        # Mostrar diálogo para guardar archivo
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Log",
            os.path.expanduser("~") + "/log_sistema.txt",
            "Archivos de texto (*.txt)"
        )
        
        if not file_path:
            return
            
        try:
            # Guardar contenido del log en el archivo
            with open(file_path, 'w') as f:
                f.write(self.log_text.toPlainText())
                
            QMessageBox.information(self, "Log Exportado", f"El log se ha exportado correctamente a:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar el log:\n{str(e)}")