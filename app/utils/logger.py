# app/utils/logger.py
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(log_level=logging.INFO):
    """
    Configurar el sistema de registro
    
    Args:
        log_level: Nivel de registro (por defecto INFO)
        
    Returns:
        Objeto logger configurado
    """
    # Crear el directorio de logs si no existe
    log_dir = os.path.join(os.path.dirname(__file__), "../../logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Nombre del archivo de log con fecha
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"pos_{today}.log")
    
    # Configurar el logger principal
    logger = logging.getLogger('pos')
    logger.setLevel(log_level)
    
    # Evitar duplicación de handlers
    if not logger.handlers:
        # Handler para archivo
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
    
    return logger


class EventLogger:
    """Clase para registrar eventos específicos del sistema"""
    
    def __init__(self, db=None):
        """
        Inicializar logger de eventos
        
        Args:
            db: Conexión a la base de datos (opcional)
        """
        self.logger = logging.getLogger('pos.events')
        self.db = db
    
    def log_login(self, user_id, username, success, ip_address=None):
        """
        Registrar intento de inicio de sesión
        
        Args:
            user_id: ID del usuario (o None si no se encontró)
            username: Nombre de usuario que intentó iniciar sesión
            success: True si el inicio de sesión fue exitoso, False si falló
            ip_address: Dirección IP desde donde se intentó el inicio de sesión (opcional)
        """
        status = "exitoso" if success else "fallido"
        self.logger.info(f"Inicio de sesión {status} - Usuario: {username} - IP: {ip_address or 'desconocida'}")
        
        # Si hay conexión a la base de datos, registrar en la tabla de eventos
        if self.db:
            try:
                query = """
                    INSERT INTO login_events (user_id, username, success, ip_address)
                    VALUES (?, ?, ?, ?)
                """
                params = [user_id, username, 1 if success else 0, ip_address]
                self.db.execute(query, params)
            except:
                # Si falla, solo registrar en el log
                pass
    
    def log_sale(self, sale_id, user_id, total_amount, payment_method):
        """
        Registrar una venta
        
        Args:
            sale_id: ID de la venta
            user_id: ID del usuario que realizó la venta
            total_amount: Monto total de la venta
            payment_method: Método de pago
        """
        self.logger.info(f"Venta #{sale_id} - Usuario: {user_id} - Total: {total_amount} - Pago: {payment_method}")
    
    def log_error(self, error_message, module=None, exception=None):
        """
        Registrar un error
        
        Args:
            error_message: Mensaje de error
            module: Módulo donde ocurrió el error (opcional)
            exception: Excepción que causó el error (opcional)
        """
        module_info = f" en {module}" if module else ""
        exception_info = f" - {str(exception)}" if exception else ""
        
        self.logger.error(f"Error{module_info}: {error_message}{exception_info}")
        
        # Si hay excepción, registrar la traza completa
        if exception:
            self.logger.exception(exception)
    
    def log_system_event(self, event_type, description):
        """
        Registrar evento del sistema
        
        Args:
            event_type: Tipo de evento (inicio, cierre, backup, etc.)
            description: Descripción del evento
        """
        self.logger.info(f"Evento de sistema - {event_type}: {description}")
    
    def log_inventory_change(self, product_id, quantity_change, user_id, reason):
        """
        Registrar cambio en el inventario
        
        Args:
            product_id: ID del producto
            quantity_change: Cambio en la cantidad (positivo o negativo)
            user_id: ID del usuario que realizó el cambio
            reason: Motivo del cambio
        """
        change_type = "incremento" if quantity_change > 0 else "decremento"
        self.logger.info(f"Inventario - {change_type} de {abs(quantity_change)} unidades - Producto: {product_id} - Usuario: {user_id} - Motivo: {reason}")
    
    def log_config_change(self, user_id, config_key, old_value, new_value):
        """
        Registrar cambio en la configuración
        
        Args:
            user_id: ID del usuario que realizó el cambio
            config_key: Clave de configuración modificada
            old_value: Valor anterior
            new_value: Nuevo valor
        """
        self.logger.info(f"Configuración modificada - Clave: {config_key} - Usuario: {user_id} - Anterior: {old_value} - Nuevo: {new_value}")