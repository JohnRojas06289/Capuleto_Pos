# app/devices/barcode_scanner.py
import time
import threading
import evdev  # Para manejar eventos de dispositivos de entrada en Linux

class BarcodeScanner:
    """Controlador para la lectora de código de barras S10-W"""
    
    def __init__(self, config=None):
        self.device_path = None
        self.device = None
        self.is_connected = False
        self.callback = None
        self.listener_thread = None
        self.running = False
        
        # Cargar configuración si se proporciona
        if config:
            self.device_path = config.get('device_path')
        
        # Si no hay configuración, intentar detectar automáticamente
        if not self.device_path:
            self.auto_detect()
    
    def auto_detect(self):
        """Intenta detectar automáticamente la lectora de códigos de barras"""
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            # La S10-W suele identificarse como un dispositivo de teclado con un nombre específico
            if 'barcode' in device.name.lower() or 's10' in device.name.lower():
                self.device_path = device.path
                break
    
    def connect(self):
        """Conectar al dispositivo"""
        if not self.device_path:
            return False
        
        try:
            self.device = evdev.InputDevice(self.device_path)
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Error al conectar con la lectora de códigos: {e}")
            return False
    
    def start_listening(self, callback):
        """Iniciar escucha de códigos de barras"""
        if not self.is_connected and not self.connect():
            return False
        
        self.callback = callback
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen_for_barcodes)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        return True
    
    def _listen_for_barcodes(self):
        """Escuchar códigos de barras (corre en un hilo separado)"""
        barcode = ""
        keys = {
            # Mapeo de códigos de teclas a caracteres
            2: '1', 3: '2', 4: '3', 5: '4', 6: '5', 7: '6', 8: '7', 9: '8', 10: '9', 11: '0',
            # Agregar más mapeos según sea necesario
        }
        
        while self.running:
            try:
                for event in self.device.read_loop():
                    if event.type == evdev.ecodes.EV_KEY and event.value == 1:  # Tecla presionada
                        if event.code == 28:  # Enter (fin del código)
                            if barcode and self.callback:
                                self.callback(barcode)
                            barcode = ""
                        elif event.code in keys:
                            barcode += keys[event.code]
            except Exception as e:
                print(f"Error en la lectura del código: {e}")
                time.sleep(1)  # Esperar antes de reintentar
    
    def stop_listening(self):
        """Detener la escucha de códigos"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=1.0)


# app/devices/thermal_printer.py
import cups
import os
from PIL import Image
from escpos.printer import Usb, File

class ThermalPrinter:
    """Controlador para la impresora térmica WPRP-260 de 58mm"""
    
    def __init__(self, config=None):
        self.printer_name = None
        self.printer_type = 'cups'  # 'cups' o 'direct'
        self.usb_vendor_id = None
        self.usb_product_id = None
        self.printer = None
        
        # Cargar configuración
        if config:
            self.printer_name = config.get('printer_name')
            self.printer_type = config.get('printer_type', 'cups')
            self.usb_vendor_id = config.get('usb_vendor_id')
            self.usb_product_id = config.get('usb_product_id')
        
        # Si no hay configuración, intentar detectar
        if not self.printer_name and self.printer_type == 'cups':
            self.auto_detect_cups()
    
    def auto_detect_cups(self):
        """Detectar impresora usando CUPS"""
        conn = cups.Connection()
        printers = conn.getPrinters()
        
        # Buscar impresoras que podrían ser térmicas
        for printer_name, printer_info in printers.items():
            if '58mm' in printer_name.lower() or 'thermal' in printer_name.lower() or 'wprp' in printer_name.lower():
                self.printer_name = printer_name
                break
    
    def connect(self):
        """Conectar a la impresora"""
        if self.printer_type == 'cups':
            # CUPS ya está conectado, verificar que la impresora exista
            if not self.printer_name:
                return False
            
            conn = cups.Connection()
            printers = conn.getPrinters()
            if self.printer_name not in printers:
                return False
            return True
        
        elif self.printer_type == 'direct':
            # Conexión directa por USB usando python-escpos
            if not self.usb_vendor_id or not self.usb_product_id:
                return False
            
            try:
                self.printer = Usb(self.usb_vendor_id, self.usb_product_id)
                return True
            except Exception as e:
                print(f"Error al conectar con la impresora: {e}")
                return False
        
        return False
    
    def print_receipt(self, receipt_data):
        """Imprimir un recibo"""
        if self.printer_type == 'cups':
            return self._print_with_cups(receipt_data)
        elif self.printer_type == 'direct' and self.printer:
            return self._print_direct(receipt_data)
        return False
    
    def _print_with_cups(self, receipt_data):
        """Imprimir usando CUPS"""
        try:
            conn = cups.Connection()
            
            # Crear archivo temporal
            temp_file = '/tmp/receipt.txt'
            with open(temp_file, 'w') as f:
                f.write(receipt_data['text'])
            
            # Imprimir
            job_id = conn.printFile(self.printer_name, temp_file, "Receipt", {})
            
            # Limpiar
            os.remove(temp_file)
            return job_id > 0
        except Exception as e:
            print(f"Error al imprimir: {e}")
            return False
    
    def _print_direct(self, receipt_data):
        """Imprimir directamente usando python-escpos"""
        try:
            p = self.printer
            
            # Encabezado
            p.set(align='center')
            p.text(receipt_data['store_name'] + '\n')
            p.text(receipt_data['store_address'] + '\n')
            p.text(receipt_data['store_phone'] + '\n')
            p.text('-' * 32 + '\n')
            
            # Fecha y número de recibo
            p.set(align='left')
            p.text(f"Fecha: {receipt_data['date']}\n")
            p.text(f"Recibo: {receipt_data['receipt_number']}\n")
            p.text(f"Cajero: {receipt_data['cashier_name']}\n")
            p.text('-' * 32 + '\n')
            
            # Productos
            p.set(align='left')
            for item in receipt_data['items']:
                p.text(f"{item['quantity']} x {item['name']}\n")
                p.text(f"{item['price']} = {item['subtotal']}\n")
            
            p.text('-' * 32 + '\n')
            
            # Totales
            p.text(f"Subtotal: {receipt_data['subtotal']}\n")
            p.text(f"IVA: {receipt_data['tax']}\n")
            p.text(f"Total: {receipt_data['total']}\n")
            
            # Método de pago
            p.text(f"Pago: {receipt_data['payment_method']}\n")
            
            # Pie de página
            p.set(align='center')
            p.text('\n¡Gracias por su compra!\n\n')
            
            # Cortar papel
            p.cut()
            
            return True
        except Exception as e:
            print(f"Error al imprimir directamente: {e}")
            return False


# app/devices/cash_drawer.py
import serial
import usb.core
import usb.util
import time

class CashDrawer:
    """Controlador para la caja de dinero SAT-119"""
    
    def __init__(self, config=None):
        self.connection_type = 'printer'  # 'printer', 'serial', 'usb'
        self.printer = None  # Referencia a la impresora térmica
        self.serial_port = None
        self.serial_baudrate = 9600
        self.usb_device = None
        self.usb_vendor_id = None
        self.usb_product_id = None
        
        # Cargar configuración
        if config:
            self.connection_type = config.get('connection_type', 'printer')
            self.serial_port = config.get('serial_port')
            self.serial_baudrate = config.get('serial_baudrate', 9600)
            self.usb_vendor_id = config.get('usb_vendor_id')
            self.usb_product_id = config.get('usb_product_id')
    
    def set_printer(self, printer):
        """Establecer la impresora a usar para abrir la caja"""
        self.printer = printer
    
    def connect(self):
        """Conectar a la caja registradora"""
        if self.connection_type == 'printer':
            # La conexión se hace a través de la impresora
            return self.printer is not None
        
        elif self.connection_type == 'serial':
            # Conexión directa por puerto serie
            if not self.serial_port:
                return False
            
            try:
                self.serial_device = serial.Serial(
                    port=self.serial_port,
                    baudrate=self.serial_baudrate,
                    timeout=1
                )
                return True
            except Exception as e:
                print(f"Error al conectar con la caja por serial: {e}")
                return False
        
        elif self.connection_type == 'usb':
            # Conexión directa por USB
            if not self.usb_vendor_id or not self.usb_product_id:
                return False
            
            try:
                self.usb_device = usb.core.find(
                    idVendor=self.usb_vendor_id,
                    idProduct=self.usb_product_id
                )
                
                if self.usb_device is None:
                    return False
                
                # Configurar el dispositivo
                if self.usb_device.is_kernel_driver_active(0):
                    self.usb_device.detach_kernel_driver(0)
                
                usb.util.claim_interface(self.usb_device, 0)
                return True
            except Exception as e:
                print(f"Error al conectar con la caja por USB: {e}")
                return False
        
        return False
    
    def open_drawer(self):
        """Abrir la caja de dinero"""
        # Comando estándar para abrir la caja registradora (ESC p m t1 t2)
        # ESC = 27 (0x1B), p = 112 (0x70), m = 0 (0x00), t1 = 50 (0x32), t2 = 50 (0x32)
        command = bytes([0x1B, 0x70, 0x00, 0x32, 0x32])
        
        if self.connection_type == 'printer':
            # Abrir a través de la impresora
            if not self.printer:
                return False
            
            try:
                if hasattr(self.printer, 'printer') and self.printer.printer:
                    # Para python-escpos
                    self.printer.printer.cashdraw(pin=2)
                    return True
                elif hasattr(self.printer, '_print_with_cups'):
                    # Para CUPS, enviar comando raw
                    import cups
                    conn = cups.Connection()
                    conn.addPrinter(self.printer.printer_name, file=command)
                    return True
            except Exception as e:
                print(f"Error al abrir la caja a través de la impresora: {e}")
                return False
        
        elif self.connection_type == 'serial' and self.serial_device:
            try:
                self.serial_device.write(command)
                return True
            except Exception as e:
                print(f"Error al abrir la caja por serial: {e}")
                return False
        
        elif self.connection_type == 'usb' and self.usb_device:
            try:
                # Encontrar el endpoint de salida
                endpoint = self.usb_device[0][(0,0)][0]
                
                # Enviar comando
                self.usb_device.write(endpoint.bEndpointAddress, command)
                return True
            except Exception as e:
                print(f"Error al abrir la caja por USB: {e}")
                return False
        
        return False