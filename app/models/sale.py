# app/models/sale.py
from datetime import datetime, timedelta

class Sale:
    """Modelo para ventas del sistema"""
    
    def __init__(self, database):
        """
        Inicializar modelo con una conexión a la base de datos
        
        Args:
            database: Objeto de conexión a la base de datos
        """
        self.db = database
    
    def get_by_id(self, sale_id):
        """
        Obtener venta por ID junto con sus detalles
        
        Args:
            sale_id: ID de la venta
            
        Returns:
            Diccionario con datos de la venta o None si no existe
        """
        # Consulta para obtener la cabecera de la venta
        sale_query = """
            SELECT s.*, u.username, u.full_name as cashier_name
            FROM sales s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.sale_id = ?
        """
        
        sale = self.db.fetch_one(sale_query, [sale_id])
        
        if not sale:
            return None
            
        # Consulta para obtener los detalles de la venta
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
    
    def create(self, user_id, items, payment_method, total_amount, tax_amount=0, 
              discount_amount=0, customer_name=None, notes=None):
        """
        Crear una nueva venta
        
        Args:
            user_id: ID del usuario que realiza la venta
            items: Lista de items a vender (cada uno con product_id, quantity, unit_price)
            payment_method: Método de pago
            total_amount: Monto total de la venta
            tax_amount: Monto de impuestos
            discount_amount: Monto de descuento
            customer_name: Nombre del cliente (opcional)
            notes: Notas adicionales (opcional)
            
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
                'paid',  # Estado inicial
                notes
            ]
            
            sale_id = self.db.execute(sale_query, sale_params)
            
            if not sale_id:
                raise Exception("No se pudo crear la venta")
            
            # Insertar items de venta
            for item in items:
                product_id = item['product_id']
                quantity = item['quantity']
                unit_price = item['unit_price']
                discount = item.get('discount', 0)
                subtotal = quantity * unit_price - discount
                
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
                
                # Actualizar stock del producto
                stock_query = """
                    UPDATE products
                    SET stock_quantity = stock_quantity - ?,
                        updated_at = ?
                    WHERE product_id = ?
                """
                
                stock_params = [
                    quantity,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    product_id
                ]
                
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
                    'sale',
                    -quantity,  # Negativo porque es una salida
                    sale_id,
                    f"Venta #{sale_id}"
                ]
                
                self.db.execute(movement_query, movement_params)
            
            # Confirmar transacción
            self.db.commit_transaction()
            
            return sale_id
            
        except Exception as e:
            # Revertir transacción en caso de error
            self.db.rollback_transaction()
            print(f"Error al crear venta: {e}")
            return None
    
    def cancel(self, sale_id, user_id, reason=None):
        """
        Cancelar una venta y restaurar el inventario
        
        Args:
            sale_id: ID de la venta a cancelar
            user_id: ID del usuario que realiza la cancelación
            reason: Motivo de la cancelación (opcional)
            
        Returns:
            True si se canceló correctamente, False en caso contrario
        """
        try:
            # Iniciar transacción
            self.db.begin_transaction()
            
            # Verificar si la venta existe y no está cancelada
            sale_query = """
                SELECT payment_status, notes
                FROM sales
                WHERE sale_id = ?
            """
            
            sale = self.db.fetch_one(sale_query, [sale_id])
            
            if not sale:
                raise Exception("Venta no encontrada")
                
            if sale['payment_status'] == 'canceled':
                raise Exception("La venta ya está cancelada")
            
            # Actualizar estado de la venta
            update_query = """
                UPDATE sales
                SET payment_status = 'canceled',
                    notes = ?
                WHERE sale_id = ?
            """
            
            new_notes = f"{sale['notes'] or ''}\nCANCELADA: {reason or 'Sin motivo'} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
            update_params = [new_notes, sale_id]
            
            self.db.execute(update_query, update_params)
            
            # Obtener items de la venta
            items_query = """
                SELECT product_id, quantity
                FROM sale_items
                WHERE sale_id = ?
            """
            
            items = self.db.fetch_all(items_query, [sale_id])
            
            # Restaurar inventario
            for item in items:
                product_id = item['product_id']
                quantity = item['quantity']
                
                # Actualizar stock
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
                
                # Registrar movimiento de inventario
                movement_query = """
                    INSERT INTO inventory_movements (
                        product_id, user_id, movement_type, quantity, reference_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """
                
                movement_params = [
                    product_id,
                    user_id,
                    'return',
                    quantity,  # Positivo porque es una entrada
                    sale_id,
                    f"Cancelación de venta #{sale_id}: {reason or 'Sin motivo'}"
                ]
                
                self.db.execute(movement_query, movement_params)
            
            # Confirmar transacción
            self.db.commit_transaction()
            
            return True
            
        except Exception as e:
            # Revertir transacción en caso de error
            self.db.rollback_transaction()
            print(f"Error al cancelar venta: {e}")
            return False
    
    def get_all(self, start_date=None, end_date=None, user_id=None, 
               payment_method=None, payment_status=None, limit=100):
        """
        Obtener listado de ventas con filtros
        
        Args:
            start_date: Fecha de inicio (formato: YYYY-MM-DD)
            end_date: Fecha de fin (formato: YYYY-MM-DD)
            user_id: ID del usuario
            payment_method: Método de pago
            payment_status: Estado del pago
            limit: Límite de resultados
            
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
        
        # Aplicar filtros
        if start_date:
            query += " AND s.sale_date >= ?"
            params.append(f"{start_date} 00:00:00")
            
        if end_date:
            query += " AND s.sale_date <= ?"
            params.append(f"{end_date} 23:59:59")
            
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
    
    def get_summary_by_day(self, start_date, end_date):
        """
        Obtener resumen de ventas agrupadas por día
        
        Args:
            start_date: Fecha de inicio (formato: YYYY-MM-DD)
            end_date: Fecha de fin (formato: YYYY-MM-DD)
            
        Returns:
            Lista con resumen de ventas por día
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
        
        params = [
            f"{start_date} 00:00:00",
            f"{end_date} 23:59:59"
        ]
        
        return self.db.fetch_all(query, params)
    
    def get_top_products(self, start_date=None, end_date=None, limit=10):
        """
        Obtener los productos más vendidos
        
        Args:
            start_date: Fecha de inicio (formato: YYYY-MM-DD)
            end_date: Fecha de fin (formato: YYYY-MM-DD)
            limit: Límite de resultados
            
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
            params.append(f"{start_date} 00:00:00")
            
        if end_date:
            query += " AND s.sale_date <= ?"
            params.append(f"{end_date} 23:59:59")
            
        query += """
            GROUP BY p.product_id, p.name, p.barcode
            ORDER BY total_quantity DESC
            LIMIT ?
        """
        
        params.append(limit)
        
        return self.db.fetch_all(query, params)
    
    def get_total_by_period(self, period='day'):
        """
        Obtener totales de ventas por período
        
        Args:
            period: Período de agrupación ('day', 'week', 'month', 'year')
            
        Returns:
            Lista con totales por período
        """
        # Definir formato de fecha según el período
        if period == 'day':
            date_format = 'DATE(sale_date)'
            period_name = 'Día'
        elif period == 'week':
            date_format = "strftime('%Y-%W', sale_date)"
            period_name = 'Semana'
        elif period == 'month':
            date_format = "strftime('%Y-%m', sale_date)"
            period_name = 'Mes'
        elif period == 'year':
            date_format = "strftime('%Y', sale_date)"
            period_name = 'Año'
        else:
            # Período no válido, usar día por defecto
            date_format = 'DATE(sale_date)'
            period_name = 'Día'
            
        query = f"""
            SELECT 
                {date_format} as period,
                '{period_name}' as period_type,
                COUNT(*) as total_sales,
                SUM(total_amount) as total_amount,
                SUM(tax_amount) as total_tax,
                AVG(total_amount) as average_sale
            FROM sales
            WHERE payment_status = 'paid'
            GROUP BY {date_format}
            ORDER BY {date_format} DESC
            LIMIT 30
        """
        
        return self.db.fetch_all(query)
    
    def get_today_sales(self):
        """
        Obtener ventas del día actual
        
        Returns:
            Lista de ventas del día actual
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        return self.get_all(start_date=today, end_date=today)
    
    # Métodos para gestión de caja
    
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
        # Verificar si ya hay una caja abierta para este usuario
        check_query = """
            SELECT register_id
            FROM cash_registers
            WHERE user_id = ? AND status = 'open'
        """
        
        check_result = self.db.fetch_one(check_query, [user_id])
        
        if check_result:
            return None  # Ya hay una caja abierta
            
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
    
    def close_cash_register(self, register_id, user_id, closing_amount, 
                           cash_sales, card_sales, other_sales, notes=None):
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
            SELECT register_id
            FROM cash_registers
            WHERE register_id = ? AND user_id = ? AND status = 'open'
        """
        
        check_result = self.db.fetch_one(check_query, [register_id, user_id])
        
        if not check_result:
            return False  # No hay caja abierta o no pertenece al usuario
            
        query = """
            UPDATE cash_registers
            SET closing_amount = ?,
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
    
    def get_open_cash_register(self, user_id):
        """
        Obtener la caja abierta para un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Datos de la caja abierta o None si no hay
        """
        query = """
            SELECT *
            FROM cash_registers
            WHERE user_id = ? AND status = 'open'
        """
        
        return self.db.fetch_one(query, [user_id])
    
    def get_cash_register_by_id(self, register_id):
        """
        Obtener un registro de caja por su ID
        
        Args:
            register_id: ID del registro de caja
            
        Returns:
            Datos del registro de caja o None si no existe
        """
        query = """
            SELECT r.*, u.username, u.full_name
            FROM cash_registers r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.register_id = ?
        """
        
        return self.db.fetch_one(query, [register_id])
    
    def get_sales_by_register(self, register_id):
        """
        Obtener ventas realizadas durante la apertura de una caja
        
        Args:
            register_id: ID del registro de caja
            
        Returns:
            Lista de ventas realizadas durante la apertura de la caja
        """
        # Obtener datos del registro
        register = self.get_cash_register_by_id(register_id)
        
        if not register:
            return []
            
        # Determinar período
        closing_time = register['closing_time'] or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        query = """
            SELECT s.*, u.username, u.full_name as cashier_name
            FROM sales s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.user_id = ?
              AND s.sale_date BETWEEN ? AND ?
            ORDER BY s.sale_date
        """
        
        params = [
            register['user_id'],
            register['opening_time'],
            closing_time
        ]
        
        return self.db.fetch_all(query, params)
        
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
        
        # Obtener ventas en el período
        sales = self.get_sales_by_register(register_id)
        
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