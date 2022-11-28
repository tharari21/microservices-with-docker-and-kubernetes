CREATE USER 'auth_user'@'localhost' IDENTIFIED BY 'auth123'; -- Create "admin" user of our app
CREATE DATABASE auth;
GRANT ALL PRIVILEGES ON auth.* TO 'auth_user'@'localhost';
USE auth;
CREATE TABLE USER (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

INSERT INTO user (email, password) VALUES ('tharari21@gmail.com', 'admin123');