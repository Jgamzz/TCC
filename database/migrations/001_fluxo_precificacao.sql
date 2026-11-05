CREATE TABLE IF NOT EXISTS log_sistema (
    id_log BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nivel VARCHAR(20) NOT NULL,
    mensagem TEXT NOT NULL,
    modulo VARCHAR(255),
    metodo VARCHAR(10),
    rota VARCHAR(255),
    usuario_id INT NULL,
    stack_trace LONGTEXT NULL,
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_log_sistema_data (data_criacao),
    INDEX ix_log_sistema_nivel (nivel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE Usuario MODIFY Password VARCHAR(255) NOT NULL;

CREATE TABLE IF NOT EXISTS feedback_cliente (
    id_feedback BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_produto BIGINT UNSIGNED NOT NULL,
    cliente VARCHAR(120),
    comentario TEXT NOT NULL,
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_feedback_produto
        FOREIGN KEY (id_produto) REFERENCES produto (id_produto)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sugestao_preco (
    id_sugestao BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_produto BIGINT UNSIGNED NOT NULL,
    id_solicitante INT NULL,
    id_aprovador INT NULL,
    preco_atual DECIMAL(12, 2) NOT NULL,
    preco_sugerido DECIMAL(12, 2) NOT NULL,
    giro_30_dias DECIMAL(12, 3) NOT NULL DEFAULT 0,
    preco_concorrente DECIMAL(12, 2) NULL,
    motivo TEXT NOT NULL,
    origem VARCHAR(30) NOT NULL DEFAULT 'MOTOR',
    feedback_cliente TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDENTE',
    observacao_aprovacao TEXT NULL,
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_decisao DATETIME NULL,
    CONSTRAINT fk_sugestao_produto
        FOREIGN KEY (id_produto) REFERENCES produto (id_produto),
    CONSTRAINT fk_sugestao_solicitante
        FOREIGN KEY (id_solicitante) REFERENCES Usuario (ID),
    CONSTRAINT fk_sugestao_aprovador
        FOREIGN KEY (id_aprovador) REFERENCES Usuario (ID),
    INDEX ix_sugestao_status (status),
    INDEX ix_sugestao_produto (id_produto)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
