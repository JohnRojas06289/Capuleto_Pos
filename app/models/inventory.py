# app/models/inventory.py
from datetime import datetime

class Inventory:
    """Modelo para gestión del inventario"""
    
    def __init__(self, database):
        """
        Inicializar modelo con una conexión a la base de datos
        
        Args:
            database: Objeto de conexión a la base de datos
        """
        self.db = database
    
    def get_movements(self, product_id=None, user_id=None, movement_type=None, 
                     start_date=None, end_date=None, limit=100):
        """
        Obtener movimientos de inventario con filtros
        
        Args:
            product_id: ID del producto (opcional)
            user_id: ID del usuario (opcional)
            movement_type: Tipo de movimiento (opcional): 'purchase', 'sale', 'adjustment', 'return'
            start_date: Fecha de inicio (formato: YYYY-MM-DD)
            end_date: Fecha de fin (formato: YYYY-MM-DD)
            limit: Límite de resultados
            
        Returns:
            Lista de movimientos de inventario
        """
        query = """
            SELECT m.*, 
                   p.name as product_name, 
                   p.barcode, 
                   u.username, 
                   u.full_name as user_name
            FROM inventory_movements m
            JOIN products p ON m.product_id = p.product_id
            JOIN users u ON m.user_id = u.user_id
            WHERE 1=1
        """
        
        params = []
        
        # Aplicar filtros
        if product_id:
            query += " AND m.product_id = ?"
            params.append(product_id)
            
        if user_id:
            query += " AND m.user_id = ?"
            params.append(user_id)
            
        if movement_type:
            query += " AND m.movement_type = ?"
            params.append(movement_type)
            
        if start_date:
            query += " AND m.movement_date >= ?"
            params.append(f"{start_date} 00:00:00")
            
        if end_date:
            query += " AND m.movement_date <= ?"
            params.append(f"{end_date} 23:59:59")
            
        query += " ORDER BY m.movement_date DESC LIMIT ?"
        params.append(limit)
        
        return self.db.fetch_all(query, params)
    
    def get_movement_by_id(self, movement_id):
        """
        Obtener un movimiento por su ID
        
        Args:
            movement_id: ID del movimiento
            
        Returns:
            Datos del movimiento o None si no existe
        """
        query = """
            SELECT m.*, 
                   p.name as product_name, 
                   p.barcode, 
                   u.username, 
                   u.full_name as user_name
            FROM inventory_movements m
            JOIN products p ON m.product_id = p.product_id
            JOIN users u ON m.user_id = u.user_id
            WHERE m.movement_id = ?
        """
        
        return self.db.fetch_one(query, [movement_id])
    
    def add_movement(self, product_id, user_id, movement_type, quantity, 
                    reference_id=None, notes=None):
        """
        Registrar un movimiento de inventario y actualizar el stock del producto
        
        Args:
            product_id: ID del producto
            user_id: ID del usuario que realiza el movimiento
            movement_type: Tipo de movimiento: 'purchase', 'sale', 'adjustment', 'return'
            quantity: Cantidad (positiva para entradas, negativa para salidas)
            reference_id: ID de referencia (opcional, por ejemplo ID de venta)
            notes: Notas adicionales (opcional)
            
        Returns:
            ID del movimiento creado o None si hay error
        """
        try:
            # Iniciar transacción
            self.db.begin_transaction()
            
            # Registrar movimiento
            movement_query = """
                INSERT INTO inventory_movements (
                    product_id, user_id, movement_type, quantity, reference_id, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            
            movement_params = [
                product_id,
                user_id,
                movement_type,
                quantity,
                reference_id,
                notes
            ]
            
            movement_id = self.db.execute(movement_query, movement_params)
            
            if not movement_id:
                raise Exception("No se pudo registrar el movimiento")
            
            # Actualizar stock del producto
            stock_query = """
                UPDATE products
                SET stock_quantity = stock_quantity + ?,
                    updated_at = ?
                WHERE product_id = ?
            """
            
            stock_params = [
                quantity,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                product_id
            ]
            
            self.db.execute(stock_query, stock_params)
            
            # Confirmar transacción
            self.db.commit_transaction()
            
            return movement_id
            
        except Exception as e:
            # Revertir transacción en caso de error
            self.db.rollback_transaction()
            print(f"Error al registrar movimiento: {e}")
            return None
    
    def adjust_stock(self, product_id, user_id, new_quantity, reason=None):
        """
        Ajustar el stock de un producto a una cantidad específica
        
        Args:
            product_id: ID del producto
            user_id: ID del usuario que realiza el ajuste
            new_quantity: Nueva cantidad de stock
            reason: Motivo del ajuste (opcional)
            
        Returns:
            True si se ajustó correctamente, False en caso contrario
        """
        try:
            # Obtener cantidad actual
            query = "SELECT stock_quantity FROM products WHERE product_id = ?"
            product = self.db.fetch_one(query, [product_id])
            
            if not product:
                return False
                
            current_quantity = product['stock_quantity']
            quantity_change = new_quantity - current_quantity
            
            if quantity_change == 0:
                return True  # No hay cambio, no es necesario ajustar
                
            # Registrar movimiento
            notes = f"Ajuste de inventario: {current_quantity} -> {new_quantity}"
            if reason:
                notes += f". Motivo: {reason}"
                
            return self.add_movement(
                product_id=product_id,
                user_id=user_id,
                movement_type='adjustment',
                quantity=quantity_change,
                notes=notes
            ) is not None
            
        except Exception as e:
            print(f"Error al ajustar stock: {e}")
            return False
    
    def get_stock_value(self):
        """
        Calcular el valor total del inventario
        
        Returns:
            Valor total del inventario y detalles por producto
        """
        query = """
            SELECT p.product_id, 
                   p.name, 
                   p.barcode, 
                   p.stock_quantity, 
                   p.cost, 
                   (p.stock_quantity * p.cost) as total_value,
                   c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.is_active = 1
            ORDER BY total_value DESC
        """
        
        products = self.db.fetch_all(query)
        
        # Calcular total general
        total_value = sum(p['total_value'] or 0 for p in products)
        
        return {
            'total_value': total_value,
            'products': products
        }
    
    def get_low_stock_products(self):
        """
        Obtener productos con stock bajo el nivel mínimo
        
        Returns:
            Lista de productos con stock bajo
        """
        query = """
            SELECT p.*, 
                   c.name as category_name,
                   (p.min_stock_level - p.stock_quantity) as missing_quantity
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.is_active = 1 AND p.stock_quantity <= p.min_stock_level
            ORDER BY missing_quantity DESC
        """
        
        return self.db.fetch_all(query)
    
    def get_product_movement_history(self, product_id, limit=50):
        """
        Obtener historial de movimientos de un producto
        
        Args:
            product_id: ID del producto
            limit: Límite de resultados
            
        Returns:
            Lista de movimientos del producto
        """
        return self.get_movements(product_id=product_id, limit=limit)
    
    def get_stock_changes_by_period(self, period='day', start_date=None, end_date=None):
        """
        Obtener cambios de stock agrupados por período
        
        Args:
            period: Período de agrupación ('day', 'week', 'month', 'year')
            start_date: Fecha de inicio (formato: YYYY-MM-DD)
            end_date: Fecha de fin (formato: YYYY-MM-DD)
            
        Returns:
            Lista con cambios de stock por período
        """
        # Definir formato de fecha según el período
        if period == 'day':
            date_format = 'DATE(movement_date)'
            period_name = 'Día'
        elif period == 'week':
            date_format = "strftime('%Y-%W', movement_date)"
            period_name = 'Semana'
        elif period == 'month':
            date_format = "strftime('%Y-%m', movement_date)"
            period_name = 'Mes'
        elif period == 'year':
            date_format = "strftime('%Y', movement_date)"
            period_name = 'Año'
        else:
            # Período no válido, usar día por defecto
            date_format = 'DATE(movement_date)'
            period_name = 'Día'
            
        query = f"""
            SELECT 
                {date_format} as period,
                '{period_name}' as period_type,
                SUM(CASE WHEN movement_type = 'purchase' THEN quantity ELSE 0 END) as purchases,
                SUM(CASE WHEN movement_type = 'sale' THEN ABS(quantity) ELSE 0 END) as sales,
                SUM(CASE WHEN movement_type = 'adjustment' THEN quantity ELSE 0 END) as adjustments,
                SUM(CASE WHEN movement_type = 'return' THEN quantity ELSE 0 END) as returns,
                SUM(quantity) as net_change
            FROM inventory_movements
            WHERE 1=1
        """
        
        params = []
        
        if start_date:
            query += " AND movement_date >= ?"
            params.append(f"{start_date} 00:00:00")
            
        if end_date:
            query += " AND movement_date <= ?"
            params.append(f"{end_date} 23:59:59")
            
        query += f"""
            GROUP BY {date_format}
            ORDER BY {date_format}
        """
        
        return self.db.fetch_all(query, params)
    
    def get_movement_summary_by_type(self, start_date=None, end_date=None):
        """
        Obtener resumen de movimientos por tipo
        
        Args:
            start_date: Fecha de inicio (formato: YYYY-MM-DD)
            end_date: Fecha de fin (formato: YYYY-MM-DD)
            
        Returns:
            Resumen de movimientos por tipo
        """
        query = """
            SELECT 
                movement_type,
                COUNT(*) as count,
                SUM(quantity) as total_quantity,
                AVG(quantity) as average_quantity
            FROM inventory_movements
            WHERE 1=1
        """
        
        params = []
        
        if start_date:
            query += " AND movement_date >= ?"
            params.append(f"{start_date} 00:00:00")
            
        if end_date:
            query += " AND movement_date <= ?"
            params.append(f"{end_date} 23:59:59")
            
        query += """
            GROUP BY movement_type
            ORDER BY movement_type
        """
        
        return self.db.fetch_all(query, params)