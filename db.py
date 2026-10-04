import os
from pymongo import MongoClient, ASCENDING


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "biblioteca")


def get_client():
    return MongoClient(MONGO_URI)


def get_database(client=None, db_name=None):
    if client is None:
        client = get_client()

    return client[db_name or DB_NAME]


def criar_indices(db):
    # ISBN dos livros deve ser único
    db.livros.create_index(
        [("isbn", ASCENDING)],
        unique=True,
        name="isbn_unico"
    )

    # Matrícula dos alunos deve ser única
    db.alunos.create_index(
        [("matricula", ASCENDING)],
        unique=True,
        name="matricula_unica"
    )

    # Índices auxiliares para as consultas de empréstimos
    db.emprestimos.create_index(
        [("isbn", ASCENDING), ("data_devolucao", ASCENDING)]
    )

    db.emprestimos.create_index(
        [("matricula", ASCENDING), ("data_devolucao", ASCENDING)]
    )

    db.emprestimos.create_index(
        [("data_prevista", ASCENDING), ("data_devolucao", ASCENDING)]
    )


def inicializar_banco():
    db = get_database()
    criar_indices(db)
    return db