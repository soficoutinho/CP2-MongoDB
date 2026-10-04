# Sistema de Empréstimo de Livros com MongoDB

Projeto desenvolvido em Python com MongoDB para gerenciamento de uma biblioteca acadêmica.

O sistema substitui o controle manual realizado por planilhas e permite gerenciar livros, alunos, empréstimos, devoluções e relatórios por meio de uma interface no terminal.

## Tecnologias utilizadas

- Python 3
- MongoDB
- PyMongo
- Docker
- Docker Compose
- Pytest

## Estrutura do projeto

```text
biblioteca-mongodb/
│
├── db.py
├── exceptions.py
├── service.py
├── main.py
├── requirements.txt
├── docker-compose.yml
├── README.md
├── .gitignore
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_service.py
```

## Arquitetura

O projeto foi dividido em camadas.

### db.py

Responsável pela conexão com o MongoDB e pela criação dos índices.

São criados índices únicos para:

- ISBN dos livros;
- matrícula dos alunos.

Também são criados índices auxiliares para consultas relacionadas aos empréstimos.

### service.py

Contém as regras de negócio do sistema, incluindo:

- cadastro de livros;
- consulta de livros;
- atualização de livros;
- remoção de livros;
- cadastro de alunos;
- consulta de alunos;
- pesquisa por título, autor e categoria;
- realização de empréstimos;
- devolução de livros;
- cálculo de multas;
- relatórios utilizando Aggregation Pipeline.

### exceptions.py

Contém as exceções personalizadas utilizadas pelas regras de negócio.

Entre elas:

- `LivroIndisponivel`;
- `LimiteEmprestimos`;
- `AlunoComAtraso`;
- `EmprestimoJaDevolvido`;
- `LivroComEmprestimoAberto`;
- `EmailInvalido`.

### main.py

Responsável pela interface do sistema através de um menu no terminal.

## Funcionalidades

### R1 - Livros

O sistema permite:

- cadastrar livros;
- buscar livro por ISBN;
- listar livros;
- atualizar livros;
- remover livros.

O ISBN possui índice único no MongoDB.

Um livro que possui empréstimo em aberto não pode ser removido.

### R2 - Alunos

O sistema permite:

- cadastrar alunos;
- buscar alunos pela matrícula.

A matrícula possui índice único.

O e-mail informado deve conter `@`.

### R3 - Busca de livros

É possível pesquisar livros:

- por parte do título;
- por parte do nome do autor;
- por categoria.

As pesquisas por título e autor são case-insensitive.

Os resultados são ordenados pelo título.

### R4 - Empréstimos

Um empréstimo somente pode ser realizado quando:

- o livro possui exemplar disponível;
- o aluno possui menos de três empréstimos em aberto;
- o aluno não possui empréstimos atrasados.

O prazo de devolução é de 7 dias.

A redução do estoque utiliza uma operação atômica do MongoDB:

```python
update_one(
    {
        "isbn": isbn,
        "exemplares_disponiveis": {"$gt": 0}
    },
    {
        "$inc": {
            "exemplares_disponiveis": -1
        }
    }
)
```

O filtro garante que o estoque somente seja reduzido quando houver pelo menos um exemplar disponível, evitando que empréstimos concorrentes tornem o estoque negativo.

### R5 - Devoluções

Na devolução:

- a data de devolução é registrada;
- o exemplar retorna ao estoque;
- empréstimos atrasados geram multa;
- a multa é de R$ 2,00 por dia de atraso;
- uma segunda devolução do mesmo empréstimo gera erro.

### R6 - Relatórios

Os relatórios são implementados utilizando Aggregation Pipeline do MongoDB.

O sistema possui os seguintes relatórios:

1. Top 5 livros mais emprestados;
2. quantidade de empréstimos por curso;
3. alunos com empréstimos atrasados, mostrando aluno, livro e dias de atraso;
4. total arrecadado em multas.

### R7 - Menu

Todas as principais funcionalidades podem ser acessadas pelo terminal através do menu disponível em `main.py`.

## Como executar o projeto

### 1. Criar o ambiente virtual

No Windows:

```powershell
python -m venv .venv
```

Ative o ambiente:

```powershell
.venv\Scripts\Activate.ps1
```

Caso o PowerShell bloqueie a execução do script, execute:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

e tente ativar novamente.

### 2. Instalar as dependências

```powershell
python -m pip install -r requirements.txt
```

### 3. Iniciar o MongoDB

O projeto possui um arquivo `docker-compose.yml`.

Com o Docker Desktop aberto, execute:

```powershell
docker compose up -d
```

Para verificar se o container está funcionando:

```powershell
docker ps
```

O MongoDB ficará disponível em:

```text
mongodb://localhost:27017
```

O banco utilizado pela aplicação é:

```text
biblioteca
```

## Executando o sistema

Com o MongoDB em execução e o ambiente virtual ativado:

```powershell
python main.py
```

O menu será exibido no terminal.

## Executando os testes

Os testes automatizados utilizam um banco separado chamado:

```text
biblioteca_test
```

Isso evita interferência nos dados da aplicação.

Para executar todos os testes:

```powershell
python -m pytest -v
```

A suíte possui testes automatizados cobrindo os requisitos R1 até R6.

## Data parametrizada

As operações relacionadas a empréstimos, devoluções e atrasos permitem informar uma data através do parâmetro `data_atual`.

Quando nenhuma data é informada, o sistema utiliza a data atual.

Essa abordagem facilita a criação de testes automatizados para prazos, atrasos e multas.

## Banco de dados

O sistema utiliza três coleções principais no MongoDB.

### livros

Exemplo:

```json
{
    "isbn": "9780000000001",
    "titulo": "Python para Todos",
    "autor": "Ana Silva",
    "ano": 2025,
    "categoria": "Tecnologia",
    "exemplares_total": 3,
    "exemplares_disponiveis": 3
}
```

### alunos

Exemplo:

```json
{
    "matricula": "RM001",
    "nome": "João da Silva",
    "curso": "Sistemas de Informação",
    "email": "joao@faculdade.com"
}
```

### emprestimos

Exemplo:

```text
{
    isbn,
    matricula,
    data_emprestimo,
    data_prevista,
    data_devolucao,
    multa
}
```

Enquanto o livro não for devolvido, `data_devolucao` permanece com valor `null`.

## Testes automatizados

A suíte de testes verifica, entre outros cenários:

- cadastro e consulta de livros;
- ISBN único;
- atualização e remoção;
- bloqueio da remoção de livro emprestado;
- cadastro e consulta de alunos;
- matrícula única;
- validação de e-mail;
- busca case-insensitive;
- filtro por categoria;
- redução de estoque;
- prazo de devolução de 7 dias;
- indisponibilidade de exemplares;
- limite de três empréstimos;
- bloqueio de aluno com atraso;
- devolução e reposição do estoque;
- cálculo de multa;
- proteção contra devolução duplicada;
- Top 5 livros;
- empréstimos por curso;
- empréstimos atrasados;
- total arrecadado em multas.

## Objetivo

O objetivo do projeto é demonstrar a utilização do MongoDB com Python em uma aplicação com regras de negócio, índices, operações atômicas, Aggregation Pipeline, tratamento de exceções, separação em camadas e testes automatizados.