# app/devices/cash_drawer.py
import logging
import time
import os

# Importar librerías opcionales para comunicación con el dispositivo
try:
    import serial
except ImportError:
    serial = None

try:
    import usb.core
    import usb.util
except ImportError:
    usb = None

class CashDrawer:
    """Controlador para la caja de dinero SAT-119"""
    
    def __init__(self, config=None):
        """
        Inicializar controlador de caja de dinero
        
        Args:
            config: Diccionario con configuración (opcional)
        """
        self.logger = logging.getLogger('pos.devices.cashdrawer')
        
        # Valores por defecto
        self.connection_type = 'printer'  # 'printer', 'serial', 'usb', 'network', 'file'
        self.printer = None  # Referencia a la impresora térmica
        self.is_connected = False
        
        # Parámetros para conexión serial
        self.serial_port = None
        self.serial_baudrate = 9600
        self.serial_device = None
        
        # Parámetros para conexión USB
        self.usb_vendor_id = None
        self.usb_product_id = None
        self.usb_device = None
        
        # Parámetros para conexión de archivo
        self.device_path = None
        
        # Parámetros para conexión de red
        self.network_host = None
        self.network_port = 9100
        
        # Cargar configuración si se proporciona
        if config:
            self._load_config(config)
    
    def _load_config(self, config):
        """
        Cargar configuración del diccionario
        
        Args:
            config: Diccionario con configuración
        """
        # Tipo de conexión
        self.connection_type = config.get('connection_type', 'printer').lower()
        
        # Parámetros según el tipo de conexión
        if self.connection_type == 'serial':
            self.serial_port = config.get('serial_port')
            self.serial_baudrate = config.get('serial_baudrate', 9600)
        elif self.connection_type == 'usb':
            self.usb_vendor_id = config.get('usb_vendor_id')
            self.usb_product_id = config.get('usb_product_id')
        elif self.connection_type == 'file':
            self.device_path = config.get('device_path')
        elif self.connection_type == 'network':
            self.network_host = config.get('network_host')
            self.network_port = config.get('network_port', 9100)
    
    def set_printer(self, printer):
        """
        Establecer la impresora a usar para abrir la caja
        
        Args:
            printer: Objeto de impresora térmica
        """
        self.printer = printer
        if self.connection_type == 'printer':
            self.is_connected = self.printer is not None
    
    def connect(self):
        """
        Conectar a la caja de dinero
        
        Returns:
            True si se conectó correctamente, False en caso contrario
        """
        try:
            if self.connection_type == 'printer':
                # La conexión se hace a través de la impresora
                if self.printer:
                    self.is_connected = True
                    self.logger.info("Caja conectada a través de la impresora")
                    return True
                else:
                    self.logger.error("No se puede conectar la caja: impresora no disponible")
                    return False
                    
            elif self.connection_type == 'serial':
                return self._connect_serial()
                
            elif self.connection_type == 'usb':
                return self._connect_usb()
                
            elif self.connection_type == 'file':
                return self._connect_file()
                
            elif self.connection_type == 'network':
                # No es necesario conectar en modo red, se conecta al abrir
                self.is_connected = True
                return True
                
            else:
                self.logger.error(f"Tipo de conexión no válido: {self.connection_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al conectar a la caja: {e}")
            return False
    
    def _connect_serial(self):
        """Conectar usando puerto serie"""
        if not serial:
            self.logger.error("Módulo 'serial' no instalado")
            return False
            
        if not self.serial_port:
            self.logger.error("Puerto serie no especificado")
            return False
            
        try:
            self.serial_device = serial.Serial(
                port=self.serial_port,
                baudrate=self.serial_baudrate,
                timeout=1
            )
            
            self.is_connected = True
            self.logger.info(f"Caja conectada por puerto serie: {self.serial_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al conectar caja por puerto serie: {e}")
            return False
    
    def _connect_usb(self):
        """Conectar usando USB directo"""
        if not usb:
            self.logger.error("Módulo 'usb' no instalado")
            return False
            
        if not self.usb_vendor_id or not self.usb_product_id:
            self.logger.error("Identificadores USB (vendor_id, product_id) no especificados")
            return False
            
        try:
            # Convertir a valores hexadecimales si son strings
            if isinstance(self.usb_vendor_id, str):
                self.usb_vendor_id = int(self.usb_vendor_id, 16)
            if isinstance(self.usb_product_id, str):
                self.usb_product_id = int(self.usb_product_id, 16)
                
            # Buscar el dispositivo
            self.usb_device = usb.core.find(
                idVendor=self.usb_vendor_id,
                idProduct=self.usb_product_id
            )
            
            if self.usb_device is None:
                self.logger.error(f"Dispositivo USB no encontrado: {self.usb_vendor_id:04x}:{self.usb_product_id:04x}")
                return False
                
            # Configurar el dispositivo
            try:
                if self.usb_device.is_kernel_driver_active(0):
                    self.usb_device.detach_kernel_driver(0)
            except Exception as e:
                # Algunos dispositivos no requieren esta operación
                self.logger.warning(f"Advertencia al configurar USB: {e}")
                
            try:
                self.usb_device.set_configuration()
                usb.util.claim_interface(self.usb_device, 0)
            except Exception as e:
                # Algunos dispositivos no requieren esta operación
                self.logger.warning(f"Advertencia al configurar USB: {e}")
            
            self.is_connected = True
            self.logger.info(f"Caja conectada por USB: {self.usb_vendor_id:04x}:{self.usb_product_id:04x}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al conectar caja por USB: {e}")
            return False
    
    def _connect_file(self):
        """Conectar usando archivo de dispositivo"""
        if not self.device_path:
            self.logger.error("Ruta de dispositivo no especificada")
            return False
            
        try:
            # Verificar que el archivo existe
            if not os.path.exists(self.device_path):
                self.logger.error(f"Archivo de dispositivo no encontrado: {self.device_path}")
                return False
                
            # Verificar permisos de escritura
            if not os.access(self.device_path, os.W_OK):
                self.logger.error(f"No tiene permisos de escritura en el dispositivo: {self.device_path}")
                return False
                
            self.is_connected = True
            self.logger.info(f"Caja conectada por archivo: {self.device_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al conectar caja por archivo: {e}")
            return False
    
    def open_drawer(self):
        """
        Abrir la caja de dinero
        
        Returns:
            True si se abrió correctamente, False en caso contrario
        """
        if not self.is_connected:
            self.logger.error("No se puede abrir la caja: no está conectada")
            return False
            
        try:
            if self.connection_type == 'printer':
                return self._open_via_printer()
                
            elif self.connection_type == 'serial':
                return self._open_via_serial()
                
            elif self.connection_type == 'usb':
                return self._open_via_usb()
                
            elif self.connection_type == 'file':
                return self._open_via_file()
                
            elif self.connection_type == 'network':
                return self._open_via_network()
                
            else:
                self.logger.error(f"Tipo de conexión no válido: {self.connection_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al abrir la caja: {e}")
            return False
    
    def _open_via_printer(self):
        """Abrir caja a través de la impresora"""
        if not self.printer:
            self.logger.error("No se puede abrir la caja: impresora no disponible")
            return False
            
        # Usar el método de la impresora para abrir la caja
        result = self.printer.open_cash_drawer()
        
        if result:
            self.logger.info("Caja abierta a través de la impresora")
        else:
            self.logger.error("Error al abrir la caja a través de la impresora")
            
        return result
    
    def _open_via_serial(self):
        """Abrir caja usando puerto serie"""
        if not self.serial_device:
            self.logger.error("No se puede abrir la caja: dispositivo serial no disponible")
            return False
            
        try:
            # Comando para abrir la caja
            # El comando exacto puede variar según el modelo
            command = self._get_open_command()
            
            # Enviar comando
            self.serial_device.write(command)
            
            self.logger.info("Comando para abrir caja enviado por puerto serie")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al abrir caja por puerto serie: {e}")
            return False
    
    def _open_via_usb(self):
        """Abrir caja usando USB directo"""
        if not self.usb_device:
            self.logger.error("No se puede abrir la caja: dispositivo USB no disponible")
            return False
            
        try:
            # Comando para abrir la caja
            command = self._get_open_command()
            
            # Encontrar el endpoint de salida
            interface = 0
            endpoint = None
            
            for cfg in self.usb_device:
                for intf in cfg:
                    for ep in intf:
                        if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                            endpoint = ep
                            interface = intf.bInterfaceNumber
                            break
                    if endpoint:
                        break
                if endpoint:
                    break
            
            if not endpoint:
                self.logger.error("No se encontró un endpoint de salida en el dispositivo USB")
                return False
                
            # Enviar comando
            try:
                if self.usb_device.is_kernel_driver_active(interface):
                    self.usb_device.detach_kernel_driver(interface)
            except:
                pass
                
            try:
                self.usb_device.write(endpoint.bEndpointAddress, command)
                self.logger.info("Comando para abrir caja enviado por USB")
                return True
            except Exception as e:
                self.logger.error(f"Error al enviar comando por USB: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al abrir caja por USB: {e}")
            return False
    
    def _open_via_file(self):
        """Abrir caja usando archivo de dispositivo"""
        if not self.device_path:
            self.logger.error("No se puede abrir la caja: ruta de dispositivo no especificada")
            return False
            
        try:
            # Comando para abrir la caja
            command = self._get_open_command()
            
            # Escribir en el archivo de dispositivo
            with open(self.device_path, 'wb') as f:
                f.write(command)
                
            self.logger.info(f"Comando para abrir caja enviado a {self.device_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al abrir caja por archivo: {e}")
            return False
    
    def _open_via_network(self):
        """Abrir caja usando conexión de red"""
        if not self.network_host:
            self.logger.error("No se puede abrir la caja: host de red no especificado")
            return False
            
        try:
            import socket
            
            # Comando para abrir la caja
            command = self._get_open_command()
            
            # Crear socket y enviar comando
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.network_host, self.network_port))
            sock.send(command)
            sock.close()
            
            self.logger.info(f"Comando para abrir caja enviado a {self.network_host}:{self.network_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al abrir caja por red: {e}")
            return False
    
    def _get_open_command(self):
        """
        Obtener el comando para abrir la caja
        
        El SAT-119 suele usar el comando estándar ESC p m t1 t2:
        - ESC = 0x1B (27 decimal) - Código de escape
        - p = 0x70 (112 decimal) - Comando de pulso
        - m = 0x00 o 0x01 (0 o 1) - Número de conector (pin 2 o pin 5)
        - t1, t2 = Duración del pulso (t1 * 2 ms)
        
        Returns:
            Bytes con el comando a enviar
        """
        # Comando estándar ESC p 0 25 250
        # Pulso de 50ms en el pin 2 (conector 0)
        return b'\x1B\x70\x00\x19\xFA'