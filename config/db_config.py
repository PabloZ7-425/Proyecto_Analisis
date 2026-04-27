# Configuración de la base de datos
# Por ahora solo placeholder, sin conexión real

class DatabaseConfig:
    """Configuración de la base de datos"""

    # Datos de conexión (para cuando se implemente)
    DB_CONFIG = {
        'host': 'db.tlrershlxqyelcxcqgjc.supabase.co',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'Techshopgt4321.'
    }

    @staticmethod
    def get_connection_string():
        """Retorna el string de conexión"""
        config = DatabaseConfig.DB_CONFIG
        return f"host={config['host']} port={config['port']} dbname={config['database']} user={config['user']} password={config['password']}"