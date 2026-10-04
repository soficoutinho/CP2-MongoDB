import pytest
from pymongo import MongoClient

from db import criar_indices
from service import BibliotecaService


TEST_MONGO_URI = "mongodb://localhost:27017"
TEST_DB_NAME = "biblioteca_test"


@pytest.fixture
def db():
    client = MongoClient(TEST_MONGO_URI)

    # Confirma que o MongoDB está disponível
    client.admin.command("ping")

    # Apaga qualquer banco de teste anterior
    client.drop_database(TEST_DB_NAME)

    # Cria um banco exclusivo para os testes
    database = client[TEST_DB_NAME]

    # Cria os mesmos índices usados no sistema real
    criar_indices(database)

    yield database

    # Limpeza após cada teste
    client.drop_database(TEST_DB_NAME)
    client.close()


@pytest.fixture
def service(db):
    return BibliotecaService(db)


@pytest.fixture
def dados_basicos(service):
    service.cadastrar_livro(
        "9780000000001",
        "Python para Todos",
        "Ana Silva",
        2025,
        "Tecnologia",
        3
    )

    service.cadastrar_aluno(
        "RM001",
        "João da Silva",
        "Sistemas de Informação",
        "joao@faculdade.com"
    )