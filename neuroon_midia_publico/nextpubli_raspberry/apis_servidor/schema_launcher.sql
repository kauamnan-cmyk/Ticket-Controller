CREATE TABLE IF NOT EXISTS raspberry_releases (
  id_release INT AUTO_INCREMENT PRIMARY KEY,
  version VARCHAR(50) NOT NULL UNIQUE,
  package_path VARCHAR(255) NOT NULL,
  package_sha256 CHAR(64) NOT NULL,
  entrypoint VARCHAR(120) NOT NULL DEFAULT 'main.py',
  status ENUM('draft', 'published', 'disabled') NOT NULL DEFAULT 'draft',
  is_active TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  published_at DATETIME NULL,
  INDEX idx_raspberry_releases_active (status, is_active, published_at)
);

CREATE TABLE IF NOT EXISTS raspberry_release_scripts (
  id_script INT AUTO_INCREMENT PRIMARY KEY,
  id_release INT NOT NULL,
  execution_order INT NOT NULL,
  name VARCHAR(120) NOT NULL,
  script_path VARCHAR(255) NOT NULL,
  script_sha256 CHAR(64) NOT NULL,
  run_as ENUM('user', 'sudo') NOT NULL DEFAULT 'user',
  is_enabled TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_raspberry_release_scripts_release (id_release, is_enabled, execution_order),
  CONSTRAINT fk_raspberry_release_scripts_release
    FOREIGN KEY (id_release) REFERENCES raspberry_releases(id_release)
);

