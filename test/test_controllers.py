# tests/test_controllers.py
import unittest
import os
import sys
import tempfile
from datetime import datetime, timedelta

# Agregar directorio raíz al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar modelos y controladores
from app.models.database import Database
from app.controllers.user_controller import UserController
from app.controllers.product_controller import ProductController
from app.controllers.sales_controller import SalesController
from app.controllers.report_controller import ReportController

class TestUserController(unittest.TestCase):
    """Pruebas para UserController"""
    
    def setUp(self):
        """Configuración para cada prueba"""
        # Crear una base de datos temporal para las pruebas
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix='.db').name
        self.db = Database(self.temp_db_file)
        self.db.connect()
        self.db.init_schema()
        
        # Instanciar controlador
        self.user_controller = UserController(self.db)
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        self.db.close()
        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)
    
    def test_create_and_authenticate(self):
        """Probar creación y autenticación de usuarios"""
        # Crear usuario
        user_id = self.user_controller.create_user(
            username="testuser",
            password="password123",
            full_name="Test User",
            role="admin"
        )
        
        self.assertIsNotNone(user_id)
        
        # Autenticar con credenciales correctas
        user = self.user_controller.authenticate("testuser", "password123")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["full_name"], "Test User")
        self.assertEqual(user["role"], "admin")
        
        # Autenticar con credenciales incorrectas
        user = self.user_controller.authenticate("testuser", "wrongpassword")
        self.assertIsNone(user)
    
    def test_get_all_users(self):
        """Probar obtención de usuarios"""
        # Crear usuarios de prueba
        self.user_controller.create_user("user1", "pass1", "User One", "admin")
        self.user_controller.create_user("user2", "pass2", "User Two", "cashier")
        self.user_controller.create_user("user3", "pass3", "User Three", "manager")
        
        # Obtener todos los usuarios
        users = self.user_controller.get_all_users()
        
        self.assertEqual(len(users), 3)
        
        # Verificar que estén todos los usuarios creados
        usernames = [user["username"] for user in users]
        self.assertIn("user1", usernames)
        self.assertIn("user2", usernames)
        self.assertIn("user3", usernames)
    
    def test_update_user(self):
        """Probar actualización de usuarios"""
        # Crear usuario de prueba
        user_id = self.user_controller.create_user("testuser", "pass1", "Test User", "cashier")
        
        # Actualizar usuario
        result = self.user_controller.update_user(user_id, full_name="Updated User", role="manager")
        self.assertTrue(result)
        
        # Verificar cambios
        user = self.user_controller.get_user_by_id(user_id)
        self.assertEqual(user["full_name"], "Updated User")
        self.assertEqual(user["role"], "manager")
    
    def test_disable_and_enable_user(self):
        """Probar desactivación y activación de usuarios"""
        # Crear usuario de prueba
        user_id = self.user_controller.create_user("testuser", "pass1", "Test User", "cashier")
        
        # Desactivar usuario
        result = self.user_controller.disable_user(user_id)
        self.assertTrue(result)
        
        # Verificar que el usuario está desactivado
        user = self.user_controller.get_user_by_id(user_id)
        self.assertEqual(user["is_active"], 0)
        
        # Verificar que no puede autenticarse
        auth_user = self.user_controller.authenticate("testuser", "pass1")
        self.assertIsNone(auth_user)
        
        # Activar usuario
        result = self.user_controller.enable_user(user_id)
        self.assertTrue(result)
        
        # Verificar que el usuario está activado
        user = self.user_controller.get_user_by_id(user_id)
        self.assertEqual(user["is_active"], 1)
        
        # Verificar que puede autenticarse
        auth_user = self.user_controller.authenticate("testuser", "pass1")
        self.assertIsNotNone(auth_user)

class TestProductController(unittest.TestCase):
    """Pruebas para ProductController"""
    
    def setUp(self):
        """Configuración para cada prueba"""
        # Crear una base de datos temporal para las pruebas
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix='.db').name
        self.db = Database(self.temp_db_file)
        self.db.connect()
        self.db.init_schema()
        
        # Instanciar controlador
        self.product_controller = ProductController(self.db)
        
        # Crear categoría de prueba
        self.db.execute("INSERT INTO categories (name, description) VALUES (?, ?)",
                      ["Test Category", "Category for testing"])
        self.category_id = self.db.cursor.lastrowid
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        self.db.close()
        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)
    
    def test_create_and_get_product(self):
        """Probar creación y obtención de productos"""
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
        product_id = self.product_controller.create_product(product_data)
        self.assertIsNotNone(product_id)
        
        # Obtener producto por ID
        product = self.product_controller.get_product_by_id(product_id)
        self.assertIsNotNone(product)
        self.assertEqual(product["name"], "Test Product")
        self.assertEqual(product["barcode"], "1234567890123")
        self.assertEqual(float(product["price"]), 10.50)
        
        # Obtener producto por código de barras
        product = self.product_controller.get_product_by_barcode("1234567890123")
        self.assertIsNotNone(product)
        self.assertEqual(product["name"], "Test Product")
    
    def test_search_products(self):
        """Probar búsqueda de productos"""
        # Crear productos de prueba
        self.product_controller.create_product({
            "name": "Agua Mineral",
            "barcode": "1111111111111",
            "category_id": self.category_id,
            "price": 10.0
        })
        
        self.product_controller.create_product({
            "name": "Refresco Cola",
            "barcode": "2222222222222",
            "category_id": self.category_id,
            "price": 15.0
        })
        
        self.product_controller.create_product({
            "name": "Jugo de Naranja",
            "barcode": "3333333333333",
            "category_id": self.category_id,
            "price": 20.0
        })
        
        # Buscar por nombre
        results = self.product_controller.search_products("agua")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Agua Mineral")
        
        # Buscar por código de barras
        results = self.product_controller.search_products("222")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Refresco Cola")
        
        # Buscar por término que coincida con varios productos
        results = self.product_controller.search_products("a")
        self.assertGreaterEqual(len(results), 2)  # Debe encontrar "Agua" y "Naranja"
    
    def test_update_stock(self):
        """Probar actualización de stock"""
        # Crear producto de prueba con stock inicial de 100
        product_id = self.product_controller.create_product({
            "name": "Test Product",
            "category_id": self.category_id,
            "price": 10.0,
            "stock_quantity": 100
        })
        
        # Incrementar stock en 50 unidades
        result = self.product_controller.update_stock(
            product_id=product_id,
            quantity_change=50,
            user_id=1,  # Usuario ficticio
            movement_type="purchase",
            notes="Compra adicional"
        )
        
        self.assertTrue(result)
        
        # Verificar que el stock se actualizó
        product = self.product_controller.get_product_by_id(product_id)
        self.assertEqual(int(product["stock_quantity"]), 150)
        
        # Decrementar stock en 30 unidades
        result = self.product_controller.update_stock(
            product_id=product_id,
            quantity_change=-30,
            user_id=1,
            movement_type="sale",
            notes="Venta"
        )
        
        self.assertTrue(result)
        
        # Verificar que el stock se actualizó
        product = self.product_controller.get_product_by_id(product_id)
        self.assertEqual(int(product["stock_quantity"]), 120)
    
    def test_get_low_stock_products(self):
        """Probar obtención de productos con stock bajo"""
        # Crear productos de prueba
        self.product_controller.create_product({
            "name": "Low Stock Product",
            "category_id": self.category_id,
            "price": 10.0,
            "stock_quantity": 5,
            "min_stock_level": 10
        })
        
        self.product_controller.create_product({
            "name": "Normal Stock Product",
            "category_id": self.category_id,
            "price": 20.0,
            "stock_quantity": 100,
            "min_stock_level": 10
        })
        
        # Obtener productos con stock bajo
        low_stock = self.product_controller.get_low_stock_products()
        
        self.assertEqual(len(low_stock), 1)
        self.assertEqual(low_stock[0]["name"], "Low Stock Product")

class TestSalesController(unittest.TestCase):
    """Pruebas para SalesController"""
    
    def setUp(self):
        """Configuración para cada prueba"""
        # Crear una base de datos temporal para las pruebas
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix='.db').name
        self.db = Database(self.temp_db_file)
        self.db.connect()
        self.db.init_schema()
        
        # Instanciar controladores
        self.sales_controller = SalesController(self.db)
        self.product_controller = ProductController(self.db)
        
        # Crear usuario de prueba
        self.db.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                      ["testuser", "password123", "Test User", "cashier"])
        self.user_id = self.db.cursor.lastrowid
        
        # Crear categoría de prueba
        self.db.execute("INSERT INTO categories (name, description) VALUES (?, ?)",
                      ["Test Category", "Category for testing"])
        self.category_id = self.db.cursor.lastrowid
        
        # Crear productos de prueba
        product_data1 = {
            "name": "Product 1",
            "barcode": "1111111111111",
            "category_id": self.category_id,
            "price": 10.0,
            "cost": 5.0,
            "stock_quantity": 100
        }
        
        product_data2 = {
            "name": "Product 2",
            "barcode": "2222222222222",
            "category_id": self.category_id,
            "price": 20.0,
            "cost": 10.0,
            "stock_quantity": 50
        }
        
        self.product1_id = self.product_controller.create_product(product_data1)
        self.product2_id = self.product_controller.create_product(product_data2)
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        self.db.close()
        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)
    
    def test_create_and_get_sale(self):
        """Probar creación y obtención de ventas"""
        # Crear venta
        items = [
            {
                "product_id": self.product1_id,
                "quantity": 2,
                "unit_price": 10.0,
                "subtotal": 20.0
            },
            {
                "product_id": self.product2_id,
                "quantity": 1,
                "unit_price": 20.0,
                "subtotal": 20.0
            }
        ]
        
        sale_id = self.sales_controller.create_sale(
            user_id=self.user_id,
            items=items,
            payment_method="cash",
            total_amount=40.0,
            tax_amount=6.4
        )
        
        self.assertIsNotNone(sale_id)
        
        # Obtener venta
        sale = self.sales_controller.get_sale_by_id(sale_id)
        self.assertIsNotNone(sale)
        
        # Verificar datos de la venta
        self.assertEqual(sale["sale"]["user_id"], self.user_id)
        self.assertEqual(float(sale["sale"]["total_amount"]), 40.0)
        self.assertEqual(float(sale["sale"]["tax_amount"]), 6.4)
        self.assertEqual(sale["sale"]["payment_method"], "cash")
        
        # Verificar items
        self.assertEqual(len(sale["items"]), 2)
        
        # Verificar que el stock se actualizó
        product1 = self.product_controller.get_product_by_id(self.product1_id)
        product2 = self.product_controller.get_product_by_id(self.product2_id)
        
        self.assertEqual(int(product1["stock_quantity"]), 98)  # 100 - 2
        self.assertEqual(int(product2["stock_quantity"]), 49)  # 50 - 1
    
    def test_cancel_sale(self):
        """Probar cancelación de ventas"""
        # Crear venta
        items = [
            {
                "product_id": self.product1_id,
                "quantity": 5,
                "unit_price": 10.0,
                "subtotal": 50.0
            }
        ]
        
        sale_id = self.sales_controller.create_sale(
            user_id=self.user_id,
            items=items,
            payment_method="cash",
            total_amount=50.0,
            tax_amount=8.0
        )
        
        # Verificar stock después de la venta
        product1 = self.product_controller.get_product_by_id(self.product1_id)
        self.assertEqual(int(product1["stock_quantity"]), 95)  # 100 - 5
        
        # Cancelar venta
        result = self.sales_controller.cancel_sale(
            sale_id=sale_id,
            user_id=self.user_id,
            reason="Producto defectuoso"
        )
        
        self.assertTrue(result)
        
        # Verificar estado de la venta
        sale = self.sales_controller.get_sale_by_id(sale_id)
        self.assertEqual(sale["sale"]["payment_status"], "canceled")
        
        # Verificar que el stock se restauró
        product1 = self.product_controller.get_product_by_id(self.product1_id)
        self.assertEqual(int(product1["stock_quantity"]), 100)  # Restaurado a 100
    
    def test_get_sales_by_date_range(self):
        """Probar obtención de ventas por rango de fechas"""
        # Crear ventas con fechas diferentes
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Insertar ventas con fechas específicas (no podemos usar create_sale aquí porque usa la fecha actual)
        self.db.execute(
            "INSERT INTO sales (user_id, total_amount, tax_amount, payment_method, payment_status, sale_date) VALUES (?, ?, ?, ?, ?, ?)",
            [self.user_id, 100.0, 16.0, "cash", "paid", f"{today} 10:00:00"]
        )
        
        self.db.execute(
            "INSERT INTO sales (user_id, total_amount, tax_amount, payment_method, payment_status, sale_date) VALUES (?, ?, ?, ?, ?, ?)",
            [self.user_id, 200.0, 32.0, "card", "paid", f"{today} 15:00:00"]
        )
        
        self.db.execute(
            "INSERT INTO sales (user_id, total_amount, tax_amount, payment_method, payment_status, sale_date) VALUES (?, ?, ?, ?, ?, ?)",
            [self.user_id, 150.0, 24.0, "cash", "paid", f"{yesterday} 14:00:00"]
        )
        
        # Obtener ventas de hoy
        today_sales = self.sales_controller.get_sales_by_date_range(today, today)
        self.assertEqual(len(today_sales), 2)
        
        # Obtener ventas de ayer
        yesterday_sales = self.sales_controller.get_sales_by_date_range(yesterday, yesterday)
        self.assertEqual(len(yesterday_sales), 1)
        
        # Obtener ventas de ayer y hoy
        all_sales = self.sales_controller.get_sales_by_date_range(yesterday, today)
        self.assertEqual(len(all_sales), 3)
    
    def test_get_sales_summary_by_day(self):
        """Probar obtención de resumen de ventas por día"""
        # Crear ventas con fechas y métodos de pago diferentes
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Ventas de hoy
        self.db.execute(
            "INSERT INTO sales (user_id, total_amount, tax_amount, payment_method, payment_status, sale_date) VALUES (?, ?, ?, ?, ?, ?)",
            [self.user_id, 100.0, 16.0, "cash", "paid", f"{today} 10:00:00"]
        )
        
        self.db.execute(
            "INSERT INTO sales (user_id, total_amount, tax_amount, payment_method, payment_status, sale_date) VALUES (?, ?, ?, ?, ?, ?)",
            [self.user_id, 200.0, 32.0, "card", "paid", f"{today} 15:00:00"]
        )
        
        # Venta de ayer
        self.db.execute(
            "INSERT INTO sales (user_id, total_amount, tax_amount, payment_method, payment_status, sale_date) VALUES (?, ?, ?, ?, ?, ?)",
            [self.user_id, 150.0, 24.0, "cash", "paid", f"{yesterday} 14:00:00"]
        )
        
        # Obtener resumen
        summary = self.sales_controller.get_sales_summary_by_day(yesterday, today)
        
        self.assertEqual(len(summary), 2)  # Debe haber datos para 2 días
        
        # Verificar resumen de hoy
        today_summary = next((s for s in summary if s["date"] == today), None)
        self.assertIsNotNone(today_summary)
        self.assertEqual(int(today_summary["total_sales"]), 2)
        self.assertEqual(float(today_summary["total_amount"]), 300.0)
        self.assertEqual(float(today_summary["cash_amount"]), 100.0)
        self.assertEqual(float(today_summary["card_amount"]), 200.0)
        
        # Verificar resumen de ayer
        yesterday_summary = next((s for s in summary if s["date"] == yesterday), None)
        self.assertIsNotNone(yesterday_summary)
        self.assertEqual(int(yesterday_summary["total_sales"]), 1)
        self.assertEqual(float(yesterday_summary["total_amount"]), 150.0)
        self.assertEqual(float(yesterday_summary["cash_amount"]), 150.0)

class TestReportController(unittest.TestCase):
    """Pruebas básicas para ReportController"""
    
    def setUp(self):
        """Configuración para cada prueba"""
        # Crear una base de datos temporal para las pruebas
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix='.db').name
        self.db = Database(self.temp_db_file)
        self.db.connect()
        self.db.init_schema()
        
        # Instanciar otros controladores necesarios
        self.sales_controller = SalesController(self.db)
        self.product_controller = ProductController(self.db)
        self.user_controller = UserController(self.db)
        
        # Instanciar controlador de reportes
        self.report_controller = ReportController(
            database=self.db,
            sales_controller=self.sales_controller,
            product_controller=self.product_controller,
            user_controller=self.user_controller
        )
        
        # Crear directorio temporal para reportes
        self.reports_dir = tempfile.mkdtemp()
        # Sobrescribir el directorio de reportes del controlador
        self.report_controller.reports_dir = self.reports_dir
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        self.db.close()
        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)
        
        # Eliminar directorio de reportes
        import shutil
        shutil.rmtree(self.reports_dir)
    
    def test_generate_daily_sales_report(self):
        """Probar generación de reporte de ventas diarias"""
        # Este es un test mínimo que solo verifica que no haya errores al generar el reporte
        # Para pruebas más completas se necesitaría configurar datos de ventas, etc.
        
        # Generar reporte CSV (más simple de verificar que PDF)
        today = datetime.now().strftime("%Y-%m-%d")
        report_path = self.report_controller.generate_daily_sales_report(date=today, format='csv')
        
        # Verificar que se generó un archivo
        self.assertIsNotNone(report_path)
        self.assertTrue(os.path.exists(report_path))
        
        # Verificar que tiene el formato esperado
        filename = os.path.basename(report_path)
        expected_prefix = f"ventas_diarias_{today.replace('-', '')}"
        self.assertTrue(filename.startswith(expected_prefix))
        self.assertTrue(filename.endswith('.csv'))
    
    def test_generate_inventory_report(self):
        """Probar generación de reporte de inventario"""
        # Este es un test mínimo que solo verifica que no haya errores al generar el reporte
        
        # Generar reporte CSV
        report_path = self.report_controller.generate_inventory_report(format='csv')
        
        # Verificar que se generó un archivo
        self.assertIsNotNone(report_path)
        self.assertTrue(os.path.exists(report_path))
        
        # Verificar que tiene el formato esperado
        filename = os.path.basename(report_path)
        expected_prefix = "inventario_completo"
        self.assertTrue(filename.startswith(expected_prefix))
        self.assertTrue(filename.endswith('.csv'))

if __name__ == '__main__':
    unittest.main()