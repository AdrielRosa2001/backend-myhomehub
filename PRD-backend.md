# PRD - Requisitos de Integração e Ajustes no Backend (MyFinance)

Este documento especifica os requisitos de backend necessários para suportar nativamente e otimizar as novas funcionalidades implementadas no front-end do MyFinance. Atualmente, o front-end realiza as operações em massa simulando-as por meio de chamadas paralelas de API cliente-side. Para melhor escalabilidade, desempenho e segurança, recomenda-se a criação dos endpoints e ajustes descritos abaixo.

---

## 1. Filtragem por Mês (Ajustes de Query Params)

### `GET /transactions/`
Adicionar suporte opcional para busca consolidada por mês e ano diretamente via parâmetros de consulta (Query Parameters), evitando a necessidade do front-end calcular as datas de início e fim do mês.

* **Novos Query Params**:
  * `month` (inteiro, 1-12) - Ex: `6` para Junho.
  * `year` (inteiro) - Ex: `2026`.
* **Comportamento**: Se `month` e `year` forem fornecidos, o backend deve ignorar ou sobrescrever os campos `start_date` e `end_date` correspondentes ao período completo desse mês.

---

## 2. Endpoints de Métricas e Gráficos Consolidados

### `GET /metrics/annual-chart`
Novo endpoint para buscar dados mensais consolidados do ano inteiro, utilizado para alimentar o gráfico **"Relatório Anual"**.

* **Query Params**:
  * `year` (inteiro, obrigatório) - Ex: `2026`.
* **Resposta Esperada (`200 OK`)**:
  Um array de exatamente 12 objetos, cada um contendo as receitas e despesas totais consolidadas daquele mês.
  ```json
  {
    "year": 2026,
    "data": [
      { "month": "Jan", "receitas": 5000.0, "despesas": 3200.0 },
      { "month": "Fev", "receitas": 4500.0, "despesas": 3100.0 },
      { "month": "Mar", "receitas": 6200.0, "despesas": 4000.0 },
      ...
      { "month": "Dez", "receitas": 8000.0, "despesas": 5500.0 }
    ]
  }
  ```

---

## 3. Endpoints para Ações em Massa (Bulk Actions)

### 3.1. Atualização em Massa (Bulk Update)
Atualiza múltiplos registros simultaneamente com os mesmos dados selecionados pelo usuário.

* **Método**: `PATCH` ou `PUT`
* **Rota**: `/transactions/bulk-update`
* **Payload**:
  ```json
  {
    "ids": [12, 13, 15],
    "fields": {
      "type": "despesa",           // Opcional
      "date": "2026-06-30",        // Opcional
      "category": "Lazer",         // Opcional
      "is_paid": true              // Opcional
    }
  }
  ```
* **Resposta Esperada (`200 OK`)**:
  ```json
  {
    "message": "3 transações atualizadas com sucesso.",
    "updated_count": 3
  }
  ```

### 3.2. Exclusão em Massa (Bulk Delete)
Exclui de uma vez todas as transações selecionadas.

* **Método**: `POST` ou `DELETE`
* **Rota**: `/transactions/bulk-delete`
* **Payload**:
  ```json
  {
    "ids": [12, 13, 15]
  }
  ```
* **Resposta Esperada (`200 OK` ou `204 No Content`)**:
  ```json
  {
    "message": "3 transações excluídas com sucesso."
  }
  ```

### 3.3. Duplicação em Massa (Bulk Duplicate)
Cria cópias exatas das transações especificadas pelos IDs no payload, porém sobrescrevendo os campos de cabeçalho configurados pelo usuário.

* **Método**: `POST`
* **Rota**: `/transactions/bulk-duplicate`
* **Payload**:
  ```json
  {
    "ids": [12, 13],
    "overrides": {
      "type": "despesa",
      "date": "2026-07-01",
      "category": "Fixas",
      "is_paid": false
    }
  }
  ```
* **Resposta Esperada (`201 Created`)**:
  ```json
  {
    "message": "2 transações duplicadas com sucesso.",
    "duplicated_count": 2
  }
  ```

---

## 4. Paginação, Ordenação e Busca via Servidor (Melhoria Futura)
Para suportar bases de dados maiores de forma eficiente, sugere-se migrar as funcionalidades de busca e ordenação para o backend.

### `GET /transactions/` (Novos Parâmetros de Query)
* **`search`** (string) - Filtro textual que busca correspondência parcial e case-insensitive nos campos `description` e `category`.
* **`sort_by`** (string) - Nome do campo para ordenar (`date`, `description`, `category`, `amount`, `is_paid`).
* **`order`** (string) - Sentido da ordenação (`asc` ou `desc`).
