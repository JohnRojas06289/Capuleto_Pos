# app/controllers/report_controller.py
import os
import csv
import json
import logging
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # Usar backend no interactivo
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages

class ReportController:
    """Controlador para generación de reportes"""
    
    def __init__(self, database, sales_controller, product_controller, user_controller):
        """
        Inicializar controlador de reportes
        
        Args:
            database: Objeto de conexión a la base de datos
            sales_controller: Controlador de ventas
            product_controller: Controlador de productos
            user_controller: Controlador de usuarios
        """
        self.db = database
        self.sales_controller = sales_controller
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.logger = logging.getLogger('pos.reports')
        
        # Directorio para guardar reportes
        self.reports_dir = os.path.join(os.path.dirname(__file__), '../../reports')
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_daily_sales_report(self, date=None, format='pdf'):
        """
        Generar reporte de ventas diarias
        
        Args:
            date: Fecha para el reporte (formato: YYYY-MM-DD) o None para hoy
            format: Formato del reporte ('pdf', 'csv', 'json')
            
        Returns:
            Ruta al archivo de reporte generado o None si hay error
        """
        try:
            # Si no se especifica fecha, usar la fecha actual
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Obtener datos de ventas del día
            sales = self.sales_controller.get_all(start_date=date, end_date=date)
            
            # Nombre del archivo
            filename = f"ventas_diarias_{date.replace('-', '')}"
            
            if format == 'pdf':
                return self._generate_daily_sales_pdf(sales, date, filename)
            elif format == 'csv':
                return self._generate_daily_sales_csv(sales, date, filename)
            elif format == 'json':
                return self._generate_daily_sales_json(sales, date, filename)
            else:
                self.logger.error(f"Formato de reporte no válido: {format}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error al generar reporte de ventas diarias: {e}")
            return None
    
    def _generate_daily_sales_pdf(self, sales, date, filename):
        """Generar reporte de ventas diarias en PDF"""
        try:
            filepath = os.path.join(self.reports_dir, f"{filename}.pdf")
            
            # Calcular totales
            total_amount = sum(sale['total_amount'] for sale in sales)
            total_tax = sum(sale['tax_amount'] for sale in sales)
            cash_sales = sum(sale['total_amount'] for sale in sales if sale['payment_method'] == 'cash')
            card_sales = sum(sale['total_amount'] for sale in sales if sale['payment_method'] == 'card')
            transfer_sales = sum(sale['total_amount'] for sale in sales if sale['payment_method'] == 'transfer')
            
            # Crear PDF
            with PdfPages(filepath) as pdf:
                # Página 1: Resumen
                plt.figure(figsize=(10, 8))
                plt.suptitle(f"Reporte de Ventas Diarias - {date}", fontsize=16)
                
                # Información general
                info_text = (
                    f"Fecha: {date}\n"
                    f"Total de ventas: {len(sales)}\n"
                    f"Monto total: ${total_amount:.2f}\n"
                    f"Impuestos: ${total_tax:.2f}\n\n"
                    f"Ventas por método de pago:\n"
                    f"  Efectivo: ${cash_sales:.2f}\n"
                    f"  Tarjeta: ${card_sales:.2f}\n"
                    f"  Transferencia: ${transfer_sales:.2f}\n"
                )
                
                plt.figtext(0.1, 0.8, info_text, fontsize=12)
                
                # Gráfico de métodos de pago
                ax1 = plt.subplot(2, 1, 2)
                labels = ['Efectivo', 'Tarjeta', 'Transferencia']
                values = [cash_sales, card_sales, transfer_sales]
                
                ax1.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
                ax1.axis('equal')
                ax1.set_title('Ventas por Método de Pago')
                
                plt.tight_layout()
                pdf.savefig()
                plt.close()
                
                # Página 2: Ventas por hora
                if sales:
                    plt.figure(figsize=(10, 8))
                    plt.suptitle(f"Ventas por Hora - {date}", fontsize=16)
                    
                    # Agrupar ventas por hora
                    sales_by_hour = {}
                    for sale in sales:
                        sale_datetime = datetime.strptime(sale['sale_date'], "%Y-%m-%d %H:%M:%S")
                        hour = sale_datetime.hour
                        if hour not in sales_by_hour:
                            sales_by_hour[hour] = {'count': 0, 'amount': 0}
                        sales_by_hour[hour]['count'] += 1
                        sales_by_hour[hour]['amount'] += sale['total_amount']
                    
                    # Ordenar por hora
                    hours = sorted(sales_by_hour.keys())
                    counts = [sales_by_hour[h]['count'] for h in hours]
                    amounts = [sales_by_hour[h]['amount'] for h in hours]
                    
                    # Gráfico de cantidad de ventas por hora
                    ax1 = plt.subplot(2, 1, 1)
                    ax1.bar(hours, counts, color='skyblue')
                    ax1.set_title('Cantidad de Ventas por Hora')
                    ax1.set_xlabel('Hora')
                    ax1.set_ylabel('Cantidad')
                    ax1.set_xticks(range(24))
                    
                    # Gráfico de monto de ventas por hora
                    ax2 = plt.subplot(2, 1, 2)
                    ax2.bar(hours, amounts, color='lightgreen')
                    ax2.set_title('Monto de Ventas por Hora')
                    ax2.set_xlabel('Hora')
                    ax2.set_ylabel('Monto ($)')
                    ax2.set_xticks(range(24))
                    
                    plt.tight_layout()
                    pdf.savefig()
                    plt.close()
                
                # Página 3: Listado de ventas
                if sales:
                    plt.figure(figsize=(10, 8))
                    plt.suptitle(f"Listado de Ventas - {date}", fontsize=16)
                    
                    # Crear tabla
                    table_data = []
                    for i, sale in enumerate(sales):
                        sale_time = datetime.strptime(sale['sale_date'], "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                        table_data.append([
                            f"{sale['sale_id']}",
                            sale_time,
                            sale['cashier_name'],
                            sale['payment_method'],
                            f"${sale['total_amount']:.2f}"
                        ])
                    
                    # Crear tabla
                    ax = plt.subplot(1, 1, 1)
                    ax.axis('off')
                    table = ax.table(
                        cellText=table_data,
                        colLabels=['ID', 'Hora', 'Cajero', 'Método de Pago', 'Total'],
                        loc='center',
                        cellLoc='center'
                    )
                    
                    # Ajustar tamaño de tabla
                    table.auto_set_font_size(False)
                    table.set_fontsize(10)
                    table.scale(1, 1.5)
                    
                    plt.tight_layout()
                    pdf.savefig()
                    plt.close()
            
            self.logger.info(f"Reporte de ventas diarias generado: {filepath}")
            return filepath
        
        except Exception as e:
            self.logger.error(f"Error al generar PDF de ventas diarias: {e}")
            return None
    
    def _generate_daily_sales_csv(self, sales, date, filename):
        """Generar reporte de ventas diarias en CSV"""
        try:
            filepath = os.path.join(self.reports_dir, f"{filename}.csv")
            
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Encabezados
                writer.writerow(['ID', 'Fecha', 'Hora', 'Cajero', 'Cliente', 'Método de Pago', 
                               'Subtotal', 'Impuestos', 'Total', 'Estado'])
                
                # Datos
                for sale in sales:
                    sale_datetime = datetime.strptime(sale['sale_date'], "%Y-%m-%d %H:%M:%S")
                    sale_date = sale_datetime.strftime("%Y-%m-%d")
                    sale_time = sale_datetime.strftime("%H:%M:%S")
                    
                    writer.writerow([
                        sale['sale_id'],
                        sale_date,
                        sale_time,
                        sale['cashier_name'],
                        sale['customer_name'] or 'N/A',
                        sale['payment_method'],
                        f"{sale['total_amount'] - sale['tax_amount']:.2f}",
                        f"{sale['tax_amount']:.2f}",
                        f"{sale['total_amount']:.2f}",
                        sale['payment_status']
                    ])
            
            self.logger.info(f"Reporte CSV de ventas diarias generado: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error al generar CSV de ventas diarias: {e}")
            return None
    
    def _generate_daily_sales_json(self, sales, date, filename):
        """Generar reporte de ventas diarias en JSON"""
        try:
            filepath = os.path.join(self.reports_dir, f"{filename}.json")
            
            # Calcular totales
            total_amount = sum(sale['total_amount'] for sale in sales)
            total_tax = sum(sale['tax_amount'] for sale in sales)
            cash_sales = sum(sale['total_amount'] for sale in sales if sale['payment_method'] == 'cash')
            card_sales = sum(sale['total_amount'] for sale in sales if sale['payment_method'] == 'card')
            transfer_sales = sum(sale['total_amount'] for sale in sales if sale['payment_method'] == 'transfer')
            
            # Crear estructura de datos
            report_data = {
                'date': date,
                'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'summary': {
                    'total_sales': len(sales),
                    'total_amount': total_amount,
                    'total_tax': total_tax,
                    'payment_methods': {
                        'cash': cash_sales,
                        'card': card_sales,
                        'transfer': transfer_sales
                    }
                },
                'sales': []
            }
            
            # Agregar datos de cada venta
            for sale in sales:
                sale_data = {
                    'id': sale['sale_id'],
                    'datetime': sale['sale_date'],
                    'cashier': {
                        'id': sale['user_id'],
                        'name': sale['cashier_name'],
                        'username': sale['username']
                    },
                    'customer': sale['customer_name'],
                    'payment_method': sale['payment_method'],
                    'payment_status': sale['payment_status'],
                    'subtotal': sale['total_amount'] - sale['tax_amount'],
                    'tax': sale['tax_amount'],
                    'total': sale['total_amount'],
                    'notes': sale['notes']
                }
                
                report_data['sales'].append(sale_data)
            
            # Guardar en archivo JSON
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=4)
            
            self.logger.info(f"Reporte JSON de ventas diarias generado: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error al generar JSON de ventas diarias: {e}")
            return None
    
    def generate_sales_by_period_report(self, start_date, end_date, period='day', format='pdf'):
        """
        Generar reporte de ventas por período
        
        Args:
            start_date: Fecha de inicio (formato: YYYY-MM-DD)
            end_date: Fecha de fin (formato: YYYY-MM-DD)
            period: Período de agrupación ('day', 'week', 'month')
            format: Formato del reporte ('pdf', 'csv', 'json')
            
        Returns:
            Ruta al archivo de reporte generado o None si hay error
        """
        try:
            # Obtener resumen de ventas por día
            summary = self.sales_controller.get_summary_by_day(start_date, end_date)
            
            # Nombre del archivo
            filename = f"ventas_{start_date.replace('-', '')}_{end_date.replace('-', '')}"
            
            if format == 'pdf':
                return self._generate_period_sales_pdf(summary, start_date, end_date, period, filename)
            elif format == 'csv':
                return self._generate_period_sales_csv(summary, start_date, end_date, period, filename)
            elif format == 'json':
                return self._generate_period_sales_json(summary, start_date, end_date, period, filename)
            else:
                self.logger.error(f"Formato de reporte no válido: {format}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error al generar reporte de ventas por período: {e}")
            return None
    
    def _generate_period_sales_pdf(self, summary, start_date, end_date, period, filename):
        """Generar reporte de ventas por período en PDF"""
        try:
            filepath = os.path.join(self.reports_dir, f"{filename}.pdf")
            
            # Calcular totales
            total_sales = sum(day['total_sales'] for day in summary)
            total_amount = sum(day['total_amount'] for day in summary)
            total_tax = sum(day['total_tax'] for day in summary)
            cash_amount = sum(day['cash_amount'] for day in summary)
            card_amount = sum(day['card_amount'] for day in summary)
            transfer_amount = sum(day['transfer_amount'] for day in summary)
            
            # Crear PDF
            with PdfPages(filepath) as pdf:
                # Página 1: Resumen
                plt.figure(figsize=(10, 8))
                plt.suptitle(f"Reporte de Ventas: {start_date} - {end_date}", fontsize=16)
                
                # Información general
                info_text = (
                    f"Período: {start_date} a {end_date}\n"
                    f"Total de ventas: {total_sales}\n"
                    f"Monto total: ${total_amount:.2f}\n"
                    f"Impuestos: ${total_tax:.2f}\n\n"
                    f"Ventas por método de pago:\n"
                    f"  Efectivo: ${cash_amount:.2f}\n"
                    f"  Tarjeta: ${card_amount:.2f}\n"
                    f"  Transferencia: ${transfer_amount:.2f}\n"
                )
                
                plt.figtext(0.1, 0.8, info_text, fontsize=12)
                
                # Gráfico de métodos de pago
                ax1 = plt.subplot(2, 1, 2)
                labels = ['Efectivo', 'Tarjeta', 'Transferencia']
                values = [cash_amount, card_amount, transfer_amount]
                
                ax1.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
                ax1.axis('equal')
                ax1.set_title('Ventas por Método de Pago')
                
                plt.tight_layout()
                pdf.savefig()
                plt.close()
                
                # Página 2: Ventas por día
                if summary:
                    plt.figure(figsize=(12, 8))
                    plt.suptitle(f"Ventas por Día: {start_date} - {end_date}", fontsize=16)
                    
                    # Preparar datos para gráficos
                    dates = [datetime.strptime(day['date'], "%Y-%m-%d") for day in summary]
                    sales_counts = [day['total_sales'] for day in summary]
                    sales_amounts = [day['total_amount'] for day in summary]
                    
                    # Gráfico de cantidad de ventas por día
                    ax1 = plt.subplot(2, 1, 1)
                    ax1.bar(dates, sales_counts, color='skyblue')
                    ax1.set_title('Cantidad de Ventas por Día')
                    ax1.set_ylabel('Cantidad')
                    
                    # Formatear eje x
                    date_format = mdates.DateFormatter('%d/%m')
                    ax1.xaxis.set_major_formatter(date_format)
                    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                    plt.xticks(rotation=45)
                    
                    # Gráfico de monto de ventas por día
                    ax2 = plt.subplot(2, 1, 2)
                    ax2.bar(dates, sales_amounts, color='lightgreen')
                    ax2.set_title('Monto de Ventas por Día')
                    ax2.set_ylabel('Monto ($)')
                    
                    # Formatear eje x
                    ax2.xaxis.set_major_formatter(date_format)
                    ax2.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                    plt.xticks(rotation=45)
                    
                    plt.tight_layout()
                    pdf.savefig()
                    plt.close()
                
                # Página 3: Tabla de resumen
                if summary:
                    plt.figure(figsize=(12, 8))
                    plt.suptitle(f"Resumen Diario: {start_date} - {end_date}", fontsize=16)
                    
                    # Crear tabla
                    table_data = []
                    for day in summary:
                        table_data.append([
                            day['date'],
                            f"{day['total_sales']}",
                            f"${day['total_amount']:.2f}",
                            f"${day['total_tax']:.2f}",
                            f"${day['cash_amount']:.2f}",
                            f"${day['card_amount']:.2f}",
                            f"${day['transfer_amount']:.2f}"
                        ])
                    
                    # Crear tabla
                    ax = plt.subplot(1, 1, 1)
                    ax.axis('off')
                    table = ax.table(
                        cellText=table_data,
                        colLabels=['Fecha', 'Ventas', 'Total', 'Impuestos', 'Efectivo', 'Tarjeta', 'Transferencia'],
                        loc='center',
                        cellLoc='center'
                    )
                    
                    # Ajustar tamaño de tabla
                    table.auto_set_font_size(False)
                    table.set_fontsize(10)
                    table.scale(1, 1.5)
                    
                    plt.tight_layout()
                    pdf.savefig()
                    plt.close()
            
            self.logger.info(f"Reporte de ventas por período generado: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error al generar PDF de ventas por período: {e}")
            return None
    
    def _generate_period_sales_csv(self, summary, start_date, end_date, period, filename):
        """Generar reporte de ventas por período en CSV"""
        try:
            filepath = os.path.join(self.reports_dir, f"{filename}.csv")
            
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Encabezados
                writer.writerow(['Fecha', 'Ventas', 'Total', 'Impuestos', 
                               'Efectivo', 'Tarjeta', 'Transferencia'])
                
                # Datos
                for day in summary:
                    writer.writerow([
                        day['date'],
                        day['total_sales'],
                        f"{day['total_amount']:.2f}",
                        f"{day['total_tax']:.2f}",
                        f"{day['cash_amount']:.2f}",
                        f"{day['card_amount']:.2f}",
                        f"{day['transfer_amount']:.2f}"
                    ])
                
                # Totales
                total_sales = sum(day['total_sales'] for day in summary)
                total_amount = sum(day['total_amount'] for day in summary)
                total_tax = sum(day['total_tax'] for day in summary)
                cash_amount = sum(day['cash_amount'] for day in summary)
                card_amount = sum(day['card_amount'] for day in summary)
                transfer_amount = sum(day['transfer_amount'] for day in summary)
                
                writer.writerow([])
                writer.writerow([
                    'TOTAL',
                    total_sales,
                    f"{total_amount:.2f}",
                    f"{total_tax:.2f}",
                    f"{cash_amount:.2f}",
                    f"{card_amount:.2f}",
                    f"{transfer_amount:.2f}"
                ])
            
            self.logger.info(f"Reporte CSV de ventas por período generado: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error al generar CSV de ventas por período: {e}")
            return None
    
    def _generate_period_sales_json(self, summary, start_date, end_date, period, filename):
        """Generar reporte de ventas por período en JSON"""
        try:
            filepath = os.path.join(self.reports_dir, f"{filename}.json")
            
            # Calcular totales
            total_sales = sum(day['total_sales'] for day in summary)
            total_amount = sum(day['total_amount'] for day in summary)
            total_tax = sum(day['total_tax'] for day in summary)
            cash_amount = sum(day['cash_amount'] for day in summary)
            card_amount = sum(day['card_amount'] for day in summary)
            transfer_amount = sum(day['transfer_amount'] for day in summary)
            
            # Crear estructura de datos
            report_data = {
                'start_date': start_date,
                'end_date': end_date,
                'period': period,
                'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'summary': {
                    'total_sales': total_sales,
                    'total_amount': total_amount,
                    'total_tax': total_tax,
                    'payment_methods': {
                        'cash': cash_amount,
                        'card': card_amount,
                        'transfer': transfer_amount
                    }
                },
                'daily_summary': []
            }
            
            # Agregar datos de cada día
            for day in summary:
                day_data = {
                    'date': day['date'],
                    'total_sales': day['total_sales'],
                    'total_amount': day['total_amount'],
                    'total_tax': day['total_tax'],
                    'payment_methods': {
                        'cash': day['cash_amount'],
                        'card': day['card_amount'],
                        'transfer': day['transfer_amount']
                    }
                }
                
                report_data['daily_summary'].append(day_data)
            
            # Guardar en archivo JSON
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=4)
            
            self.logger.info(f"Reporte JSON de ventas por período generado: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error al generar JSON de ventas por período: {e}")
            return None
    
    def generate_top_products_report(self, start_date=None, end_date=None, limit=10, format='pdf'):
        """
        Generar reporte de productos más vendidos
        
        Args:
            start_date: Fecha de inicio (formato: YYYY-MM-DD)
            end_date: Fecha de fin (formato: YYYY-MM-DD)
            limit: Límite de productos a incluir
            format: Formato del reporte ('pdf', 'csv', 'json')
            
        Returns:
            Ruta al archivo de reporte generado o None si hay error
        """
        try:
            # Obtener productos más vendidos
            top_products = self.sales_controller.get_top_products(start_date, end_date, limit)
            
            # Determinar período para el nombre del archivo
            period_str = ""
            if start_date:
                period_str += f"_{start_date.replace('-', '')}"
            if end_date:
                period_str += f"_{end_date.replace('-', '')}"
            
            # Nombre del archivo
            filename = f"top_productos{period_str}"
            
            if format == 'pdf':
                return self._generate_top_products_pdf(top_products, start_date, end_date, filename)
            elif format == 'csv':
                return self._generate_top_products_csv(top_products, start_date, end_date, filename)
            elif format == 'json':
                return self._generate_top_products_json(top_products, start_date, end_date, filename)
            else:
                self.logger.error(f"Formato de reporte no válido: {format}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error al generar reporte de productos más vendidos: {e}")
            return None
    
    def _generate_top_products_pdf(self, products, start_date, end_date, filename):
        """Generar reporte de productos más vendidos en PDF"""
        try:
            filepath = os.path.join(self.reports_dir, f"{filename}.pdf")
            
            # Título del reporte con período
            if start_date and end_date:
                title = f"Productos Más Vendidos: {start_date} - {end_date}"
            elif start_date:
                title = f"Productos Más Vendidos desde {start_date}"
            elif end_date:
                title = f"Productos Más Vendidos hasta {end_date}"
            else:
                title = "Productos Más Vendidos"
            
            # Crear PDF
            with PdfPages(filepath) as pdf:
                # Gráfico de barras
                plt.figure(figsize=(10, 8))
                plt.suptitle(title, fontsize=16)
                
                # Preparar datos para gráfico
                if products:
                    names = [p['product_name'] for p in products]
                    quantities = [p['total_quantity'] for p in products]
                    
                    # Truncar nombres largos
                    names = [name[:20] + '...' if len(name) > 20 else name for name in names]
                    
                    # Crear gráfico de barras horizontales
                    plt.barh(names, quantities, color='skyblue')
                    plt.xlabel('Cantidad Vendida')
                    plt.ylabel('Producto')
                    plt.grid(axis='x', linestyle='--', alpha=0.7)
                    
                    # Añadir valores en las barras
                    for i, v in enumerate(quantities):
                        plt.text(v + 0.1, i, str(v), va='center')
                    
                    plt.tight_layout()
                    pdf.savefig()
                    plt.close()
                
                # Tabla de productos
                plt.figure(figsize=(10, 8))
                plt.suptitle(f"Detalle de {len(products)} Productos Más Vendidos", fontsize=16)
                
                if products:
                    # Crear tabla
                    table_data = []
                    for i, product in enumerate(products):
                        table_data.append([
                            f"{i+1}",
                            product['product_name'],
                            product['barcode'] or 'N/A',
                            f"{product['total_quantity']}",
                            f"${product['total_amount']:.2f}"
                        ])
                    
                    # Crear tabla
                    ax = plt.subplot(1, 1, 1)
                    ax.axis('off')
                    table = ax.table(
                        cellText=table_data,
                        colLabels=['#', 'Producto', 'Código', 'Cantidad', 'Total'],
                        loc='center',
                        cellLoc='center'
                    )
                    
                    # Ajustar tamaño de tabla
                    table.auto_set_font_size(False)
                    table.set_fontsize(10)
                    table.scale(1, 1.5)
                    
                    plt.tight_layout()
                    pdf.savefig()
                    plt.close()
            
            self.logger.info(f"Reporte de productos más vendidos generado: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error al generar PDF de productos más vendidos: {e}")
            return None