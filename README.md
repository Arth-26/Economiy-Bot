# Economiy-Bot
Um chatbot para WhatsApp desenvolvido para auxiliar usuários no controle de suas despesas e finanças.

## Visão Geral

O Economiy-Bot é um assistente financeiro que interage com os usuários via WhatsApp. Ele utiliza Processamento de Linguagem Natural (PLN) para entender as mensagens dos usuários, permitindo que eles registrem transações financeiras (receitas e despesas) e consultem seu histórico financeiro de forma conversacional. O bot é projetado para ser implantado usando Docker e se integra com o WAHA (WhatsApp HTTP API) para as funcionalidades de mensagens.

## Funcionalidades

* **Cadastro de Usuário**: Novos usuários podem se cadastrar no bot para começar a rastrear suas finanças. O processo de cadastro envolve o fornecimento de nome, sobrenome e um limite de gastos mensal através de um formulário do WhatsForm.
* **Registro de Transações**: Usuários podem reportar despesas e receitas através de mensagens em linguagem natural (ex: "Gastei 50 reais no mercado"). O bot analisa essas mensagens para extrair detalhes como produto, descrição, valor, tipo (despesa/receita), categoria, forma de pagamento e data.
* **Consultas Financeiras**: Usuários podem fazer perguntas sobre seus dados financeiros, como "Quanto gastei este mês?" ou "Me mostre meu extrato da semana passada."
* **Interação via PLN**: Utiliza um Modelo de Linguagem Grande (Llama 3.3 70B via Groq) para entender a intenção do usuário e extrair informações relevantes das mensagens.
* **Busca Vetorial para Consultas**: Emprega FAISS e embeddings de `sentence-transformers` para corresponder as perguntas dos usuários com instruções SQL predefinidas, otimizando a recuperação de dados.
* **Integração com WhatsApp**: Conecta-se ao WhatsApp usando o WAHA (WhatsApp HTTP API) para enviar e receber mensagens.
* **Persistência de Dados**: Armazena dados de usuários, extratos financeiros e lançamentos de transações em um banco de dados PostgreSQL.

## Tecnologias Utilizadas

* **Backend**: Python
* **API WhatsApp**: WAHA (WhatsApp HTTP API)
* **PLN**: Llama (via Groq), Langchain
* **Busca Vetorial**: FAISS, HuggingFace Embeddings (`sentence-transformers/all-MiniLM-L6-v2`)
* **Banco de Dados**: PostgreSQL
* **Conteinerização**: Docker, Docker Compose

## Arquitetura

O sistema é composto por três componentes principais orquestrados pelo Docker Compose:

* **API (Aplicação Flask)**: Localizada no diretório `code/`, esta aplicação Python recebe mensagens do WhatsApp através de um webhook configurado no WAHA. Ela processa as mensagens utilizando PLN (com `LlamaClass`), interage com o banco de dados PostgreSQL (via `DataBase` e modelos em `models/`) e envia respostas de volta através do WAHA (usando `WahaBot`).
* **WAHA (WhatsApp HTTP API)**: Atua como um gateway para o WhatsApp, responsável por enviar e receber mensagens. A configuração do webhook é feita pela `WahaBot` para apontar para a API Flask.
* **Banco de Dados PostgreSQL (`db`)**: Armazena informações dos usuários, extratos mensais e lançamentos financeiros individuais. O schema é inicializado pelo script `data/db/init.sql`.

## Configuração e Instalação

1.  Clone o repositório.
2.  Crie um arquivo `.env` na raiz do projeto. Você precisará configurar as seguintes variáveis de ambiente (verifique `docker-compose.yml` e os scripts em `code/services/` para referências):
    ```env
    POSTGRES_HOST=db
    POSTGRES_DATABASE=nome_do_seu_banco
    POSTGRES_USER=seu_usuario_pg
    POSTGRES_PASSWORD=sua_senha_pg
    GROQ_API_KEY=sua_chave_api_groq
    MY_CHAT_ID=seu_chat_id_whatsapp # Ex: 5511XXXXXXXX@c.us (usado em WahaBot)
    ```
3.  No terminal, na raiz do projeto, execute o comando para construir e iniciar os contêineres:
    ```bash
    docker-compose up --build
    ```
4.  Após a inicialização:
    * A API Flask estará disponível em `http://localhost:5000`.
    * O WAHA estará acessível em `http://localhost:3000`.
    * O script `app.py` tentará configurar automaticamente o webhook no WAHA para `http://api:5000/economy_bot/webhook/`, que é o endereço da API dentro da rede Docker.

## Como Funciona

1.  O usuário envia uma mensagem para o número do WhatsApp conectado ao WAHA.
2.  O WAHA encaminha a mensagem para o endpoint `/economy_bot/webhook/` da API Flask.
3.  A API (`app.py`) recebe a mensagem. Primeiramente, verifica se o usuário (identificado pelo `chat_id`) já está cadastrado no sistema utilizando `Usuarios().verificar_usuario(numero_telefone)`.
4.  **Se o usuário não estiver cadastrado**:
    * A `BotClass().define_proxima_mensagem()` guia o usuário através de um fluxo de conversa para o cadastro.
    * O usuário é instruído a preencher um formulário externo (`https://whatsform.com/uucley`).
    * Após o preenchimento, a resposta do formulário (que contém "Cadastro Economy Bot") é enviada de volta para o webhook, e `Usuarios().cadastrar_usuario()` processa esses dados para criar o novo usuário.
5.  **Se o usuário estiver cadastrado**:
    * A `LlamaClass().identificar_função()` é chamada para classificar a intenção da mensagem do usuário em uma das três categorias: `QUERY_FUNCTION` (para consultas financeiras), `FIN_FUNCTION` (para registrar uma nova transação financeira), ou `NOT_FUNCTION` (se a intenção não for clara).
    * **Para `FIN_FUNCTION`**:
        * `LlamaClass().gerar_mensagem_cadastro()` usa o LLM para analisar a mensagem do usuário, extrair os detalhes da transação (produto, valor, tipo, categoria, etc.) e formatá-los.
        * `BotClass().captura_dados_mensagem()` recebe a mensagem formatada, e `parse_entrada_data()` valida e estrutura os dados.
        * A classe `Extratos()` verifica se já existe um extrato para o usuário no mês e ano correspondentes (`verifica_extrato_existe()`); se não, cria um novo (`cria_extrato_usuario()`). Em seguida, cadastra a nova entrada financeira (`cadastra_entrada()`) no banco de dados.
    * **Para `QUERY_FUNCTION`**:
        * `LlamaClass().selecionar_query_por_similaridade()` usa um modelo de embedding e FAISS para encontrar a consulta SQL mais similar à pergunta do usuário, com base nos exemplos definidos em `project_files/scripts/scripts.json`.
        * `LlamaClass().processar_consulta_do_usuario()` executa a query SQL no banco de dados.
        * `LlamaClass().mostra_resultados_consulta_usuario()` formata os resultados da consulta para serem apresentados ao usuário.
    * **Para `NOT_FUNCTION`**:
        * `LlamaClass().funcao_nao_identificada()` envia uma mensagem ao usuário pedindo para que ele reformule sua solicitação de maneira mais clara.
6.  Finalmente, a `WahaBot().send_message()` envia a resposta processada de volta para o usuário via WhatsApp.

## Diagrama de Relacionamentos do Banco de Dados

O banco de dados PostgreSQL é fundamental para o armazenamento dos dados da aplicação. Ele é composto por três tabelas principais, conforme detalhado no arquivo `data/db/init.sql` e visualizado no diagrama conceitual encontrado em `project_files/Diagrama Economy Bot.pdf`.

**Tabela `usuarios`**
Armazena informações sobre os usuários cadastrados no bot.
* `id`: SERIAL, Chave Primária
* `nome`: VARCHAR(100) - Nome do usuário.
* `sobrenome`: VARCHAR(100) - Sobrenome do usuário.
* `telefone`: VARCHAR(12), Não Nulo - Número de telefone do usuário (usado como identificador no WhatsApp).
* `limite`: DECIMAL(12,2) - Limite de gastos mensal definido pelo usuário.

**Tabela `extratos`**
Organiza as transações financeiras dos usuários por mês e ano, funcionando como um agrupador para as entradas.
* `id`: SERIAL, Chave Primária
* `usuario_id`: INTEGER, Não Nulo, Chave Estrangeira referenciando `usuarios(id)` - Identifica a qual usuário o extrato pertence.
* `mes`: INTEGER, Não Nulo - Mês de referência do extrato.
* `ano`: INTEGER, Não Nulo - Ano de referência do extrato.

**Tabela `entradas`**
Contém os detalhes de cada transação financeira individual (receita ou despesa).
* `id`: SERIAL, Chave Primária
* `extrato_id`: INTEGER, Não Nulo, Chave Estrangeira referenciando `extratos(id)` - Identifica a qual extrato (mês/ano do usuário) a entrada pertence.
* `produto`: VARCHAR(100) - Nome ou identificação do produto/serviço da transação.
* `categoria`: VARCHAR(150) - Categoria da transação (ex: ALIMENTAÇÃO, LAZER, SALÁRIO).
* `tipo`: VARCHAR(30) - Tipo da transação (RECEITA ou DESPESA).
* `data`: DATE, Não Nulo - Data em que a transação ocorreu.
* `valor`: DECIMAL(12,2), Não Nulo - Montante financeiro da transação.
* `tipo_pagamento`: VARCHAR(255) - Método de pagamento utilizado (ex: Pix, Débito, Crédito, Dinheiro).
* `descricao`: VARCHAR(255) - Descrição adicional ou observações sobre a transação.

**Relacionamentos:**
* Um `usuario` pode ter vários `extratos` (um para cada combinação de mês e ano em que houve atividade).
* Cada `extrato` pertence a um único `usuario`.
* Um `extrato` pode conter várias `entradas` (transações financeiras).
* Cada `entrada` está associada a um único `extrato`.

[Diagrama de relacionamento](./project_files/Diagrama%20Economy%20Bot.pdf)
