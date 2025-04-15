# tests/test_devices.py
import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Agregar el directorio raíz al path para importar los módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.devices.barcode_scanner import BarcodeScanner
from app.devices.thermal_printer import ThermalPrinter
from app.devices.cash_drawer import CashDrawer

class TestBarcodeScanner(unittest.TestCase):
    """Pruebas para el controlador de lector de códigos de barras"""
    
    def test_init_without_config(self):
        """Probar inicialización sin configuración"""
        # Crear mock para auto_detect
        with patch.object(BarcodeScanner, 'auto_detect') as mock_auto_detect:
            scanner = BarcodeScanner()
            
            # Verificar que se llamó auto_detect
            mock_auto_detect.assert_called_once()
            
            # Verificar estados iniciales
            self.assertFalse(scanner.is_connected)
            self.assertIsNone(scanner.device)
    
    def test_init_with_config(self):
        """Probar inicialización con configuración"""
        # Configuración de prueba
        config = {
            'device_path': '/dev/test'
        }
        
        # Crear mock para auto_detect
        with patch.object(BarcodeScanner, 'auto_detect') as mock_auto_detect:
            scanner = BarcodeScanner(config)
            
            # Verificar que no se llamó auto_detect
            mock_auto_detect.assert_not_called()
            
            # Verificar que se usó la configuración
            self.assertEqual(scanner.device_path, '/dev/test')
    
    @patch('evdev.InputDevice')
    @patch('evdev.list_devices')
    def test_auto_detect(self, mock_list_devices, mock_input_device):
        """Probar detección automática"""
        # Configurar mocks
        mock_list_devices.return_value = ['/dev/input/event0', '/dev/input/event1']
        
        # Crear dispositivos simulados
        mock_device1 = MagicMock()
        mock_device1.name = 'Test Keyboard'
        
        mock_device2 = MagicMock()
        mock_device2.name = 'Barcode Scanner S10'
        mock_device2.path = '/dev/input/event1'
        
        # Configurar el retorno del constructor de InputDevice
        mock_input_device.side_effect = [mock_device1, mock_device2]
        
        # Probar la detección
        scanner = BarcodeScanner()
        scanner.auto_detect()
        
        # Verificar que se encontró el dispositivo correcto
        self.assertEqual(scanner.device_path, '/dev/input/event1')
    
    @patch('evdev.InputDevice')
    def test_connect_success(self, mock_input_device):
        """Probar conexión exitosa"""
        # Configurar mock
        mock_device = MagicMock()
        mock_input_device.return_value = mock_device
        
        # Crear scanner con device_path
        scanner = BarcodeScanner({'device_path': '/dev/test'})
        
        # Probar conexión
        result = scanner.connect()
        
        # Verificar resultado
        self.assertTrue(result)
        self.assertTrue(scanner.is_connected)
        self.assertEqual(scanner.device, mock_device)
        
        # Verificar que se llamó al constructor
        mock_input_device.assert_called_once_with('/dev/test')
    
    @patch('evdev.InputDevice')
    def test_connect_failure(self, mock_input_device):
        """Probar conexión fallida"""
        # Configurar mock para lanzar una excepción
        mock_input_device.side_effect = Exception("Test error")
        
        # Crear scanner con device_path
        scanner = BarcodeScanner({'device_path': '/dev/test'})
        
        # Probar conexión
        result = scanner.connect()
        
        # Verificar resultado
        self.assertFalse(result)
        self.assertFalse(scanner.is_connected)
        self.assertIsNone(scanner.device)
    
    @patch('threading.Thread')
    def test_start_listening(self, mock_thread):
        """Probar inicio de escucha"""
        # Crear mock para connect
        with patch.object(BarcodeScanner, 'connect', return_value=True) as mock_connect:
            # Crear scanner
            scanner = BarcodeScanner({'device_path': '/dev/test'})
            scanner.is_connected = True
            
            # Callback de prueba
            mock_callback = MagicMock()
            
            # Probar inicio de escucha
            result = scanner.start_listening(mock_callback)
            
            # Verificar resultado
            self.assertTrue(result)
            self.assertEqual(scanner.callback, mock_callback)
            self.assertTrue(scanner.running)
            
            # Verificar que se creó e inició el hilo
            mock_thread.assert_called_once()
            mock_thread.return_value.start.assert_called_once()
    
    def test_stop_listening(self):
        """Probar detención de escucha"""
        # Crear scanner
        scanner = BarcodeScanner()
        scanner.running = True
        
        # Crear mock para el hilo
        scanner.listener_thread = MagicMock()
        
        # Probar detención
        scanner.stop_listening()
        
        # Verificar estado
        self.assertFalse(scanner.running)
        
        # Verificar que se llamó join en el hilo
        scanner.listener_thread.join.assert_called_once()


class TestThermalPrinter(unittest.TestCase):
    """Pruebas para el controlador de impresora térmica"""
    
    def test_init_without_config(self):
        """Probar inicialización sin configuración"""
        # Crear mock para auto_detect_cups
        with patch.object(ThermalPrinter, '_auto_detect') as mock_auto_detect:
            printer = ThermalPrinter()
            
            # Verificar que se llamó auto_detect
            mock_auto_detect.assert_called_once()
            
            # Verificar estados iniciales
            self.assertEqual(printer.connection_type, 'cups')
            self.assertIsNone(printer.printer_name)
            self.assertIsNone(printer.printer)
    
    def test_init_with_config(self):
        """Probar inicialización con configuración"""
        # Configuración de prueba
        config = {
            'connection_type': 'usb',
            'usb_vendor_id': '0x1234',
            'usb_product_id': '0x5678'
        }
        
        # Crear mock para auto_detect
        with patch.object(ThermalPrinter, '_auto_detect') as mock_auto_detect:
            printer = ThermalPrinter(config)
            
            # Verificar que no se llamó auto_detect
            mock_auto_detect.assert_not_called()
            
            # Verificar que se usó la configuración
            self.assertEqual(printer.connection_type, 'usb')
            self.assertEqual(printer.usb_vendor_id, '0x1234')
            self.assertEqual(printer.usb_product_id, '0x5678')
    
    @patch('cups.Connection')
    def test_auto_detect_cups(self, mock_cups_connection):
        """Probar detección automática de impresora CUPS"""
        # Configurar mocks
        mock_connection = MagicMock()
        mock_connection.getPrinters.return_value = {
            'printer1': {'device-uri': 'usb://Generic/Regular-Printer'},
            'WPRP-260': {'device-uri': 'usb://WPRP/Thermal-Printer'},
            'printer3': {'device-uri': 'usb://Another/Printer'}
        }
        mock_cups_connection.return_value = mock_connection
        
        # Crear impresora
        printer = ThermalPrinter()
        printer._auto_detect()
        
        # Verificar que se encontró la impresora correcta
        self.assertEqual(printer.printer_name, 'WPRP-260')
    
    @patch('cups.Connection')
    def test_connect_cups_success(self, mock_cups_connection):
        """Probar conexión CUPS exitosa"""
        # Configurar mocks
        mock_connection = MagicMock()
        mock_connection.getPrinters.return_value = {'WPRP-260': {}}
        mock_cups_connection.return_value = mock_connection
        
        # Crear impresora
        printer = ThermalPrinter({'connection_type': 'cups', 'printer_name': 'WPRP-260'})
        
        # Probar conexión
        result = printer.connect()
        
        # Verificar resultado
        self.assertTrue(result)
    
    @patch('cups.Connection')
    def test_connect_cups_failure(self, mock_cups_connection):
        """Probar conexión CUPS fallida"""
        # Configurar mocks
        mock_connection = MagicMock()
        mock_connection.getPrinters.return_value = {'OtherPrinter': {}}
        mock_cups_connection.return_value = mock_connection
        
        # Crear impresora
        printer = ThermalPrinter({'connection_type': 'cups', 'printer_name': 'WPRP-260'})
        
        # Probar conexión
        result = printer.connect()
        
        # Verificar resultado
        self.assertFalse(result)
    
    @patch('cups.Connection')
    def test_print_receipt_cups(self, mock_cups_connection):
        """Probar impresión de recibo usando CUPS"""
        # Configurar mocks
        mock_connection = MagicMock()
        mock_connection.printFile.return_value = 123  # Job ID
        mock_cups_connection.return_value = mock_connection
        
        # Crear impresora
        printer = ThermalPrinter({'connection_type': 'cups', 'printer_name': 'WPRP-260'})
        
        # Datos de recibo de prueba
        receipt_data = {
            'store_name': 'Test Store',
            'store_address': 'Test Address',
            'store_phone': '123-456-7890',
            'date': '2025-04-14 10:00:00',
            'receipt_number': '1001',
            'cashier_name': 'Test Cashier',
            'items': [
                {'name': 'Product 1', 'quantity': 2, 'price': 10.0, 'subtotal': 20.0},
                {'name': 'Product 2', 'quantity': 1, 'price': 15.0, 'subtotal': 15.0}
            ],
            'subtotal': 35.0,
            'tax': 5.6,
            'total': 40.6,
            'payment_method': 'cash',
            'text': 'Test receipt content'
        }
        
        # Probar impresión
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            with patch('os.unlink') as mock_unlink:
                result = printer._print_cups(receipt_data)
                
                # Verificar resultado
                self.assertTrue(result)
                
                # Verificar que se llamó a printFile
                mock_connection.printFile.assert_called_once()
                
                # Verificar que se creó y eliminó el archivo temporal
                mock_file.assert_called_once()
                mock_unlink.assert_called_once()
    
    def test_format_receipt_text(self):
        """Probar formateo de texto del recibo"""
        # Crear impresora
        printer = ThermalPrinter()
        
        # Datos de recibo de prueba
        receipt_data = {
            'store_name': 'Test Store',
            'store_address': 'Test Address',
            'store_phone': '123-456-7890',
            'date': '2025-04-14 10:00:00',
            'receipt_number': '1001',
            'cashier_name': 'Test Cashier',
            'items': [
                {'name': 'Product 1', 'quantity': 2, 'price': 10.0, 'subtotal': 20.0},
                {'name': 'Product 2', 'quantity': 1, 'price': 15.0, 'subtotal': 15.0}
            ],
            'subtotal': 35.0,
            'tax': 5.6,
            'total': 40.6,
            'payment_method': 'cash'
        }
        
        # Formatear recibo
        formatted_text = printer._format_receipt_text(receipt_data)
        
        # Verificar contenido
        self.assertIn('Test Store', formatted_text)
        self.assertIn('Test Address', formatted_text)
        self.assertIn('Product 1', formatted_text)
        self.assertIn('Product 2', formatted_text)
        self.assertIn('SUBTOTAL', formatted_text)
        self.assertIn('TOTAL', formatted_text)
    
    @patch('cups.Connection')
    def test_open_cash_drawer(self, mock_cups_connection):
        """Probar apertura del cajón de dinero"""
        # Configurar mocks
        mock_connection = MagicMock()
        mock_connection.printFile.return_value = 123  # Job ID
        mock_cups_connection.return_value = mock_connection
        
        # Crear impresora
        printer = ThermalPrinter({'connection_type': 'cups', 'printer_name': 'WPRP-260'})
        
        # Probar apertura del cajón
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            with patch('os.unlink') as mock_unlink:
                result = printer.open_cash_drawer()
                
                # Verificar resultado
                self.assertTrue(result)
                
                # Verificar que se llamó a printFile
                mock_connection.printFile.assert_called_once()
                
                # Verificar que se creó y eliminó el archivo temporal
                mock_file.assert_called_once()
                mock_unlink.assert_called_once()


class TestCashDrawer(unittest.TestCase):
    """Pruebas para el controlador de caja de dinero"""
    
    def test_init_without_config(self):
        """Probar inicialización sin configuración"""
        drawer = CashDrawer()
        
        # Verificar estados iniciales
        self.assertEqual(drawer.connection_type, 'printer')
        self.assertIsNone(drawer.printer)
        self.assertFalse(drawer.is_connected)
    
    def test_init_with_config(self):
        """Probar inicialización con configuración"""
        # Configuración de prueba
        config = {
            'connection_type': 'serial',
            'serial_port': '/dev/ttyS0',
            'serial_baudrate': 9600
        }
        
        drawer = CashDrawer(config)
        
        # Verificar que se usó la configuración
        self.assertEqual(drawer.connection_type, 'serial')
        self.assertEqual(drawer.serial_port, '/dev/ttyS0')
        self.assertEqual(drawer.serial_baudrate, 9600)
    
    def test_set_printer(self):
        """Probar establecimiento de la impresora"""
        # Crear caja
        drawer = CashDrawer()
        
        # Crear mock de impresora
        mock_printer = MagicMock()
        
        # Establecer impresora
        drawer.set_printer(mock_printer)
        
        # Verificar que se guardó la referencia
        self.assertEqual(drawer.printer, mock_printer)
        
        # Verificar que se estableció la conexión si el tipo es 'printer'
        self.assertTrue(drawer.is_connected)
    
    def test_connect_printer(self):
        """Probar conexión a través de la impresora"""
        # Crear caja
        drawer = CashDrawer()
        
        # Crear mock de impresora
        mock_printer = MagicMock()
        drawer.printer = mock_printer
        
        # Probar conexión
        result = drawer.connect()
        
        # Verificar resultado
        self.assertTrue(result)
        self.assertTrue(drawer.is_connected)
    
    @patch('serial.Serial')
    def test_connect_serial(self, mock_serial):
        """Probar conexión serial"""
        # Crear caja
        drawer = CashDrawer({
            'connection_type': 'serial',
            'serial_port': '/dev/ttyS0',
            'serial_baudrate': 9600
        })
        
        # Probar conexión
        result = drawer._connect_serial()
        
        # Verificar resultado
        self.assertTrue(result)
        self.assertTrue(drawer.is_connected)
        
        # Verificar que se llamó al constructor de Serial
        mock_serial.assert_called_once_with(
            port='/dev/ttyS0',
            baudrate=9600,
            timeout=1
        )
    
    def test_open_drawer_printer(self):
        """Probar apertura del cajón a través de la impresora"""
        # Crear caja
        drawer = CashDrawer()
        drawer.is_connected = True
        
        # Crear mock de impresora
        mock_printer = MagicMock()
        mock_printer.open_cash_drawer.return_value = True
        drawer.printer = mock_printer
        
        # Probar apertura
        result = drawer._open_via_printer()
        
        # Verificar resultado
        self.assertTrue(result)
        
        # Verificar que se llamó al método de la impresora
        mock_printer.open_cash_drawer.assert_called_once()
    
    def test_get_open_command(self):
        """Probar obtención del comando para abrir el cajón"""
        # Crear caja
        drawer = CashDrawer()
        
        # Obtener comando
        command = drawer._get_open_command()
        
        # Verificar que es un comando ESC/POS válido
        self.assertEqual(command[0], 0x1B)  # ESC
        self.assertEqual(command[1], 0x70)  # p
        self.assertEqual(len(command), 5)   # ESC p m t1 t2

if __name__ == '__main__':
    unittest.main()