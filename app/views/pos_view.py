# app/views/pos_view.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                              QLineEdit, QGridLayout, QFrame, QDialog, QComboBox,
                              QMessageBox, QHeaderView, QSplitter, QTabWidget)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QIcon, QKeySequence, QShortcut

class POSView(QMainWindow):
    """Vista principal del punto de venta"""

    barcode_scanned = Signal(str)  # Señal cuando se detecta un código de barras
    product_selected = Signal(int)  # Señal cuando se selecciona un producto de la lista
    checkout_requested = Signal(dict)  # Señal cuando se solicita finalizar la venta
    open_drawer_requested = Signal()  # Señal para abrir la caja
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sistema POS")
        self.resize(1024, 768)  # Tamaño inicial
        
        # Configurar la interfaz principal
        self.setup_ui()
        
        # Conectar señales internas
        self._connect_signals()
        
        # Accesos rápidos de teclado
        self._setup_shortcuts()

    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Diseño principal
        main_layout = QHBoxLayout(central_widget)
        
        # Dividir la pantalla: carrito a la izquierda, catálogo a la derecha
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Panel izquierdo (carrito de compra)
        cart_widget = QWidget()
        cart_layout = QVBoxLayout(cart_widget)
        
        # Información superior
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_layout = QHBoxLayout(info_frame)
        
        # Información del cajero y fecha
        self.cashier_label = QLabel("Cajero: Juan Pérez")
        self.date_label = QLabel("Fecha: 14/04/2025")
        info_layout.addWidget(self.cashier_label)
        info_layout.addWidget(self.date_label)
        
        cart_layout.addWidget(info_frame)
        
        # Campo de búsqueda/escaneo
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Escanear código o buscar producto...")
        self.barcode_input.returnPressed.connect(self._on_barcode_entered)
        
        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self._on_barcode_entered)
        
        search_layout.addWidget(self.barcode_input, 4)
        search_layout.addWidget(search_button, 1)
        
        cart_layout.addWidget(search_frame)
        
        # Tabla del carrito
        self.cart_table = QTableWidget(0, 5)  # Filas, Columnas
        self.cart_table.setHorizontalHeaderLabels(["Producto", "Precio", "Cantidad", "Subtotal", ""])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        cart_layout.addWidget(self.cart_table, 1)
        
        # Área de totales
        totals_frame = QFrame()
        totals_frame.setFrameShape(QFrame.StyledPanel)
        totals_layout = QGridLayout(totals_frame)
        
        # Etiquetas y valores
        subtotal_label = QLabel("Subtotal:")
        self.subtotal_value = QLabel("$0.00")
        
        tax_label = QLabel("IVA:")
        self.tax_value = QLabel("$0.00")
        
        total_label = QLabel("TOTAL:")
        self.total_value = QLabel("$0.00")
        self.total_value.setStyleSheet("font-size: 18pt; font-weight: bold;")
        
        # Colocar en el grid
        totals_layout.addWidget(subtotal_label, 0, 0)
        totals_layout.addWidget(self.subtotal_value, 0, 1)
        totals_layout.addWidget(tax_label, 1, 0)
        totals_layout.addWidget(self.tax_value, 1, 1)
        totals_layout.addWidget(total_label, 2, 0)
        totals_layout.addWidget(self.total_value, 2, 1)
        
        cart_layout.addWidget(totals_frame)
        
        # Botones de acción
        action_frame = QFrame()
        action_layout = QHBoxLayout(action_frame)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14pt;")
        
        self.checkout_button = QPushButton("Cobrar")
        self.checkout_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14pt;")
        
        action_layout.addWidget(self.cancel_button)
        action_layout.addWidget(self.checkout_button)
        
        cart_layout.addWidget(action_frame)
        
        # Agregar el panel del carrito al splitter
        splitter.addWidget(cart_widget)
        
        # Panel derecho (catálogo de productos)
        catalog_widget = QWidget()
        catalog_layout = QVBoxLayout(catalog_widget)
        
        # Pestañas para el catálogo
        tab_widget = QTabWidget()
        
        # Pestaña de productos
        products_tab = QWidget()
        products_layout = QVBoxLayout(products_tab)
        
        # Rejilla de productos
        products_grid = QGridLayout()
        
        # Aquí se agregarían dinámicamente los botones de productos
        # Simulemos algunos productos para el ejemplo
        product_names = ["Agua 500ml", "Refresco", "Pan", "Leche", "Huevos", 
                         "Café", "Azúcar", "Arroz", "Aceite", "Galletas",
                         "Jabón", "Papel", "Detergente", "Pasta", "Atún"]
        
        # Crear botones de productos
        row, col = 0, 0
        for i, name in enumerate(product_names):
            product_button = QPushButton(name)
            product_button.setMinimumSize(120, 100)
            product_button.setStyleSheet("font-size: 12pt;")
            product_button.clicked.connect(lambda checked, pid=i+1: self.product_selected.emit(pid))
            
            products_grid.addWidget(product_button, row, col)
            
            col += 1
            if col > 2:  # 3 columnas
                col = 0
                row += 1
        
        products_layout.addLayout(products_grid)
        tab_widget.addTab(products_tab, "Productos")
        
        # Pestaña de categorías
        categories_tab = QWidget()
        categories_layout = QVBoxLayout(categories_tab)
        
        # Botones de categorías
        categories_grid = QGridLayout()
        category_names = ["Bebidas", "Panadería", "Lácteos", "Abarrotes", "Limpieza"]
        
        row, col = 0, 0
        for i, name in enumerate(category_names):
            category_button = QPushButton(name)
            category_button.setMinimumSize(180, 100)
            category_button.setStyleSheet("font-size: 14pt;")
            
            categories_grid.addWidget(category_button, row, col)
            
            col += 1
            if col > 1:  # 2 columnas
                col = 0
                row += 1
        
        categories_layout.addLayout(categories_grid)
        tab_widget.addTab(categories_tab, "Categorías")
        
        # Añadir las pestañas al layout del catálogo
        catalog_layout.addWidget(tab_widget)
        
        # Agregar el panel del catálogo al splitter
        splitter.addWidget(catalog_widget)
        
        # Configurar proporciones iniciales del splitter
        splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        
        # Barra de estado
        self.statusBar().showMessage("Sistema listo")

    def _connect_signals(self):
        """Conectar señales internas"""
        self.checkout_button.clicked.connect(self._on_checkout_clicked)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
    
    def _setup_shortcuts(self):
        """Configurar atajos de teclado"""
        # F1 - Ayuda
        help_shortcut = QShortcut(QKeySequence("F1"), self)
        help_shortcut.activated.connect(self._show_help)
        
        # F2 - Buscar producto
        search_shortcut = QShortcut(QKeySequence("F2"), self)
        search_shortcut.activated.connect(lambda: self.barcode_input.setFocus())
        
        # F3 - Abrir caja
        drawer_shortcut = QShortcut(QKeySequence("F3"), self)
        drawer_shortcut.activated.connect(lambda: self.open_drawer_requested.emit())
        
        # F12 - Cobrar
        checkout_shortcut = QShortcut(QKeySequence("F12"), self)
        checkout_shortcut.activated.connect(self._on_checkout_clicked)
        
        # Escape - Cancelar venta
        cancel_shortcut = QShortcut(QKeySequence("Escape"), self)
        cancel_shortcut.activated.connect(self._on_cancel_clicked)
    
    @Slot()
    def _on_barcode_entered(self):
        """Manejar entrada de código de barras"""
        barcode = self.barcode_input.text().strip()
        if barcode:
            self.barcode_scanned.emit(barcode)
            self.barcode_input.clear()
    
    @Slot()
    def _on_checkout_clicked(self):
        """Iniciar proceso de cobro"""
        # Verificar si hay productos en el carrito
        if self.cart_table.rowCount() == 0:
            QMessageBox.warning(self, "Carrito vacío", "No hay productos en el carrito.")
            return
        
        # Mostrar diálogo de pago
        payment_dialog = PaymentDialog(self.subtotal_value.text(), 
                                      self.tax_value.text(), 
                                      self.total_value.text(), 
                                      parent=self)
        
        if payment_dialog.exec() == QDialog.Accepted:
            # Obtener datos del pago
            payment_data = payment_dialog.get_payment_data()
            
            # Recopilar información de la venta
            sale_data = {
                'items': self._get_cart_items(),
                'subtotal': self.subtotal_value.text(),
                'tax': self.tax_value.text(),
                'total': self.total_value.text(),
                'payment': payment_data
            }
            
            # Emitir señal de cobro
            self.checkout_requested.emit(sale_data)
    
    def _get_cart_items(self):
        """Obtener items del carrito"""
        items = []
        for row in range(self.cart_table.rowCount()):
            item = {
                'product_id': self.cart_table.item(row, 0).data(Qt.UserRole),
                'name': self.cart_table.item(row, 0).text(),
                'price': self.cart_table.item(row, 1).text(),
                'quantity': self.cart_table.item(row, 2).text(),
                'subtotal': self.cart_table.item(row, 3).text()
            }
            items.append(item)
        return items
    
    @Slot()
    def _on_cancel_clicked(self):
        """Cancelar la venta actual"""
        if self.cart_table.rowCount() > 0:
            confirm = QMessageBox.question(
                self, 
                "Cancelar venta", 
                "¿Está seguro de cancelar la venta actual?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                self.clear_cart()
    
    def clear_cart(self):
        """Limpiar el carrito"""
        self.cart_table.setRowCount(0)
        self.update_totals(0, 0, 0)
    
    def add_product_to_cart(self, product_data):
        """Añadir producto al carrito"""
        # Verificar si el producto ya está en el carrito
        for row in range(self.cart_table.rowCount()):
            if self.cart_table.item(row, 0).data(Qt.UserRole) == product_data['id']:
                # Actualizar cantidad
                quantity_item = self.cart_table.item(row, 2)
                current_quantity = int(quantity_item.text())
                new_quantity = current_quantity + 1
                quantity_item.setText(str(new_quantity))
                
                # Actualizar subtotal
                price = float(product_data['price'])
                subtotal = price * new_quantity
                self.cart_table.item(row, 3).setText(f"${subtotal:.2f}")
                
                self._update_cart_totals()
                return
        
        # Si no existe, agregar nueva fila
        row_position = self.cart_table.rowCount()
        self.cart_table.insertRow(row_position)
        
        # Producto
        product_item = QTableWidgetItem(product_data['name'])
        product_item.setData(Qt.UserRole, product_data['id'])
        self.cart_table.setItem(row_position, 0, product_item)
        
        # Precio
        price_item = QTableWidgetItem(f"${float(product_data['price']):.2f}")
        self.cart_table.setItem(row_position, 1, price_item)
        
        # Cantidad
        quantity_item = QTableWidgetItem("1")
        self.cart_table.setItem(row_position, 2, quantity_item)
        
        # Subtotal
        subtotal = float(product_data['price'])
        subtotal_item = QTableWidgetItem(f"${subtotal:.2f}")
        self.cart_table.setItem(row_position, 3, subtotal_item)
        
        # Botón eliminar
        remove_button = QPushButton("X")
        remove_button.setMaximumWidth(30)
        remove_button.clicked.connect(lambda: self._remove_cart_item(row_position))
        self.cart_table.setCellWidget(row_position, 4, remove_button)
        
        self._update_cart_totals()
    
    def _remove_cart_item(self, row):
        """Eliminar item del carrito"""
        self.cart_table.removeRow(row)
        self._update_cart_totals()
    
    def _update_cart_totals(self):
        """Actualizar totales del carrito"""
        subtotal = 0
        
        for row in range(self.cart_table.rowCount()):
            # Obtener el texto del subtotal y convertirlo a número
            subtotal_text = self.cart_table.item(row, 3).text()
            if subtotal_text.startswith('):
                subtotal_text = subtotal_text[1:]  # Quitar el símbolo $
            
            subtotal += float(subtotal_text)
        
        # Calcular impuestos (16% IVA)
        tax = subtotal * 0.16
        total = subtotal + tax
        
        # Actualizar las etiquetas
        self.update_totals(subtotal, tax, total)
    
    def update_totals(self, subtotal, tax, total):
        """Actualizar etiquetas de totales"""
        self.subtotal_value.setText(f"${subtotal:.2f}")
        self.tax_value.setText(f"${tax:.2f}")
        self.total_value.setText(f"${total:.2f}")
    
    def _show_help(self):
        """Mostrar ayuda rápida"""
        help_text = """
        <h3>Atajos de teclado:</h3>
        <ul>
            <li><b>F1</b> - Mostrar esta ayuda</li>
            <li><b>F2</b> - Buscar producto / Escanear código</li>
            <li><b>F3</b> - Abrir caja registradora</li>
            <li><b>F12</b> - Cobrar venta</li>
            <li><b>ESC</b> - Cancelar venta</li>
        </ul>
        """
        
        QMessageBox.information(self, "Ayuda rápida", help_text)


class PaymentDialog(QDialog):
    """Diálogo para procesar el pago"""
    
    def __init__(self, subtotal, tax, total, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Procesar pago")
        self.resize(400, 300)
        
        # Guardar valores
        self.subtotal = subtotal
        self.tax = tax
        self.total = total
        
        # Eliminar el símbolo $ y convertir a float
        self.total_value = float(total.replace(', ''))
        
        # Configurar la interfaz
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Información de la venta
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_layout = QGridLayout(info_frame)
        
        # Etiquetas y valores
        subtotal_label = QLabel("Subtotal:")
        subtotal_value = QLabel(self.subtotal)
        
        tax_label = QLabel("IVA:")
        tax_value = QLabel(self.tax)
        
        total_label = QLabel("TOTAL:")
        total_value = QLabel(self.total)
        total_value.setStyleSheet("font-size: 16pt; font-weight: bold;")
        
        # Colocar en el grid
        info_layout.addWidget(subtotal_label, 0, 0)
        info_layout.addWidget(subtotal_value, 0, 1)
        info_layout.addWidget(tax_label, 1, 0)
        info_layout.addWidget(tax_value, 1, 1)
        info_layout.addWidget(total_label, 2, 0)
        info_layout.addWidget(total_value, 2, 1)
        
        layout.addWidget(info_frame)
        
        # Método de pago
        payment_frame = QFrame()
        payment_layout = QVBoxLayout(payment_frame)
        
        payment_label = QLabel("Método de pago:")
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Efectivo", "Tarjeta", "Transferencia"])
        self.payment_method.currentIndexChanged.connect(self._on_payment_method_changed)
        
        payment_layout.addWidget(payment_label)
        payment_layout.addWidget(self.payment_method)
        
        # Campos para efectivo
        self.cash_frame = QFrame()
        cash_layout = QGridLayout(self.cash_frame)
        
        amount_label = QLabel("Monto recibido:")
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.textChanged.connect(self._calculate_change)
        
        change_label = QLabel("Cambio:")
        self.change_value = QLabel("$0.00")
        self.change_value.setStyleSheet("font-size: 14pt; font-weight: bold;")
        
        cash_layout.addWidget(amount_label, 0, 0)
        cash_layout.addWidget(self.amount_input, 0, 1)
        cash_layout.addWidget(change_label, 1, 0)
        cash_layout.addWidget(self.change_value, 1, 1)
        
        payment_layout.addWidget(self.cash_frame)
        
        # Campos para tarjeta (ocultos inicialmente)
        self.card_frame = QFrame()
        self.card_frame.setVisible(False)
        card_layout = QGridLayout(self.card_frame)
        
        card_number_label = QLabel("Últimos 4 dígitos:")
        self.card_number_input = QLineEdit()
        self.card_number_input.setMaxLength(4)
        self.card_number_input.setPlaceholderText("0000")
        
        auth_code_label = QLabel("Código de autorización:")
        self.auth_code_input = QLineEdit()
        
        card_layout.addWidget(card_number_label, 0, 0)
        card_layout.addWidget(self.card_number_input, 0, 1)
        card_layout.addWidget(auth_code_label, 1, 0)
        card_layout.addWidget(self.auth_code_input, 1, 1)
        
        payment_layout.addWidget(self.card_frame)
        
        # Campos para transferencia (ocultos inicialmente)
        self.transfer_frame = QFrame()
        self.transfer_frame.setVisible(False)
        transfer_layout = QGridLayout(self.transfer_frame)
        
        reference_label = QLabel("Referencia:")
        self.reference_input = QLineEdit()
        
        transfer_layout.addWidget(reference_label, 0, 0)
        transfer_layout.addWidget(self.reference_input, 0, 1)
        
        payment_layout.addWidget(self.transfer_frame)
        
        layout.addWidget(payment_frame)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        
        self.accept_button = QPushButton("Completar Venta")
        self.accept_button.setDefault(True)
        self.accept_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.accept_button)
        
        layout.addLayout(button_layout)
    
    def _on_payment_method_changed(self, index):
        """Cambiar los campos según el método de pago"""
        # Ocultar todos los frames
        self.cash_frame.setVisible(False)
        self.card_frame.setVisible(False)
        self.transfer_frame.setVisible(False)
        
        # Mostrar el frame correspondiente
        if index == 0:  # Efectivo
            self.cash_frame.setVisible(True)
        elif index == 1:  # Tarjeta
            self.card_frame.setVisible(True)
        elif index == 2:  # Transferencia
            self.transfer_frame.setVisible(True)
    
    def _calculate_change(self):
        """Calcular el cambio a devolver"""
        try:
            amount = float(self.amount_input.text())
            change = amount - self.total_value
            
            if change >= 0:
                self.change_value.setText(f"${change:.2f}")
                self.change_value.setStyleSheet("font-size: 14pt; font-weight: bold; color: black;")
            else:
                self.change_value.setText("Monto insuficiente")
                self.change_value.setStyleSheet("font-size: 14pt; font-weight: bold; color: red;")
        except ValueError:
            self.change_value.setText("$0.00")
    
    def get_payment_data(self):
        """Obtener los datos del pago"""
        method = self.payment_method.currentText()
        payment_data = {
            'method': method
        }
        
        if method == "Efectivo":
            payment_data['amount_received'] = self.amount_input.text()
            change_text = self.change_value.text()
            if change_text.startswith('):
                payment_data['change'] = change_text
            else:
                payment_data['change'] = "$0.00"
        
        elif method == "Tarjeta":
            payment_data['card_number'] = self.card_number_input.text()
            payment_data['auth_code'] = self.auth_code_input.text()
        
        elif method == "Transferencia":
            payment_data['reference'] = self.reference_input.text()
        
        return payment_data