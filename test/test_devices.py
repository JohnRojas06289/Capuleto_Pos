# tests/test_devices.py
import unittest
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# Agregar directorio raíz al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar dispositivos
from app.devices.barcode_scanner import BarcodeScanner
from app.devices.thermal_printer import ThermalPrinter
from app.devices.cash_drawer import CashDrawer

class TestBarcodeScanner(unittest.TestCase):
    """Pruebas para el controlador de lectora de código de barras"""
    
    def setUp(self):
        """Configuración para cada prueba"""
        # Configuración de prueba
        self.test_config = {
            'device_path': '/dev/input/mock_scanner',
            'auto_detect': False
        }
    
    @patch('app.devices.barcode_scanner.evdev')
    def test_initialization(self, mock_evdev):
        """Probar inicialización del scanner"""
        # Configurar el mock
        mock_evdev.list_devices.return_value = []
        
        # Crear scanner con configuración
        scanner = BarcodeScanner(self.test_config)
        
        # Verificar que se inicializó correctamente
        self.assertEqual(scanner.device_path, self.test_config['device_path'])
        self.assertFalse(scanner.is_connected)
    
    @patch('app.devices.barcode_scanner.evdev')
    def test_auto_detect(self, mock_evdev):
        """Probar detección automática del scanner"""
        # Crear dispositivo mock
        mock_device = MagicMock()
        mock_device.path = '/dev/input/event0'
        mock_device.name = 'S10-W Barcode Scanner'
        
        # Configurar el mock
        mock_evdev.list_devices.return_value = [mock_device]
        
        # Crear scanner con auto-detección
        config = {'auto_detect': True}
        scanner = BarcodeScanner(config)
        
        # Verificar que detectó el dispositivo
        self.assertEqual(scanner.device_path, '/dev/input/event0')
    
    @patch('app.devices.barcode_scanner.evdev')
    def test_connect(self, mock_evdev):
        """Probar conexión al scanner"""
        # Configurar el mock
        mock_device = MagicMock()
        mock_evdev.InputDevice.return_value = mock_device
        
        # Crear scanner
        scanner = BarcodeScanner(self.test_config)
        
        # Conectar
        result = scanner.connect()
        
        # Verificar que se conectó correctamente
        self.assertTrue(result)
        self.assertTrue(scanner.is_connected)
        mock_evdev.InputDevice.assert_called_once_with(self.test_config['device_path'])
    
    @patch('app.devices.barcode_scanner.evdev')
    def test_start_listening(self, mock_evdev):
        """Probar inicio de escucha del scanner"""
        # Configurar el mock
        mock_device = MagicMock()
        mock_evdev.InputDevice.return_value = mock_device
        
        # Crear scanner y conectar
        scanner = BarcodeScanner(self.test_config)
        scanner.connect()
        
        # Crear callback mock
        callback = MagicMock()
        
        # Iniciar escucha
        with patch('threading.Thread') as mock_thread:
            result = scanner.start_listening(callback)
            
            # Verificar que se inició la escucha correctamente
            self.assertTrue(result)
            self.assertEqual(scanner.callback, callback)
            self.assertTrue(scanner.running)
            mock_thread.assert_called_once()
    
    @patch('app.devices.barcode_scanner.evdev')
    def test_stop_listening(self, mock_evdev):
        """Probar detención de escucha del scanner"""
        # Configurar el mock
        mock_device = MagicMock()
        mock_evdev.InputDevice.return_value = mock_device
        
        # Crear scanner y conectar
        scanner = BarcodeScanner(self.test_config)
        scanner.connect()
        
        # Iniciar escucha con thread mock
        scanner.listener_thread = MagicMock()
        scanner.running = True
        
        # Detener escucha
        scanner.stop_listening()
        
        # Verificar que se detuvo la escucha
        self.assertFalse(scanner.running)
        scanner.listener_thread.join.assert_called_once()

class TestThermalPrinter(unittest.TestCase):
    """Pruebas para el controlador de impresora