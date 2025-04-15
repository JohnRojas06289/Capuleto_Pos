# app/devices/thermal_printer.py
import cups
import os
import logging
from datetime import datetime
try:
    from escpos.printer import Usb, File, Network
except ImportError:
    # Si python-escpos no está instalado, crear clases dummy
    class Usb:
        def __init__(self, *args, **kwargs):
            pass
    class File:
        def __init__(self, *args, **kwargs):
            pass
    class Network:
        def __init__(self, *args, **kwargs):
            pass

class ThermalPrinter:
    """Controlador para la impresora térmica WPRP-260 de 58mm"""
    
    # Ancho de papel en caracteres (para 58mm suele ser 32 caracteres)
    PAPER_WIDTH_CHARS = 32
    
    def __init__(self, config=None):
        """
        Inicializar controlador de impresora
        
        Args:
            config: Diccionario con configuración (opcional)
        """
        self.logger = logging.getLogger('pos.devices.printer')
        
        # Valores por defecto
        self.printer_name = None
        self.connection_type = 'cups'  # 'cups', 'usb', 'file', 'network'
        self.printer = None
        
        # Parámetros para conexión USB
        self.usb_vendor_id = None
        self.usb_product_id = None
        self.usb_in_ep = 0x82
        self.usb_out_ep = 0x01
        
        # Parámetros para conexión de archivo (generalmente /dev/usb/lp0)
        self.device_path = None
        
        # Parámetros para conexión de red
        self.network_host = None
        self.network_port = 9100
        
        # Cargar configuración si se proporciona
        if config:
            self._load_config(config)
            
        # Intentar autodetectar la impresora si no se especificó
        if not self.printer_name and self.connection_type == 'cups':
            self._auto_detect()
    
    def _load_config(self, config):
        """
        Cargar configuración del diccionario
        
        Args:
            config: Diccionario con configuración
        """
        # Tipo de conexión
        self.connection_type = config.get('connection_type', 'cups').lower()
        
        # Parámetros según el tipo de conexión
        if self.connection_type == 'cups':
            self.printer_name = config.get('printer_name')
        elif self.connection_type == 'usb':
            self.usb_vendor_id = config.get('usb_vendor_id')
            self.usb_product_id = config.get('usb_product_id')
            self.usb_in_ep = config.get('usb_in_ep', 0x82)
            self.usb_out_ep = config.get('usb_out_ep', 0x01)
        elif self.connection_type == 'file':
            self.device_path = config.get('device_path')
        elif self.connection_type == 'network':
            self.network_host = config.get('network_host')
            self.network_port = config.get('network_port', 9100)
    
    def _auto_detect(self):
        """Intentar detectar automáticamente la impresora térmica"""
        try:
            # Conexión a CUPS
            conn = cups.Connection()
            printers = conn.getPrinters()
            
            # Buscar impresoras que podrían ser térmicas
            for name, printer in printers.items():
                # Verificar por nombres comunes de impresoras térmicas
                if any(keyword in name.lower() for keyword in ['thermal', 'receipt', '58mm', '80mm', 'pos', 'wprp']):
                    self.printer_name = name
                    self.logger.info(f"Impresora térmica detectada automáticamente: {name}")
                    return
                
                # Verificar por marcas comunes de impresoras térmicas
                if 'printer-make-and-model' in printer:
                    model = printer['printer-make-and-model'].lower()
                    if any(brand in model for brand in ['epson tm', 'star', 'wprp', 'pos', 'thermal']):
                        self.printer_name = name
                        self.logger.info(f"Impresora térmica detectada automáticamente: {name} ({model})")
                        return
            
            self.logger.warning("No se pudo detectar automáticamente una impresora térmica")
        except Exception as e:
            self.logger.error(f"Error al intentar detectar impresora: {e}")
    
    def connect(self):
        """
        Conectar a la impresora
        
        Returns:
            True si se conectó correctamente, False en caso contrario
        """
        try:
            if self.connection_type == 'cups':
                return self._connect_cups()
            elif self.connection_type == 'usb':
                return self._connect_usb()
            elif self.connection_type == 'file':
                return self._connect_file()
            elif self.connection_type == 'network':
                return self._connect_network()
            else:
                self.logger.error(f"Tipo de conexión no válido: {self.connection_type}")
                return False
        except Exception as e:
            self.logger.error(f"Error al conectar a la impresora: {e}")
            return False
    
    def _connect_cups(self):
        """Conectar usando CUPS"""
        if not self.printer_name:
            self.logger.error("Nombre de impresora no especificado para conexión CUPS")
            return False
            
        try:
            conn = cups.Connection()
            printers = conn.getPrinters()
            
            if self.printer_name not in printers:
                self.logger.error(f"Impresora no encontrada en CUPS: {self.printer_name}")
                return False
                
            self.logger.info(f"Impresora CUPS conectada: {self.printer_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error al conectar a impresora CUPS: {e}")
            return False
    
    def _connect_usb(self):
        """Conectar directamente por USB usando python-escpos"""
        if not self.usb_vendor_id or not self.usb_product_id:
            self.logger.error("Identificadores USB (vendor_id, product_id) no especificados")
            return False
            
        try:
            # Convertir a valores hexadecimales si son strings
            if isinstance(self.usb_vendor_id, str):
                self.usb_vendor_id = int(self.usb_vendor_id, 16)
            if isinstance(self.usb_product_id, str):
                self.usb_product_id = int(self.usb_product_id, 16)
                
            self.printer = Usb(
                self.usb_vendor_id,
                self.usb_product_id,
                0,  # USB interface
                self.usb_in_ep,
                self.usb_out_ep
            )
            
            self.logger.info(f"Impresora USB conectada: {self.usb_vendor_id:04x}:{self.usb_product_id:04x}")
            return True
        except Exception as e:
            self.logger.error(f"Error al conectar a impresora USB: {e}")
            return False
    
    def _connect_file(self):
        """Conectar a través de un archivo de dispositivo"""
        if not self.device_path:
            self.logger.error("Ruta de dispositivo no especificada")
            return False
            
        try:
            self.printer = File(self.device_path)
            self.logger.info(f"Impresora conectada por archivo: {self.device_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error al conectar a impresora por archivo: {e}")
            return False
    
    def _connect_network(self):
        """Conectar a través de la red"""
        if not self.network_host:
            self.logger.error("Host de red no especificado")
            return False
            
        try:
            self.printer = Network(self.network_host, self.network_port)
            self.logger.info(f"Impresora conectada por red: {self.network_host}:{self.network_port}")
            return True
        except Exception as e:
            self.logger.error(f"Error al conectar a impresora por red: {e}")
            return False
    
    def print_receipt(self, receipt_data):
        """
        Imprimir un recibo
        
        Args:
            receipt_data: Diccionario con datos del recibo
                - store_name: Nombre de la tienda
                - store_address: Dirección de la tienda
                - store_phone: Teléfono de la tienda
                - date: Fecha y hora
                - receipt_number: Número de recibo
                - cashier_name: Nombre del cajero
                - items: Lista de productos vendidos (cada uno con name, quantity, price, subtotal)
                - subtotal: Subtotal
                - tax: Impuestos
                - total: Total
                - payment_method: Método de pago
                - custom_text: Texto personalizado (opcional)
                
        Returns:
            True si se imprimió correctamente, False en caso contrario
        """
        if self.connection_type == 'cups':
            return self._print_cups(receipt_data)
        else:
            return self._print_escpos(receipt_data)
    
    def _print_cups(self, receipt_data):
        """Imprimir usando CUPS"""
        if not self.printer_name:
            self.logger.error("Nombre de impresora no especificado para impresión CUPS")
            return False
            
        try:
            # Generar contenido del recibo
            content = self._format_receipt_text(receipt_data)
            
            # Crear archivo temporal
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            temp_file = f"/tmp/pos_receipt_{timestamp}.txt"
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Imprimir usando CUPS
            conn = cups.Connection()
            job_id = conn.printFile(
                self.printer_name,
                temp_file,
                f"Recibo #{receipt_data.get('receipt_number', timestamp)}",
                {}
            )
            
            # Eliminar archivo temporal
            os.unlink(temp_file)
            
            if job_id:
                self.logger.info(f"Recibo impreso con CUPS - Job ID: {job_id}")
                return True
            else:
                self.logger.error("Error al imprimir recibo con CUPS: trabajo no creado")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al imprimir recibo con CUPS: {e}")
            return False
    
    def _print_escpos(self, receipt_data):
        """Imprimir usando python-escpos"""
        if not self.printer:
            self.logger.error("Impresora no conectada para impresión ESC/POS")
            return False
            
        try:
            p = self.printer
            
            # Encabezado
            p.set(align='center', text_type='b')
            p.text(receipt_data.get('store_name', 'Mi Tienda') + '\n')
            p.set(align='center', text_type='normal')
            p.text(receipt_data.get('store_address', '') + '\n')
            p.text(receipt_data.get('store_phone', '') + '\n')
            p.text('-' * self.PAPER_WIDTH_CHARS + '\n')
            
            # Fecha y número de recibo
            p.set(align='left')
            p.text(f"Fecha: {receipt_data.get('date', datetime.now().strftime('%d/%m/%Y %H:%M'))}\n")
            p.text(f"Recibo: #{receipt_data.get('receipt_number', '')}\n")
            p.text(f"Cajero: {receipt_data.get('cashier_name', '')}\n")
            p.text('-' * self.PAPER_WIDTH_CHARS + '\n')
            
            # Encabezados de columnas
            p.text('CANT  DESCRIPCION            PRECIO   TOTAL\n')
            p.text('-' * self.PAPER_WIDTH_CHARS + '\n')
            
            # Productos
            for item in receipt_data.get('items', []):
                name = item.get('name', '')
                quantity = item.get('quantity', 1)
                price = item.get('price', 0)
                subtotal = item.get('subtotal', 0)
                
                # Formatear para que quepa en el ancho del papel
                if isinstance(quantity, str):
                    try:
                        quantity = float(quantity.replace(',', '.'))
                    except:
                        quantity = 1
                
                # Convertir precio y subtotal a float si son strings
                if isinstance(price, str):
                    try:
                        price = float(price.replace('$', '').replace(',', '.'))
                    except:
                        price = 0
                        
                if isinstance(subtotal, str):
                    try:
                        subtotal = float(subtotal.replace('$', '').replace(',', '.'))
                    except:
                        subtotal = 0
                
                # Formatear nombre para que quepa en el ancho disponible
                if len(name) > 20:
                    name = name[:17] + '...'
                
                # Imprimir producto
                p.text(f"{quantity:<5}{name:<20}${price:<7.2f}${subtotal:.2f}\n")
            
            p.text('-' * self.PAPER_WIDTH_CHARS + '\n')
            
            # Totales
            p.set(align='right')
            
            # Convertir valores a float si son strings
            subtotal = receipt_data.get('subtotal', 0)
            if isinstance(subtotal, str):
                try:
                    subtotal = float(subtotal.replace('$', '').replace(',', '.'))
                except:
                    subtotal = 0
                    
            tax = receipt_data.get('tax', 0)
            if isinstance(tax, str):
                try:
                    tax = float(tax.replace('$', '').replace(',', '.'))
                except:
                    tax = 0
                    
            total = receipt_data.get('total', 0)
            if isinstance(total, str):
                try:
                    total = float(total.replace('$', '').replace(',', '.'))
                except:
                    total = 0
            
            p.text(f"SUBTOTAL: ${subtotal:.2f}\n")
            p.text(f"IMPUESTO: ${tax:.2f}\n")
            p.set(text_type='b')
            p.text(f"TOTAL:    ${total:.2f}\n")
            p.set(text_type='normal')
            
            # Método de pago
            payment_method = receipt_data.get('payment_method', 'Efectivo')
            p.text(f"PAGO:     {payment_method}\n")
            
            # Si es pago en efectivo, mostrar monto y cambio
            if payment_method.lower() == 'efectivo' or payment_method.lower() == 'cash':
                amount_received = receipt_data.get('amount_received', 0)
                if isinstance(amount_received, str):
                    try:
                        amount_received = float(amount_received.replace('$', '').replace(',', '.'))
                    except:
                        amount_received = 0
                        
                change = receipt_data.get('change', 0)
                if isinstance(change, str):
                    try:
                        change = float(change.replace('$', '').replace(',', '.'))
                    except:
                        change = 0
                
                if amount_received > 0:
                    p.text(f"RECIBIDO: ${amount_received:.2f}\n")
                    p.text(f"CAMBIO:   ${change:.2f}\n")
            
            # Pie de página
            p.set(align='center')
            p.text('\n')
            p.text(receipt_data.get('custom_text', '¡Gracias por su compra!') + '\n')
            p.text('\n')
            
            # Código de barras o QR (opcional)
            if 'qr_data' in receipt_data:
                p.qr(receipt_data['qr_data'])
            elif 'barcode_data' in receipt_data:
                p.barcode(receipt_data['barcode_data'], 'CODE39')
            
            # Cortar papel
            p.cut()
            
            self.logger.info("Recibo impreso con ESC/POS")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al imprimir recibo con ESC/POS: {e}")
            return False
    
    def _format_receipt_text(self, receipt_data):
        """Formatear recibo como texto plano para impresión con CUPS"""
        # Ancho de papel
        width = self.PAPER_WIDTH_CHARS
        
        # Construir el contenido
        lines = []
        
        # Encabezado
        store_name = receipt_data.get('store_name', 'Mi Tienda')
        lines.append(store_name.center(width))
        
        store_address = receipt_data.get('store_address', '')
        if store_address:
            lines.append(store_address.center(width))
            
        store_phone = receipt_data.get('store_phone', '')
        if store_phone:
            lines.append(store_phone.center(width))
            
        lines.append('-' * width)
        
        # Fecha y número de recibo
        date = receipt_data.get('date', datetime.now().strftime('%d/%m/%Y %H:%M'))
        lines.append(f"Fecha: {date}")
        
        receipt_number = receipt_data.get('receipt_number', '')
        lines.append(f"Recibo: #{receipt_number}")
        
        cashier_name = receipt_data.get('cashier_name', '')
        lines.append(f"Cajero: {cashier_name}")
        
        lines.append('-' * width)
        
        # Encabezados de columnas
        lines.append('CANT  DESCRIPCION            PRECIO   TOTAL')
        lines.append('-' * width)
        
        # Productos
        for item in receipt_data.get('items', []):
            name = item.get('name', '')
            quantity = item.get('quantity', 1)
            price = item.get('price', 0)
            subtotal = item.get('subtotal', 0)
            
            # Formatear para que quepa en el ancho del papel
            if len(name) > 20:
                name = name[:17] + '...'
            
            # Convertir a valores numéricos si son strings
            if isinstance(quantity, str):
                try:
                    quantity = float(quantity.replace(',', '.'))
                except:
                    quantity = 1
            
            if isinstance(price, str):
                try:
                    price = float(price.replace('$', '').replace(',', '.'))
                except:
                    price = 0
                    
            if isinstance(subtotal, str):
                try:
                    subtotal = float(subtotal.replace('$', '').replace(',', '.'))
                except:
                    subtotal = 0
            
            # Formatear línea del producto
            lines.append(f"{quantity:<5}{name:<20}${price:<7.2f}${subtotal:.2f}")
        
        lines.append('-' * width)
        
        # Totales
        subtotal = receipt_data.get('subtotal', 0)
        tax = receipt_data.get('tax', 0)
        total = receipt_data.get('total', 0)
        
        # Convertir a valores numéricos si son strings
        if isinstance(subtotal, str):
            try:
                subtotal = float(subtotal.replace('$', '').replace(',', '.'))
            except:
                subtotal = 0
                
        if isinstance(tax, str):
            try:
                tax = float(tax.replace('$', '').replace(',', '.'))
            except:
                tax = 0
                
        if isinstance(total, str):
            try:
                total = float(total.replace('$', '').replace(',', '.'))
            except:
                total = 0
        
        # Alinear a la derecha
        lines.append(f"{'SUBTOTAL:':<{width-9}} ${subtotal:.2f}")
        lines.append(f"{'IMPUESTO:':<{width-9}} ${tax:.2f}")
        lines.append(f"{'TOTAL:':<{width-9}} ${total:.2f}")
        
        # Método de pago
        payment_method = receipt_data.get('payment_method', 'Efectivo')
        lines.append(f"{'PAGO:':<{width-9}} {payment_method}")
        
        # Si es pago en efectivo, mostrar monto y cambio
        if payment_method.lower() == 'efectivo' or payment_method.lower() == 'cash':
            amount_received = receipt_data.get('amount_received', 0)
            change = receipt_data.get('change', 0)
            
            # Convertir a valores numéricos si son strings
            if isinstance(amount_received, str):
                try:
                    amount_received = float(amount_received.replace('$', '').replace(',', '.'))
                except:
                    amount_received = 0
                    
            if isinstance(change, str):
                try:
                    change = float(change.replace('$', '').replace(',', '.'))
                except:
                    change = 0
            
            if amount_received > 0:
                lines.append(f"{'RECIBIDO:':<{width-9}} ${amount_received:.2f}")
                lines.append(f"{'CAMBIO:':<{width-9}} ${change:.2f}")
        
        # Pie de página
        lines.append('')
        custom_text = receipt_data.get('custom_text', '¡Gracias por su compra!')
        lines.append(custom_text.center(width))
        lines.append('')
        
        # Unir todas las líneas
        return '\n'.join(lines) + '\n\n\n\n\n'  # Añadir espacios al final para avanzar el papel
    
    def print_test(self):
        """
        Imprimir página de prueba
        
        Returns:
            True si se imprimió correctamente, False en caso contrario
        """
        # Datos de prueba
        test_data = {
            'store_name': 'PRUEBA DE IMPRESIÓN',
            'store_address': 'Sistema POS',
            'store_phone': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'receipt_number': 'TEST',
            'cashier_name': 'Sistema',
            'items': [
                {'name': 'Producto de prueba 1', 'quantity': 1, 'price': 10.00, 'subtotal': 10.00},
                {'name': 'Producto de prueba 2', 'quantity': 2, 'price': 15.50, 'subtotal': 31.00},
            ],
            'subtotal': 41.00,
            'tax': 6.56,
            'total': 47.56,
            'payment_method': 'Prueba',
            'custom_text': 'Si puede leer esto, la impresora está funcionando correctamente.'
        }
        
        return self.print_receipt(test_data)
    
    def open_cash_drawer(self):
        """
        Abrir cajón de dinero
        
        Returns:
            True si se envió el comando correctamente, False en caso contrario
        """
        try:
            # Si estamos usando python-escpos
            if self.printer and self.connection_type != 'cups':
                self.printer.cashdraw(2)
                self.logger.info("Comando para abrir cajón enviado usando ESC/POS")
                return True
            
            # Si estamos usando CUPS
            elif self.connection_type == 'cups' and self.printer_name:
                # Comando ESC/POS para abrir el cajón (pulse pin 2)
                # ESC p m t1 t2 - donde m es el pin (0 o 1), t1 y t2 son tiempos
                drawer_command = b'\x1B\x70\x00\x19\x19'  # 25ms de pulso en pin 0
                
                # Crear archivo temporal con el comando
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                temp_file = f"/tmp/pos_drawer_{timestamp}.bin"
                
                with open(temp_file, 'wb') as f:
                    f.write(drawer_command)
                
                # Enviar comando a la impresora
                conn = cups.Connection()
                job_id = conn.printFile(
                    self.printer_name,
                    temp_file,
                    "Abrir cajón",
                    {"raw": "true"}  # Importante: enviar como comando raw
                )
                
                # Eliminar archivo temporal
                os.unlink(temp_file)
                
                if job_id:
                    self.logger.info(f"Comando para abrir cajón enviado usando CUPS - Job ID: {job_id}")
                    return True
                else:
                    self.logger.error("Error al enviar comando para abrir cajón usando CUPS")
                    return False
            else:
                self.logger.error("No se puede abrir el cajón: impresora no configurada")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al abrir cajón de dinero: {e}")
            return False
    
    def cut_paper(self):
        """
        Cortar papel
        
        Returns:
            True si se envió el comando correctamente, False en caso contrario
        """
        try:
            # Si estamos usando python-escpos
            if self.printer and self.connection_type != 'cups':
                self.printer.cut()
                self.logger.info("Comando para cortar papel enviado usando ESC/POS")
                return True
            
            # Si estamos usando CUPS
            elif self.connection_type == 'cups' and self.printer_name:
                # Comando ESC/POS para cortar papel
                cut_command = b'\x1D\x56\x41\x00'  # GS V A 0 - corte completo
                
                # Crear archivo temporal con el comando
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                temp_file = f"/tmp/pos_cut_{timestamp}.bin"
                
                with open(temp_file, 'wb') as f:
                    f.write(cut_command)
                
                # Enviar comando a la impresora
                conn = cups.Connection()
                job_id = conn.printFile(
                    self.printer_name,
                    temp_file,
                    "Cortar papel",
                    {"raw": "true"}  # Importante: enviar como comando raw
                )
                
                # Eliminar archivo temporal
                os.unlink(temp_file)
                
                if job_id:
                    self.logger.info(f"Comando para cortar papel enviado usando CUPS - Job ID: {job_id}")
                    return True
                else:
                    self.logger.error("Error al enviar comando para cortar papel usando CUPS")
                    return False
            else:
                self.logger.error("No se puede cortar papel: impresora no configurada")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al cortar papel: {e}")
            return False
    
    def get_status(self):
        """
        Obtener estado de la impresora
        
        Returns:
            Diccionario con el estado de la impresora o None si no se pudo obtener
        """
        try:
            if self.connection_type == 'cups' and self.printer_name:
                conn = cups.Connection()
                printers = conn.getPrinters()
                
                if self.printer_name in printers:
                    printer_info = printers[self.printer_name]
                    
                    # Obtener trabajos de impresión pendientes
                    jobs = conn.getJobs(which_jobs='not-completed')
                    printer_jobs = [j for j in jobs.values() if j['printer'] == self.printer_name]
                    
                    status = {
                        'name': self.printer_name,
                        'state': printer_info.get('printer-state', 0),
                        'state_message': printer_info.get('printer-state-message', ''),
                        'is_accepting_jobs': printer_info.get('printer-is-accepting-jobs', True),
                        'is_shared': printer_info.get('printer-is-shared', False),
                        'pending_jobs': len(printer_jobs),
                        'connection_type': 'cups'
                    }
                    
                    return status
                else:
                    self.logger.error(f"Impresora no encontrada en CUPS: {self.printer_name}")
                    return None
            
            # Para conexiones directas, no podemos obtener estado detallado fácilmente
            elif self.printer and self.connection_type != 'cups':
                return {
                    'connection_type': self.connection_type,
                    'is_connected': True
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error al obtener estado de la impresora: {e}")
            return None