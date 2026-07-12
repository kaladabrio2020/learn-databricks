# Databricks notebook source
# MAGIC %md
# MAGIC No ecossistema do **Databricks**, especialmente com o uso do **Unity Catalog**, os conceitos de Catálogo, Schema e Volume formam a estrutura lógica que organiza seus dados. Essa hierarquia é essencial para garantir governança, controle de acesso e facilidade de descoberta de dados.
# MAGIC
# MAGIC Aqui está como eles se organizam:
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### A Hierarquia de Dados (Unity Catalog)
# MAGIC
# MAGIC Imagine a hierarquia como um sistema de arquivos bem estruturado:
# MAGIC
# MAGIC 1. **Catalog (Catálogo):** É o nível mais alto. Geralmente representa um ambiente completo (como `desenvolvimento`, `homologação` ou `produção`) ou uma unidade de negócio. Ele é o contêiner principal para todos os dados que você gerencia.
# MAGIC 2. **Schema (Schema/Banco de Dados):** Fica dentro do Catálogo. É um agrupamento lógico para organizar suas tabelas, visões e volumes. Você pode pensar nele como um "banco de dados" dentro do catálogo, usado para separar projetos ou domínios de dados (ex: `vendas`, `marketing`, `RH`).
# MAGIC 3. **Volume:** Fica dentro de um Schema. É um objeto que gerencia **dados não estruturados** (arquivos PDF, imagens, logs, arquivos .csv brutos, etc.). Ele permite que você acesse esses arquivos de forma organizada, como se estivessem em um diretório de arquivos, mas com o benefício da segurança e governança do Unity Catalog.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Resumo Visual da Hierarquia
# MAGIC
# MAGIC | Nível | Função | Exemplo Prático |
# MAGIC | --- | --- | --- |
# MAGIC | **Catalog** | Nível de ambiente ou unidade | `empresa_prod` |
# MAGIC | **Schema** | Nível de projeto ou domínio | `vendas_regionais` |
# MAGIC | **Volume / Table** | Nível de armazenamento (Dados brutos vs. Estruturados) | `raw_files` / `tabela_clientes` |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Por que usar essa estrutura?
# MAGIC
# MAGIC * **Governança Unificada:** Você pode definir permissões em qualquer nível. Por exemplo: "O time de analistas pode ler o *Catálogo* inteiro, mas apenas o *Schema* de vendas".
# MAGIC * **Nomeação de 3 Níveis:** Para acessar qualquer dado no Databricks, você utiliza o padrão:
# MAGIC `catalog.schema.objeto`
# MAGIC *Exemplo:* `empresa_prod.vendas_regionais.clientes` (para uma tabela) ou `empresa_prod.vendas_regionais.arquivos_log` (para um volume).
# MAGIC * **Diferença fundamental:**
# MAGIC * **Tabelas:** Guardam dados estruturados (linhas e colunas) que podem ser consultados via SQL.
# MAGIC * **Volumes:** Guardam arquivos (objetos) que não seguem um esquema fixo de tabelas, sendo ideais para ingestão de dados brutos ou modelos de ML salvos como arquivos.
# MAGIC
# MAGIC
# MAGIC
# MAGIC Essa organização torna o seu trabalho com Data Science e Data Engineering muito mais limpo, especialmente quando você estiver rodando seus projetos no Databricks, evitando que arquivos ou tabelas fiquem "soltos" e difíceis de encontrar ou proteger.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC Para criar esses objetos no Databricks, utilizamos comandos SQL no editor de consultas (ou notebooks). Abaixo, veja como criar cada nível da hierarquia:
# MAGIC
# MAGIC ### 1. Criar um Catálogo (Catalog)
# MAGIC
# MAGIC O catálogo é o nível superior. Você pode criar um catálogo para separar ambientes, por exemplo.
# MAGIC
# MAGIC ```sql
# MAGIC CREATE CATALOG IF NOT EXISTS meu_catalogo_producao;
# MAGIC
# MAGIC ```
# MAGIC
# MAGIC ### 2. Criar um Schema (Schema)
# MAGIC
# MAGIC Dentro do catálogo, você cria schemas para organizar as tabelas e volumes de um domínio específico.
# MAGIC
# MAGIC ```sql
# MAGIC -- Primeiro, defina qual catálogo usar (opcional, mas recomendado)
# MAGIC USE CATALOG meu_catalogo_producao;
# MAGIC
# MAGIC -- Agora crie o schema
# MAGIC CREATE SCHEMA IF NOT EXISTS vendas_norte;
# MAGIC
# MAGIC ```
# MAGIC
# MAGIC ### 3. Criar um Volume
# MAGIC
# MAGIC Os volumes são usados para arquivos não estruturados. Você pode criar um volume "gerenciado" (onde o Databricks cuida do armazenamento) ou "externo" (apontando para uma pasta no seu Cloud Storage, como S3 ou ADLS).
# MAGIC
# MAGIC **Exemplo de Volume Gerenciado (Mais comum):**
# MAGIC
# MAGIC ```sql
# MAGIC -- Criando um volume dentro do schema definido anteriormente
# MAGIC CREATE VOLUME IF NOT EXISTS meu_catalogo_producao.vendas_norte.arquivos_brutos;
# MAGIC
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### Exemplo de uso conjunto (O caminho completo)
# MAGIC
# MAGIC Se você quiser ver como esses comandos se conectam em um fluxo de trabalho, seria assim:
# MAGIC
# MAGIC ```sql
# MAGIC -- 1. Criar a hierarquia
# MAGIC CREATE CATALOG IF NOT EXISTS lojinha_db;
# MAGIC CREATE SCHEMA IF NOT EXISTS lojinha_db.marketing;
# MAGIC CREATE VOLUME IF NOT EXISTS lojinha_db.marketing.imagens_promocionais;
# MAGIC
# MAGIC -- 2. Acessando os arquivos no volume
# MAGIC -- No Databricks, você acessa os arquivos dentro de um volume com o prefixo /Volumes/
# MAGIC -- Exemplo: /Volumes/lojinha_db/marketing/imagens_promocionais/banner.png
# MAGIC
# MAGIC ```
# MAGIC
# MAGIC ### Dicas importantes:
# MAGIC
# MAGIC * **IF NOT EXISTS:** Sempre use essa cláusula para evitar erros caso você execute o código mais de uma vez ou o objeto já exista.
# MAGIC * **Comentários:** É uma boa prática adicionar descrições aos seus objetos para facilitar a governança:
# MAGIC ```sql
# MAGIC CREATE SCHEMA IF NOT EXISTS vendas_norte 
# MAGIC COMMENT 'Dados de vendas referentes à região norte do país';
# MAGIC
# MAGIC ```
# MAGIC
# MAGIC
# MAGIC * **Permissões:** Lembre-se que, após criar, você precisará usar comandos `GRANT` para permitir que outros usuários ou grupos acessem esses objetos (ex: `GRANT USAGE ON CATALOG...`, `GRANT SELECT ON SCHEMA...`).
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC [Referencias](https://docs.databricks.com/aws/pt/reference/api)
# MAGIC

# COMMAND ----------

spark

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM samples.tpch.lineitem

# COMMAND ----------

spark.sql(
    "SELECT * FROM samples.tpch.lineitem LIMIT 10"
).show(2)

# COMMAND ----------

# Criar catalogo
spark.sql("CREATE CATALOG IF NOT EXISTS exemple_del_learn")
## cascade deleta tudo em cascata

# COMMAND ----------

# MAGIC %md
# MAGIC Criando catalogo

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS learn_databricks;

# COMMAND ----------

# MAGIC %md
# MAGIC Criando esquema

# COMMAND ----------

spark.sql("CREATE SCHEMA IF NOT EXISTS learn_databricks.schema")

# COMMAND ----------

# MAGIC %md
# MAGIC Criando tabela

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE learn_databricks.schema.tabela_example_create (ID INT, NAME STRING);

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE VOLUME IF NOT EXISTS learn_databricks.schema.volume

# COMMAND ----------

# MAGIC %sql
# MAGIC drop schema if exists exemple_del_learn cascade;

# COMMAND ----------

# MAGIC %sql
# MAGIC drop catalog if exists exemple_del_learn cascade;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC -------------------

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS learn_databricks.dados_estaticos;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE VOLUME IF NOT EXISTS learn_databricks.dados_estaticos.volume;

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER SCHEMA learn_databricks.dados_estaticos RENAME TO learn_databricks.datasets