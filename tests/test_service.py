from datetime import datetime, timedelta

import pytest
from pymongo.errors import DuplicateKeyError

from exceptions import (
    LivroDuplicado,
    LivroComEmprestimoAberto,
    LivroIndisponivel,
    EmailInvalido,
    LimiteEmprestimos,
    AlunoComAtraso,
    EmprestimoJaDevolvido,
)


# ============================================================
# R1 - CRUD DE LIVROS
# ============================================================

def test_r1_cadastrar_e_buscar_livro(service):
    service.cadastrar_livro(
        "111",
        "Banco de Dados",
        "Carlos Souza",
        2024,
        "Tecnologia",
        2
    )

    livro = service.buscar_livro_por_isbn("111")

    assert livro["isbn"] == "111"
    assert livro["titulo"] == "Banco de Dados"
    assert livro["exemplares_total"] == 2
    assert livro["exemplares_disponiveis"] == 2


def test_r1_isbn_deve_ser_unico(service):
    service.cadastrar_livro(
        "111",
        "Livro A",
        "Autor A",
        2020,
        "Teste",
        1
    )

    with pytest.raises(LivroDuplicado):
        service.cadastrar_livro(
            "111",
            "Livro B",
            "Autor B",
            2021,
            "Teste",
            1
        )


def test_r1_listar_livros_ordenados(service):
    service.cadastrar_livro(
        "1", "Zebra", "Autor", 2020, "Teste", 1
    )

    service.cadastrar_livro(
        "2", "Algoritmos", "Autor", 2020, "Teste", 1
    )

    livros = service.listar_livros()

    assert livros[0]["titulo"] == "Algoritmos"
    assert livros[1]["titulo"] == "Zebra"


def test_r1_atualizar_livro(service):
    service.cadastrar_livro(
        "111",
        "Título Antigo",
        "Autor",
        2020,
        "Teste",
        1
    )

    atualizado = service.atualizar_livro(
        "111",
        {"titulo": "Título Novo"}
    )

    assert atualizado["titulo"] == "Título Novo"


def test_r1_remover_livro(service):
    service.cadastrar_livro(
        "111",
        "Livro",
        "Autor",
        2020,
        "Teste",
        1
    )

    service.remover_livro("111")

    assert service.livros.find_one(
        {"isbn": "111"}
    ) is None


def test_r1_nao_remove_livro_com_emprestimo_aberto(
    service,
    dados_basicos
):
    data = datetime(2026, 1, 1)

    service.emprestar_livro(
        "9780000000001",
        "RM001",
        data
    )

    with pytest.raises(LivroComEmprestimoAberto):
        service.remover_livro(
            "9780000000001"
        )


# ============================================================
# R2 - CADASTRO DE ALUNOS
# ============================================================

def test_r2_cadastrar_e_buscar_aluno(service):
    service.cadastrar_aluno(
        "RM100",
        "Maria",
        "Engenharia",
        "maria@email.com"
    )

    aluno = service.buscar_aluno_por_matricula(
        "RM100"
    )

    assert aluno["nome"] == "Maria"
    assert aluno["matricula"] == "RM100"


def test_r2_email_deve_conter_arroba(service):
    with pytest.raises(EmailInvalido):
        service.cadastrar_aluno(
            "RM100",
            "Maria",
            "Engenharia",
            "email-invalido"
        )


def test_r2_matricula_deve_ser_unica(db):
    db.alunos.insert_one({
        "matricula": "RM100",
        "nome": "Aluno 1",
        "curso": "ADS",
        "email": "a@a.com"
    })

    with pytest.raises(DuplicateKeyError):
        db.alunos.insert_one({
            "matricula": "RM100",
            "nome": "Aluno 2",
            "curso": "ADS",
            "email": "b@b.com"
        })


# ============================================================
# R3 - BUSCA DE LIVROS
# ============================================================

def test_r3_busca_por_titulo_case_insensitive(service):
    service.cadastrar_livro(
        "1",
        "Introdução ao Python",
        "Ana",
        2024,
        "Tecnologia",
        1
    )

    service.cadastrar_livro(
        "2",
        "MongoDB Avançado",
        "Carlos",
        2024,
        "Tecnologia",
        1
    )

    resultado = service.buscar_livros("PYTHON")

    assert len(resultado) == 1
    assert (
        resultado[0]["titulo"]
        == "Introdução ao Python"
    )


def test_r3_busca_por_parte_do_autor(service):
    service.cadastrar_livro(
        "1",
        "Dom Casmurro",
        "Machado de Assis",
        1899,
        "Literatura",
        1
    )

    resultado = service.buscar_livros(
        "MACHADO"
    )

    assert len(resultado) == 1
    assert (
        resultado[0]["autor"]
        == "Machado de Assis"
    )


def test_r3_filtra_categoria_e_ordena_titulo(service):
    service.cadastrar_livro(
        "1",
        "Zebra",
        "Autor",
        2020,
        "Tecnologia",
        1
    )

    service.cadastrar_livro(
        "2",
        "Algoritmos",
        "Autor",
        2020,
        "Tecnologia",
        1
    )

    service.cadastrar_livro(
        "3",
        "Romance",
        "Autor",
        2020,
        "Literatura",
        1
    )

    resultado = service.buscar_livros(
        categoria="tecnologia"
    )

    assert len(resultado) == 2
    assert resultado[0]["titulo"] == "Algoritmos"
    assert resultado[1]["titulo"] == "Zebra"


# ============================================================
# R4 - EMPRESTAR LIVRO
# ============================================================

def test_r4_emprestimo_reduz_estoque_e_prazo_7_dias(
    service,
    dados_basicos
):
    data = datetime(2026, 1, 1)

    emprestimo = service.emprestar_livro(
        "9780000000001",
        "RM001",
        data
    )

    livro = service.buscar_livro_por_isbn(
        "9780000000001"
    )

    assert livro["exemplares_disponiveis"] == 2

    assert emprestimo["data_prevista"] == (
        data + timedelta(days=7)
    )


def test_r4_nao_empresta_sem_exemplar(service):
    service.cadastrar_livro(
        "SEMESTOQUE",
        "Livro Sem Estoque",
        "Autor",
        2020,
        "Teste",
        0
    )

    service.cadastrar_aluno(
        "RM1",
        "Aluno",
        "ADS",
        "aluno@email.com"
    )

    with pytest.raises(LivroIndisponivel):
        service.emprestar_livro(
            "SEMESTOQUE",
            "RM1",
            datetime(2026, 1, 1)
        )


def test_r4_limite_de_tres_emprestimos(service):
    service.cadastrar_aluno(
        "RM1",
        "Aluno",
        "ADS",
        "aluno@email.com"
    )

    for numero in range(4):
        service.cadastrar_livro(
            str(numero),
            f"Livro {numero}",
            "Autor",
            2020,
            "Teste",
            1
        )

    data = datetime(2026, 1, 1)

    service.emprestar_livro(
        "0", "RM1", data
    )

    service.emprestar_livro(
        "1", "RM1", data
    )

    service.emprestar_livro(
        "2", "RM1", data
    )

    with pytest.raises(LimiteEmprestimos):
        service.emprestar_livro(
            "3", "RM1", data
        )


def test_r4_aluno_atrasado_nao_pode_emprestar(
    service
):
    service.cadastrar_aluno(
        "RM1",
        "Aluno",
        "ADS",
        "aluno@email.com"
    )

    service.cadastrar_livro(
        "1",
        "Livro 1",
        "Autor",
        2020,
        "Teste",
        1
    )

    service.cadastrar_livro(
        "2",
        "Livro 2",
        "Autor",
        2020,
        "Teste",
        1
    )

    data_inicial = datetime(2026, 1, 1)

    service.emprestar_livro(
        "1",
        "RM1",
        data_inicial
    )

    # O primeiro empréstimo deveria ser devolvido
    # em 08/01/2026.
    data_futura = datetime(2026, 1, 20)

    with pytest.raises(AlunoComAtraso):
        service.emprestar_livro(
            "2",
            "RM1",
            data_futura
        )


# ============================================================
# R5 - DEVOLVER LIVRO
# ============================================================

def test_r5_devolucao_sem_atraso_retorna_estoque(
    service,
    dados_basicos
):
    inicio = datetime(2026, 1, 1)

    emprestimo = service.emprestar_livro(
        "9780000000001",
        "RM001",
        inicio
    )

    resultado = service.devolver_livro(
        emprestimo["_id"],
        datetime(2026, 1, 5)
    )

    assert resultado["multa"] == 0.0

    livro = service.buscar_livro_por_isbn(
        "9780000000001"
    )

    assert livro["exemplares_disponiveis"] == 3


def test_r5_multa_de_dois_reais_por_dia(
    service,
    dados_basicos
):
    inicio = datetime(2026, 1, 1)

    emprestimo = service.emprestar_livro(
        "9780000000001",
        "RM001",
        inicio
    )

    # Data prevista = 08/01/2026
    # Devolução = 11/01/2026
    # Atraso = 3 dias
    resultado = service.devolver_livro(
        emprestimo["_id"],
        datetime(2026, 1, 11)
    )

    assert resultado["dias_atraso"] == 3
    assert resultado["multa"] == 6.0


def test_r5_nao_pode_devolver_duas_vezes(
    service,
    dados_basicos
):
    inicio = datetime(2026, 1, 1)

    emprestimo = service.emprestar_livro(
        "9780000000001",
        "RM001",
        inicio
    )

    service.devolver_livro(
        emprestimo["_id"],
        datetime(2026, 1, 5)
    )

    with pytest.raises(
        EmprestimoJaDevolvido
    ):
        service.devolver_livro(
            emprestimo["_id"],
            datetime(2026, 1, 6)
        )


# ============================================================
# R6 - RELATÓRIOS / AGGREGATION PIPELINE
# ============================================================

def test_r6_top_5_livros_mais_emprestados(
    service,
    db
):
    service.cadastrar_livro(
        "1",
        "Livro A",
        "Autor",
        2020,
        "Teste",
        1
    )

    service.cadastrar_livro(
        "2",
        "Livro B",
        "Autor",
        2020,
        "Teste",
        1
    )

    db.emprestimos.insert_many([
        {
            "isbn": "1",
            "matricula": "A",
            "multa": 0
        },
        {
            "isbn": "1",
            "matricula": "B",
            "multa": 0
        },
        {
            "isbn": "1",
            "matricula": "C",
            "multa": 0
        },
        {
            "isbn": "2",
            "matricula": "A",
            "multa": 0
        },
    ])

    resultado = (
        service.top_5_livros_mais_emprestados()
    )

    assert resultado[0]["isbn"] == "1"

    assert (
        resultado[0]["quantidade_emprestimos"]
        == 3
    )


def test_r6_quantidade_emprestimos_por_curso(
    service,
    db
):
    service.cadastrar_aluno(
        "A1",
        "Ana",
        "ADS",
        "ana@email.com"
    )

    service.cadastrar_aluno(
        "A2",
        "Carlos",
        "Medicina",
        "carlos@email.com"
    )

    db.emprestimos.insert_many([
        {
            "isbn": "1",
            "matricula": "A1",
            "multa": 0
        },
        {
            "isbn": "2",
            "matricula": "A1",
            "multa": 0
        },
        {
            "isbn": "3",
            "matricula": "A2",
            "multa": 0
        },
    ])

    resultado = (
        service.emprestimos_por_curso()
    )

    ads = next(
        item
        for item in resultado
        if item["curso"] == "ADS"
    )

    assert ads["quantidade"] == 2


def test_r6_alunos_com_emprestimos_atrasados(
    service,
    dados_basicos
):
    inicio = datetime(2026, 1, 1)

    service.emprestar_livro(
        "9780000000001",
        "RM001",
        inicio
    )

    resultado = (
        service.alunos_com_emprestimos_atrasados(
            datetime(2026, 1, 11)
        )
    )

    assert len(resultado) == 1

    assert (
        resultado[0]["nome"]
        == "João da Silva"
    )

    assert resultado[0]["dias_atraso"] == 3


def test_r6_total_arrecadado_em_multas(
    service,
    db
):
    db.emprestimos.insert_many([
        {
            "isbn": "1",
            "matricula": "1",
            "multa": 10.0
        },
        {
            "isbn": "2",
            "matricula": "2",
            "multa": 6.0
        },
        {
            "isbn": "3",
            "matricula": "3",
            "multa": 0.0
        },
    ])

    total = (
        service.total_arrecadado_multas()
    )

    assert total == 16.0