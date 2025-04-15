# app/controllers/sales_controller.py
from datetime import datetime, timedelta

class SalesController:
    """Controlador para la gestión de ventas"""
    
    def __init__(self, database):
        """Inicializar controlador con una conexión a la base de datos"""
        self.db = database
    
    def create_sale(self, user_id, items, payment_method, total_amount, tax_amount=0, discount_amount=0, customer_name=None, notes=None):
        """
        Crear una nueva venta
        
        Args:
            user_id: ID del usuario que realiza la venta
            items: Lista de productos vendidos con sus cantidades
            payment_method: Método de pago ('cash', 'card', 'transfer')
            total_amount: Monto total de la venta
            tax_amount: Monto de impuestos
            discount_amount: Monto de descuento
            customer_name: Nombre del cliente (opcional)
            notes: Notas adicionales
        
        Returns:
            ID de la venta creada o None si hay error
        """
        try:
            # Iniciar transacción
            self.db.begin_transaction()
            
            # Insertar cabecera de venta
            sale_query = """
                INSERT INTO sales (
                    user_id, customer_name, total_amount, tax_amount, 
                    discount_amount, payment_method, payment_status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            sale_params = [
                user_id,
                customer_name,
                total_amount,
                tax_amount,
                discount_amount,
                payment_method,
                'paid',  # Estado de pago por defecto
                notes
            ]
            
            sale_id = self.db.execute(sale_query, sale_params)
            
            if not sale_id:
                raise Exception("No se pudo crear la venta")
            
            # Insertar detalles de venta
            for item in items:
                product_id = item.get('product_id')
                quantity = int(item.get('quantity', 1))
                unit_price = float(item.get('price').replace('$', '')) if isinstance(item.get('price'), str) else float(item.get('price', 0))
                discount = float(item.get('discount', 0))
                subtotal = float(item.get('subtotal').replace('$', '')) if isinstance(item.get('subtotal'), str) else float(item.get('subtotal', 0))
                
                # Insertar detalle
                item_query = """
                    INSERT INTO sale_items (
                        sale_id, product_id, quantity, unit_price, discount, subtotal
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """
                
                item_params = [
                    sale_id,
                    product_id,
                    quantity,
                    unit_price,
                    discount,
                    subtotal
                ]
                
                self.db.execute(item_query, item_params)
                
                # Actualizar stock (restar)
                stock_query = """
                    UPDATE products 
                    SET stock_quantity = stock_quantity - ? 
                    WHERE product_id = ?
                """
                
                stock_params = [quantity, product_id]
                self.db.execute(stock_query, stock_params)
                
                # Registrar movimiento de inventario
                movement_query = """
                    INSERT INTO inventory_movements (
                        product_id, user_id, movement_type, quantity, reference_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """
                
                movement_params = [
                    product_id,
                    user_id,
                    'sale',  # Tipo de movimiento
                    -quantity,  # Cantidad negativa (salida)
                    sale_id,  # Referencia a la venta
                    f"Venta #{sale_id}"
                ]
                
                self.db.execute(movement_query, movement_params)
            
            # Finalizar transacción
            self.db.commit_transaction()
            
            return sale_id
            
        except Exception as e:
            # Revertir cambios en caso de error
            self.db.rollback_transaction()
            print(f"Error al crear venta: {e}")
            return None
    
    def cancel_sale(self, sale_id, user_id, reason=None):
        """
        Cancelar una venta y restaurar el inventario
        
        Args:
            sale_id: ID de la venta a cancelar
            user_id: ID del usuario que realiza la cancelación
            reason: Motivo de la cancelación
            
        Returns:
            True si se canceló correctamente, False en caso contrario
        """
        try:
            # Iniciar transacción
            self.db.begin_transaction()
            
            # Verificar si la venta existe
            sale_query = "SELECT * FROM sales WHERE sale_id = ?"
            sale = self.db.fetch_one(sale_query, [sale_id])
            
            if not sale:
                raise Exception("Venta no encontrada")
            
            if sale['payment_status'] == 'canceled':
                raise Exception("La venta ya está cancelada")
            
            # Actualizar estado de la venta
            update_query = """
                UPDATE sales 
                SET payment_status = 'canceled', notes = ? 
                WHERE sale_id = ?
            """
            
            notes = f"{sale['notes'] or ''}\nCANCELADA: {reason or 'Sin motivo'}"
            update_params = [notes, sale_id]
            
            self.db.execute(update_query, update_params)
            
            # Obtener detalles de la venta
            items_query = "SELECT * FROM sale_items WHERE sale_id = ?"
            items = self.db.fetch_all(items_query, [sale_id])
            
            for item in items:
                product_id = item['product_id']
                quantity = item['quantity']
                
                # Restaurar stock
                stock_query = """
                    UPDATE products 
                    SET stock_quantity = stock_quantity + ? 
                    WHERE product_id = ?
                """
                
                stock_params = [quantity, product_id]
                self.db.execute(stock_query, stock_params)
                
                # Registrar movimiento de inventario
                movement_query = """
                    INSERT INTO inventory_movements (
                        product_id, user_id, movement_type, quantity, reference_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """
                
                movement_params = [
                    product_id,
                    user_id,
                    'return',  # Tipo de movimiento
                    quantity,  # Cantidad positiva (entrada)
                    sale_id,  # Referencia a la venta
                    f"Cancelación de venta #{sale_id}: {reason or 'Sin motivo'}"
                ]
                
                self.db.execute(movement_query, movement_params)
            
            # Finalizar transacción
            self.db.commit_transaction()
            
            return True
            
        except Exception as e:
            # Revertir cambios en caso de error
            self.db.rollback_transaction()
            print(f"Error al cancelar venta: {e}")
            return False
    
    def get_sale_by_id(self, sale_id):
        """
        Obtener una venta por su ID
        
        Args:
            sale_id: ID de la venta
            
        Returns:
            Diccionario con la información de la venta y sus detalles
        """
        # Consultar cabecera de venta
        sale_query = """
            SELECT s.*, u.username, u.full_name as cashier_name
            FROM sales s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.sale_id = ?
        """
        
        sale = self.db.fetch_one(sale_query, [sale_id])
        
        if not sale:
            return None
        
        # Consultar detalles de venta
        items_query = """
            SELECT si.*, p.name as product_name, p.barcode
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            WHERE si.sale_id = ?
        """
        
        items = self.db.fetch_all(items_query, [sale_id])
        
        # Construir resultado completo
        result = {
            'sale': sale,
            'items': items
        }
        
        return result
    
    def get_sales(self, start_date=None, end_date=None, user_id=None, payment_method=None, payment_status=None, limit=100):
        """
        Obtener listado de ventas con filtros
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            user_id: ID del usuario (opcional)
            payment_method: Método de pago (opcional)
            payment_status: Estado de pago (opcional)
            limit: Límite de resultados (por defecto 100)
            
        Returns:
            Lista de ventas
        """
        query = """
            SELECT s.*, u.username, u.full_name as cashier_name
            FROM sales s
            JOIN users u ON s.user_id = u.user_id
            WHERE 1=1
        """
        
        params = []
        
        if start_date:
            query += " AND s.sale_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND s.sale_date <= ?"
            params.append(end_date)
        
        if user_id:
            query += " AND s.user_id = ?"
            params.append(user_id)
        
        if payment_method:
            query += " AND s.payment_method = ?"
            params.append(payment_method)
        
        if payment_status:
            query += " AND s.payment_status = ?"
            params.append(payment_status)
        
        query += " ORDER BY s.sale_date DESC LIMIT ?"
        params.append(limit)
        
        return self.db.fetch_all(query, params)
    
    def get_sales_by_date_range(self, start_date, end_date):
        """
        Obtener ventas en un rango de fechas para reportes
        
        Args:
            start_date: Fecha de inicio (formato YYYY-MM-DD)
            end_date: Fecha de fin (formato YYYY-MM-DD)
            
        Returns:
            Lista de ventas en el rango de fechas
        """
        # Ajustar el rango para incluir todo el día
        start = f"{start_date} 00:00:00"
        end = f"{end_date} 23:59:59"
        
        query = """
            SELECT s.*, u.username, u.full_name as cashier_name
            FROM sales s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.sale_date BETWEEN ? AND ?
            ORDER BY s.sale_date
        """
        
        params = [start, end]
        
        return self.db.fetch_all(query, params)
    
    def get_sales_summary_by_day(self, start_date, end_date):
        """
        Obtener resumen de ventas agrupadas por día
        
        Args:
            start_date: Fecha de inicio (formato YYYY-MM-DD)
            end_date: Fecha de fin (formato YYYY-MM-DD)
            
        Returns:
            Resumen de ventas por día
        """
        query = """
            SELECT 
                DATE(sale_date) as date,
                COUNT(*) as total_sales,
                SUM(total_amount) as total_amount,
                SUM(tax_amount) as total_tax,
                SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END) as cash_amount,
                SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END) as card_amount,
                SUM(CASE WHEN payment_method = 'transfer' THEN total_amount ELSE 0 END) as transfer_amount
            FROM sales
            WHERE sale_date BETWEEN ? AND ?
            AND payment_status = 'paid'
            GROUP BY DATE(sale_date)
            ORDER BY DATE(sale_date)
        """
        
        # Ajustar el rango para incluir todo el día
        start = f"{start_date} 00:00:00"
        end = f"{end_date} 23:59:59"
        
        params = [start, end]
        
        return self.db.fetch_all(query, params)
    
    def get_top_selling_products(self, start_date=None, end_date=None, limit=10):
        """
        Obtener los productos más vendidos
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            limit: Límite de resultados (por defecto 10)
            
        Returns:
            Lista de productos más vendidos
        """
        query = """
            SELECT 
                p.product_id,
                p.name as product_name,
                p.barcode,
                SUM(si.quantity) as total_quantity,
                SUM(si.subtotal) as total_amount
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE s.payment_status = 'paid'
        """
        
        params = []
        
        if start_date:
            query += " AND s.sale_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND s.sale_date <= ?"
            params.append(end_date)
        
        query += """
            GROUP BY p.product_id, p.name, p.barcode
            ORDER BY total_quantity DESC
            LIMIT ?
        """
        
        params.append(limit)
        
        return self.db.fetch_all(query, params)
    
    def get_daily_cash_flow(self, date=None):
        """
        Obtener el flujo de caja diario
        
        Args:
            date: Fecha a consultar (por defecto hoy)
            
        Returns:
            Resumen del flujo de caja
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Ajustar para incluir todo el día
        start_date = f"{date} 00:00:00"
        end_date = f"{date} 23:59:59"
        
        query = """
            SELECT 
                SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END) as cash_sales,
                SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END) as card_sales,
                SUM(CASE WHEN payment_method = 'transfer' THEN total_amount ELSE 0 END) as transfer_sales,
                SUM(total_amount) as total_sales,
                COUNT(*) as total_transactions
            FROM sales
            WHERE sale_date BETWEEN ? AND ?
            AND payment_status = 'paid'
        """
        
        params = [start_date, end_date]
        
        return self.db.fetch_one(query, params)
    
    def open_cash_register(self, user_id, opening_amount, notes=None):
        """
        Abrir caja registradora
        
        Args:
            user_id: ID del usuario que abre la caja
            opening_amount: Monto inicial
            notes: Notas adicionales
            
        Returns:
            ID del registro de caja o None si hay error
        """
        # Verificar si hay una caja abierta
        check_query = """
            SELECT * FROM cash_registers
            WHERE user_id = ? AND status = 'open'
        """
        
        check_params = [user_id]
        existing = self.db.fetch_one(check_query, check_params)
        
        if existing:
            # Ya hay una caja abierta para este usuario
            return None
        
        # Insertar registro de apertura
        query = """
            INSERT INTO cash_registers (
                user_id, opening_amount, opening_time, status, notes
            ) VALUES (?, ?, ?, ?, ?)
        """
        
        params = [
            user_id,
            opening_amount,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'open',
            notes
        ]
        
        return self.db.execute(query, params)
    
    def close_cash_register(self, register_id, user_id, closing_amount, cash_sales, card_sales, other_sales, notes=None):
        """
        Cerrar caja registradora
        
        Args:
            register_id: ID del registro de caja
            user_id: ID del usuario que cierra la caja
            closing_amount: Monto final
            cash_sales: Ventas en efectivo
            card_sales: Ventas con tarjeta
            other_sales: Otras ventas
            notes: Notas adicionales
            
        Returns:
            True si se cerró correctamente, False en caso contrario
        """
        # Verificar si la caja existe y está abierta
        check_query = """
            SELECT * FROM cash_registers
            WHERE register_id = ? AND user_id = ? AND status = 'open'
        """
        
        check_params = [register_id, user_id]
        register = self.db.fetch_one(check_query, check_params)
        
        if not register:
            # No se encontró la caja o ya está cerrada
            return False
        
        # Actualizar registro con datos de cierre
        query = """
            UPDATE cash_registers SET
                closing_amount = ?,
                cash_sales = ?,
                card_sales = ?,
                other_sales = ?,
                closing_time = ?,
                status = 'closed',
                notes = ?
            WHERE register_id = ?
        """
        
        params = [
            closing_amount,
            cash_sales,
            card_sales,
            other_sales,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            notes,
            register_id
        ]
        
        return self.db.execute(query, params) > 0
    
    def get_register_status(self, user_id):
        """
        Verificar estado de caja para un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con información de la caja o None si no hay caja abierta
        """
        query = """
            SELECT * FROM cash_registers
            WHERE user_id = ? AND status = 'open'
            ORDER BY opening_time DESC
            LIMIT 1
        """
        
        params = [user_id]
        
        return self.db.fetch_one(query, params)
    
    def get_register_sales(self, register_id):
        """
        Obtener ventas asociadas a un registro de caja
        
        Args:
            register_id: ID del registro de caja
            
        Returns:
            Ventas realizadas durante la apertura de caja
        """
        # Obtener datos del registro
        register_query = "SELECT * FROM cash_registers WHERE register_id = ?"
        register = self.db.fetch_one(register_query, [register_id])
        
        if not register:
            return []
        
        # Obtener ventas en el periodo
        sales_query = """
            SELECT * FROM sales
            WHERE user_id = ?
            AND sale_date BETWEEN ? AND ?
            ORDER BY sale_date
        """
        
        closing_time = register['closing_time'] or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        params = [
            register['user_id'],
            register['opening_time'],
            closing_time
        ]
        
        return self.db.fetch_all(sales_query, params)
    
    def generate_z_report(self, register_id):
        """
        Generar reporte Z (cierre de caja)
        
        Args:
            register_id: ID del registro de caja
            
        Returns:
            Diccionario con información del reporte Z
        """
        # Obtener datos del registro
        register_query = """
            SELECT r.*, u.username, u.full_name
            FROM cash_registers r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.register_id = ?
        """
        
        register = self.db.fetch_one(register_query, [register_id])
        
        if not register:
            return None
        
        # Obtener ventas en el periodo
        sales = self.get_register_sales(register_id)
        
        # Calcular totales
        total_cash = sum(s['total_amount'] for s in sales if s['payment_method'] == 'cash' and s['payment_status'] == 'paid')
        total_card = sum(s['total_amount'] for s in sales if s['payment_method'] == 'card' and s['payment_status'] == 'paid')
        total_transfer = sum(s['total_amount'] for s in sales if s['payment_method'] == 'transfer' and s['payment_status'] == 'paid')
        total_sales = total_cash + total_card + total_transfer
        
        # Calcular cancelaciones
        total_canceled = sum(s['total_amount'] for s in sales if s['payment_status'] == 'canceled')
        
        # Preparar resultado
        result = {
            'register': register,
            'sales_count': len([s for s in sales if s['payment_status'] == 'paid']),
            'canceled_count': len([s for s in sales if s['payment_status'] == 'canceled']),
            'total_cash': total_cash,
            'total_card': total_card,
            'total_transfer': total_transfer,
            'total_sales': total_sales,
            'total_canceled': total_canceled,
            'opening_amount': register['opening_amount'],
            'closing_amount': register['closing_amount'],
            'expected_amount': register['opening_amount'] + total_cash,
            'difference': (register['closing_amount'] or 0) - (register['opening_amount'] + total_cash),
            'opening_time': register['opening_time'],
            'closing_time': register['closing_time'],
            'sales': sales
        }
        
        return result