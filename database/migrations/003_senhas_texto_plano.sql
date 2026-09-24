ALTER TABLE Usuario
    MODIFY COLUMN Password VARCHAR(50) NOT NULL;

UPDATE Usuario
SET Password = CASE Username
    WHEN 'Kauã' THEN '9d8sAD!#4ds'
    WHEN 'Tanaka' THEN '487ds@RffCS'
    WHEN 'Bernardo' THEN '48da@EfsdX'
    ELSE Password
END
WHERE Username IN ('Kauã', 'Tanaka', 'Bernardo');
