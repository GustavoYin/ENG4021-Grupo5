-- Baseado em "App Saúde/modelagemDados.txt" (domínios de identidade, evolução e nutrição).
-- Campos marcados com [+] não estão na modelagem original, mas as telas de
-- login/cadastro/perfil precisam deles.

CREATE TABLE IF NOT EXISTS usuarios (
    id               TEXT PRIMARY KEY,                -- UUID
    nome_completo    TEXT NOT NULL,
    email            TEXT NOT NULL UNIQUE,            -- [+] login
    cpf              TEXT NOT NULL UNIQUE,            -- [+] login (só dígitos)
    celular          TEXT NOT NULL,                   -- [+]
    senha_hash       TEXT NOT NULL,                   -- [+] nunca guardar senha pura
    apelido          TEXT,                            -- [+] aparece no ranking
    data_nascimento  TEXT,                            -- YYYY-MM-DD (idade é calculada)
    sexo_biologico   TEXT CHECK (sexo_biologico IN ('masculino','feminino')),
    altura_cm        INTEGER,
    peso_meta_kg     REAL,                            -- [+] "peso desejado" (opcional)
    biotipo          TEXT CHECK (biotipo IN ('ectomorfo','mesomorfo','endomorfo')),
    objetivo         TEXT CHECK (objetivo IN ('emagrecimento','manutencao','hipertrofia','saude')),
    avatar_url       TEXT,
    data_cadastro    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS historico_medidas (
    id                TEXT PRIMARY KEY,
    usuario_id        TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    data_registro     TEXT NOT NULL DEFAULT (datetime('now')),   -- eixo X do gráfico
    peso_kg           REAL NOT NULL,                              -- eixo Y do gráfico
    objetivo_momento  TEXT,
    foto_shape_url    TEXT
);

CREATE TABLE IF NOT EXISTS metas_nutricionais (
    id               TEXT PRIMARY KEY,
    usuario_id       TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    data_inicio      TEXT NOT NULL,
    meta_agua_ml     INTEGER NOT NULL,
    meta_calorias    INTEGER NOT NULL,
    meta_proteina_g  REAL NOT NULL,
    meta_carbo_g     REAL NOT NULL,
    meta_gordura_g   REAL NOT NULL
);

-- [+] Esportes do passo 3 do perfil (não existe na modelagem original)
CREATE TABLE IF NOT EXISTS esportes_usuario (
    id           TEXT PRIMARY KEY,
    usuario_id   TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    esporte      TEXT NOT NULL,
    frequencia   TEXT NOT NULL,      -- '1x'..'6x' ou 'Diário'
    intensidade  TEXT NOT NULL,      -- leve | moderada | intensa | máxima
    UNIQUE (usuario_id, esporte)
);
