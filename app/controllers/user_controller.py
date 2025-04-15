# app/controllers/user_controller.py
import hashlib
from datetime import datetime

class UserController:
    """Controlador para la gestión de usuarios"""
    
    def __init__(self, database):
        """Inicializar controlador con una conexión a la base de datos"""
        self.db = database
    
    def authenticate(self, username, password):
        """
        Autenticar un usuario
        
        Args:
            username: Nombre de usuario
            password: Contraseña (en texto claro)
            
        Returns:
            Datos del usuario si la autenticación es exitosa, None si falla
        """
        # Encriptar la contraseña para compararla con la almacenada
        password_hash = self._hash_password(password)
        
        query = """
            SELECT user_id, username, full_name, role, is_active
            FROM users
            WHERE username = ? AND password = ? AND is_active = 1
        """
        
        params = [username, password_hash]
        
        user = self.db.fetch_one(query, params)
        
        if user:
            # Actualizar último inicio de sesión
            self._update_last_login(user['user_id'])
            return user
        
        return None
    
    def _update_last_login(self, user_id):
        """Actualizar fecha de último inicio de sesión"""
        query = "UPDATE users SET last_login = ? WHERE user_id = ?"
        params = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id]
        
        self.db.execute(query, params)
    
    def _hash_password(self, password):
        """
        Generar hash SHA-256 para una contraseña
        
        Args:
            password: Contraseña en texto claro
            
        Returns:
            Hash SHA-256 de la contraseña
        """
        if not password:
            return None
        
        # Convertir a bytes si es un string
        if isinstance(password, str):
            password = password.encode('utf-8')
        
        # Generar hash SHA-256
        return hashlib.sha256(password).hexdigest()
    
    def get_all_users(self):
        """Obtener todos los usuarios"""
        query = """
            SELECT user_id, username, full_name, role, is_active, created_at, last_login
            FROM users
            ORDER BY username
        """
        
        return self.db.fetch_all(query)
    
    def get_user_by_id(self, user_id):
        """Obtener usuario por ID"""
        query = """
            SELECT user_id, username, full_name, role, is_active, created_at, last_login
            FROM users
            WHERE user_id = ?
        """
        
        params = [user_id]
        
        return self.db.fetch_one(query, params)
    
    def get_user_by_username(self, username):
        """Obtener usuario por nombre de usuario"""
        query = """
            SELECT user_id, username, full_name, role, is_active, created_at, last_login
            FROM users
            WHERE username = ?
        """
        
        params = [username]
        
        return self.db.fetch_one(query, params)
    
    def create_user(self, username, password, full_name, role='cashier', is_active=True):
        """
        Crear un nuevo usuario
        
        Args:
            username: Nombre de usuario (único)
            password: Contraseña (en texto claro)
            full_name: Nombre completo
            role: Rol del usuario ('admin', 'cashier', etc.)
            is_active: Estado del usuario
            
        Returns:
            ID del usuario creado o None si hay error
        """
        # Verificar si el usuario ya existe
        existing = self.get_user_by_username(username)
        if existing:
            return None
        
        # Encriptar contraseña
        password_hash = self._hash_password(password)
        
        query = """
            INSERT INTO users (username, password, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?)
        """
        
        params = [username, password_hash, full_name, role, 1 if is_active else 0]
        
        return self.db.execute(query, params)
    
    def update_user(self, user_id, full_name=None, role=None, is_active=None):
        """
        Actualizar datos de un usuario (sin cambiar contraseña)
        
        Args:
            user_id: ID del usuario
            full_name: Nuevo nombre completo (opcional)
            role: Nuevo rol (opcional)
            is_active: Nuevo estado (opcional)
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        # Obtener datos actuales
        current = self.get_user_by_id(user_id)
        if not current:
            return False
        
        # Usar valores actuales si no se proporcionan nuevos
        full_name = full_name if full_name is not None else current['full_name']
        role = role if role is not None else current['role']
        is_active = is_active if is_active is not None else current['is_active']
        
        query = """
            UPDATE users
            SET full_name = ?, role = ?, is_active = ?
            WHERE user_id = ?
        """
        
        params = [full_name, role, 1 if is_active else 0, user_id]
        
        return self.db.execute(query, params) > 0
    
    def change_password(self, user_id, new_password):
        """
        Cambiar contraseña de un usuario
        
        Args:
            user_id: ID del usuario
            new_password: Nueva contraseña (en texto claro)
            
        Returns:
            True si se cambió correctamente, False en caso contrario
        """
        # Encriptar nueva contraseña
        password_hash = self._hash_password(new_password)
        
        query = "UPDATE users SET password = ? WHERE user_id = ?"
        params = [password_hash, user_id]
        
        return self.db.execute(query, params) > 0
    
    def disable_user(self, user_id):
        """
        Desactivar un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se desactivó correctamente, False en caso contrario
        """
        return self.update_user(user_id, is_active=False)
    
    def enable_user(self, user_id):
        """
        Activar un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se activó correctamente, False en caso contrario
        """
        return self.update_user(user_id, is_active=True)
    
    def verify_current_password(self, user_id, current_password):
        """
        Verificar si la contraseña actual es correcta
        
        Args:
            user_id: ID del usuario
            current_password: Contraseña actual (en texto claro)
            
        Returns:
            True si la contraseña es correcta, False en caso contrario
        """
        # Encriptar contraseña para comparar
        password_hash = self._hash_password(current_password)
        
        query = "SELECT COUNT(*) as count FROM users WHERE user_id = ? AND password = ?"
        params = [user_id, password_hash]
        
        result = self.db.fetch_one(query, params)
        
        return result and result['count'] > 0