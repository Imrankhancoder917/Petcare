import pymysql
from config import Config


def get_connection():
    """Return a new PyMySQL connection."""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def init_db():
    """Create tables if they do not exist yet."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('user','volunteer','admin') NOT NULL DEFAULT 'user',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    image VARCHAR(255),
                    lat DECIMAL(10,8),
                    lng DECIMAL(11,8),
                    status ENUM('OPEN','ASSIGNED','IN_PROGRESS','RESOLVED') NOT NULL DEFAULT 'OPEN',
                    urgency ENUM('HIGH','LOW') NOT NULL DEFAULT 'LOW',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    report_id INT NOT NULL,
                    volunteer_id INT NOT NULL,
                    status ENUM('ACTIVE','COMPLETED','CANCELLED') NOT NULL DEFAULT 'ACTIVE',
                    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
                    FOREIGN KEY (volunteer_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_report_volunteer (report_id, volunteer_id)
                )
            """)
        conn.commit()
    finally:
        conn.close()
