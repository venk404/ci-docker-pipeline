CREATE TABLE IF NOT EXISTS students (
    ID SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    age INTEGER,
    phone VARCHAR(50)
);