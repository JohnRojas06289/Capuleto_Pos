# app/utils/config.py
import os
import json
import logging

class Config:
    """Clase para gestionar la configuración del sistema"""
    
    def __init__(self, config_path=None):
        """
        Inicializar configuración
        
        Args:
            config_path: Ruta al archivo de configuración (opcional)
        """
        # Si no se proporciona una ruta, usar la ruta por defecto
        if not config_path:
            self.config_path = os.path.join(os.path.dirname(__file__), 
                                           "../../config/app_config.json")
        else:
            self.config_path = config_path
        
        self.config = {}
        self.logger = logging.getLogger('pos.config')
    
    def load_config(self):
        """
        Cargar configuración desde el archivo
        
        Returns:
            True si se cargó correctamente, False en caso contrario
        """
        try:
            # Verificar si el archivo existe
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Configuración cargada desde: {self.config_path}")
                return True
            else:
                # Si no existe, crear configuración por defecto
                self.config = self._default_config()
                self.save_config()
                self.logger.info("Archivo de configuración no encontrado, se creó uno por defecto")
                return True
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {e}")
            self.config = self._default_config()
            return False
    
    def _default_config(self):
        """Crear configuración por defecto"""
        return {
            "store_name": "Mi Tienda",
            "store_address": "Dirección #123",
            "store_phone": "123-456-7890",
            "tax_rate": 0.16,
            "currency_symbol": "$",
            "database_path": "../database/pos_database.db",
            "language": "es",
            "theme": "light",
            "receipt_header": "Gracias por su compra",
            "receipt_footer": "Vuelva pronto",
            "backup_path": "../backups",
            "auto_backup": True,
            "backup_frequency": "daily",  # daily, weekly, monthly
            "log_level": "INFO"
        }
    
    def save_config(self):
        """
        Guardar configuración en el archivo
        
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            # Asegurarse de que el directorio exista
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            self.logger.info(f"Configuración guardada en: {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error al guardar configuración: {e}")
            return False
    
    def get(self, key, default=None):
        """
        Obtener valor de configuración
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si la clave no existe
            
        Returns:
            Valor de configuración o valor por defecto
        """
        return self.config.get(key, default)
    
    def set(self, key, value):
        """
        Establecer valor de configuración
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
            
        Returns:
            True si se estableció correctamente, False en caso contrario
        """
        try:
            self.config[key] = value
            return True
        except Exception as e:
            self.logger.error(f"Error al establecer configuración: {e}")
            return False
    
    def update(self, new_config):
        """
        Actualizar múltiples valores de configuración
        
        Args:
            new_config: Diccionario con nuevos valores
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            self.config.update(new_config)
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error al actualizar configuración: {e}")
            return False
    
    def reset(self):
        """
        Restablecer configuración a valores por defecto
        
        Returns:
            True si se restableció correctamente, False en caso contrario
        """
        try:
            self.config = self._default_config()
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error al restablecer configuración: {e}")
            return False