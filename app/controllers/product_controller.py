# app/controllers/product_controller.py
from datetime import datetime

class ProductController:
    """Controlador para la gestión de productos"""
    
    def __init__(self, database):
        """Inicializar controlador con una conexión a la base de datos"""
        self.db = database
    
    def get_all_products(self, active_only=True):
        """Obtener todos los productos"""
        query = "SELECT * FROM products"
        
        if active_only:
            query += " WHERE is_active = 1"
        
        query += " ORDER BY name"
        
        return self.db.fetch_all(query)
    
    def get_products_by_category(self, category_id, active_only=True):
        """Obtener productos por categoría"""
        query = "SELECT * FROM products WHERE category_id = ?"
        params = [category_id]
        
        if active_only:
            query += " AND is_active = 1"
        
        query += " ORDER BY name"
        
        return self.db.fetch_all(query, params)
    
    def get_product_by_id(self, product_id):
        """Obtener producto por ID"""
        query = "SELECT * FROM products WHERE product_id = ?"
        params = [product_id]
        
        return self.db.fetch_one(query, params)
    
    def get_product_by_barcode(self, barcode):
        """Obtener producto por código de barras"""
        query = "SELECT * FROM products WHERE barcode = ? AND is_active = 1"
        params = [barcode]
        
        return self.db.fetch_one(query, params)
    
    def search_products(self, search_term, active_only=True):
        """Buscar productos por nombre o descripción"""
        query = """
            SELECT * FROM products 
            WHERE (name LIKE ? OR description LIKE ? OR barcode LIKE ?)
        """
        
        if active_only:
            query += " AND is_active = 1"
        
        query += " ORDER BY name"
        
        # Usar '%' para busqueda parcial
        search_param = f"%{search_term}%"
        params = [search_param, search_param, search_param]
        
        return self.db.fetch_all(query, params)
    
    def create_product(self, product_data):
        """Crear un nuevo producto"""
        query = """
            INSERT INTO products (
                barcode, name, description, category_id, 
                price, cost, stock_quantity, min_stock_level, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = [
            product_data.get('barcode'),
            product_data.get('name'),
            product_data.get('description'),
            product_data.get('category_id'),
            product_data.get('price'),
            product_data.get('cost'),
            product_data.get('stock_quantity', 0),
            product_data.get('min_stock_level', 5),
            product_data.get('is_active', 1)
        ]
        
        return self.db.execute(query, params)
    
    def update_product(self, product_id, product_data):
        """Actualizar un producto existente"""
        query = """
            UPDATE products SET 
                barcode = ?, 
                name = ?, 
                description = ?, 
                category_id = ?, 
                price = ?, 
                cost = ?, 
                stock_quantity = ?, 
                min_stock_level = ?, 
                is_active = ?,
                updated_at = ?
            WHERE product_id = ?
        """
        
        params = [
            product_data.get('barcode'),
            product_data.get('name'),
            product_data.get('description'),
            product_data.get('category_id'),
            product_data.get('price'),
            product_data.get('cost'),
            product_data.get('stock_quantity'),
            product_data.get('min_stock_level'),
            product_data.get('is_active'),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            product_id
        ]
        
        return self.db.execute(query, params)
    
    def delete_product(self, product_id):
        """Eliminar un producto (marcarlo como inactivo)"""
        query = "UPDATE products SET is_active = 0 WHERE product_id = ?"
        params = [product_id]
        
        return self.db.execute(query, params)
    
    def update_stock(self, product_id, quantity_change, user_id, movement_type, notes=None, reference_id=None):
        """
        Actualizar el stock de un producto
        
        Args:
            product_id: ID del producto
            quantity_change: Cantidad a cambiar (positivo para incrementar, negativo para disminuir)
            user_id: ID del usuario que realiza el movimiento
            movement_type: Tipo de movimiento ('purchase', 'sale', 'adjustment', 'return')
            notes: Notas opcionales
            reference_id: ID de referencia (ej. ID de venta)
        
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            # Iniciar transacción
            self.db.begin_transaction()
            
            # Actualizar stock del producto
            update_query = "UPDATE products SET stock_quantity = stock_quantity + ? WHERE product_id = ?"
            update_params = [quantity_change, product_id]
            self.db.execute(update_query, update_params)
            
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
                quantity_change, 
                reference_id, 
                notes
            ]
            self.db.execute(movement_query, movement_params)
            
            # Finalizar transacción
            self.db.commit_transaction()
            return True
            
        except Exception as e:
            # Revertir cambios en caso de error
            self.db.rollback_transaction()
            print(f"Error al actualizar stock: {e}")
            return False
    
    def get_low_stock_products(self):
        """Obtener productos con stock bajo el nivel mínimo"""
        query = """
            SELECT * FROM products 
            WHERE is_active = 1 AND stock_quantity <= min_stock_level
            ORDER BY name
        """
        
        return self.db.fetch_all(query)
    
    def get_stock_movements(self, product_id=None, start_date=None, end_date=None, movement_type=None):
        """
        Obtener movimientos de inventario
        
        Args:
            product_id: Filtrar por ID de producto (opcional)
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            movement_type: Tipo de movimiento (opcional)
        
        Returns:
            Lista de movimientos
        """
        query = """
            SELECT m.*, p.name as product_name, u.username as user_name
            FROM inventory_movements m
            JOIN products p ON m.product_id = p.product_id
            JOIN users u ON m.user_id = u.user_id
            WHERE 1=1
        """
        
        params = []
        
        if product_id:
            query += " AND m.product_id = ?"
            params.append(product_id)
        
        if start_date:
            query += " AND m.movement_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND m.movement_date <= ?"
            params.append(end_date)
        
        if movement_type:
            query += " AND m.movement_type = ?"
            params.append(movement_type)
        
        query += " ORDER BY m.movement_date DESC"
        
        return self.db.fetch_all(query, params)
    
    def get_all_categories(self):
        """Obtener todas las categorías"""
        query = "SELECT * FROM categories ORDER BY name"
        return self.db.fetch_all(query)
    
    def create_category(self, name, description=None):
        """Crear una nueva categoría"""
        query = "INSERT INTO categories (name, description) VALUES (?, ?)"
        params = [name, description]
        
        return self.db.execute(query, params)
    
    def update_category(self, category_id, name, description=None):
        """Actualizar una categoría existente"""
        query = "UPDATE categories SET name = ?, description = ? WHERE category_id = ?"
        params = [name, description, category_id]
        
        return self.db.execute(query, params)
    
    def delete_category(self, category_id):
        """Eliminar una categoría"""
        # Verificar que no existan productos asociados
        check_query = "SELECT COUNT(*) as count FROM products WHERE category_id = ?"
        check_params = [category_id]
        
        result = self.db.fetch_one(check_query, check_params)
        
        if result and result['count'] > 0:
            return False  # No se puede eliminar si hay productos asociados
        
        # Eliminar la categoría
        query = "DELETE FROM categories WHERE category_id = ?"
        params = [category_id]
        
        return self.db.execute(query, params)