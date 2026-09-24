UPDATE Cargo
SET Name = CASE ID
    WHEN 1 THEN 'Admin'
    WHEN 2 THEN 'Gerente'
    WHEN 3 THEN 'Usuário'
    ELSE Name
END
WHERE ID IN (1, 2, 3);

UPDATE Usuario
SET Cargo_ID = CASE ID
    WHEN 1 THEN 3
    WHEN 2 THEN 2
    WHEN 3 THEN 1
    ELSE Cargo_ID
END,
Password = CASE
    WHEN ID IN (1, 2, 3) THEN 'Senha123'
    ELSE Password
END
WHERE ID IN (1, 2, 3);
