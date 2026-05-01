-- ElectaVerse — Users table migration
USE electaverse;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('voter','official','observer') DEFAULT 'voter',
    constituency_id VARCHAR(10) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME NULL,
    FOREIGN KEY (constituency_id) REFERENCES constituencies(id) ON DELETE SET NULL
);
