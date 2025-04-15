# app/views/inventory_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                              QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                              QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                              QSpinBox, QDoubleSpinBox, QMessageBox, QTabWidget,
                              QHeaderView, QGroupBox, QRadioButton, QTreeWidget,
                              QTreeWidgetItem, QSplitter, QStackedWidget, QFrame)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon, QFont, QColor

import logging

class InventoryView(QWidget):
    """Vista para la gestión de inventario"""
    
    # Señales
    product_created = Signal(dict)
    product_updated = Signal(int, dict)
    product_deleted = Signal(int)
    stock_adjusted = Signal(int, int, str)
    category_created = Signal(str, str)
    category_updated = Signal(int, str, str)
    category_deleted = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración básica
        self.logger = logging.getLogger('pos.views.inventory')
        
        # Inicializar la interfaz
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Pestañas
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Pestaña de productos
        products_tab = self.create_products_tab()
        tab_widget.addTab(products_tab, "Productos")
        
        # Pestaña de categorías
        categories_tab = self.create_categories_tab()
        tab_widget.addTab(categories_tab, "Categorías")
        
        # Pestaña de movimientos
        movements_tab = self.create_movements_tab()
        tab_widget.addTab(movements_tab, "Movimientos")
    
    def create_products_tab(self):
        """Crear pestaña de gestión de productos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Encabezado con filtros
        header_layout = QHBoxLayout()
        
        # Búsqueda
        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        self.product_search_input = QLineEdit()
        self.product_search_input.setPlaceholderText("Nombre, código de barras, descripción...")
        self.product_search_input.returnPressed.connect(self.search_products)
        
        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.search_products)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.product_search_input, 1)
        search_layout.addWidget(search_button)
        
        header_layout.addLayout(search_layout, 1)
        
        # Filtro por categoría
        category_layout = QHBoxLayout()
        category_label = QLabel("Categoría:")
        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItem("Todas", None)
        
        # En un sistema real, cargaríamos las categorías desde el controlador
        self.category_filter_combo.addItem("Bebidas", 1)
        self.category_filter_combo.addItem("Alimentos", 2)
        self.category_filter_combo.addItem("Limpieza", 3)
        
        self.category_filter_combo.currentIndexChanged.connect(self.filter_products)
        
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_filter_combo)
        
        header_layout.addLayout(category_layout)
        
        # Botón para mostrar solo productos con stock bajo
        self.low_stock_check = QRadioButton("Stock Bajo")
        self.low_stock_check.toggled.connect(self.filter_products)
        
        # Botón para mostrar todos los productos
        self.all_products_check = QRadioButton("Todos")
        self.all_products_check.setChecked(True)
        self.all_products_check.toggled.connect(self.filter_products)
        
        stock_filter_layout = QHBoxLayout()
        stock_filter_layout.addWidget(self.all_products_check)
        stock_filter_layout.addWidget(self.low_stock_check)
        
        header_layout.addLayout(stock_filter_layout)
        
        # Botón para nuevo producto
        new_product_button = QPushButton("Nuevo Producto")
        new_product_button.clicked.connect(self.show_new_product_dialog)
        header_layout.addWidget(new_product_button)
        
        layout.addLayout(header_layout)
        
        # Tabla de productos
        self.products_table = QTableWidget(0, 8)  # Filas, Columnas
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Código", "Nombre", "Categoría", "Precio", "Costo", "Stock", "Acciones"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.products_table)
        
        # Cargar datos de productos (simulado)
        self.load_sample_products()
        
        return tab
    
    def create_categories_tab(self):
        """Crear pestaña de gestión de categorías"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Encabezado
        header_layout = QHBoxLayout()
        header_label = QLabel("Gestión de Categorías")
        header_label.setFont(QFont('Arial', 14, QFont.Bold))
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Botón para nueva categoría
        new_category_button = QPushButton("Nueva Categoría")
        new_category_button.clicked.connect(self.show_new_category_dialog)
        header_layout.addWidget(new_category_button)
        
        layout.addLayout(header_layout)
        
        # Contenedor dividido
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Árbol de categorías
        categories_frame = QFrame()
        categories_layout = QVBoxLayout(categories_frame)
        
        self.categories_tree = QTreeWidget()
        self.categories_tree.setHeaderLabels(["Categorías"])
        self.categories_tree.setColumnWidth(0, 300)
        self.categories_tree.itemClicked.connect(self.on_category_selected)
        
        categories_layout.addWidget(self.categories_tree)
        
        splitter.addWidget(categories_frame)
        
        # Panel de detalles de categoría
        details_frame = QFrame()
        details_layout = QVBoxLayout(details_frame)
        
        self.category_details_widget = QStackedWidget()
        
        # Widget para cuando no hay categoría seleccionada
        no_selection_widget = QWidget()
        no_selection_layout = QVBoxLayout(no_selection_widget)
        no_selection_label = QLabel("Seleccione una categoría para ver sus detalles")
        no_selection_label.setAlignment(Qt.AlignCenter)
        no_selection_layout.addWidget(no_selection_label)
        
        self.category_details_widget.addWidget(no_selection_widget)
        
        # Widget para detalles de categoría
        category_widget = QWidget()
        category_layout = QVBoxLayout(category_widget)
        
        # Formulario de detalles
        form_layout = QFormLayout()
        
        self.category_name_label = QLabel()
        self.category_name_label.setFont(QFont('Arial', 14, QFont.Bold))
        
        self.category_description_label = QLabel()
        self.category_description_label.setWordWrap(True)
        
        self.category_count_label = QLabel()
        
        form_layout.addRow("Nombre:", self.category_name_label)
        form_layout.addRow("Descripción:", self.category_description_label)
        form_layout.addRow("Productos:", self.category_count_label)
        
        category_layout.addLayout(form_layout)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        edit_category_button = QPushButton("Editar")
        edit_category_button.clicked.connect(self.show_edit_category_dialog)
        
        delete_category_button = QPushButton("Eliminar")
        delete_category_button.clicked.connect(self.confirm_delete_category)
        
        buttons_layout.addWidget(edit_category_button)
        buttons_layout.addWidget(delete_category_button)
        
        category_layout.addLayout(buttons_layout)
        category_layout.addStretch()
        
        self.category_details_widget.addWidget(category_widget)
        
        details_layout.addWidget(self.category_details_widget)
        
        splitter.addWidget(details_frame)
        
        # Establecer proporciones
        splitter.setSizes([int(self.width() * 0.4), int(self.width() * 0.6)])
        
        # Cargar categorías (simulado)
        self.load_sample_categories()
        
        return tab
    
    def create_movements_tab(self):
        """Crear pestaña de movimientos de inventario"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Encabezado con filtros
        header_layout = QHBoxLayout()
        
        # Selección de producto
        product_layout = QHBoxLayout()
        product_label = QLabel("Producto:")
        self.product_filter_combo = QComboBox()
        self.product_filter_combo.setMinimumWidth(200)
        self.product_filter_combo.addItem("Todos", None)
        
        # En un sistema real, cargaríamos los productos desde el controlador
        self.product_filter_combo.addItem("Agua 500ml", 1)
        self.product_filter_combo.addItem("Refresco", 2)
        self.product_filter_combo.addItem("Pan", 3)
        
        self.product_filter_combo.currentIndexChanged.connect(self.filter_movements)
        
        product_layout.addWidget(product_label)
        product_layout.addWidget(self.product_filter_combo)
        
        header_layout.addLayout(product_layout)
        
        # Filtro por tipo de movimiento
        type_layout = QHBoxLayout()
        type_label = QLabel("Tipo:")
        self.movement_type_combo = QComboBox()
        self.movement_type_combo.addItem("Todos", None)
        self.movement_type_combo.addItem("Entrada", "purchase")
        self.movement_type_combo.addItem("Salida", "sale")
        self.movement_type_combo.addItem("Ajuste", "adjustment")
        self.movement_type_combo.addItem("Devolución", "return")
        
        self.movement_type_combo.currentIndexChanged.connect(self.filter_movements)
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.movement_type_combo)
        
        header_layout.addLayout(type_layout)
        
        # Botón para nuevo movimiento
        new_movement_button = QPushButton("Nuevo Movimiento")
        new_movement_button.clicked.connect(self.show_new_movement_dialog)
        header_layout.addWidget(new_movement_button)
        
        layout.addLayout(header_layout)
        
        # Tabla de movimientos
        self.movements_table = QTableWidget(0, 7)  # Filas, Columnas
        self.movements_table.setHorizontalHeaderLabels([
            "ID", "Fecha", "Producto", "Tipo", "Cantidad", "Usuario", "Notas"
        ])
        self.movements_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.movements_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.movements_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.movements_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.movements_table)
        
        # Cargar datos de movimientos (simulado)
        self.load_sample_movements()
        
        return tab
    
    def load_sample_products(self):
        """Cargar datos de ejemplo de productos (para demostración)"""
        # Limpiar tabla
        self.products_table.setRowCount(0)
        
        # Datos de ejemplo
        products = [
            {"product_id": 1, "barcode": "7501055310209", "name": "Agua 500ml", "category": "Bebidas", "price": 10.0, "cost": 5.0, "stock": 24},
            {"product_id": 2, "barcode": "7501055310216", "name": "Refresco", "category": "Bebidas", "price": 15.0, "cost": 8.0, "stock": 35},
            {"product_id": 3, "barcode": "7501055310223", "name": "Pan", "category": "Alimentos", "price": 20.0, "cost": 12.0, "stock": 8},
            {"product_id": 4, "barcode": "7501055310230", "name": "Leche", "category": "Lácteos", "price": 25.0, "cost": 18.0, "stock": 16},
            {"product_id": 5, "barcode": "7501055310247", "name": "Huevos", "category": "Alimentos", "price": 30.0, "cost": 22.0, "stock": 4}
        ]
        
        # Agregar datos a la tabla
        for product in products:
            row_position = self.products_table.rowCount()
            self.products_table.insertRow(row_position)
            
            # ID
            id_item = QTableWidgetItem(str(product["product_id"]))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.products_table.setItem(row_position, 0, id_item)
            
            # Código de barras
            barcode_item = QTableWidgetItem(product["barcode"])
            barcode_item.setTextAlignment(Qt.AlignCenter)
            self.products_table.setItem(row_position, 1, barcode_item)
            
            # Nombre
            name_item = QTableWidgetItem(product["name"])
            self.products_table.setItem(row_position, 2, name_item)
            
            # Categoría
            category_item = QTableWidgetItem(product["category"])
            category_item.setTextAlignment(Qt.AlignCenter)
            self.products_table.setItem(row_position, 3, category_item)
            
            # Precio
            price_item = QTableWidgetItem(f"${product['price']:.2f}")
            price_item.setTextAlignment(Qt.AlignCenter)
            self.products_table.setItem(row_position, 4, price_item)
            
            # Costo
            cost_item = QTableWidgetItem(f"${product['cost']:.2f}")
            cost_item.setTextAlignment(Qt.AlignCenter)
            self.products_table.setItem(row_position, 5, cost_item)
            
            # Stock
            stock_item = QTableWidgetItem(str(product["stock"]))
            stock_item.setTextAlignment(Qt.AlignCenter)
            
            # Colorear stock bajo
            if product["stock"] <= 5:
                stock_item.setBackground(QColor(255, 200, 200))  # Rojo claro
            
            self.products_table.setItem(row_position, 6, stock_item)
            
            # Botones de acción
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_button = QPushButton("Editar")
            edit_button.setProperty("product_id", product["product_id"])
            edit_button.clicked.connect(lambda checked, product_id=product["product_id"]: self.show_edit_product_dialog(product_id))
            
            stock_button = QPushButton("Stock")
            stock_button.setProperty("product_id", product["product_id"])
            stock_button.clicked.connect(lambda checked, product_id=product["product_id"]: self.show_adjust_stock_dialog(product_id))
            
            delete_button = QPushButton("Eliminar")
            delete_button.setProperty("product_id", product["product_id"])
            delete_button.clicked.connect(lambda checked, product_id=product["product_id"]: self.confirm_delete_product(product_id))
            
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(stock_button)
            actions_layout.addWidget(delete_button)
            
            self.products_table.setCellWidget(row_position, 7, actions_widget)
    
    def load_sample_categories(self):
        """Cargar datos de ejemplo de categorías (para demostración)"""
        # Limpiar árbol
        self.categories_tree.clear()
        
        # Datos de ejemplo
        categories = [
            {"category_id": 1, "name": "Bebidas", "description": "Todo tipo de bebidas", "product_count": 15},
            {"category_id": 2, "name": "Alimentos", "description": "Productos alimenticios", "product_count": 25},
            {"category_id": 3, "name": "Lácteos", "description": "Productos lácteos y derivados", "product_count": 10},
            {"category_id": 4, "name": "Limpieza", "description": "Productos de limpieza", "product_count": 8},
            {"category_id": 5, "name": "Higiene Personal", "description": "Productos de higiene personal", "product_count": 12}
        ]
        
        # Agregar al árbol
        for category in categories:
            item = QTreeWidgetItem([category["name"]])
            item.setData(0, Qt.UserRole, category)
            
            # Mostrar cantidad de productos
            item.setText(0, f"{category['name']} ({category['product_count']})")
            
            self.categories_tree.addTopLevelItem(item)
    
    def load_sample_movements(self):
        """Cargar datos de ejemplo de movimientos (para demostración)"""
        # Limpiar tabla
        self.movements_table.setRowCount(0)
        
        # Datos de ejemplo
        movements = [
            {"movement_id": 1, "date": "14/04/2025 08:30", "product": "Agua 500ml", "type": "purchase", "quantity": 50, "user": "admin", "notes": "Compra inicial"},
            {"movement_id": 2, "date": "14/04/2025 09:15", "product": "Refresco", "type": "purchase", "quantity": 40, "user": "admin", "notes": "Compra inicial"},
            {"movement_id": 3, "date": "14/04/2025 10:20", "product": "Agua 500ml", "type": "sale", "quantity": -2, "user": "cajero1", "notes": "Venta #1001"},
            {"movement_id": 4, "date": "14/04/2025 11:05", "product": "Pan", "type": "sale", "quantity": -5, "user": "cajero1", "notes": "Venta #1002"},
            {"movement_id": 5, "date": "14/04/2025 11:30", "product": "Refresco", "type": "sale", "quantity": -3, "user": "cajero1", "notes": "Venta #1003"},
            {"movement_id": 6, "date": "14/04/2025 12:15", "product": "Huevos", "type": "adjustment", "quantity": -2, "user": "admin", "notes": "Ajuste por daño"}
        ]
        
        # Agregar datos a la tabla
        for movement in movements:
            row_position = self.movements_table.rowCount()
            self.movements_table.insertRow(row_position)
            
            # ID
            id_item = QTableWidgetItem(str(movement["movement_id"]))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.movements_table.setItem(row_position, 0, id_item)
            
            # Fecha
            date_item = QTableWidgetItem(movement["date"])
            date_item.setTextAlignment(Qt.AlignCenter)
            self.movements_table.setItem(row_position, 1, date_item)
            
            # Producto
            product_item = QTableWidgetItem(movement["product"])
            self.movements_table.setItem(row_position, 2, product_item)
            
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
            self.movements_table.setItem(row_position, 3, type_item)
            
            # Cantidad
            quantity_item = QTableWidgetItem(str(movement["quantity"]))
            quantity_item.setTextAlignment(Qt.AlignCenter)
            
            # Colorear según el tipo
            if movement["quantity"] > 0:
                quantity_item.setForeground(QColor(0, 128, 0))  # Verde
            else:
                quantity_item.setForeground(QColor(255, 0, 0))  # Rojo
            
            self.movements_table.setItem(row_position, 4, quantity_item)
            
            # Usuario
            user_item = QTableWidgetItem(movement["user"])
            user_item.setTextAlignment(Qt.AlignCenter)
            self.movements_table.setItem(row_position, 5, user_item)
            
            # Notas
            notes_item = QTableWidgetItem(movement["notes"])
            self.movements_table.setItem(row_position, 6, notes_item)
    
    def search_products(self):
        """Buscar productos según el texto ingresado"""
        # En un sistema real, invocaríamos al controlador para la búsqueda
        
        # Para demostración, simulamos la búsqueda
        search_text = self.product_search_input.text().strip().lower()
        
        if not search_text:
            # Si no hay texto, mostrar todos los productos
            self.load_sample_products()
            return
            
        # Filtrar los productos (simulado)
        self.filter_products()
        
        # Mostrar mensaje de búsqueda
        self.statusBar().showMessage(f"Buscando productos que contengan '{search_text}'...", 3000)
    
    def filter_products(self):
        """Filtrar productos según categoría y estado de stock"""
        # En un sistema real, invocaríamos al controlador para el filtrado
        
        # Para demostración, simulamos el filtrado
        category_id = self.category_filter_combo.currentData()
        low_stock_only = self.low_stock_check.isChecked()
        
        # Recargar productos (simulado)
        self.load_sample_products()
        
        # Mostrar mensaje de filtrado
        if category_id is not None:
            category_name = self.category_filter_combo.currentText()
            self.statusBar().showMessage(f"Filtrando productos de la categoría '{category_name}'...", 3000)
        
        if low_stock_only:
            self.statusBar().showMessage("Mostrando productos con stock bajo...", 3000)
    
    def filter_movements(self):
        """Filtrar movimientos según producto y tipo"""
        # En un sistema real, invocaríamos al controlador para el filtrado
        
        # Para demostración, simulamos el filtrado
        product_id = self.product_filter_combo.currentData()
        movement_type = self.movement_type_combo.currentData()
        
        # Recargar movimientos (simulado)
        self.load_sample_movements()
        
        # Mostrar mensaje de filtrado
        filters = []
        
        if product_id is not None:
            product_name = self.product_filter_combo.currentText()
            filters.append(f"producto '{product_name}'")
        
        if movement_type is not None:
            type_name = self.movement_type_combo.currentText()
            filters.append(f"tipo '{type_name}'")
        
        if filters:
            self.statusBar().showMessage(f"Filtrando movimientos por {' y '.join(filters)}...", 3000)
    
    def on_category_selected(self, item):
        """Manejar selección de categoría en el árbol"""
        # Obtener datos de la categoría
        category_data = item.data(0, Qt.UserRole)
        
        if not category_data:
            return
            
        # Actualizar panel de detalles
        self.category_name_label.setText(category_data["name"])
        self.category_description_label.setText(category_data["description"])
        self.category_count_label.setText(str(category_data["product_count"]))
        
        # Mostrar panel de detalles
        self.category_details_widget.setCurrentIndex(1)
    
    def show_new_product_dialog(self):
        """Mostrar diálogo para crear un nuevo producto"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Producto")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Formulario
        form_layout = QFormLayout()
        
        barcode_input = QLineEdit()
        barcode_input.setPlaceholderText("Código de barras")
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Nombre del producto")
        
        description_input = QLineEdit()
        description_input.setPlaceholderText("Descripción (opcional)")
        
        category_combo = QComboBox()
        category_combo.addItem("Seleccione una categoría", None)
        
        # En un sistema real, cargaríamos las categorías desde el controlador
        category_combo.addItem("Bebidas", 1)
        category_combo.addItem("Alimentos", 2)
        category_combo.addItem("Lácteos", 3)
        category_combo.addItem("Limpieza", 4)
        category_combo.addItem("Higiene Personal", 5)
        
        price_input = QDoubleSpinBox()
        price_input.setPrefix("$")
        price_input.setMaximum(99999.99)
        price_input.setDecimals(2)
        
        cost_input = QDoubleSpinBox()
        cost_input.setPrefix("$")
        cost_input.setMaximum(99999.99)
        cost_input.setDecimals(2)
        
        stock_input = QSpinBox()
        stock_input.setMinimum(0)
        stock_input.setMaximum(99999)
        
        min_stock_input = QSpinBox()
        min_stock_input.setMinimum(1)
        min_stock_input.setMaximum(999)
        min_stock_input.setValue(5)  # Valor por defecto
        
        form_layout.addRow("Código de barras:", barcode_input)
        form_layout.addRow("Nombre:", name_input)
        form_layout.addRow("Descripción:", description_input)
        form_layout.addRow("Categoría:", category_combo)
        form_layout.addRow("Precio de venta:", price_input)
        form_layout.addRow("Costo:", cost_input)
        form_layout.addRow("Stock inicial:", stock_input)
        form_layout.addRow("Stock mínimo:", min_stock_input)
        
        layout.addLayout(form_layout)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)

        # Mostrar diálogo
        if dialog.exec() == QDialog.Accepted:
            # Verificar campos obligatorios
            if not name_input.text():
                QMessageBox.warning(self, "Error", "El nombre del producto es obligatorio")
                return

            if price_input.value() == 0:
                QMessageBox.warning(self, "Error", "El precio de venta debe ser mayor que cero")
                return

            # Crear producto
            product_data = {
                "barcode": barcode_input.text(),
                "name": name_input.text(),
                "description": description_input.text(),
                "category_id": category_combo.currentData(),
                "price": price_input.value(),
                "cost": cost_input.value(),
                "stock_quantity": stock_input.value(),
                "min_stock_level": min_stock_input.value()
            }

            # Emitir señal (en un sistema real, esto invocaría al controlador)
            self.product_created.emit(product_data)

            # Para demostración, recargar los productos
            self.load_sample_products()

            QMessageBox.information(self, "Producto Creado", f"Producto '{product_data['name']}' creado correctamente")
    
    def show_edit_product_dialog(self, product_id):
        """
        Mostrar diálogo para editar un producto existente
        
        Args:
            product_id: ID del producto a editar
        """
        # En un sistema real, obtendríamos los datos del producto desde el controlador
        # Para demostración, usamos datos de ejemplo
        product_data = None
        for row in range(self.products_table.rowCount()):
            if int(self.products_table.item(row, 0).text()) == product_id:
                product_data = {
                    "product_id": product_id,
                    "barcode": self.products_table.item(row, 1).text(),
                    "name": self.products_table.item(row, 2).text(),
                    "category": self.products_table.item(row, 3).text(),
                    "price": float(self.products_table.item(row, 4).text().replace('$', '')),
                    "cost": float(self.products_table.item(row, 5).text().replace('$', '')),
                    "stock_quantity": int(self.products_table.item(row, 6).text())
                }
                break
                
        if not product_data:
            QMessageBox.warning(self, "Error", f"Producto con ID {product_id} no encontrado")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Editar Producto: {product_data['name']}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Formulario
        form_layout = QFormLayout()
        
        barcode_input = QLineEdit(product_data["barcode"])
        
        name_input = QLineEdit(product_data["name"])
        
        description_input = QLineEdit()  # En un sistema real, se cargaría del producto
        
        category_combo = QComboBox()
        category_combo.addItem("Seleccione una categoría", None)
        
        # En un sistema real, cargaríamos las categorías desde el controlador
        category_combo.addItem("Bebidas", 1)
        category_combo.addItem("Alimentos", 2)
        category_combo.addItem("Lácteos", 3)
        category_combo.addItem("Limpieza", 4)
        category_combo.addItem("Higiene Personal", 5)
        
        # Seleccionar la categoría actual
        category_index = category_combo.findText(product_data["category"])
        if category_index >= 0:
            category_combo.setCurrentIndex(category_index)
        
        price_input = QDoubleSpinBox()
        price_input.setPrefix("$")
        price_input.setMaximum(99999.99)
        price_input.setDecimals(2)
        price_input.setValue(product_data["price"])
        
        cost_input = QDoubleSpinBox()
        cost_input.setPrefix("$")
        cost_input.setMaximum(99999.99)
        cost_input.setDecimals(2)
        cost_input.setValue(product_data["cost"])
        
        min_stock_input = QSpinBox()
        min_stock_input.setMinimum(1)
        min_stock_input.setMaximum(999)
        min_stock_input.setValue(5)  # En un sistema real, se cargaría del producto
        
        stock_label = QLabel(str(product_data["stock_quantity"]))
        stock_label.setFont(QFont('Arial', 10, QFont.Bold))
        
        form_layout.addRow("Código de barras:", barcode_input)
        form_layout.addRow("Nombre:", name_input)
        form_layout.addRow("Descripción:", description_input)
        form_layout.addRow("Categoría:", category_combo)
        form_layout.addRow("Precio de venta:", price_input)
        form_layout.addRow("Costo:", cost_input)
        form_layout.addRow("Stock actual:", stock_label)
        form_layout.addRow("Stock mínimo:", min_stock_input)
        
        layout.addLayout(form_layout)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        
        # Mostrar diálogo
        if dialog.exec() == QDialog.Accepted:
            # Verificar campos obligatorios
            if not name_input.text():
                QMessageBox.warning(self, "Error", "El nombre del producto es obligatorio")
                return
                
            if price_input.value() == 0:
                QMessageBox.warning(self, "Error", "El precio de venta debe ser mayor que cero")
                return
                
            # Actualizar producto
            updated_data = {
                "barcode": barcode_input.text(),
                "name": name_input.text(),
                "description": description_input.text(),
                "category_id": category_combo.currentData(),
                "price": price_input.value(),
                "cost": cost_input.value(),
                "min_stock_level": min_stock_input.value()
            }
            
            # Emitir señal (en un sistema real, esto invocaría al controlador)
            self.product_updated.emit(product_id, updated_data)
            
            # Para demostración, recargar los productos
            self.load_sample_products()
            
            QMessageBox.information(self, "Producto Actualizado", f"Producto '{updated_data['name']}' actualizado correctamente")
    
    def show_adjust_stock_dialog(self, product_id):
        """
        Mostrar diálogo para ajustar el stock de un producto
        
        Args:
            product_id: ID del producto a ajustar
        """
        # En un sistema real, obtendríamos los datos del producto desde el controlador
        # Para demostración, usamos datos de ejemplo
        product_data = None
        for row in range(self.products_table.rowCount()):
            if int(self.products_table.item(row, 0).text()) == product_id:
                product_data = {
                    "product_id": product_id,
                    "name": self.products_table.item(row, 2).text(),
                    "stock_quantity": int(self.products_table.item(row, 6).text())
                }
                break
                
        if not product_data:
            QMessageBox.warning(self, "Error", f"Producto con ID {product_id} no encontrado")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ajustar Stock: {product_data['name']}")
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        
        # Etiqueta de información
        info_label = QLabel(f"Producto: {product_data['name']}")
        info_label.setFont(QFont('Arial', 11, QFont.Bold))
        layout.addWidget(info_label)
        
        # Stock actual
        current_stock_layout = QHBoxLayout()
        current_stock_label = QLabel("Stock actual:")
        current_stock_value = QLabel(str(product_data["stock_quantity"]))
        current_stock_value.setFont(QFont('Arial', 11, QFont.Bold))
        
        current_stock_layout.addWidget(current_stock_label)
        current_stock_layout.addWidget(current_stock_value)
        
        layout.addLayout(current_stock_layout)
        
        # Opciones de ajuste
        adjustment_group = QGroupBox("Tipo de Ajuste")
        adjustment_layout = QVBoxLayout(adjustment_group)
        
        # Opciones de radio
        self.add_stock_radio = QRadioButton("Agregar al stock actual")
        self.add_stock_radio.setChecked(True)
        
        self.remove_stock_radio = QRadioButton("Restar del stock actual")
        
        self.set_stock_radio = QRadioButton("Establecer nuevo valor")
        
        adjustment_layout.addWidget(self.add_stock_radio)
        adjustment_layout.addWidget(self.remove_stock_radio)
        adjustment_layout.addWidget(self.set_stock_radio)
        
        layout.addWidget(adjustment_group)
        
        # Cantidad a ajustar
        quantity_layout = QHBoxLayout()
        quantity_label = QLabel("Cantidad:")
        
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(9999)
        
        quantity_layout.addWidget(quantity_label)
        quantity_layout.addWidget(self.quantity_input)
        
        layout.addLayout(quantity_layout)
        
        # Motivo del ajuste
        reason_layout = QFormLayout()
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("Motivo del ajuste")
        
        reason_layout.addRow("Motivo:", self.reason_input)
        
        layout.addLayout(reason_layout)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        
        # Mostrar diálogo
        if dialog.exec() == QDialog.Accepted:
            # Obtener cantidad y tipo de ajuste
            quantity = self.quantity_input.value()
            reason = self.reason_input.text()
            
            if self.add_stock_radio.isChecked():
                # Agregar al stock
                adjustment_type = "add"
            elif self.remove_stock_radio.isChecked():
                # Restar del stock
                adjustment_type = "remove"
                # Verificar que no se reste más de lo que hay
                if quantity > product_data["stock_quantity"]:
                    QMessageBox.warning(self, "Error", "No puede restar más unidades de las que hay en stock")
                    return
            else:
                # Establecer nuevo valor
                adjustment_type = "set"
            
            # Emitir señal (en un sistema real, esto invocaría al controlador)
            self.stock_adjusted.emit(product_id, quantity, adjustment_type)
            
            # Para demostración, recargar los productos
            self.load_sample_products()
            
            # Mensaje según el tipo de ajuste
            if adjustment_type == "add":
                message = f"Se agregaron {quantity} unidades al stock"
            elif adjustment_type == "remove":
                message = f"Se restaron {quantity} unidades del stock"
            else:
                message = f"Se estableció el stock en {quantity} unidades"
                
            QMessageBox.information(self, "Stock Ajustado", message)
    
    def confirm_delete_product(self, product_id):
        """
        Confirmar eliminación de un producto
        
        Args:
            product_id: ID del producto a eliminar
        """
        # Obtener nombre del producto
        product_name = ""
        for row in range(self.products_table.rowCount()):
            if int(self.products_table.item(row, 0).text()) == product_id:
                product_name = self.products_table.item(row, 2).text()
                break
                
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el producto '{product_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Emitir señal (en un sistema real, esto invocaría al controlador)
            self.product_deleted.emit(product_id)
            
            # Para demostración, recargar los productos
            self.load_sample_products()
            
            QMessageBox.information(self, "Producto Eliminado", f"Producto '{product_name}' eliminado correctamente")
    
    def show_new_category_dialog(self):
        """Mostrar diálogo para crear una nueva categoría"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Nueva Categoría")
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        
        # Formulario
        form_layout = QFormLayout()
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Nombre de la categoría")
        
        description_input = QLineEdit()
        description_input.setPlaceholderText("Descripción (opcional)")
        
        form_layout.addRow("Nombre:", name_input)
        form_layout.addRow("Descripción:", description_input)
        
        layout.addLayout(form_layout)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        
        # Mostrar diálogo
        if dialog.exec() == QDialog.Accepted:
            # Verificar campos obligatorios
            if not name_input.text():
                QMessageBox.warning(self, "Error", "El nombre de la categoría es obligatorio")
                return
                
            # Crear categoría
            name = name_input.text()
            description = description_input.text()
            
            # Emitir señal (en un sistema real, esto invocaría al controlador)
            self.category_created.emit(name, description)
            
            # Para demostración, recargar las categorías
            self.load_sample_categories()
            
            QMessageBox.information(self, "Categoría Creada", f"Categoría '{name}' creada correctamente")
    
    def show_edit_category_dialog(self):
        """Mostrar diálogo para editar la categoría seleccionada"""
        # Obtener la categoría seleccionada
        selected_items = self.categories_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "No hay categoría seleccionada")
            return
            
        item = selected_items[0]
        category_data = item.data(0, Qt.UserRole)
        
        if not category_data:
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Editar Categoría: {category_data['name']}")
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        
        # Formulario
        form_layout = QFormLayout()
        
        name_input = QLineEdit(category_data["name"])
        
        description_input = QLineEdit(category_data["description"])
        
        form_layout.addRow("Nombre:", name_input)
        form_layout.addRow("Descripción:", description_input)
        
        layout.addLayout(form_layout)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        
        # Mostrar diálogo
        if dialog.exec() == QDialog.Accepted:
            # Verificar campos obligatorios
            if not name_input.text():
                QMessageBox.warning(self, "Error", "El nombre de la categoría es obligatorio")
                return
                
            # Actualizar categoría
            category_id = category_data["category_id"]
            name = name_input.text()
            description = description_input.text()
            
            # Emitir señal (en un sistema real, esto invocaría al controlador)
            self.category_updated.emit(category_id, name, description)
            
            # Para demostración, recargar las categorías
            self.load_sample_categories()
            
            QMessageBox.information(self, "Categoría Actualizada", f"Categoría '{name}' actualizada correctamente")
    
    def confirm_delete_category(self):
        """Confirmar eliminación de la categoría seleccionada"""
        # Obtener la categoría seleccionada
        selected_items = self.categories_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "No hay categoría seleccionada")
            return
            
        item = selected_items[0]
        category_data = item.data(0, Qt.UserRole)
        
        if not category_data:
            return
            
        # Verificar si tiene productos asociados
        if category_data["product_count"] > 0:
            QMessageBox.warning(
                self, 
                "No se puede eliminar", 
                f"La categoría '{category_data['name']}' tiene {category_data['product_count']} productos asociados.\n\n"
                "Debe reasignar o eliminar estos productos antes de eliminar la categoría."
            )
            return
            
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar la categoría '{category_data['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Emitir señal (en un sistema real, esto invocaría al controlador)
            self.category_deleted.emit(category_data["category_id"])
            
            # Para demostración, recargar las categorías
            self.load_sample_categories()
            
            # Ocultar panel de detalles
            self.category_details_widget.setCurrentIndex(0)
            
            QMessageBox.information(self, "Categoría Eliminada", f"Categoría '{category_data['name']}' eliminada correctamente")
    
    def show_new_movement_dialog(self):
        """Mostrar diálogo para registrar un nuevo movimiento de inventario"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuevo Movimiento de Inventario")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Formulario
        form_layout = QFormLayout()
        
        # Selección de producto
        product_combo = QComboBox()
        product_combo.setMinimumWidth(250)
        product_combo.addItem("Seleccione un producto", None)
        
        # En un sistema real, cargaríamos los productos desde el controlador
        product_combo.addItem("Agua 500ml", 1)
        product_combo.addItem("Refresco", 2)
        product_combo.addItem("Pan", 3)
        product_combo.addItem("Leche", 4)
        product_combo.addItem("Huevos", 5)
        
        # Tipo de movimiento
        movement_type_combo = QComboBox()
        movement_type_combo.addItem("Entrada", "purchase")
        movement_type_combo.addItem("Salida", "sale")
        movement_type_combo.addItem("Ajuste", "adjustment")
        movement_type_combo.addItem("Devolución", "return")
        
        # Cantidad
        quantity_spin = QSpinBox()
        quantity_spin.setMinimum(1)
        quantity_spin.setMaximum(9999)
        
        # Referencia
        reference_input = QLineEdit()
        reference_input.setPlaceholderText("Número de factura, orden, etc. (opcional)")
        
        # Notas
        notes_input = QLineEdit()
        notes_input.setPlaceholderText("Detalles adicionales (opcional)")
        
        form_layout.addRow("Producto:", product_combo)
        form_layout.addRow("Tipo:", movement_type_combo)
        form_layout.addRow("Cantidad:", quantity_spin)
        form_layout.addRow("Referencia:", reference_input)
        form_layout.addRow("Notas:", notes_input)
        
        layout.addLayout(form_layout)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        
        # Mostrar diálogo
        if dialog.exec() == QDialog.Accepted:
            # Verificar producto
            if product_combo.currentData() is None:
                QMessageBox.warning(self, "Error", "Debe seleccionar un producto")
                return
                
            # Obtener datos
            product_id = product_combo.currentData()
            product_name = product_combo.currentText()
            movement_type = movement_type_combo.currentData()
            movement_type_name = movement_type_combo.currentText()
            quantity = quantity_spin.value()
            reference = reference_input.text()
            notes = notes_input.text()

            if movement_type in ["sale", "adjustment"]:
                quantity = -quantity
            
            # En un sistema real, invocaríamos al controlador para registrar el movimiento
            
            # Para demostración, recargar los movimientos
            self.load_sample_movements()
            
            QMessageBox.information(
                self, 
                "Movimiento Registrado", 
                f"Se ha registrado un movimiento de {movement_type_name} "
                f"para el producto '{product_name}' con cantidad {abs(quantity)}."
            )
    
    def statusBar(self):
        """Obtener la barra de estado de la ventana principal"""
        # Buscar la ventana principal (QMainWindow)
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'statusBar'):
                return parent.statusBar()
            parent = parent.parent()
        return None  # Si no se encuentra