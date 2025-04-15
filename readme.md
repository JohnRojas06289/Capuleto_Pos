# Sistema POS (Point of Sale)

Un sistema completo de punto de venta (POS) para negocios minoristas, con soporte para múltiples dispositivos, gestión de inventario, y múltiples usuarios. Diseñado específicamente para funcionar en entornos Linux con interfaces táctiles.

## Características

- **Interfaz táctil intuitiva**: Diseñada para facilitar la operación tanto con pantalla táctil como con teclado y mouse.
- **Gestión de usuarios**: Diferentes roles (administrador, cajero) con permisos específicos.
- **Integración de dispositivos**: 
  - Lector de códigos de barras S10-W
  - Impresora térmica WPRP-260 (58mm)
  - Caja de dinero SAT-119
- **Gestión de inventario**: Control de stock, alertas de inventario bajo, movimientos.
- **Ventas y cobros**: Múltiples métodos de pago (efectivo, tarjeta, transferencia).
- **Reportes**: Ventas diarias, movimientos de inventario, productos más vendidos.
- **Base de datos**: Sistema robusto basado en SQLite (escalable a PostgreSQL).
- **Liviano pero potente**: Optimizado para equipos con recursos limitados.

## Requisitos del sistema

- Sistema operativo Linux
- Python 3.7 o superior
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/ejemplo/pos_system.git
   cd pos_system
   ```

2. Instalar las dependencias:
   ```
   pip install -r requirements.txt
   ```

3. Instalar el paquete (opcional):
   ```
   pip install -e .
   ```

4. Configurar los dispositivos en `config/device_config.json`

## Ejecución

Para iniciar el sistema POS:

```
python -m app.main
```

O si instalaste el paquete:

```
pos_system
```

## Credenciales por defecto

- **Administrador**: 
  - Usuario: admin
  - Contraseña: admin

- **Cajero**:
  - Usuario: cajero
  - Contraseña: cajero

## Estructura del proyecto

```
pos_system/
├── app/                        # Código principal de la aplicación
│   ├── controllers/            # Lógica de negocio
│   ├── models/                 # Modelos de datos
│   ├── views/                  # Interfaces de usuario
│   ├── devices/                # Integración de hardware
│   └── utils/                  # Utilidades comunes
├── resources/                  # Recursos estáticos
├── database/                   # Directorio para la base de datos
├── logs/                       # Registros del sistema
├── config/                     # Archivos de configuración
├── tests/                      # Pruebas automatizadas
├── requirements.txt            # Dependencias del proyecto
├── setup.py                    # Script de instalación
└── README.md                   # Esta documentación
```

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, envíe un pull request o abra un issue para discutir los cambios propuestos.