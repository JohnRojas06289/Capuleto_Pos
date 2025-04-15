# app/utils/helpers.py
import os
import re
import csv
import json
import random
import string
import hashlib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('pos.utils')

def format_currency(amount, symbol='$'):
    """
    Formatear un valor como moneda
    
    Args:
        amount: Cantidad a formatear
        symbol: Símbolo de moneda
        
    Returns:
        True si coincide, False en caso contrario
    """
    if not password or not password_hash:
        return False
        
    # Generar hash de la contraseña a verificar
    check_hash = hash_password(password)
    
    # Comparar los hashes
    return check_hash == password_hash

def truncate_text(text, max_length=50, suffix='...'):
    """
    Truncar un texto si excede una longitud máxima
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima permitida
        suffix: Sufijo a agregar si se trunca
        
    Returns:
        Texto truncado
    """
    if not text:
        return ''
        
    if len(text) <= max_length:
        return text
        
    return text[:max_length - len(suffix)] + suffix

def get_app_version():
    """
    Obtener la versión de la aplicación
    
    Returns:
        String con la versión
    """
    try:
        # Intentar leer desde el módulo principal
        from app import __version__
        return __version__
    except ImportError:
        # Valor por defecto
        return '1.0.0'

def bytes_to_human_readable(size_bytes):
    """
    Convertir bytes a formato legible para humanos
    
    Args:
        size_bytes: Tamaño en bytes
        
    Returns:
        String con formato legible (KB, MB, GB, etc.)
    """
    if size_bytes <= 0:
        return "0B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f}{units[i]}"

def sanitize_filename(filename):
    """
    Sanear un nombre de archivo quitando caracteres no permitidos
    
    Args:
        filename: Nombre de archivo original
        
    Returns:
        Nombre de archivo saneado
    """
    # Eliminar caracteres no permitidos
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Reemplazar espacios por guiones bajos
    sanitized = sanitized.replace(' ', '_')
    # Asegurarse de que no sea demasiado largo
    if len(sanitized) > 255:
        sanitized = sanitized[:250] + '...'
    return sanitized

def is_valid_path(path):
    """
    Verificar si una ruta es válida
    
    Args:
        path: Ruta a verificar
        
    Returns:
        True si es válida, False en caso contrario
    """
    try:
        # Verificar si la ruta es absoluta
        is_absolute = os.path.isabs(path)
        
        # Verificar si el directorio padre existe
        parent = os.path.dirname(path)
        parent_exists = os.path.exists(parent) if parent else True
        
        # Verificar si tiene caracteres válidos
        is_valid_chars = os.path.normpath(path) == path
        
        return is_absolute and parent_exists and is_valid_chars
    except:
        return False

def generate_random_password(length=8):
    """
    Generar una contraseña aleatoria
    
    Args:
        length: Longitud de la contraseña
        
    Returns:
        Contraseña generada
    """
    # Asegurar que tenga al menos un carácter de cada tipo
    lowercase = random.choice(string.ascii_lowercase)
    uppercase = random.choice(string.ascii_uppercase)
    digit = random.choice(string.digits)
    special = random.choice('!@#$%&*+-')
    
    # Generar el resto de caracteres aleatorios
    remaining_length = length - 4
    all_chars = string.ascii_letters + string.digits + '!@#$%&*+-'
    remaining = ''.join(random.choice(all_chars) for _ in range(remaining_length))
    
    # Combinar todos los caracteres y mezclarlos
    password = lowercase + uppercase + digit + special + remaining
    password_list = list(password)
    random.shuffle(password_list)
    
    return ''.join(password_list)
        String con el valor formateado como moneda
    """
    try:
        return f"{symbol}{float(amount):.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"

def parse_currency(currency_str):
    """
    Convertir una cadena de moneda a float
    
    Args:
        currency_str: String con formato de moneda (por ejemplo: "$123.45")
        
    Returns:
        Valor numérico (float)
    """
    try:
        # Eliminar símbolo de moneda y otros caracteres no numéricos excepto punto y signo
        clean_str = re.sub(r'[^\d.-]', '', currency_str)
        return float(clean_str)
    except (ValueError, TypeError):
        return 0.0

def generate_receipt_number():
    """
    Generar un número de recibo único
    
    Returns:
        Número de recibo (string)
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{timestamp}-{random_chars}"

def calculate_tax(amount, tax_rate=0.16):
    """
    Calcular impuesto sobre un monto
    
    Args:
        amount: Monto base
        tax_rate: Tasa de impuesto (por defecto 16%)
        
    Returns:
        Monto del impuesto
    """
    try:
        return float(amount) * tax_rate
    except (ValueError, TypeError):
        return 0.0

def format_date(date_obj=None, format_str="%Y-%m-%d"):
    """
    Formatear una fecha
    
    Args:
        date_obj: Objeto datetime (por defecto fecha actual)
        format_str: Formato de salida
        
    Returns:
        String con la fecha formateada
    """
    if not date_obj:
        date_obj = datetime.now()
    return date_obj.strftime(format_str)

def parse_date(date_str, format_str="%Y-%m-%d"):
    """
    Convertir una cadena de fecha a objeto datetime
    
    Args:
        date_str: String con la fecha
        format_str: Formato de la fecha
        
    Returns:
        Objeto datetime o None si hay error
    """
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        return None

def date_range(start_date, end_date):
    """
    Generar un rango de fechas
    
    Args:
        start_date: Fecha de inicio (objeto datetime)
        end_date: Fecha de fin (objeto datetime)
        
    Returns:
        Lista de objetos datetime
    """
    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]

def export_to_csv(data, filepath, headers=None):
    """
    Exportar datos a un archivo CSV
    
    Args:
        data: Lista de diccionarios o lista de listas
        filepath: Ruta del archivo a crear
        headers: Lista de encabezados (opcional)
        
    Returns:
        True si se exportó correctamente, False en caso contrario
    """
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if headers:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data) if isinstance(data[0], dict) else None
            else:
                writer = csv.writer(csvfile)
                if isinstance(data[0], dict):
                    # Si son diccionarios y no hay headers, usar las claves del primer dict
                    headers = data[0].keys()
                    writer.writerow(headers)
                    for row in data:
                        writer.writerow([row.get(key, '') for key in headers])
                else:
                    writer.writerows(data)
        return True
    except Exception as e:
        logger.error(f"Error al exportar a CSV: {e}")
        return False

def export_to_json(data, filepath, pretty=True):
    """
    Exportar datos a un archivo JSON
    
    Args:
        data: Datos a exportar (debe ser serializable a JSON)
        filepath: Ruta del archivo a crear
        pretty: Si es True, formatea el JSON con indentación
        
    Returns:
        True si se exportó correctamente, False en caso contrario
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            indent = 4 if pretty else None
            json.dump(data, jsonfile, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Error al exportar a JSON: {e}")
        return False

def create_backup(db_path, backup_dir=None):
    """
    Crear una copia de seguridad de la base de datos
    
    Args:
        db_path: Ruta del archivo de base de datos
        backup_dir: Directorio para guardar la copia (opcional)
        
    Returns:
        Ruta del archivo de copia o None si hay error
    """
    try:
        if not os.path.exists(db_path):
            logger.error(f"No se encontró la base de datos: {db_path}")
            return None
            
        # Si no se especifica directorio, usar uno por defecto
        if not backup_dir:
            backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
            
        # Crear directorio si no existe
        os.makedirs(backup_dir, exist_ok=True)
        
        # Nombre del archivo de backup con fecha y hora
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = os.path.basename(db_path)
        backup_filename = f"{os.path.splitext(db_name)[0]}_{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copiar archivo
        import shutil
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"Copia de seguridad creada: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Error al crear copia de seguridad: {e}")
        return None

def validate_barcode(barcode):
    """
    Validar si un código de barras tiene formato válido
    
    Args:
        barcode: Código de barras a validar
        
    Returns:
        True si es válido, False en caso contrario
    """
    # EAN-13 (13 dígitos)
    if re.match(r'^\d{13}$', barcode):
        return True
        
    # UPC-A (12 dígitos)
    if re.match(r'^\d{12}$', barcode):
        return True
        
    # EAN-8 (8 dígitos)
    if re.match(r'^\d{8}$', barcode):
        return True
        
    # CODE-39 (variable, caracteres válidos)
    if re.match(r'^[A-Z0-9\-\.\$\/\+\%\s]{4,48}$', barcode):
        return True
        
    # Formatos personalizados (admitir alfanuméricos y algunos símbolos)
    if re.match(r'^[A-Za-z0-9\-\.\_]{4,32}$', barcode):
        return True
        
    return False

def generate_random_barcode(format='EAN13'):
    """
    Generar un código de barras aleatorio
    
    Args:
        format: Formato del código ('EAN13', 'UPC', 'EAN8', 'CODE39')
        
    Returns:
        Código de barras generado
    """
    if format == 'EAN13':
        # 12 dígitos aleatorios (el 13º es checksum)
        digits = [str(random.randint(0, 9)) for _ in range(12)]
        return ''.join(digits)
        
    elif format == 'UPC':
        # 11 dígitos aleatorios (el 12º es checksum)
        digits = [str(random.randint(0, 9)) for _ in range(11)]
        return ''.join(digits)
        
    elif format == 'EAN8':
        # 7 dígitos aleatorios (el 8º es checksum)
        digits = [str(random.randint(0, 9)) for _ in range(7)]
        return ''.join(digits)
        
    elif format == 'CODE39':
        # Caracteres válidos para CODE39
        chars = string.ascii_uppercase + string.digits + '-. $/+%'
        length = random.randint(6, 12)
        return ''.join(random.choice(chars) for _ in range(length))
        
    else:
        # Formato personalizado (alfanumérico)
        chars = string.ascii_uppercase + string.digits
        length = random.randint(8, 16)
        return ''.join(random.choice(chars) for _ in range(length))

def hash_password(password):
    """
    Generar hash SHA-256 para una contraseña
    
    Args:
        password: Contraseña en texto claro
        
    Returns:
        Hash SHA-256 de la contraseña
    """
    if not password:
        return None
        
    # Convertir a bytes si es string
    if isinstance(password, str):
        password = password.encode('utf-8')
        
    # Generar hash SHA-256
    return hashlib.sha256(password).hexdigest()

def verify_password(password, password_hash):
    """
    Verificar si una contraseña coincide con un hash
    
    Args:
        password: Contraseña en texto claro
        password_hash: Hash de la contraseña
        
    Returns