# app/views/reports_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                              QPushButton, QLabel, QDateEdit, QComboBox,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QLineEdit, QGroupBox, QFormLayout, QSpinBox,
                              QRadioButton, QButtonGroup, QMessageBox,
                              QFileDialog, QDialog, QDialogButtonBox,
                              QStackedWidget, QCheckBox, QFrame, QSplitter)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QIcon, QFont

import os
import logging
from datetime import datetime, timedelta

class ReportsView(QWidget):
    """Vista para la generación y visualización de reportes"""
    
    # Señales
    report_requested = Signal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración básica
        self.logger = logging.getLogger('pos.views.reports')
        
        # Inicializar la interfaz
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Pestañas de reportes
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Pestaña de ventas
        sales_tab = self.create_sales_tab()
        tab_widget.addTab(sales_tab, "Ventas")
        
        # Pestaña de inventario
        inventory_tab = self.create_inventory_tab()
        tab_widget.addTab(inventory_tab, "Inventario")
        
        # Pestaña de caja
        cashier_tab = self.create_cashier_tab()
        tab_widget.addTab(cashier_tab, "Caja")
    
    def create_sales_tab(self):
        """Crear pestaña de reportes de ventas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Sección de filtros
        filters_group = QGroupBox("Filtros")
        filters_layout = QHBoxLayout(filters_group)
        
        # Período
        period_form = QFormLayout()
        
        # Fecha inicio
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))  # Último mes por defecto
        
        # Fecha fin
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        
        period_form.addRow("Desde:", self.start_date_edit)
        period_form.addRow("Hasta:", self.end_date_edit)
        
        filters_layout.addLayout(period_form)
        
        # Agrupación
        grouping_form = QFormLayout()
        
        self.grouping_combo = QComboBox()
        self.grouping_combo.addItem("Diario", "day")
        self.grouping_combo.addItem("Semanal", "week")
        self.grouping_combo.addItem("Mensual", "month")
        
        grouping_form.addRow("Agrupación:", self.grouping_combo)
        
        filters_layout.addLayout(grouping_form)
        
        # Tipo de reporte
        report_type_group = QGroupBox("Tipo de Reporte")
        report_type_layout = QVBoxLayout(report_type_group)
        
        self.report_type_group = QButtonGroup()
        
        self.sales_summary_radio = QRadioButton("Resumen de Ventas")
        self.sales_summary_radio.setChecked(True)
        
        self.top_products_radio = QRadioButton("Productos Más Vendidos")
        
        self.sales_by_payment_radio = QRadioButton("Ventas por Método de Pago")
        
        self.report_type_group.addButton(self.sales_summary_radio, 1)
        self.report_type_group.addButton(self.top_products_radio, 2)
        self.report_type_group.addButton(self.sales_by_payment_radio, 3)
        
        report_type_layout.addWidget(self.sales_summary_radio)
        report_type_layout.addWidget(self.top_products_radio)
        report_type_layout.addWidget(self.sales_by_payment_radio)
        
        filters_layout.addWidget(report_type_group)
        
        # Botones de acción
        actions_layout = QVBoxLayout()
        
        self.generate_report_button = QPushButton("Generar Reporte")
        self.generate_report_button.clicked.connect(self.generate_sales_report)
        
        self.export_report_button = QPushButton("Exportar")
        self.export_report_button.clicked.connect(self.export_sales_report)
        self.export_report_button.setEnabled(False)  # Inicialmente deshabilitado
        
        actions_layout.addWidget(self.generate_report_button)
        actions_layout.addWidget(self.export_report_button)
        actions_layout.addStretch()
        
        filters_layout.addLayout(actions_layout)
        
        layout.addWidget(filters_group)
        
        # Área de visualización del reporte
        self.sales_report_widget = QStackedWidget()
        
        # Widget para cuando no hay reporte generado
        no_report_widget = QWidget()
        no_report_layout = QVBoxLayout(no_report_widget)
        no_report_label = QLabel("Configure los filtros y haga clic en 'Generar Reporte' para visualizar.")
        no_report_label.setAlignment(Qt.AlignCenter)
        no_report_layout.addWidget(no_report_label)
        
        self.sales_report_widget.addWidget(no_report_widget)
        
        # Tabla para mostrar resultados
        report_table_widget = QWidget()
        report_table_layout = QVBoxLayout(report_table_widget)
        
        # Etiqueta de título
        self.report_title_label = QLabel("Reporte de Ventas")
        self.report_title_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.report_title_label.setAlignment(Qt.AlignCenter)
        report_table_layout.addWidget(self.report_title_label)
        
        # Tabla de resultados
        self.report_table = QTableWidget()
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        report_table_layout.addWidget(self.report_table)
        
        self.sales_report_widget.addWidget(report_table_widget)
        
        layout.addWidget(self.sales_report_widget)
        
        return tab
    
    def create_inventory_tab(self):
        """Crear pestaña de reportes de inventario"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Sección de filtros
        filters_group = QGroupBox("Filtros")
        filters_layout = QHBoxLayout(filters_group)
        
        # Categoría
        category_form = QFormLayout()
        
        self.inventory_category_combo = QComboBox()
        self.inventory_category_combo.addItem("Todas las categorías", None)
        
        # En un sistema real, cargaríamos las categorías desde el controlador
        self.inventory_category_combo.addItem("Bebidas", 1)
        self.inventory_category_combo.addItem("Alimentos", 2)
        self.inventory_category_combo.addItem("Lácteos", 3)
        
        category_form.addRow("Categoría:", self.inventory_category_combo)
        
        filters_layout.addLayout(category_form)
        
        # Opciones de reporte
        options_group = QGroupBox("Opciones")
        options_layout = QVBoxLayout(options_group)
        
        self.low_stock_checkbox = QCheckBox("Solo productos con stock bajo")
        self.include_cost_checkbox = QCheckBox("Incluir costos")
        self.include_cost_checkbox.setChecked(True)
        
        options_layout.addWidget(self.low_stock_checkbox)
        options_layout.addWidget(self.include_cost_checkbox)
        
        filters_layout.addWidget(options_group)
        
        # Tipo de reporte
        report_type_group = QGroupBox("Tipo de Reporte")
        report_type_layout = QVBoxLayout(report_type_group)
        
        self.inventory_report_type_group = QButtonGroup()
        
        self.inventory_summary_radio = QRadioButton("Resumen de Inventario")
        self.inventory_summary_radio.setChecked(True)
        
        self.stock_value_radio = QRadioButton("Valor del Inventario")
        
        self.inventory_movements_radio = QRadioButton("Movimientos de Inventario")
        
        self.inventory_report_type_group.addButton(self.inventory_summary_radio, 1)
        self.inventory_report_type_group.addButton(self.stock_value_radio, 2)
        self.inventory_report_type_group.addButton(self.inventory_movements_radio, 3)
        
        report_type_layout.addWidget(self.inventory_summary_radio)
        report_type_layout.addWidget(self.stock_value_radio)
        report_type_layout.addWidget(self.inventory_movements_radio)
        
        filters_layout.addWidget(report_type_group)
        
        # Botones de acción
        actions_layout = QVBoxLayout()
        
        self.generate_inventory_report_button = QPushButton("Generar Reporte")
        self.generate_inventory_report_button.clicked.connect(self.generate_inventory_report)
        
        self.export_inventory_report_button = QPushButton("Exportar")
        self.export_inventory_report_button.clicked.connect(self.export_inventory_report)
        self.export_inventory_report_button.setEnabled(False)  # Inicialmente deshabilitado
        
        actions_layout.addWidget(self.generate_inventory_report_button)
        actions_layout.addWidget(self.export_inventory_report_button)
        actions_layout.addStretch()
        
        filters_layout.addLayout(actions_layout)
        
        layout.addWidget(filters_group)
        
        # Área de visualización del reporte
        self.inventory_report_widget = QStackedWidget()
        
        # Widget para cuando no hay reporte generado
        no_report_widget = QWidget()
        no_report_layout = QVBoxLayout(no_report_widget)
        no_report_label = QLabel("Configure los filtros y haga clic en 'Generar Reporte' para visualizar.")
        no_report_label.setAlignment(Qt.AlignCenter)
        no_report_layout.addWidget(no_report_label)
        
        self.inventory_report_widget.addWidget(no_report_widget)
        
        # Tabla para mostrar resultados
        inventory_table_widget = QWidget()
        inventory_table_layout = QVBoxLayout(inventory_table_widget)
        
        # Etiqueta de título
        self.inventory_report_title_label = QLabel("Reporte de Inventario")
        self.inventory_report_title_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.inventory_report_title_label.setAlignment(Qt.AlignCenter)
        inventory_table_layout.addWidget(self.inventory_report_title_label)
        
        # Tabla de resultados
        self.inventory_report_table = QTableWidget()
        self.inventory_report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        inventory_table_layout.addWidget(self.inventory_report_table)
        
        self.inventory_report_widget.addWidget(inventory_table_widget)
        
        layout.addWidget(self.inventory_report_widget)
        
        return tab
    
    def create_cashier_tab(self):
        """Crear pestaña de reportes de caja"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Sección de filtros
        filters_group = QGroupBox("Filtros")
        filters_layout = QHBoxLayout(filters_group)
        
        # Fecha
        date_form = QFormLayout()
        
        self.cashier_date_edit = QDateEdit()
        self.cashier_date_edit.setCalendarPopup(True)
        self.cashier_date_edit.setDate(QDate.currentDate())
        
        date_form.addRow("Fecha:", self.cashier_date_edit)
        
        filters_layout.addLayout(date_form)
        
        # Cajero
        cashier_form = QFormLayout()
        
        self.cashier_combo = QComboBox()
        self.cashier_combo.addItem("Todos los cajeros", None)
        
        # En un sistema real, cargaríamos los cajeros desde el controlador
        self.cashier_combo.addItem("Admin", 1)
        self.cashier_combo.addItem("Cajero 1", 2)
        self.cashier_combo.addItem("Cajero 2", 3)
        
        cashier_form.addRow("Cajero:", self.cashier_combo)
        
        filters_layout.addLayout(cashier_form)
        
        # Tipo de reporte
        report_type_group = QGroupBox("Tipo de Reporte")
        report_type_layout = QVBoxLayout(report_type_group)
        
        self.cashier_report_type_group = QButtonGroup()
        
        self.z_report_radio = QRadioButton("Reporte Z (Cierre de Caja)")
        self.z_report_radio.setChecked(True)
        
        self.x_report_radio = QRadioButton("Reporte X (Parcial)")
        
        self.cashier_report_type_group.addButton(self.z_report_radio, 1)
        self.cashier_report_type_group.addButton(self.x_report_radio, 2)
        
        report_type_layout.addWidget(self.z_report_radio)
        report_type_layout.addWidget(self.x_report_radio)
        
        filters_layout.addWidget(report_type_group)
        
        # Botones de acción
        actions_layout = QVBoxLayout()
        
        self.generate_cashier_report_button = QPushButton("Generar Reporte")
        self.generate_cashier_report_button.clicked.connect(self.generate_cashier_report)
        
        self.print_cashier_report_button = QPushButton("Imprimir")
        self.print_cashier_report_button.clicked.connect(self.print_cashier_report)
        self.print_cashier_report_button.setEnabled(False)  # Inicialmente deshabilitado
        
        self.export_cashier_report_button = QPushButton("Exportar")
        self.export_cashier_report_button.clicked.connect(self.export_cashier_report)
        self.export_cashier_report_button.setEnabled(False)  # Inicialmente deshabilitado
        
        actions_layout.addWidget(self.generate_cashier_report_button)
        actions_layout.addWidget(self.print_cashier_report_button)
        actions_layout.addWidget(self.export_cashier_report_button)
        actions_layout.addStretch()
        
        filters_layout.addLayout(actions_layout)
        
        layout.addWidget(filters_group)
        
        # Área de visualización del reporte
        self.cashier_report_widget = QStackedWidget()
        
        # Widget para cuando no hay reporte generado
        no_report_widget = QWidget()
        no_report_layout = QVBoxLayout(no_report_widget)
        no_report_label = QLabel("Configure los filtros y haga clic en 'Generar Reporte' para visualizar.")
        no_report_label.setAlignment(Qt.AlignCenter)
        no_report_layout.addWidget(no_report_label)
        
        self.cashier_report_widget.addWidget(no_report_widget)
        
        # Widget para mostrar el reporte Z
        z_report_widget = QWidget()
        z_report_layout = QVBoxLayout(z_report_widget)
        
        # Marco para información de la caja
        register_frame = QFrame()
        register_frame.setFrameShape(QFrame.StyledPanel)
        register_layout = QFormLayout(register_frame)
        
        self.register_id_label = QLabel()
        self.cashier_name_label = QLabel()
        self.opening_time_label = QLabel()
        self.closing_time_label = QLabel()
        
        register_layout.addRow("ID de Caja:", self.register_id_label)
        register_layout.addRow("Cajero:", self.cashier_name_label)
        register_layout.addRow("Apertura:", self.opening_time_label)
        register_layout.addRow("Cierre:", self.closing_time_label)
        
        z_report_layout.addWidget(register_frame)
        
        # Marco para resumen de operaciones
        operations_frame = QFrame()
        operations_frame.setFrameShape(QFrame.StyledPanel)
        operations_layout = QFormLayout(operations_frame)
        
        self.sales_count_label = QLabel()
        self.canceled_count_label = QLabel()
        
        operations_layout.addRow("Ventas Realizadas:", self.sales_count_label)
        operations_layout.addRow("Ventas Canceladas:", self.canceled_count_label)
        
        z_report_layout.addWidget(operations_frame)
        
        # Marco para resumen de pagos
        payments_frame = QFrame()
        payments_frame.setFrameShape(QFrame.StyledPanel)
        payments_layout = QFormLayout(payments_frame)
        
        self.cash_sales_label = QLabel()
        self.card_sales_label = QLabel()
        self.transfer_sales_label = QLabel()
        self.total_sales_label = QLabel()
        self.total_sales_label.setFont(QFont('Arial', 11, QFont.Bold))
        
        payments_layout.addRow("Efectivo:", self.cash_sales_label)
        payments_layout.addRow("Tarjeta:", self.card_sales_label)
        payments_layout.addRow("Transferencia:", self.transfer_sales_label)
        payments_layout.addRow("TOTAL VENTAS:", self.total_sales_label)
        
        z_report_layout.addWidget(payments_frame)
        
        # Marco para balance de caja
        balance_frame = QFrame()
        balance_frame.setFrameShape(QFrame.StyledPanel)
        balance_layout = QFormLayout(balance_frame)
        
        self.opening_amount_label = QLabel()
        self.cash_amount_label = QLabel()
        self.expected_amount_label = QLabel()
        self.closing_amount_label = QLabel()
        self.difference_label = QLabel()
        self.difference_label.setFont(QFont('Arial', 11, QFont.Bold))
        
        balance_layout.addRow("Monto Inicial:", self.opening_amount_label)
        balance_layout.addRow("Ventas en Efectivo:", self.cash_amount_label)
        balance_layout.addRow("Efectivo Esperado:", self.expected_amount_label)
        balance_layout.addRow("Efectivo Real:", self.closing_amount_label)
        balance_layout.addRow("Diferencia:", self.difference_label)
        
        z_report_layout.addWidget(balance_frame)
        
        self.cashier_report_widget.addWidget(z_report_widget)
        
        layout.addWidget(self.cashier_report_widget)
        
        return tab
    
    def generate_sales_report(self):
        """Generar reporte de ventas según los filtros seleccionados"""
        # Obtener fechas
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        # Verificar fechas
        if self.start_date_edit.date() > self.end_date_edit.date():
            QMessageBox.warning(self, "Error", "La fecha de inicio debe ser anterior a la fecha de fin")
            return
        
        # Obtener agrupación
        grouping = self.grouping_combo.currentData()
        
        # Obtener tipo de reporte
        report_type_id = self.report_type_group.checkedId()
        if report_type_id == 1:
            report_type = "sales_summary"
        elif report_type_id == 2:
            report_type = "top_products"
        elif report_type_id == 3:
            report_type = "sales_by_payment"
        else:
            report_type = "sales_summary"
        
        # Configurar parámetros del reporte
        report_params = {
            "start_date": start_date,
            "end_date": end_date,
            "grouping": grouping,
            "report_type": report_type
        }
        
        # En un sistema real, invocaríamos al controlador para generar el reporte
        # self.report_requested.emit(report_type, report_params)
        
        # Para demostración, simulamos la generación del reporte
        self.show_sample_sales_report(report_type, report_params)
        
        # Habilitar botón de exportación
        self.export_report_button.setEnabled(True)
    
    def show_sample_sales_report(self, report_type, params):
        """Mostrar datos de ejemplo para el reporte de ventas"""
        # Limpiar tabla
        self.report_table.clear()
        
        # Configurar título según el tipo de reporte
        title = ""
        if report_type == "sales_summary":
            title = "Resumen de Ventas"
            self.show_sales_summary_sample(params)
        elif report_type == "top_products":
            title = "Productos Más Vendidos"
            self.show_top_products_sample(params)
        elif report_type == "sales_by_payment":
            title = "Ventas por Método de Pago"
            self.show_sales_by_payment_sample(params)
        
        # Configurar título completo
        period_text = f"{params['start_date']} - {params['end_date']}"
        self.report_title_label.setText(f"{title}: {period_text}")
        
        # Mostrar la tabla de resultados
        self.sales_report_widget.setCurrentIndex(1)
    
    def show_sales_summary_sample(self, params):
        """Mostrar datos de ejemplo para el resumen de ventas"""
        # Configurar columnas
        self.report_table.setColumnCount(7)
        self.report_table.setHorizontalHeaderLabels([
            "Fecha", "Ventas", "Total", "Impuestos", "Efectivo", "Tarjeta", "Transferencia"
        ])
        
        # Datos de ejemplo
        start_date = datetime.strptime(params["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(params["end_date"], "%Y-%m-%d")
        
        # Generar fechas en el rango
        current_date = start_date
        row = 0
        
        while current_date <= end_date:
            # Formato de fecha según agrupación
            if params["grouping"] == "day":
                date_str = current_date.strftime("%Y-%m-%d")
                increment = timedelta(days=1)
            elif params["grouping"] == "week":
                date_str = f"Semana {current_date.strftime('%U')} - {current_date.year}"
                increment = timedelta(weeks=1)
            elif params["grouping"] == "month":
                date_str = current_date.strftime("%B %Y")
                # Avanzar al primer día del siguiente mes
                if current_date.month == 12:
                    next_month = datetime(current_date.year + 1, 1, 1)
                else:
                    next_month = datetime(current_date.year, current_date.month + 1, 1)
                increment = next_month - current_date
            else:
                date_str = current_date.strftime("%Y-%m-%d")
                increment = timedelta(days=1)
            
            # Generar datos aleatorios para el ejemplo
            import random
            sales_count = random.randint(10, 50)
            total_amount = random.uniform(1000, 5000)
            tax_amount = total_amount * 0.16
            cash_amount = total_amount * random.uniform(0.3, 0.5)
            card_amount = total_amount * random.uniform(0.3, 0.5)
            transfer_amount = total_amount - cash_amount - card_amount
            
            # Agregar fila
            self.report_table.insertRow(row)
            
            # Fecha
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 0, date_item)
            
            # Ventas
            sales_item = QTableWidgetItem(str(sales_count))
            sales_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 1, sales_item)
            
            # Total
            total_item = QTableWidgetItem(f"${total_amount:.2f}")
            total_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 2, total_item)
            
            # Impuestos
            tax_item = QTableWidgetItem(f"${tax_amount:.2f}")
            tax_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 3, tax_item)
            
            # Efectivo
            cash_item = QTableWidgetItem(f"${cash_amount:.2f}")
            cash_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 4, cash_item)
            
            # Tarjeta
            card_item = QTableWidgetItem(f"${card_amount:.2f}")
            card_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 5, card_item)
            
            # Transferencia
            transfer_item = QTableWidgetItem(f"${transfer_amount:.2f}")
            transfer_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 6, transfer_item)
            
            # Avanzar a la siguiente fecha
            current_date += increment
            row += 1
            
            # Limitar a 10 filas para el ejemplo
            if row >= 10:
                break
    
    def show_top_products_sample(self, params):
        """Mostrar datos de ejemplo para los productos más vendidos"""
        # Configurar columnas
        self.report_table.setColumnCount(5)
        self.report_table.setHorizontalHeaderLabels([
            "Posición", "Producto", "Código", "Cantidad", "Total"
        ])
        
        # Datos de ejemplo
        products = [
            {"name": "Agua 500ml", "barcode": "7501055310209", "quantity": 125, "total": 1250.00},
            {"name": "Refresco", "barcode": "7501055310216", "quantity": 98, "total": 1470.00},
            {"name": "Pan", "barcode": "7501055310223", "quantity": 75, "total": 1500.00},
            {"name": "Leche", "barcode": "7501055310230", "quantity": 62, "total": 1550.00},
            {"name": "Huevos", "barcode": "7501055310247", "quantity": 48, "total": 1440.00},
            {"name": "Café", "barcode": "7501055310254", "quantity": 43, "total": 1290.00},
            {"name": "Galletas", "barcode": "7501055310261", "quantity": 40, "total": 800.00},
            {"name": "Refresco 2L", "barcode": "7501055310278", "quantity": 35, "total": 875.00},
            {"name": "Papel Higiénico", "barcode": "7501055310285", "quantity": 30, "total": 900.00},
            {"name": "Jabón", "barcode": "7501055310292", "quantity": 28, "total": 560.00}
        ]
        
        # Agregar datos a la tabla
        for i, product in enumerate(products):
            row = i
            self.report_table.insertRow(row)
            
            # Posición
            position_item = QTableWidgetItem(str(i + 1))
            position_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 0, position_item)
            
            # Producto
            name_item = QTableWidgetItem(product["name"])
            self.report_table.setItem(row, 1, name_item)
            
            # Código
            barcode_item = QTableWidgetItem(product["barcode"])
            barcode_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 2, barcode_item)
            
            # Cantidad
            quantity_item = QTableWidgetItem(str(product["quantity"]))
            quantity_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 3, quantity_item)
            
            # Total
            total_item = QTableWidgetItem(f"${product['total']:.2f}")
            total_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 4, total_item)
    
    def show_sales_by_payment_sample(self, params):
        """Mostrar datos de ejemplo para ventas por método de pago"""
        # Configurar columnas
        self.report_table.setColumnCount(3)
        self.report_table.setHorizontalHeaderLabels([
            "Método de Pago", "Cantidad", "Total"
        ])
        
        # Datos de ejemplo
        payment_methods = [
            {"method": "Efectivo", "count": 150, "total": 7500.00},
            {"method": "Tarjeta", "count": 120, "total": 9600.00},
            {"method": "Transferencia", "count": 50, "total": 4000.00}
        ]
        
        # Agregar datos a la tabla
        for i, payment in enumerate(payment_methods):
            row = i
            self.report_table.insertRow(row)
            
            # Método de pago
            method_item = QTableWidgetItem(payment["method"])
            self.report_table.setItem(row, 0, method_item)
            
            # Cantidad
            count_item = QTableWidgetItem(str(payment["count"]))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 1, count_item)
            
            # Total
            total_item = QTableWidgetItem(f"${payment['total']:.2f}")
            total_item.setTextAlignment(Qt.AlignCenter)
            self.report_table.setItem(row, 2, total_item)
    
    def export_sales_report(self):
        """Exportar reporte de ventas a un archivo"""
        # Verificar que haya un reporte generado
        if self.sales_report_widget.currentIndex() == 0:
            QMessageBox.warning(self, "Error", "Primero debe generar un reporte")
            return
            
        # Mostrar diálogo para seleccionar formato
        formats = ["PDF", "CSV", "Excel"]
        selected_format, ok = QInputDialog.getItem(
            self, "Exportar Reporte", "Seleccione el formato:", formats, 0, False
        )
        
        if not ok:
            return
            
        # Mostrar diálogo para guardar archivo
        file_extension = ""
        if selected_format == "PDF":
            file_extension = "pdf"
        elif selected_format == "CSV":
            file_extension = "csv"
        elif selected_format == "Excel":
            file_extension = "xlsx"
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte",
            os.path.expanduser("~") + f"/reporte_ventas.{file_extension}",
            f"Archivos {selected_format.upper()} (*.{file_extension})"
        )
        
        if not file_path:
            return
            
        # En un sistema real, invocaríamos al controlador para exportar el reporte
        
        # Para demostración, mostrar mensaje de éxito
        QMessageBox.information(
            self,
            "Reporte Exportado",
            f"El reporte ha sido exportado correctamente a {file_path}"
        )
    
    def generate_inventory_report(self):
        """Generar reporte de inventario según los filtros seleccionados"""
        # Obtener categoría
        category_id = self.inventory_category_combo.currentData()
        category_name = self.inventory_category_combo.currentText() if category_id else "Todas"
        
        # Obtener opciones
        low_stock_only = self.low_stock_checkbox.isChecked()
        include_cost = self.include_cost_checkbox.isChecked()
        
        # Obtener tipo de reporte
        report_type_id = self.inventory_report_type_group.checkedId()
        if report_type_id == 1:
            report_type = "inventory_summary"
        elif report_type_id == 2:
            report_type = "stock_value"
        elif report_type_id == 3:
            report_type = "inventory_movements"
        else:
            report_type = "inventory_summary"
        
        # Configurar parámetros del reporte
        report_params = {
            "category_id": category_id,
            "category_name": category_name,
            "low_stock_only": low_stock_only,
            "include_cost": include_cost,
            "report_type": report_type
        }
        
        # En un sistema real, invocaríamos al controlador para generar el reporte
        # self.report_requested.emit(report_type, report_params)
        
        # Para demostración, simulamos la generación del reporte
        self.show_sample_inventory_report(report_type, report_params)
        
        # Habilitar botón de exportación
        self.export_inventory_report_button.setEnabled(True)
    
    def show_sample_inventory_report(self, report_type, params):
        """Mostrar datos de ejemplo para el reporte de inventario"""
        # Limpiar tabla
        self.inventory_report_table.clear()
        
        # Configurar título según el tipo de reporte
        title = ""
        if report_type == "inventory_summary":
            title = "Resumen de Inventario"
            self.show_inventory_summary_sample(params)
        elif report_type == "stock_value":
            title = "Valor del Inventario"
            self.show_stock_value_sample(params)
        elif report_type == "inventory_movements":
            title = "Movimientos de Inventario"
            self.show_inventory_movements_sample(params)
        
        # Filtros aplicados
        filters = []
        if params["category_id"]:
            filters.append(f"Categoría: {params['category_name']}")
        if params["low_stock_only"]:
            filters.append("Solo productos con stock bajo")
        
        filters_text = " | ".join(filters) if filters else ""
        
        # Configurar título completo
        if filters_text:
            full_title = f"{title} ({filters_text})"
        else:
            full_title = title
            
        self.inventory_report_title_label.setText(full_title)
        
        # Mostrar la tabla de resultados
        self.inventory_report_widget.setCurrentIndex(1)
    
    def show_inventory_summary_sample(self, params):
        """Mostrar datos de ejemplo para el resumen de inventario"""
        # Columnas a mostrar
        if params["include_cost"]:
            self.inventory_report_table.setColumnCount(8)
            self.inventory_report_table.setHorizontalHeaderLabels([
                "Código", "Producto", "Categoría", "Stock", "Mínimo", "Precio", "Costo", "Estado"
            ])
        else:
            self.inventory_report_table.setColumnCount(6)
            self.inventory_report_table.setHorizontalHeaderLabels([
                "Código", "Producto", "Categoría", "Stock", "Mínimo", "Estado"
            ])
        
        # Datos de ejemplo
        products = [
            {"barcode": "7501055310209", "name": "Agua 500ml", "category": "Bebidas", "stock": 24, "min_stock": 10, "price": 10.0, "cost": 5.0},
            {"barcode": "7501055310216", "name": "Refresco", "category": "Bebidas", "stock": 35, "min_stock": 15, "price": 15.0, "cost": 8.0},
            {"barcode": "7501055310223", "name": "Pan", "category": "Alimentos", "stock": 8, "min_stock": 10, "price": 20.0, "cost": 12.0},
            {"barcode": "7501055310230", "name": "Leche", "category": "Lácteos", "stock": 16, "min_stock": 12, "price": 25.0, "cost": 18.0},
            {"barcode": "7501055310247", "name": "Huevos", "category": "Alimentos", "stock": 4, "min_stock": 6, "price": 30.0, "cost": 22.0}
        ]
        
        # Filtrar por categoría si es necesario
        if params["category_id"]:
            products = [p for p in products if p["category"] == params["category_name"]]
            
        # Filtrar por stock bajo si es necesario
        if params["low_stock_only"]:
            products = [p for p in products if p["stock"] <= p["min_stock"]]
        
        # Agregar datos a la tabla
        for i, product in enumerate(products):
            row = i
            self.inventory_report_table.insertRow(row)
            
            # Código
            barcode_item = QTableWidgetItem(product["barcode"])
            barcode_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_report_table.setItem(row, 0, barcode_item)
            
            # Producto
            name_item = QTableWidgetItem(product["name"])
            self.inventory_report_table.setItem(row, 1, name_item)
            
            # Categoría
            category_item = QTableWidgetItem(product["category"])
            category_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_report_table.setItem(row, 2, category_item)
            
            # Stock
            stock_item = QTableWidgetItem(str(product["stock"]))
            stock_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_report_table.setItem(row, 3, stock_item)
            
            # Mínimo
            min_stock_item = QTableWidgetItem(str(product["min_stock"]))
            min_stock_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_report_table.setItem(row, 4, min_stock_item)
            
            if params["include_cost"]:
                # Precio
                price_item = QTableWidgetItem(f"${product['price']:.2f}")
                price_item.setTextAlignment(Qt.AlignCenter)
                self.inventory_report_table.setItem(row, 5, price_item)
                
                # Costo
                cost_item = QTableWidgetItem(f"${product['cost']:.2f}")
                cost_item.setTextAlignment(Qt.AlignCenter)
                self.inventory_report_table.setItem(row, 6, cost_item)
                
                # Estado
                status_text = "BAJO" if product["stock"] <= product["min_stock"] else "OK"
                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignCenter)
                self.inventory_report_table.setItem(row, 7, status_item)
            else:
                # Estado
                status_text = "BAJO" if product["stock"] <= product["min_stock"] else "OK"
                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignCenter)
                self.inventory_report_table.setItem(row, 5, status_item)
    
    def show_stock_value_sample(self, params):
        """Mostrar datos de ejemplo para el valor del inventario"""
        # Configurar columnas
        self.inventory_report_table.setColumnCount(6)
        self.inventory_report_table.setHorizontalHeaderLabels([
            "Código", "Producto", "Categoría", "Stock", "Costo Unit.", "Valor Total"
        ])
        
        # Datos de ejemplo
        products = [
            {"barcode": "7501055310209", "name": "Agua 500ml", "category": "Bebidas", "stock": 24, "cost": 5.0, "value": 120.0},
            {"barcode": "7501055310216", "name": "Refresco", "category": "Bebidas", "stock": 35, "cost": 8.0, "value": 280.0},
            {"barcode": "7501055310223", "name": "Pan", "category": "Alimentos", "stock": 8, "cost": 12.0, "value": 96.0},
            {"barcode": "7501055310230", "name": "Leche", "category": "Lácteos", "stock": 16, "cost": 18.0, "value": 288.0},
            {"barcode": "7501055310247", "name": "Huevos", "category": "Alimentos", "stock": 4, "cost": 22.0, "value": 88.0},
            {"barcode": "7501055310254", "name": "Café", "category": "Bebidas", "stock": 12, "cost": 45.0, "value": 540.0},
            {"barcode": "7501055310261", "name": "Galletas", "category": "Alimentos", "stock": 18, "cost": 15.0, "value": 270.0},
            {"barcode": "7501055310278", "name": "Jabón", "category": "Limpieza", "stock": 10, "cost": 20.0, "value": 200.0}
        ]
        
        # Filtrar por categoría si es necesario
        if params["category_id"]:
            products = [p for p in products if p["category"] == params["category_name"]]
            
        # Filtrar por stock bajo si es necesario
        if params["low_stock_only"]:
            # Asumimos un nivel de stock mínimo para el ejemplo
            products = [p for p in products if p["stock"] <= 10]
        
        # Agregar datos a la tabla
        for i, product in enumerate(products):
            row = i
            self.inventory_report_table.insertRow(row)
            
            # Código
            barcode_item = QTableWidgetItem(product["barcode"])
            barcode_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_report_table.setItem(row, 0, barcode_item)
            
            # Producto
            name_item = QTableWidgetItem(product["name"])
            self.inventory_report_table.setItem(row, 1, name_item)
            
            # Categoría
            category_item = QTableWidgetItem(product["category"])
            category_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_report_table.setItem(row, 2, category_item)
            
            # Stock
            stock_item = QTableWidgetItem(str(product["stock"]))
            stock_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_report_table.setItem(row, 3, stock_item)
            
            # Costo unitario
            cost_item = QTableWidgetItem(f"${product['cost']:.2f}")
            cost_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_report_table.setItem(row, 4, cost_item)
            
            # Valor total
            value_item = QTableWidgetItem(f"${product['value']:.2f}")
            value_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_report_table.setItem(row, 5, value_item)
        
        # Agregar fila de total
        total_row = self.inventory_report_table.rowCount()
        self.inventory_report_table.insertRow(total_row)
        
        # Celda vacía para código
        self.inventory_report_table.setItem(total_row, 0, QTableWidgetItem(""))
        
        # Etiqueta de total
        total_label = QTableWidgetItem("TOTAL")
        total_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.inventory_report_table.setItem(total_row, 1, total_label)
        
        # Celdas vacías para categoría, stock y costo unitario
        self.inventory_report_table.setItem(total_row, 2, QTableWidgetItem(""))
        self.inventory_report_table.setItem(total_row, 3, QTableWidgetItem(""))
        self.inventory_report_table.setItem(total_row, 4, QTableWidgetItem(""))
        
        # Valor total del inventario
        total_value = sum(p["value"] for p in products)
        total_value_item = QTableWidgetItem(f"${total_value:.2f}")
        total_value_item.setFont(QFont('Arial', 10, QFont.Bold))
        total_value_item.setTextAlignment(Qt.AlignCenter)
        self.inventory_report_table.setItem(total_row, 5, total_value_item)
    
    def show_inventory_movements_sample(self, params):
        """Mostrar datos de ejemplo para los movimientos de inventario"""
        # Configurar columnas
        self.inventory_report_table.setColumnCount(7)
        self.inventory_report_table.setHorizontalHeaderLabels([
            "Fecha", "Producto", "Tipo", "Cantidad", "Usuario", "Referencia", "Notas"
        ])
        
        # Datos de ejemplo
        movements = [
            {"date": "14/04/2025 08:30", "product": "Agua 500ml", "type": "purchase", "quantity": 50, "user": "admin", "reference": "Factura #1001", "notes": "Compra inicial"},
            {"date": "14/04/2025 09:15", "product": "Refresco", "type": "purchase", "quantity": 40, "user": "admin", "reference": "Factura #1001", "notes": "Compra inicial"},
            {"date": "14/04/2025 10:20", "product": "Agua 500ml", "type": "sale", "quantity": -2, "user": "cajero1", "reference": "Venta #1001", "notes": ""},
            {"date": "14/04/2025 11:05", "product": "Pan", "type": "sale", "quantity": -5, "user": "cajero1", "reference": "Venta #1002", "notes": ""},
            {"date": "14/04/2025 11:30", "product": "Refresco", "type": "sale", "quantity": -3, "user": "cajero1", "reference": "Venta #1003", "notes": ""},
            {"date": "14/04/2025 12:15", "product": "Huevos", "type": "adjustment", "quantity": -2, "user": "admin", "reference": "", "notes": "Ajuste por daño"},
            {"date": "14/04/2025 13:40", "product": "Café", "type": "purchase", "quantity": 10, "user": "admin", "reference": "Factura #1002", "notes": ""},
            {"date": "14/04/2025 14:25", "product": "Galletas", "type": "sale", "quantity": -4, "user": "cajero2", "reference": "Venta #1004", "notes": ""},
            {"date": "14/04/2025 15:10", "product": "Leche", "type": "return", "quantity": 2, "user": "cajero1", "reference": "Devolución #101", "notes": "Cliente insatisfecho"},
            {"date": "14/04/2025 16:00", "product": "Agua 500ml", "type": "sale", "quantity": -6, "user": "cajero2", "reference": "Venta #1005", "notes": ""}
        ]
        
        # Filtrar por categoría si es necesario (simulación)
        if params["category_id"]:
            # Supongamos que los productos de la categoría seleccionada son estos
            category_products = []
            if params["category_name"] == "Bebidas":
                category_products = ["Agua 500ml", "Refresco", "Café"]
            elif params["category_name"] == "Alimentos":
                category_products = ["Pan", "Huevos", "Galletas"]
            elif params["category_name"] == "Lácteos":
                category_products = ["Leche"]
                
            movements = [m for m in movements if m["product"] in category_products]
        
        # Agregar datos a la tabla
        for i, movement in enumerate(movements):
            row = i
            self.inventory_report_table.insertRow(row)
            
            # Fecha
            date_item = QTableWidgetItem(movement["date"])
            date_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_report_table.setItem(row, 0, date_item)
            
            # Producto
            product_item = QTableWidgetItem(movement["product"])
            self.inventory_report_table.setItem(row, 1, product_item)
            
            # Tipo
            type_name = ""
            type_color = QColor(255, 255, 255)  # Blanco por defecto
            
            if movement["type"] == "purchase":
                type_name = "Entrada"
                type_color = QColor(200, 255, 200)  # Verde claro
            elif movement["type"] == "sale":
                type_name = "Salida"
                type_color = QColor(255, 200, 200)  # Rojo claro
            elif movement["type"] == "adjustment":
                type_name = "Ajuste"
                type_color = QColor(255, 255, 200)  # Amarillo claro
            elif movement["type"] == "return":
                type_name = "Devolución"
                type_color = QColor(200, 200, 255)  # Azul claro
            
            type_item = QTableWidgetItem(type_name)
            type_item.setTextAlignment(Qt.AlignCenter)
            type_item.setBackground(type_color)
            self.inventory_report_table.setItem(row, 2, type_item)
            
            # Cantidad
            quantity_item = QTableWidgetItem(str(movement["quantity"]))
            quantity_item.setTextAlignment(Qt.AlignCenter)
            
            # Colorear según el tipo
            if movement["quantity"] > 0:
                quantity_item.setForeground(QColor(0, 128, 0))  # Verde
            else:
                quantity_item.setForeground(QColor(255, 0, 0))  # Rojo
            
            self.inventory_report_table.setItem(row, 3, quantity_item)
            
            # Usuario
            user_item = QTableWidgetItem(movement["user"])
            user_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_report_table.setItem(row, 4, user_item)
            
            # Referencia
            reference_item = QTableWidgetItem(movement["reference"])
            self.inventory_report_table.setItem(row, 5, reference_item)
            
            # Notas
            notes_item = QTableWidgetItem(movement["notes"])
            self.inventory_report_table.setItem(row, 6, notes_item)
    
    def export_inventory_report(self):
        """Exportar reporte de inventario a un archivo"""
        # Verificar que haya un reporte generado
        if self.inventory_report_widget.currentIndex() == 0:
            QMessageBox.warning(self, "Error", "Primero debe generar un reporte")
            return
            
        # Mostrar diálogo para seleccionar formato
        formats = ["PDF", "CSV", "Excel"]
        selected_format, ok = QInputDialog.getItem(
            self, "Exportar Reporte", "Seleccione el formato:", formats, 0, False
        )
        
        if not ok:
            return
            
        # Mostrar diálogo para guardar archivo
        file_extension = ""
        if selected_format == "PDF":
            file_extension = "pdf"
        elif selected_format == "CSV":
            file_extension = "csv"
        elif selected_format == "Excel":
            file_extension = "xlsx"
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte",
            os.path.expanduser("~") + f"/reporte_inventario.{file_extension}",
            f"Archivos {selected_format.upper()} (*.{file_extension})"
        )
        
        if not file_path:
            return
            
        # En un sistema real, invocaríamos al controlador para exportar el reporte
        
        # Para demostración, mostrar mensaje de éxito
        QMessageBox.information(
            self,
            "Reporte Exportado",
            f"El reporte ha sido exportado correctamente a {file_path}"
        )
    
    def generate_cashier_report(self):
        """Generar reporte de caja según los filtros seleccionados"""
        # Obtener fecha
        date = self.cashier_date_edit.date().toString("yyyy-MM-dd")
        
        # Obtener cajero
        cashier_id = self.cashier_combo.currentData()
        cashier_name = self.cashier_combo.currentText() if cashier_id else "Todos"
        
        # Obtener tipo de reporte
        report_type_id = self.cashier_report_type_group.checkedId()
        if report_type_id == 1:
            report_type = "z_report"
        elif report_type_id == 2:
            report_type = "x_report"
        else:
            report_type = "z_report"
        
        # Configurar parámetros del reporte
        report_params = {
            "date": date,
            "cashier_id": cashier_id,
            "cashier_name": cashier_name,
            "report_type": report_type
        }
        
        # En un sistema real, invocaríamos al controlador para generar el reporte
        # self.report_requested.emit(report_type, report_params)
        
        # Para demostración, simulamos la generación del reporte
        self.show_sample_cashier_report(report_type, report_params)
        
        # Habilitar botones
        self.print_cashier_report_button.setEnabled(True)
        self.export_cashier_report_button.setEnabled(True)
    
    def show_sample_cashier_report(self, report_type, params):
        """Mostrar datos de ejemplo para el reporte de caja"""
        if report_type == "z_report":
            self.show_z_report_sample(params)
        elif report_type == "x_report":
            self.show_x_report_sample(params)
    
    def show_z_report_sample(self, params):
        """Mostrar datos de ejemplo para el reporte Z"""
        # Datos de ejemplo
        register_data = {
            "register_id": 101,
            "cashier_name": params["cashier_name"] if params["cashier_id"] else "Admin",
            "opening_time": "14/04/2025 08:00:00",
            "closing_time": "14/04/2025 17:00:00",
            "sales_count": 25,
            "canceled_count": 2,
            "cash_sales": 2500.00,
            "card_sales": 3200.00,
            "transfer_sales": 1300.00,
            "total_sales": 7000.00,
            "opening_amount": 1000.00,
            "closing_amount": 3450.00,
            "expected_amount": 3500.00,
            "difference": -50.00
        }
        
        # Actualizar UI con los datos
        self.register_id_label.setText(str(register_data["register_id"]))
        self.cashier_name_label.setText(register_data["cashier_name"])
        self.opening_time_label.setText(register_data["opening_time"])
        self.closing_time_label.setText(register_data["closing_time"])
        
        self.sales_count_label.setText(str(register_data["sales_count"]))
        self.canceled_count_label.setText(str(register_data["canceled_count"]))
        
        self.cash_sales_label.setText(f"${register_data['cash_sales']:.2f}")
        self.card_sales_label.setText(f"${register_data['card_sales']:.2f}")
        self.transfer_sales_label.setText(f"${register_data['transfer_sales']:.2f}")
        self.total_sales_label.setText(f"${register_data['total_sales']:.2f}")
        
        self.opening_amount_label.setText(f"${register_data['opening_amount']:.2f}")
        self.cash_amount_label.setText(f"${register_data['cash_sales']:.2f}")
        self.expected_amount_label.setText(f"${register_data['expected_amount']:.2f}")
        self.closing_amount_label.setText(f"${register_data['closing_amount']:.2f}")
        
        difference = register_data["difference"]
        difference_text = f"${abs(difference):.2f}"
        if difference < 0:
            difference_text = f"-${abs(difference):.2f}"
            self.difference_label.setStyleSheet("color: red; font-weight: bold;")
        elif difference > 0:
            difference_text = f"+${difference:.2f}"
            self.difference_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.difference_label.setStyleSheet("font-weight: bold;")
            
        self.difference_label.setText(difference_text)
        
        # Mostrar el reporte
        self.cashier_report_widget.setCurrentIndex(1)
    
    def show_x_report_sample(self, params):
        """Mostrar datos de ejemplo para el reporte X"""
        # El reporte X es similar al Z pero con datos actuales (sin cierre)
        # Por simplicidad, usamos la misma lógica pero con algunos cambios
        
        # Datos de ejemplo
        register_data = {
            "register_id": 101,
            "cashier_name": params["cashier_name"] if params["cashier_id"] else "Admin",
            "opening_time": "14/04/2025 08:00:00",
            "closing_time": "En curso",  # Sin cierre aún
            "sales_count": 18,
            "canceled_count": 1,
            "cash_sales": 1800.00,
            "card_sales": 2400.00,
            "transfer_sales": 900.00,
            "total_sales": 5100.00,
            "opening_amount": 1000.00,
            "closing_amount": None,  # Sin cierre aún
            "expected_amount": 2800.00,
            "difference": None  # Sin diferencia calculada aún
        }
        
        # Actualizar UI con los datos
        self.register_id_label.setText(str(register_data["register_id"]))
        self.cashier_name_label.setText(register_data["cashier_name"])
        self.opening_time_label.setText(register_data["opening_time"])
        self.closing_time_label.setText(register_data["closing_time"])
        
        self.sales_count_label.setText(str(register_data["sales_count"]))
        self.canceled_count_label.setText(str(register_data["canceled_count"]))
        
        self.cash_sales_label.setText(f"${register_data['cash_sales']:.2f}")
        self.card_sales_label.setText(f"${register_data['card_sales']:.2f}")
        self.transfer_sales_label.setText(f"${register_data['transfer_sales']:.2f}")
        self.total_sales_label.setText(f"${register_data['total_sales']:.2f}")
        
        self.opening_amount_label.setText(f"${register_data['opening_amount']:.2f}")
        self.cash_amount_label.setText(f"${register_data['cash_sales']:.2f}")
        self.expected_amount_label.setText(f"${register_data['expected_amount']:.2f}")
        self.closing_amount_label.setText("Pendiente")
        
        self.difference_label.setText("Pendiente")
        self.difference_label.setStyleSheet("font-weight: bold;")
        
        # Mostrar el reporte
        self.cashier_report_widget.setCurrentIndex(1)
    
    def print_cashier_report(self):
        """Imprimir reporte de caja"""
        # Verificar que haya un reporte generado
        if self.cashier_report_widget.currentIndex() == 0:
            QMessageBox.warning(self, "Error", "Primero debe generar un reporte")
            return
            
        # En un sistema real, invocaríamos al controlador para imprimir el reporte
        
        # Para demostración, mostrar mensaje de éxito
        QMessageBox.information(
            self,
            "Reporte Impreso",
            "El reporte ha sido enviado a la impresora"
        )
    
    def export_cashier_report(self):
        """Exportar reporte de caja a un archivo"""
        # Verificar que haya un reporte generado
        if self.cashier_report_widget.currentIndex() == 0:
            QMessageBox.warning(self, "Error", "Primero debe generar un reporte")
            return
            
        # Mostrar diálogo para seleccionar formato
        formats = ["PDF", "CSV"]
        selected_format, ok = QInputDialog.getItem(
            self, "Exportar Reporte", "Seleccione el formato:", formats, 0, False
        )
        
        if not ok:
            return
            
        # Mostrar diálogo para guardar archivo
        file_extension = "pdf" if selected_format == "PDF" else "csv"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte",
            os.path.expanduser("~") + f"/reporte_caja.{file_extension}",
            f"Archivos {selected_format.upper()} (*.{file_extension})"
        )
        
        if not file_path:
            return
            
        # En un sistema real, invocaríamos al controlador para exportar el reporte
        
        # Para demostración, mostrar mensaje de éxito
        QMessageBox.information(
            self,
            "Reporte Exportado",
            f"El reporte ha sido exportado correctamente a {file_path}"
        )self,# app/views/reports_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                              QPushButton, QLabel, QDateEdit, QComboBox,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QLineEdit, QGroupBox, QFormLayout, QSpinBox,
                              QRadioButton, QButtonGroup, QMessageBox,
                              QFileDialog, QDialog, QDialogButtonBox,
                              QStackedWidget, QCheckBox, QFrame, QSplitter)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QIcon, QFont

import os
import logging
from datetime import datetime, timedelta

class ReportsView(QWidget):
    """Vista para la generación y visualización de reportes"""
    
    # Señales
    report_requested = Signal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración básica
        self.logger = logging.getLogger('pos.views.reports')
        
        # Inicializar la interfaz
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Pestañas de reportes
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Pestaña de ventas
        sales_tab = self.create_sales_tab()
        tab_widget.addTab(sales_tab, "Ventas")
        
        # Pestaña de inventario
        inventory_tab = self.create_inventory_tab()
        tab_widget.addTab(inventory_tab, "Inventario")
        
        # Pestaña de caja
        cashier_tab = self.create_cashier_tab()
        tab_widget.addTab(cashier_tab, "Caja")
    
    def create_sales_tab(self):
        """Crear pestaña de reportes de ventas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Sección de filtros
        filters_group = QGroupBox("Filtros")
        filters_layout = QHBoxLayout(filters_group)
        
        # Período
        period_form = QFormLayout()
        
        # Fecha inicio
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))  # Último mes por defecto
        
        # Fecha fin
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        
        period_form.addRow("Desde:", self.start_date_edit)
        period_form.addRow("Hasta:", self.end_date_edit)
        
        filters_layout.addLayout(period_form)
        
        # Agrupación
        grouping_form = QFormLayout()
        
        self.grouping_combo = QComboBox()
        self.grouping_combo.addItem("Diario", "day")
        self.grouping_combo.addItem("Semanal", "week")
        self.grouping_combo.addItem("Mensual", "month")
        
        grouping_form.addRow("Agrupación:", self.grouping_combo)
        
        filters_layout.addLayout(grouping_form)
        
        # Tipo de reporte
        report_type_group = QGroupBox("Tipo de Reporte")
        report_type_layout = QVBoxLayout(report_type_group)
        
        self.report_type_group = QButtonGroup()
        
        self.sales_summary_radio = QRadioButton("Resumen de Ventas")
        self.sales_summary_radio.setChecked(True)
        
        self.top_products_radio = QRadioButton("Productos Más Vendidos")
        
        self.sales_by_payment_radio = QRadioButton("Ventas por Método de Pago")
        
        self.report_type_group.addButton(self.sales_summary_radio, 1)
        self.report_type_group.addButton(self.top_products_radio, 2)
        self.report_type_group.addButton(self.sales_by_payment_radio, 3)
        
        report_type_layout.addWidget(self.sales_summary_radio)
        report_type_layout.addWidget(self.top_products_radio)
        report_type_layout.addWidget(self.sales_by_payment_radio)
        
        filters_layout.addWidget(report_type_group)
        
        # Botones de acción
        actions_layout = QVBoxLayout()
        
        self.generate_report_button = QPushButton("Generar Reporte")
        self.generate_report_button.clicked.connect(self.generate_sales_report)
        
        self.export_report_button = QPushButton("Exportar")
        self.export_report_button.clicked.connect(self.export_sales_report)
        self.export_report_button.setEnabled(False)  # Inicialmente deshabilitado
        
        actions_layout.addWidget(self.generate_report_button)
        actions_layout.addWidget(self.export_report_button)
        actions_layout.addStretch()
        
        filters_layout.addLayout(actions_layout)
        
        layout.addWidget(filters_group)
        
        # Área de visualización del reporte
        self.sales_report_widget = QStackedWidget()
        
        # Widget para cuando no hay reporte generado
        no_report_widget = QWidget()
        no_report_layout = QVBoxLayout(no_report_widget)
        no_report_label = QLabel("Configure los filtros y haga clic en 'Generar Reporte' para visualizar.")
        no_report_label.setAlignment(Qt.AlignCenter)
        no_report_layout.addWidget(no_report_label)
        
        self.sales_report_widget.addWidget(no_report_widget)
        
        # Tabla para mostrar resultados
        report_table_widget = QWidget()
        report_table_layout = QVBoxLayout(report_table_widget)
        
        # Etiqueta de título
        self.report_title_label = QLabel("Reporte de Ventas")
        self.report_title_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.report_title_label.setAlignment(Qt.AlignCenter)
        report_table_layout.addWidget(self.report_title_label)
        
        # Tabla de resultados
        self.report_table = QTableWidget()
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        report_table_layout.addWidget(self.report_table)
        
        self.sales_report_widget.addWidget(report_table_widget)
        
        layout.addWidget(self.sales_report_widget)
        
        return tab
    
    def create_inventory_tab(self):
        """Crear pestaña de reportes de inventario"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Sección de filtros
        filters_group = QGroupBox("Filtros")
        filters_layout = QHBoxLayout(filters_group)
        
        # Categoría
        category_form = QFormLayout()
        
        self.inventory_category_combo = QComboBox()
        self.inventory_category_combo.addItem("Todas las categorías", None)
        
        # En un sistema real, cargaríamos las categorías desde el controlador
        self.inventory_category_combo.addItem("Bebidas", 1)
        self.inventory_category_combo.addItem("Alimentos", 2)
        self.inventory_category_combo.addItem("Lácteos", 3)
        
        category_form.addRow("Categoría:", self.inventory_category_combo)
        
        filters_layout.addLayout(category_form)
        
        # Opciones de reporte
        options_group = QGroupBox("Opciones")
        options_layout = QVBoxLayout(options_group)
        
        self.low_stock_checkbox = QCheckBox("Solo productos con stock bajo")
        self.include_cost_checkbox = QCheckBox("Incluir costos")
        self.include_cost_checkbox.setChecked(True)
        
        options_layout.addWidget(self.low_stock_checkbox)
        options_layout.addWidget(self.include_cost_checkbox)
        
        filters_layout.addWidget(options_group)
        
        # Tipo de reporte
        report_type_group = QGroupBox("Tipo de Reporte")
        report_type_layout = QVBoxLayout(report_type_group)
        
        self.inventory_report_type_group = QButtonGroup()
        
        self.inventory_summary_radio = QRadioButton("Resumen de Inventario")
        self.inventory_summary_radio.setChecked(True)
        
        self.stock_value_radio = QRadioButton("Valor del Inventario")
        
        self.inventory_movements_radio = QRadioButton("Movimientos de Inventario")
        
        self.inventory_report_type_group.addButton(self.inventory_summary_radio, 1)
        self.inventory_report_type_group.addButton(self.stock_value_radio, 2)
        self.inventory_report_type_group.addButton(self.inventory_movements_radio, 3)
        
        report_type_layout.addWidget(self.inventory_summary_radio)
        report_type_layout.addWidget(self.stock_value_radio)
        report_type_layout.addWidget(self.inventory_movements_radio)
        
        filters_layout.addWidget(report_type_group)
        
        # Botones de acción
        actions_layout = QVBoxLayout()
        
        self.generate_inventory_report_button = QPushButton("Generar Reporte")
        self.generate_inventory_report_button.clicked.connect(self.generate_inventory_report)
        
        self.export_inventory_report_button = QPushButton("Exportar")
        self.export_inventory_report_button.clicked.connect(self.export_inventory_report)
        self.export_inventory_report_button.setEnabled(False)  # Inicialmente deshabilitado
        
        actions_layout.addWidget(self.generate_inventory_report_button)
        actions_layout.addWidget(self.export_inventory_report_button)
        actions_layout.addStretch()
        
        filters_layout.addLayout(actions_layout)
        
        layout.addWidget(filters_group)
        
        # Área de visualización del reporte
        self.inventory_report_widget = QStackedWidget()
        
        # Widget para cuando no hay reporte generado
        no_report_widget = QWidget()
        no_report_layout = QVBoxLayout(no_report_widget