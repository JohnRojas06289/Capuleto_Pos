# app/models/user.py
import hashlib
from datetime import datetime

class User:
    """Modelo para usuarios del sistema"""
    
    def __init__(self, database):
        """
        Inicializar modelo con una conexión a la base de datos
        
        Args:
            database: Objeto de conexión a la base de datos
        """
        self.db = database
    
    def get_by_id(self, user_id):
        """
        Obtener usuario por ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con datos del usuario o None si no existe
        """
        query = """
            SELECT user_id, username, full_name, role, is_active, created_at, last_login
            FROM users
            WHERE user_id = ?
        """
        return self.db.fetch_one(query, [user_id])
    
    def get_by_username(self, username):
        """
        Obtener usuario por nombre de usuario
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Diccionario con datos del usuario o None si no existe
        """
        query = """
            SELECT user_id, username, full_name, role, is_active, created_at, last_login
            FROM users
            WHERE username = ?
        """
        return self.db.fetch_one(query, [username])
    
    def get_all(self, active_only=False):
        """
        Obtener todos los usuarios
        
        Args:
            active_only: Si es True, solo devuelve usuarios activos
            
        Returns:
            Lista de diccionarios con datos de usuarios
        """
        query = """
            SELECT user_id, username, full_name, role, is_active, created_at, last_login
            FROM users
        """
        
        if active_only:
            query += " WHERE is_active = 1"
            
        query += " ORDER BY username"
        
        return self.db.fetch_all(query)
    
    def create(self, username, password, full_name, role="cashier", is_active=True):
        """
        Crear un nuevo usuario
        
        Args:
            username: Nombre de usuario (único)
            password: Contraseña
            full_name: Nombre completo
            role: Rol del usuario (admin, cashier, etc.)
            is_active: Si el usuario está activo
            
        Returns:
            ID del usuario creado o None si hay error
        """
        # Verificar si el usuario ya existe
        if self.get_by_username(username):
            return None
            
        # Cifrar contraseña
        password_hash = self._hash_password(password)
        
        query = """
            INSERT INTO users (username, password, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?)
        """
        
        params = [username, password_hash, full_name, role, 1 if is_active else 0]
        
        return self.db.execute(query, params)
    
    def update(self, user_id, full_name=None, role=None, is_active=None):
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
        user = self.get_by_id(user_id)
        if not user:
            return False
            
        # Usar valores actuales si no se proporcionan nuevos
        full_name = full_name if full_name is not None else user['full_name']
        role = role if role is not None else user['role']
        is_active = is_active if is_active is not None else user['is_active']
        
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
            new_password: Nueva contraseña
            
        Returns:
            True si se cambió correctamente, False en caso contrario
        """
        password_hash = self._hash_password(new_password)
        
        query = """
            UPDATE users
            SET password = ?
            WHERE user_id = ?
        """
        
        params = [password_hash, user_id]
        
        return self.db.execute(query, params) > 0
    
    def verify_password(self, username, password):
        """
        Verificar si la contraseña es correcta para un usuario
        
        Args:
            username: Nombre de usuario
            password: Contraseña a verificar
            
        Returns:
            True si la contraseña es correcta, False en caso contrario
        """
        password_hash = self._hash_password(password)
        
        query = """
            SELECT COUNT(*) as count
            FROM users
            WHERE username = ? AND password = ?
        """
        
        params = [username, password_hash]
        
        result = self.db.fetch_one(query, params)
        
        return result and result['count'] > 0
    
    def authenticate(self, username, password):
        """
        Autenticar un usuario y actualizar su último inicio de sesión
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            Diccionario con datos del usuario si la autenticación es exitosa, None si falla
        """
        if not self.verify_password(username, password):
            return None
            
        # Obtener datos del usuario
        user = self.get_by_username(username)
        
        if user and user['is_active']:
            # Actualizar último inicio de sesión
            self._update_last_login(user['user_id'])
            return user
            
        return None
    
    def _update_last_login(self, user_id):
        """
        Actualizar la fecha del último inicio de sesión
        
        Args:
            user_id: ID del usuario
        """
        query = """
            UPDATE users
            SET last_login = ?
            WHERE user_id = ?
        """
        
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