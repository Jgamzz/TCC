CREATE TABLE IF NOT EXISTS preco_concorrente_planilha (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_arquivo VARCHAR(255) NOT NULL,
    nome_aba VARCHAR(100) NOT NULL,
    linha_excel INT NOT NULL,
    nome_produto VARCHAR(255) NOT NULL,
    valor DECIMAL(12, 2) NOT NULL,
    data_importacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_preco_planilha_origem
        UNIQUE (nome_arquivo, nome_aba, linha_excel),
    INDEX ix_preco_planilha_produto (nome_produto)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
