# tests/test_models.py
import unittest
import os
import sys
import tempfile
from datetime import datetime

# Agregar directorio raíz al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar modelos
from app.models.database import Database
from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale
from app.models.inventory import Inventory

class TestDatabase(unittest.TestCase):
    """Pruebas para la clase Database"""
    
    def setUp(self):
        """Configuración para cada prueba"""
        # Crear una base de datos temporal para las pruebas
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix='.db').name
        self.db = Database(self.temp_db_file)
        self.db.connect()
        self.db.init_schema()
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        self.db.close()
        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)
    
    def test_connection(self):
        """Probar conexión a la base de datos"""
        self.assertTrue(os.path.exists(self.temp_db_file))
    
    def test_execute_and_fetch(self):
        """Probar ejecución de consultas y obtención de resultados"""
        # Insertar datos de prueba
        self.db.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                      ["testuser", "password123", "Test User", "admin"])
        
        # Obtener datos
        user = self.db.fetch_one("SELECT * FROM users WHERE username = ?", ["testuser"])
        
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["full_name"], "Test User")
        self.assertEqual(user["role"], "admin")
    
    def test_transaction(self):
        """Probar transacciones"""
        # Iniciar transacción
        self.db.begin_transaction()
        
        # Insertar datos
        self.db.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                      ["user1", "pass1", "User One", "cashier"])
        
        # Confirmar transacción
        self.db.commit_transaction()
        
        # Verificar que se insertaron los datos
        user = self.db.fetch_one("SELECT * FROM users WHERE username = ?", ["user1"])
        self.assertIsNotNone(user)
        
        # Iniciar otra transacción
        self.db.begin_transaction()
        
        # Insertar datos
        self.db.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                      ["user2", "pass2", "User Two", "cashier"])
        
        # Revertir transacción
        self.db.rollback_transaction()
        
        # Verificar que no se insertaron los datos
        user = self.db.fetch_one("SELECT * FROM users WHERE username = ?", ["user2"])
        self.assertIsNone(user)

class TestUserModel(unittest.TestCase):
    """Pruebas para el modelo User"""
    
    def setUp(self):
        """Configuración para cada prueba"""
        # Crear una base de datos temporal para las pruebas
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix='.db').name
        self.db = Database(self.temp_db_file)
        self.db.connect()
        self.db.init_schema()
        
        # Instanciar modelo de usuario
        self.user_model = User(self.db)
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        self.db.close()
        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)
    
    def test_create_user(self):
        """Probar creación de usuarios"""
        # Crear usuario de prueba
        user_id = self.user_model.create("testuser", "password123", "Test User", "admin")
        
        # Verificar que se creó el usuario
        self.assertIsNotNone(user_id)
        
        # Obtener usuario
        user = self.user_model.get_by_username("testuser")
        
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["full_name"], "Test User")
        self.assertEqual(user["role"], "admin")
    
    def test_authenticate(self):
        """Probar autenticación de usuarios"""
        # Crear usuario de prueba
        self.user_model.create("testuser", "password123", "Test User", "admin")
        
        # Autenticar con credenciales correctas
        user = self.user_model.authenticate("testuser", "password123")
        self.assertIsNotNone(user)
        
        # Autenticar con credenciales incorrectas
        user = self.user_model.authenticate("testuser", "wrongpassword")
        self.assertIsNone(user)
        
        user = self.user_model.authenticate("nonexistent", "password123")
        self.assertIsNone(user)
    
    def test_update_user(self):
        """Probar actualización de usuarios"""
        # Crear usuario de prueba
        user_id = self.user_model.create("testuser", "password123", "Test User", "admin")
        
        # Actualizar usuario
        result = self.user_model.update(user_id, "Updated User", "manager")
        self.assertTrue(result)
        
        # Verificar cambios
        user = self.user_model.get_by_id(user_id)
        self.assertEqual(user["full_name"], "Updated User")
        self.assertEqual(user["role"], "manager")
    
    def test_change_password(self):
        """Probar cambio de contraseña"""
        # Crear usuario de prueba
        user_id = self.user_model.create("testuser", "password123", "Test User", "admin")
        
        # Cambiar contraseña
        result = self.user_model.change_password(user_id, "newpassword")
        self.assertTrue(result)
        
        # Verificar que la autenticación funciona con la nueva contraseña
        user = self.user_model.authenticate("testuser", "newpassword")
        self.assertIsNotNone(user)
        
        # Verificar que la autenticación falla con la contraseña anterior
        user = self.user_model.authenticate("testuser", "password123")
        self.assertIsNone(user)

class TestProductModel(unittest.TestCase):
    """Pruebas para el modelo Product"""
    
    def setUp(self):
        """Configuración para cada prueba"""
        # Crear una base de datos temporal para las pruebas
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix='.db').name
        self.db = Database(self.temp_db_file)
        self.db.connect()
        self.db.init_schema()
        
        # Instanciar modelo de producto
        self.product_model = Product(self.db)
        
        # Crear categoría de prueba
        self.db.execute("INSERT INTO categories (name, description) VALUES (?, ?)",
                      ["Test Category", "Category for testing"])
        self.category_id = self.db.cursor.lastrowid
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        self.db.close()
        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)
    
    def test_create_product(self):
        """Probar creación de productos"""
        # Datos de producto
        product_data = {
            "name": "Test Product",
            "barcode": "1234567890123",
            "description": "Product for testing",
            "category_id": self.category_id,
            "price": 10.50,
            "cost": 5.25,
            "stock_quantity": 100,
            "min_stock_level": 10
        }
        
        # Crear producto
        product_id = self.product_model.create(product_data)
        
        # Verificar que se creó el producto
        self.assertIsNotNone(product_id)
        
        # Obtener producto
        product = self.product_model.get_by_id(product_id)
        
        self.assertIsNotNone(product)
        self.assertEqual(product["name"], "Test Product")
        self.assertEqual(product["barcode"], "1234567890123")
        self.assertEqual(float(product["price"]), 10.50)
        self.assertEqual(int(product["stock_quantity"]), 100)
    
    def test_update_product(self):
        """Probar actualización de productos"""
        # Crear producto de prueba
        product_data = {
            "name": "Test Product",
            "price": 10.50,
            "category_id": self.category_id
        }
        product_id = self.product_model.create(product_data)
        
        # Datos actualizados
        updated_data = {
            "name": "Updated Product",
            "price": 15.75,
            "stock_quantity": 50
        }
        
        # Actualizar producto
        result = self.product_model.update(product_id, updated_data)
        self.assertTrue(result)
        
        # Verificar cambios
        product = self.product_model.get_by_id(product_id)
        self.assertEqual(product["name"], "Updated Product")
        self.assertEqual(float(product["price"]), 15.75)
        self.assertEqual(int(product["stock_quantity"]), 50)
    
    def test_update_stock(self):
        """Probar actualización de stock"""
        # Crear producto de prueba
        product_data = {
            "name": "Test Product",
            "price": 10.50,
            "category_id": self.category_id,
            "stock_quantity": 100
        }
        product_id = self.product_model.create(product_data)
        
        # Actualizar stock (incrementar)
        result = self.product_model.update_stock(product_id, 50)
        self.assertTrue(result)
        
        # Verificar incremento
        product = self.product_model.get_by_id(product_id)
        self.assertEqual(int(product["stock_quantity"]), 150)
        
        # Actualizar stock (decrementar)
        result = self.product_model.update_stock(product_id, -30)
        self.assertTrue(result)
        
        # Verificar decremento
        product = self.product_model.get_by_id(product_id)
        self.assertEqual(int(product["stock_quantity"]), 120)
    
    def test_get_low_stock(self):
        """Probar obtención de productos con stock bajo"""
        # Crear productos de prueba
        self.product_model.create({
            "name": "Low Stock Product",
            "price": 10.50,
            "category_id": self.category_id,
            "stock_quantity": 5,
            "min_stock_level": 10
        })
        
        self.product_model.create({
            "name": "Normal Stock Product",
            "price": 15.75,
            "category_id": self.category_id,
            "stock_quantity": 100,
            "min_stock_level": 10
        })
        
        # Obtener productos con stock bajo
        low_stock_products = self.product_model.get_low_stock()
        
        self.assertEqual(len(low_stock_products), 1)
        self.assertEqual(low_stock_products[0]["name"], "Low Stock Product")

class TestSaleModel(unittest.TestCase):
    """Pruebas para el modelo Sale"""
    
    def setUp(self):
        """Configuración para cada prueba"""
        # Crear una base de datos temporal para las pruebas
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix='.db').name
        self.db = Database(self.temp_db_file)
        self.db.connect()
        self.db.init_schema()
        
        # Instanciar modelos
        self.sale_model = Sale(self.db)
        self.user_model = User(self.db)
        self.product_model = Product(self.db)
        
        # Crear usuario de prueba
        self.user_id = self.user_model.create("testuser", "password123", "Test User", "cashier")
        
        # Crear categoría de prueba
        self.db.execute("INSERT INTO categories (name, description) VALUES (?, ?)",
                      ["Test Category", "Category for testing"])
        self.category_id = self.db.cursor.lastrowid
        
        # Crear productos de prueba
        self.product1_id = self.product_model.create({
            "name": "Product 1",
            "price": 10.50,
            "cost": 5.25,
            "category_id": self.category_id,
            "stock_quantity": 100
        })
        
        self.product2_id = self.product_model.create({
            "name": "Product 2",
            "price": 15.75,
            "cost": 7.80,
            "category_id": self.category_id,
            "stock_quantity": 50
        })
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        self.db.close()
        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)
    
    def test_create_sale(self):
        """Probar creación de ventas"""
        # Items para la venta
        items = [
            {"product_id": self.product1_id, "quantity": 2, "unit_price": 10.50},
            {"product_id": self.product2_id, "quantity": 1, "unit_price": 15.75}
        ]
        
        # Crear venta
        sale_id = self.sale_model.create(
            user_id=self.user_id,
            items=items,
            payment_method="cash",
            total_amount=36.75,
            tax_amount=5.88
        )
        
        # Verificar que se creó la venta
        self.assertIsNotNone(sale_id)
        
        # Obtener venta
        sale = self.sale_model.get_by_id(sale_id)
        
        self.assertIsNotNone(sale)
        self.assertEqual(sale["sale"]["user_id"], self.user_id)
        self.assertEqual(float(sale["sale"]["total_amount"]), 36.75)
        self.assertEqual(float(sale["sale"]["tax_amount"]), 5.88)
        self.assertEqual(sale["sale"]["payment_method"], "cash")
        self.assertEqual(len(sale["items"]), 2)
        
        # Verificar que el stock se actualizó
        product1 = self.product_model.get_by_id(self.product1_id)
        product2 = self.product_model.get_by_id(self.product2_id)
        
        self.assertEqual(int(product1["stock_quantity"]), 98)  # 100 - 2
        self.assertEqual(int(product2["stock_quantity"]), 49)  # 50 - 1
    
    def test_cancel_sale(self):
        """Probar cancelación de ventas"""
        # Crear venta de prueba
        items = [
            {"product_id": self.product1_id, "quantity": 2, "unit_price": 10.50}
        ]
        
        sale_id = self.sale_model.create(
            user_id=self.user_id,
            items=items,
            payment_method="cash",
            total_amount=21.00,
            tax_amount=3.36
        )
        
        # Verificar stock después de la venta
        product1 = self.product_model.get_by_id(self.product1_id)
        self.assertEqual(int(product1["stock_quantity"]), 98)  # 100 - 2
        
        # Cancelar venta
        result = self.sale_model.cancel(sale_id, self.user_id, "Prueba de cancelación")
        self.assertTrue(result)
        
        # Verificar estado de la venta
        sale = self.sale_model.get_by_id(sale_id)
        self.assertEqual(sale["sale"]["payment_status"], "canceled")
        
        # Verificar que el stock se restauró
        product1 = self.product_model.get_by_id(self.product1_id)
        self.assertEqual(int(product1["stock_quantity"]), 100)  # Restaurado a 100
    
    def test_get_total_by_period(self):
        """Probar obtención de totales por período"""
        # Crear ventas de prueba
        items1 = [{"product_id": self.product1_id, "quantity": 2, "unit_price": 10.50}]
        items2 = [{"product_id": self.product2_id, "quantity": 3, "unit_price": 15.75}]
        
        self.sale_model.create(user_id=self.user_id, items=items1, payment_method="cash", total_amount=21.00, tax_amount=3.36)
        self.sale_model.create(user_id=self.user_id, items=items2, payment_method="card", total_amount=47.25, tax_amount=7.56)
        
        # Obtener totales por día
        totals = self.sale_model.get_total_by_period("day")
        
        self.assertGreaterEqual(len(totals), 1)
        
        # Debe haber al menos un registro para el día actual
        today = datetime.now().strftime("%Y-%m-%d")
        today_total = next((t for t in totals if t["period"].startswith(today)), None)
        
        self.assertIsNotNone(today_total)
        self.assertEqual(int(today_total["total_sales"]), 2)
        self.assertAlmostEqual(float(today_total["total_amount"]), 68.25, places=2)

class TestInventoryModel(unittest.TestCase):
    """Pruebas para el modelo Inventory"""
    
    def setUp(self):
        """Configuración para cada prueba"""
        # Crear una base de datos temporal para las pruebas
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix='.db').name
        self.db = Database(self.temp_db_file)
        self.db.connect()
        self.db.init_schema()
        
        # Instanciar modelos
        self.inventory_model = Inventory(self.db)
        self.user_model = User(self.db)
        self.product_model = Product(self.db)
        
        # Crear usuario de prueba
        self.user_id = self.user_model.create("testuser", "password123", "Test User", "admin")
        
        # Crear categoría de prueba
        self.db.execute("INSERT INTO categories (name, description) VALUES (?, ?)",
                      ["Test Category", "Category for testing"])
        self.category_id = self.db.cursor.lastrowid
        
        # Crear producto de prueba
        self.product_id = self.product_model.create({
            "name": "Test Product",
            "price": 10.50,
            "cost": 5.25,
            "category_id": self.category_id,
            "stock_quantity": 0  # Iniciamos con stock 0
        })
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        self.db.close()
        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)
    
    def test_add_movement(self):
        """Probar registro de movimientos de inventario"""
        # Registrar entrada de stock
        movement_id = self.inventory_model.add_movement(
            product_id=self.product_id,
            user_id=self.user_id,
            movement_type="purchase",
            quantity=100,
            notes="Compra inicial"
        )
        
        # Verificar que se registró el movimiento
        self.assertIsNotNone(movement_id)
        
        # Verificar que el stock se actualizó
        product = self.product_model.get_by_id(self.product_id)
        self.assertEqual(int(product["stock_quantity"]), 100)
        
        # Registrar salida de stock
        movement_id = self.inventory_model.add_movement(
            product_id=self.product_id,
            user_id=self.user_id,
            movement_type="sale",
            quantity=-10,
            notes="Venta"
        )
        
        # Verificar que se registró el movimiento
        self.assertIsNotNone(movement_id)
        
        # Verificar que el stock se actualizó
        product = self.product_model.get_by_id(self.product_id)
        self.assertEqual(int(product["stock_quantity"]), 90)
    
    def test_adjust_stock(self):
        """Probar ajuste de stock"""
        # Primero agregamos stock inicial
        self.inventory_model.add_movement(
            product_id=self.product_id,
            user_id=self.user_id,
            movement_type="purchase",
            quantity=100,
            notes="Compra inicial"
        )
        
        # Ajustar stock a un valor específico
        result = self.inventory_model.adjust_stock(
            product_id=self.product_id,
            user_id=self.user_id,
            new_quantity=80,
            reason="Ajuste por inventario físico"
        )
        
        self.assertTrue(result)
        
        # Verificar que el stock se ajustó
        product = self.product_model.get_by_id(self.product_id)
        self.assertEqual(int(product["stock_quantity"]), 80)
        
        # Verificar que se registró el movimiento
        movements = self.inventory_model.get_movements(product_id=self.product_id)
        self.assertGreaterEqual(len(movements), 2)  # Al menos los dos movimientos que hemos hecho
        
        # El último movimiento debe ser el ajuste
        last_movement = movements[0]  # Los movimientos se ordenan por fecha descendente
        self.assertEqual(last_movement["movement_type"], "adjustment")
        self.assertEqual(int(last_movement["quantity"]), -20)  # 80 - 100 = -20
    
    def test_get_movement_summary(self):
        """Probar obtención de resumen de movimientos"""
        # Registrar diversos movimientos
        self.inventory_model.add_movement(product_id=self.product_id, user_id=self.user_id,
                                         movement_type="purchase", quantity=100, notes="Compra inicial")
        self.inventory_model.add_movement(product_id=self.product_id, user_id=self.user_id,
                                         movement_type="sale", quantity=-10, notes="Venta 1")
        self.inventory_model.add_movement(product_id=self.product_id, user_id=self.user_id,
                                         movement_type="sale", quantity=-5, notes="Venta 2")
        self.inventory_model.add_movement(product_id=self.product_id, user_id=self.user_id,
                                         movement_type="adjustment", quantity=-2, notes="Ajuste por daño")
        self.inventory_model.add_movement(product_id=self.product_id, user_id=self.user_id,
                                         movement_type="return", quantity=3, notes="Devolución")
        
        # Obtener resumen
        summary = self.inventory_model.get_movement_summary_by_type()
        
        # Verificar que existen todas las categorías de movimientos
        purchase_summary = next((s for s in summary if s["movement_type"] == "purchase"), None)
        sale_summary = next((s for s in summary if s["movement_type"] == "sale"), None)
        adjustment_summary = next((s for s in summary if s["movement_type"] == "adjustment"), None)
        return_summary = next((s for s in summary if s["movement_type"] == "return"), None)
        
        self.assertIsNotNone(purchase_summary)
        self.assertIsNotNone(sale_summary)
        self.assertIsNotNone(adjustment_summary)
        self.assertIsNotNone(return_summary)
        
        # Verificar cantidades
        self.assertEqual(int(purchase_summary["count"]), 1)
        self.assertEqual(int(purchase_summary["total_quantity"]), 100)
        
        self.assertEqual(int(sale_summary["count"]), 2)
        self.assertEqual(int(sale_summary["total_quantity"]), -15)
        
        self.assertEqual(int(adjustment_summary["count"]), 1)
        self.assertEqual(int(adjustment_summary["total_quantity"]), -2)
        
        self.assertEqual(int(return_summary["count"]), 1)
        self.assertEqual(int(return_summary["total_quantity"]), 3)

if __name__ == '__main__':
    unittest.main()