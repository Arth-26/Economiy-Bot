create table if not exists usuarios(
	id SERIAL primary key,
	nome varchar(100),
	sobrenome varchar(100),
	telefone varchar(12) not null,
	limite decimal(12,2)
);

create table if not exists extratos(
	id SERIAL primary key,
	usuario_id integer not null,
	mes integer not null,
	ano integer not null
);

create table if not exists entradas(
	id SERIAL primary key,
	extrato_id integer not null,
	produto varchar(100),
	categoria varchar(150),
	tipo varchar(30),
	data date not null,
	valor decimal(12,2) not null,
	tipo_pagamento varchar(255),
	descricao varchar(255)
);

DO $$
BEGIN
	IF NOT EXISTS (
		SELECT 1 FROM information_schema.table_constraints
		WHERE constraint_name = 'fk_extratos_usuario'
	) THEN
		ALTER TABLE extratos ADD CONSTRAINT fk_extratos_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id);
	END IF;

	IF NOT EXISTS (
		SELECT 1 FROM information_schema.table_constraints
		WHERE constraint_name = 'fk_entradas_extrato'
	) THEN
		ALTER TABLE entradas ADD CONSTRAINT fk_entradas_extrato FOREIGN KEY (extrato_id) REFERENCES extratos(id);
	END IF;
END$$;

