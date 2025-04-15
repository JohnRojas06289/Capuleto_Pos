# app/main.py
import sys
import os
import json
from datetime import datetime
from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer

# Importar componentes del sistema
from views.login_view import LoginView
from views.pos_view import POSView
from views.admin_view import AdminView
from controllers.user_controller import UserController
from controllers.sales_controller import SalesController
from controllers.product_controller import ProductController
from models.database import Database
from devices.barcode_scanner import BarcodeScanner
from devices.thermal_printer import ThermalPrinter
from devices.cash_drawer import CashDrawer
from utils.config import Config
from utils.logger import setup_logger

class POSApplication:
    """Aplicación principal del sistema POS"""
    
    def __init__(self):
        # Inicializar la aplicación Qt
        self.app = QApplication(sys.argv)
        
        # Configurar el tema de la aplicación
        self.app.setStyle("Fusion")
        
        # Mostrar pantalla de carga
        self.show_splash()
        
        # Inicializar el logger
        self.logger = setup_logger()
        self.logger.info("Iniciando sistema POS")
        
        # Cargar configuración
        self.config = Config()
        self.config.load_config()
        
        # Conectar a la base de datos
        self.init_database()
        
        # Inicializar controladores
        self.init_controllers()
        
        # Inicializar dispositivos
        self.init_devices()
        
        # Inicializar vistas
        self.init_views()
        
        # Conectar señales
        self.connect_signals()
        
        # Timer para cerrar splash después de 2 segundos
        QTimer.singleShot(2000, self.show_login)
    
    def show_splash(self):
        """Mostrar pantalla de carga"""
        # Ruta al archivo de splash
        splash_path = os.path.join(os.path.dirname(__file__), "../resources/icons/splash.png")
        
        # Si no existe el archivo, crear un splash vacío
        if not os.path.exists(splash_path):
            self.splash = QSplashScreen(QPixmap(400, 300))
            self.splash.showMessage("Cargando Sistema POS...", 
                                   Qt.AlignCenter | Qt.AlignBottom, Qt.white)
        else:
            self.splash = QSplashScreen(QPixmap(splash_path))
        
        self.splash.show()
        self.app.processEvents()
    
    def init_database(self):
        """Inicializar conexión a base de datos"""
        try:
            db_path = self.config.get("database_path", "../database/pos_database.db")
            self.database = Database(db_path)
            self.database.connect()
            
            # Verificar si se necesita inicializar la base de datos
            if self.database.is_new_database():
                self.logger.info("Nueva base de datos detectada, inicializando...")
                self.database.init_schema()
        except Exception as e:
            self.logger.error(f"Error al conectar a la base de datos: {e}")
            QMessageBox.critical(None, "Error de base de datos", 
                               f"No se pudo conectar a la base de datos: {e}")
            sys.exit(1)
    
    def init_controllers(self):
        """Inicializar controladores del sistema"""
        self.user_controller = UserController(self.database)
        self.sales_controller = SalesController(self.database)
        self.product_controller = ProductController(self.database)
    
    def init_devices(self):
        """Inicializar dispositivos de hardware"""
        # Cargar configuraciones de dispositivos
        device_config_path = os.path.join(os.path.dirname(__file__), 
                                         "../config/device_config.json")
        device_config = {}
        
        if os.path.exists(device_config_path):
            try:
                with open(device_config_path, 'r') as f:
                    device_config = json.load(f)
            except Exception as e:
                self.logger.error(f"Error al cargar configuración de dispositivos: {e}")
        
        # Inicializar dispositivos
        try:
            self.barcode_scanner = BarcodeScanner(device_config.get('barcode_scanner'))
            self.thermal_printer = ThermalPrinter(device_config.get('thermal_printer'))
            self.cash_drawer = CashDrawer(device_config.get('cash_drawer'))
            
            # Conectar dispositivos
            scanner_ok = self.barcode_scanner.connect()
            printer_ok = self.thermal_printer.connect()
            
            # La caja registradora suele conectarse a través de la impresora
            self.cash_drawer.set_printer(self.thermal_printer)
            drawer_ok = self.cash_drawer.connect()
            
            self.logger.info(f"Estado de dispositivos - Scanner: {scanner_ok}, " +
                           f"Impresora: {printer_ok}, Caja: {drawer_ok}")
        
        except Exception as e:
            self.logger.error(f"Error al inicializar dispositivos: {e}")
    
    def init_views(self):
        """Inicializar vistas de la aplicación"""
        self.login_view = LoginView()
        self.pos_view = POSView()
        self.admin_view = AdminView()
        
        # Configurar vistas
        store_name = self.config.get("store_name", "Mi Tienda")
        self.pos_view.setWindowTitle(f"Sistema POS - {store_name}")
    
    def connect_signals(self):
        """Conectar señales entre componentes"""
        # Login
        self.login_view.login_successful.connect(self.on_login_successful)
        
        # POS View
        self.pos_view.barcode_scanned.connect(self.on_barcode_scanned)
        self.pos_view.product_selected.connect(self.on_product_selected)
        self.pos_view.checkout_requested.connect(self.on_checkout)
        self.pos_view.open_drawer_requested.connect(self.open_cash_drawer)
        
        # Escaneo de código de barras
        if self.barcode_scanner.is_connected:
            self.barcode_scanner.start_listening(self.on_barcode_scanned)
    
    def show_login(self):
        """Mostrar pantalla de inicio de sesión"""
        self.splash.finish(self.login_view)
        self.login_view.show()
    
    def on_login_successful(self, user_data):
        """Manejar inicio de sesión exitoso"""
        self.current_user = user_data
        self.logger.info(f"Usuario {user_data['username']} ha iniciado sesión")
        
        # Actualizar información del cajero en la vista POS
        self.pos_view.cashier_label.setText(f"Cajero: {user_data['full_name']}")
        
        # Actualizar fecha
        current_date = datetime.now().strftime("%d/%m/%Y")
        self.pos_view.date_label.setText(f"Fecha: {current_date}")
        
        # Mostrar vista según el rol del usuario
        if user_data['role'] == 'admin':
            self.admin_view.show()
        else:
            self.pos_view.show()
        
        self.login_view.hide()
    
    def on_barcode_scanned(self, barcode):
        """Manejar escaneo de código de barras"""
        self.logger.info(f"Código escaneado: {barcode}")
        
        # Buscar producto por código de barras
        product = self.product_controller.get_product_by_barcode(barcode)
        
        if product:
            # Añadir al carrito
            self.pos_view.add_product_to_cart(product)
        else:
            # Producto no encontrado
            QMessageBox.warning(self.pos_view, "Producto no encontrado", 
                              f"No se encontró un producto con el código: {barcode}")
    
    def on_product_selected(self, product_id):
        """Manejar selección de producto desde la interfaz"""
        product = self.product_controller.get_product_by_id(product_id)
        
        if product:
            self.pos_view.add_product_to_cart(product)
    
    def on_checkout(self, sale_data):
        """Procesar venta"""
        try:
            # Registrar la venta en la base de datos
            sale_id = self.sales_controller.create_sale(
                user_id=self.current_user['user_id'],
                items=sale_data['items'],
                payment_method=sale_data['payment']['method'],
                total_amount=float(sale_data['total'].replace('$', '')),
                tax_amount=float(sale_data['tax'].replace('$', ''))
            )
            
            if sale_id:
                # Preparar datos para el recibo
                receipt_data = {
                    'store_name': self.config.get("store_name", "Mi Tienda"),
                    'store_address': self.config.get("store_address", ""),
                    'store_phone': self.config.get("store_phone", ""),
                    'date': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    'receipt_number': str(sale_id),
                    'cashier_name': self.current_user['full_name'],
                    'items': sale_data['items'],
                    'subtotal': sale_data['subtotal'],
                    'tax': sale_data['tax'],
                    'total': sale_data['total'],
                    'payment_method': sale_data['payment']['method']
                }
                
                # Si es pago en efectivo, agregar información de cambio
                if sale_data['payment']['method'] == 'Efectivo':
                    receipt_data['amount_received'] = sale_data['payment'].get('amount_received', '0.00')
                    receipt_data['change'] = sale_data['payment'].get('change', '$0.00')
                
                # Imprimir recibo
                self.print_receipt(receipt_data)
                
                # Abrir caja registradora
                self.open_cash_drawer()
                
                # Limpiar carrito
                self.pos_view.clear_cart()
                
                # Mostrar mensaje de éxito
                QMessageBox.information(self.pos_view, "Venta completada", 
                                      f"Venta #{sale_id} registrada correctamente.")
            else:
                raise Exception("No se pudo registrar la venta")
                
        except Exception as e:
            self.logger.error(f"Error al procesar la venta: {e}")
            QMessageBox.critical(self.pos_view, "Error en la venta", 
                               f"No se pudo completar la venta: {e}")
    
    def print_receipt(self, receipt_data):
        """Imprimir recibo"""
        try:
            if self.thermal_printer.connect():
                self.thermal_printer.print_receipt(receipt_data)
                self.logger.info(f"Recibo impreso para la venta #{receipt_data['receipt_number']}")
                return True
            else:
                self.logger.warning("No se pudo conectar con la impresora")
                return False
        except Exception as e:
            self.logger.error(f"Error al imprimir recibo: {e}")
            return False
    
    def open_cash_drawer(self):
        """Abrir la caja registradora"""
        try:
            if self.cash_drawer.connect():
                result = self.cash_drawer.open_drawer()
                if result:
                    self.logger.info("Caja registradora abierta")
                else:
                    self.logger.warning("No se pudo abrir la caja registradora")
                return result
            else:
                self.logger.warning("No se pudo conectar con la caja registradora")
                return False
        except Exception as e:
            self.logger.error(f"Error al abrir la caja: {e}")
            return False
    
    def run(self):
        """Ejecutar la aplicación"""
        return self.app.exec()


# Punto de entrada al programa
if __name__ == "__main__":
    # Crear y ejecutar la aplicación
    pos_app = POSApplication()
    sys.exit(pos_app.run())