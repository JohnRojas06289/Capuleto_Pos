# app/models/product.py
from datetime import datetime

class Product:
    """Modelo para productos del sistema"""
    
    def __init__(self, database):
        """
        Inicializar modelo con una conexión a la base de datos
        
        Args:
            category_id: ID de la categoría
            
        Returns:
            Diccionario con datos de la categoría o None si no existe
        """
        query = """
            SELECT c.*, 
                   (SELECT COUNT(*) FROM products p WHERE p.category_id = c.category_id) as product_count
            FROM categories c
            WHERE c.category_id = ?
        """
        
        return self.db.fetch_one(query, [category_id])
    
    def create_category(self, name, description=None):
        """
        Crear una nueva categoría
        
        Args:
            name: Nombre de la categoría
            description: Descripción (opcional)
            
        Returns:
            ID de la categoría creada o None si hay error
        """
        query = """
            INSERT INTO categories (name, description)
            VALUES (?, ?)
        """
        
        params = [name, description]
        
        return self.db.execute(query, params)
    
    def update_category(self, category_id, name=None, description=None):
        """
        Actualizar una categoría existente
        
        Args:
            category_id: ID de la categoría
            name: Nuevo nombre (opcional)
            description: Nueva descripción (opcional)
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        # Obtener datos actuales
        category = self.get_category_by_id(category_id)
        if not category:
            return False
            
        # Usar valores actuales si no se proporcionan nuevos
        name = name if name is not None else category['name']
        description = description if description is not None else category['description']
        
        query = """
            UPDATE categories
            SET name = ?, description = ?
            WHERE category_id = ?
        """
        
        params = [name, description, category_id]
        
        return self.db.execute(query, params) > 0
    
    def delete_category(self, category_id):
        """
        Eliminar una categoría
        
        Args:
            category_id: ID de la categoría
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        # Verificar si hay productos en esta categoría
        product_count_query = """
            SELECT COUNT(*) as count
            FROM products
            WHERE category_id = ?
        """
        
        result = self.db.fetch_one(product_count_query, [category_id])
        if result and result['count'] > 0:
            return False  # No se puede eliminar si tiene productos asociados
            
        query = """
            DELETE FROM categories
            WHERE category_id = ?
        """
        
        params = [category_id]
        
        return self.db.execute(query, params) > 0
            database: Objeto de conexión a la base de datos
        """
        self.db = database
    
    def get_by_id(self, product_id):
        """
        Obtener producto por ID
        
        Args:
            product_id: ID del producto
            
        Returns:
            Diccionario con datos del producto o None si no existe
        """
        query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.product_id = ?
        """
        return self.db.fetch_one(query, [product_id])
    
    def get_by_barcode(self, barcode):
        """
        Obtener producto por código de barras
        
        Args:
            barcode: Código de barras del producto
            
        Returns:
            Diccionario con datos del producto o None si no existe
        """
        query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.barcode = ?
        """
        return self.db.fetch_one(query, [barcode])
    
    def get_all(self, active_only=True):
        """
        Obtener todos los productos
        
        Args:
            active_only: Si es True, solo devuelve productos activos
            
        Returns:
            Lista de diccionarios con datos de productos
        """
        query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
        """
        
        if active_only:
            query += " WHERE p.is_active = 1"
            
        query += " ORDER BY p.name"
        
        return self.db.fetch_all(query)
    
    def get_by_category(self, category_id, active_only=True):
        """
        Obtener productos por categoría
        
        Args:
            category_id: ID de la categoría
            active_only: Si es True, solo devuelve productos activos
            
        Returns:
            Lista de diccionarios con datos de productos
        """
        query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.category_id = ?
        """
        
        if active_only:
            query += " AND p.is_active = 1"
            
        query += " ORDER BY p.name"
        
        return self.db.fetch_all(query, [category_id])
    
    def search(self, term, active_only=True):
        """
        Buscar productos por nombre, descripción o código de barras
        
        Args:
            term: Término de búsqueda
            active_only: Si es True, solo devuelve productos activos
            
        Returns:
            Lista de diccionarios con datos de productos
        """
        query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE (p.name LIKE ? OR p.description LIKE ? OR p.barcode LIKE ?)
        """
        
        if active_only:
            query += " AND p.is_active = 1"
            
        query += " ORDER BY p.name"
        
        search_term = f"%{term}%"
        params = [search_term, search_term, search_term]
        
        return self.db.fetch_all(query, params)
    
    def create(self, data):
        """
        Crear un nuevo producto
        
        Args:
            data: Diccionario con datos del producto
                - name: Nombre del producto (obligatorio)
                - barcode: Código de barras (opcional)
                - description: Descripción (opcional)
                - category_id: ID de la categoría (opcional)
                - price: Precio de venta (obligatorio)
                - cost: Costo de adquisición (opcional)
                - stock_quantity: Cantidad en stock (opcional, por defecto 0)
                - min_stock_level: Nivel mínimo de stock (opcional, por defecto 5)
                - is_active: Si el producto está activo (opcional, por defecto True)
                
        Returns:
            ID del producto creado o None si hay error
        """
        # Validar campos obligatorios
        if 'name' not in data or 'price' not in data:
            return None
            
        query = """
            INSERT INTO products (
                name, barcode, description, category_id, 
                price, cost, stock_quantity, min_stock_level, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = [
            data.get('name'),
            data.get('barcode'),
            data.get('description'),
            data.get('category_id'),
            data.get('price'),
            data.get('cost'),
            data.get('stock_quantity', 0),
            data.get('min_stock_level', 5),
            1 if data.get('is_active', True) else 0
        ]
        
        return self.db.execute(query, params)
    
    def update(self, product_id, data):
        """
        Actualizar un producto existente
        
        Args:
            product_id: ID del producto a actualizar
            data: Diccionario con datos del producto a actualizar
                - name: Nombre del producto (opcional)
                - barcode: Código de barras (opcional)
                - description: Descripción (opcional)
                - category_id: ID de la categoría (opcional)
                - price: Precio de venta (opcional)
                - cost: Costo de adquisición (opcional)
                - stock_quantity: Cantidad en stock (opcional)
                - min_stock_level: Nivel mínimo de stock (opcional)
                - is_active: Si el producto está activo (opcional)
                
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        # Obtener datos actuales
        product = self.get_by_id(product_id)
        if not product:
            return False
            
        # Preparar campos a actualizar
        update_fields = []
        params = []
        
        for field in ['name', 'barcode', 'description', 'category_id', 'price', 
                     'cost', 'stock_quantity', 'min_stock_level', 'is_active']:
            if field in data:
                value = data[field]
                if field == 'is_active':
                    value = 1 if value else 0
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        # Agregar fecha de actualización
        update_fields.append("updated_at = ?")
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Agregar ID del producto al final de los parámetros
        params.append(product_id)
        
        if not update_fields:
            return False
            
        query = f"""
            UPDATE products 
            SET {', '.join(update_fields)}
            WHERE product_id = ?
        """
        
        return self.db.execute(query, params) > 0
    
    def update_stock(self, product_id, quantity_change):
        """
        Actualizar la cantidad en stock de un producto
        
        Args:
            product_id: ID del producto
            quantity_change: Cambio en la cantidad (positivo para aumentar, negativo para disminuir)
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        query = """
            UPDATE products
            SET stock_quantity = stock_quantity + ?,
                updated_at = ?
            WHERE product_id = ?
        """
        
        params = [
            quantity_change,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            product_id
        ]
        
        return self.db.execute(query, params) > 0
    
    def delete(self, product_id):
        """
        Eliminar lógicamente un producto (marcar como inactivo)
        
        Args:
            product_id: ID del producto
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        query = """
            UPDATE products
            SET is_active = 0,
                updated_at = ?
            WHERE product_id = ?
        """
        
        params = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            product_id
        ]
        
        return self.db.execute(query, params) > 0
    
    def get_low_stock(self):
        """
        Obtener productos con stock bajo el nivel mínimo
        
        Returns:
            Lista de diccionarios con datos de productos con stock bajo
        """
        query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.is_active = 1 AND p.stock_quantity <= p.min_stock_level
            ORDER BY (p.min_stock_level - p.stock_quantity) DESC
        """
        
        return self.db.fetch_all(query)
    
    # Métodos para categorías
    
    def get_all_categories(self):
        """
        Obtener todas las categorías de productos
        
        Returns:
            Lista de diccionarios con datos de categorías
        """
        query = """
            SELECT c.*, 
                   (SELECT COUNT(*) FROM products p WHERE p.category_id = c.category_id) as product_count
            FROM categories c
            ORDER BY c.name
        """
        
        return self.db.fetch_all(query)
    
    def get_category_by_id(self, category_id):
        """
        Obtener una categoría por su ID
        
        Args: