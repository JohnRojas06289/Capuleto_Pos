# app/models/database.py
import os
import sqlite3
import logging
from datetime import datetime

class Database:
    """Clase para gestionar la conexión y operaciones con la base de datos SQLite"""
    
    def __init__(self, db_path):
        """
        Inicializar conexión a base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.logger = logging.getLogger('pos.database')
    
    def connect(self):
        """
        Establecer conexión a la base de datos
        
        Returns:
            Diccionario con el resultado o None si no hay resultados
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            row = self.cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            self.logger.error(f"Error al ejecutar consulta: {e}\nQuery: {query}\nParams: {params}")
            raise
    
    def fetch_all(self, query, params=None):
        """
        Ejecutar una consulta SQL y obtener todos los resultados
        
        Args:
            query: Consulta SQL
            params: Parámetros para la consulta (opcional)
            
        Returns:
            Lista de diccionarios con los resultados
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            rows = self.cursor.fetchall()
            
            # Convertir cada fila a diccionario
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error al ejecutar consulta: {e}\nQuery: {query}\nParams: {params}")
            raise
    
    def begin_transaction(self):
        """Iniciar una transacción"""
        self.conn.execute("BEGIN TRANSACTION")
    
    def commit_transaction(self):
        """Confirmar una transacción"""
        self.conn.commit()
    
    def rollback_transaction(self):
        """Revertir una transacción"""
        self.conn.rollback():
            True si se conectó correctamente, False en caso contrario
        """
        try:
            # Asegurarse de que el directorio exista
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Conectar a la base de datos
            self.conn = sqlite3.connect(self.db_path)
            
            # Configurar para devolver resultados como diccionarios
            self.conn.row_factory = sqlite3.Row
            
            # Crear cursor
            self.cursor = self.conn.cursor()
            
            self.logger.info(f"Conexión establecida a la base de datos: {self.db_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error al conectar a la base de datos: {e}")
            return False
    
    def is_new_database(self):
        """
        Verificar si la base de datos es nueva
        
        Returns:
            True si es una base de datos nueva, False si ya está inicializada
        """
        try:
            # Verificar si la tabla 'users' existe
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            result = self.cursor.fetchone()
            
            return result is None
        except Exception as e:
            self.logger.error(f"Error al verificar si la base de datos es nueva: {e}")
            return True  # Si hay error, asumir que es nueva
    
    def init_schema(self):
        """
        Inicializar el esquema de la base de datos
        
        Returns:
            True si se inicializó correctamente, False en caso contrario
        """
        try:
            # Cargar y ejecutar el script SQL
            script_path = os.path.join(os.path.dirname(__file__), '../../database/schema.sql')
            
            # Si existe el archivo, cargarlo
            if os.path.exists(script_path):
                with open(script_path, 'r') as f:
                    sql_script = f.read()
                self.conn.executescript(sql_script)
            else:
                # Si no existe, crear las tablas básicas manualmente
                self._create_basic_schema()
            
            self.conn.commit()
            self.logger.info("Esquema de base de datos inicializado")
            return True
        except Exception as e:
            self.logger.error(f"Error al inicializar el esquema: {e}")
            return False
    
    def _create_basic_schema(self):
        """Crear esquema básico si no existe el archivo de esquema"""
        # Tabla de usuarios
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Tabla de categorías
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            )
        ''')
        
        # Tabla de productos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                category_id INTEGER,
                price DECIMAL(10,2) NOT NULL,
                cost DECIMAL(10,2),
                stock_quantity INTEGER DEFAULT 0,
                min_stock_level INTEGER DEFAULT 5,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        ''')
        
        # Tabla de ventas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                customer_name TEXT,
                total_amount DECIMAL(10,2) NOT NULL,
                tax_amount DECIMAL(10,2) DEFAULT 0,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                payment_method TEXT NOT NULL,
                payment_status TEXT NOT NULL,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Tabla de detalles de venta
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                discount DECIMAL(10,2) DEFAULT 0,
                subtotal DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(sale_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        ''')
        
        # Tabla de movimientos de inventario
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_movements (
                movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                reference_id INTEGER,
                movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Tabla de cajas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cash_registers (
                register_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                opening_amount DECIMAL(10,2) NOT NULL,
                closing_amount DECIMAL(10,2),
                cash_sales DECIMAL(10,2) DEFAULT 0,
                card_sales DECIMAL(10,2) DEFAULT 0,
                other_sales DECIMAL(10,2) DEFAULT 0,
                opening_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closing_time TIMESTAMP,
                notes TEXT,
                status TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Tabla de configuración
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT NOT NULL UNIQUE,
                config_value TEXT NOT NULL,
                description TEXT
            )
        ''')
        
        # Insertar configuración inicial
        self.cursor.execute('''
            INSERT INTO system_config (config_key, config_value, description) VALUES
            ('store_name', 'Mi Tienda', 'Nombre del negocio'),
            ('store_address', 'Dirección #123', 'Dirección del negocio'),
            ('store_phone', '123-456-7890', 'Teléfono del negocio'),
            ('tax_rate', '0.16', 'Tasa de impuesto por defecto (IVA)'),
            ('printer_model', 'WPRP-260', 'Modelo de impresora'),
            ('currency_symbol', '$', 'Símbolo de moneda')
        ''')
        
        # Insertar usuario administrador por defecto (contraseña: admin)
        self.cursor.execute('''
            INSERT INTO users (username, password, full_name, role) VALUES
            ('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Administrador', 'admin')
        ''')
    
    def close(self):
        """Cerrar la conexión a la base de datos"""
        if self.conn:
            self.conn.close()
            self.logger.info("Conexión a la base de datos cerrada")
    
    def execute(self, query, params=None):
        """
        Ejecutar una consulta SQL que modifica datos
        
        Args:
            query: Consulta SQL
            params: Parámetros para la consulta (opcional)
            
        Returns:
            ID del último registro insertado o número de filas afectadas
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            self.conn.commit()
            
            # Si es una inserción, devolver el ID del último registro insertado
            if query.strip().upper().startswith("INSERT"):
                return self.cursor.lastrowid
            else:
                return self.cursor.rowcount
        except Exception as e:
            self.logger.error(f"Error al ejecutar consulta: {e}\nQuery: {query}\nParams: {params}")
            raise
    
    def fetch_one(self, query, params=None):
        """
        Ejecutar una consulta SQL y obtener un único resultado
        
        Args:
            query: Consulta SQL
            params: Parámetros para la consulta (opcional)
            
        Returns