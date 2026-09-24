INSERT INTO Cargo (ID, Name, Is_Active)
SELECT 1, 'Admin', TRUE
WHERE NOT EXISTS (
    SELECT 1
    FROM Cargo
    WHERE ID = 1 OR UPPER(Name) = 'USUARIO'
);

INSERT INTO Cargo (ID, Name, Is_Active)
SELECT 2, 'Gerente', TRUE
WHERE NOT EXISTS (
    SELECT 1
    FROM Cargo
    WHERE ID = 2 OR UPPER(Name) = 'GERENTE'
);

INSERT INTO Cargo (ID, Name, Is_Active)
SELECT 3, 'Usuário', TRUE
WHERE NOT EXISTS (
    SELECT 1
    FROM Cargo
    WHERE ID = 3 OR UPPER(Name) = 'ADMIN'
);

INSERT INTO Usuario (ID, Name, Username, Password, Is_Active, Cargo_ID)
SELECT 1, 'Kauã', 'Kauã', 'Senha123', TRUE, 3
WHERE NOT EXISTS (
    SELECT 1
    FROM Usuario
    WHERE ID = 1 OR Username = 'Kauã'
);

INSERT INTO Usuario (ID, Name, Username, Password, Is_Active, Cargo_ID)
SELECT 2, 'Tanaka', 'Tanaka', 'Senha123', TRUE, 2
WHERE NOT EXISTS (
    SELECT 1
    FROM Usuario
    WHERE ID = 2 OR Username = 'Tanaka'
);

INSERT INTO Usuario (ID, Name, Username, Password, Is_Active, Cargo_ID)
SELECT 3, 'Bernardo', 'Bernardo', 'Senha123', TRUE, 1
WHERE NOT EXISTS (
    SELECT 1
    FROM Usuario
    WHERE ID = 3 OR Username = 'Bernardo'
);

UPDATE Usuario
SET Cargo_ID = 3
WHERE (ID = 1 OR Username = 'Kauã') AND Cargo_ID IS NULL;

UPDATE Usuario
SET Cargo_ID = 2
WHERE (ID = 2 OR Username = 'Tanaka')
  AND Cargo_ID IS NULL;

UPDATE Usuario
SET Cargo_ID = 1
WHERE (ID = 3 OR Username = 'Bernardo')
  AND Cargo_ID IS NULL;
