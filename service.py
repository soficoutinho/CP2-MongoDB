from datetime import datetime, timedelta

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from exceptions import (
    LivroNaoEncontrado,
    LivroDuplicado,
    LivroComEmprestimoAberto,
    LivroIndisponivel,
    AlunoNaoEncontrado,
    AlunoDuplicado,
    EmailInvalido,
    LimiteEmprestimos,
    AlunoComAtraso,
    EmprestimoNaoEncontrado,
    EmprestimoJaDevolvido,
    DadosInvalidos,
)


class BibliotecaService:

    def __init__(self, db):
        self.db = db
        self.livros = db.livros
        self.alunos = db.alunos
        self.emprestimos = db.emprestimos

    # ============================================================
    # R1 - CADASTRO DE LIVROS (CRUD)
    # ============================================================

    def cadastrar_livro(
        self,
        isbn,
        titulo,
        autor,
        ano,
        categoria,
        exemplares_total
    ):
        if exemplares_total < 0:
            raise DadosInvalidos(
                "A quantidade de exemplares não pode ser negativa."
            )

        livro = {
            "isbn": isbn,
            "titulo": titulo,
            "autor": autor,
            "ano": ano,
            "categoria": categoria,
            "exemplares_total": exemplares_total,
            "exemplares_disponiveis": exemplares_total,
        }

        try:
            resultado = self.livros.insert_one(livro)
            livro["_id"] = resultado.inserted_id
            return livro

        except DuplicateKeyError:
            raise LivroDuplicado(
                f"Já existe um livro com ISBN {isbn}."
            )

    def buscar_livro_por_isbn(self, isbn):
        livro = self.livros.find_one({"isbn": isbn})

        if not livro:
            raise LivroNaoEncontrado(
                f"Livro com ISBN {isbn} não encontrado."
            )

        return livro

    def listar_livros(self):
        return list(
            self.livros.find().sort("titulo", 1)
        )

    def atualizar_livro(self, isbn, dados):
        dados = dados.copy()

        # Campos que não devem ser alterados diretamente.
        dados.pop("_id", None)
        dados.pop("isbn", None)
        dados.pop("exemplares_disponiveis", None)

        resultado = self.livros.find_one_and_update(
            {"isbn": isbn},
            {"$set": dados},
            return_document=ReturnDocument.AFTER,
        )

        if not resultado:
            raise LivroNaoEncontrado(
                f"Livro com ISBN {isbn} não encontrado."
            )

        return resultado

    def remover_livro(self, isbn):
        livro = self.buscar_livro_por_isbn(isbn)

        emprestimo_aberto = self.emprestimos.find_one({
            "isbn": isbn,
            "data_devolucao": None,
        })

        if emprestimo_aberto:
            raise LivroComEmprestimoAberto(
                "O livro possui empréstimo em aberto e não pode ser removido."
            )

        self.livros.delete_one({"_id": livro["_id"]})

        return True

    # ============================================================
    # R2 - CADASTRO DE ALUNOS
    # ============================================================

    def cadastrar_aluno(self, matricula, nome, curso, email):
        if "@" not in email:
            raise EmailInvalido(
                "E-mail inválido. O endereço deve conter @."
            )

        aluno = {
            "matricula": matricula,
            "nome": nome,
            "curso": curso,
            "email": email,
        }

        try:
            resultado = self.alunos.insert_one(aluno)
            aluno["_id"] = resultado.inserted_id
            return aluno

        except DuplicateKeyError:
            raise AlunoDuplicado(
                f"Já existe um aluno com matrícula {matricula}."
            )

    def buscar_aluno_por_matricula(self, matricula):
        aluno = self.alunos.find_one({
            "matricula": matricula
        })

        if not aluno:
            raise AlunoNaoEncontrado(
                f"Aluno com matrícula {matricula} não encontrado."
            )

        return aluno

    # ============================================================
    # R3 - BUSCA DE LIVROS
    # ============================================================

    def buscar_livros(self, termo=None, categoria=None):
        filtros = []

        if termo:
            filtros.append({
                "$or": [
                    {
                        "titulo": {
                            "$regex": termo,
                            "$options": "i"
                        }
                    },
                    {
                        "autor": {
                            "$regex": termo,
                            "$options": "i"
                        }
                    },
                ]
            })

        if categoria:
            filtros.append({
                "categoria": {
                    "$regex": f"^{categoria}$",
                    "$options": "i"
                }
            })

        if not filtros:
            consulta = {}

        elif len(filtros) == 1:
            consulta = filtros[0]

        else:
            consulta = {"$and": filtros}

        return list(
            self.livros.find(consulta).sort("titulo", 1)
        )

    # ============================================================
    # R4 - EMPRESTAR LIVRO
    # ============================================================

    def emprestar_livro(
        self,
        isbn,
        matricula,
        data_atual=None
    ):
        if data_atual is None:
            data_atual = datetime.now()

        # Verifica se o aluno existe.
        self.buscar_aluno_por_matricula(matricula)

        # Verifica se o livro existe.
        self.buscar_livro_por_isbn(isbn)

        # Cada aluno pode ter no máximo 3 empréstimos em aberto.
        quantidade_abertos = self.emprestimos.count_documents({
            "matricula": matricula,
            "data_devolucao": None,
        })

        if quantidade_abertos >= 3:
            raise LimiteEmprestimos(
                "O aluno já possui 3 empréstimos em aberto."
            )

        # Aluno com empréstimo atrasado não pode pegar outro livro.
        atrasado = self.emprestimos.find_one({
            "matricula": matricula,
            "data_devolucao": None,
            "data_prevista": {"$lt": data_atual},
        })

        if atrasado:
            raise AlunoComAtraso(
                "O aluno possui empréstimo atrasado."
            )

        # Atualização atômica do estoque.
        #
        # IMPORTANTE:
        # O enunciado exige update_one com filtro
        # exemplares_disponiveis > 0 e operador $inc.
        # Dessa forma, empréstimos concorrentes não fazem
        # o estoque ficar negativo.
        resultado_estoque = self.livros.update_one(
            {
                "isbn": isbn,
                "exemplares_disponiveis": {"$gt": 0},
            },
            {
                "$inc": {
                    "exemplares_disponiveis": -1
                }
            },
        )

        if resultado_estoque.modified_count == 0:
            raise LivroIndisponivel(
                "Não há exemplares disponíveis."
            )

        # Prazo de devolução: 7 dias.
        data_prevista = data_atual + timedelta(days=7)

        emprestimo = {
            "isbn": isbn,
            "matricula": matricula,
            "data_emprestimo": data_atual,
            "data_prevista": data_prevista,
            "data_devolucao": None,
            "multa": 0.0,
        }

        try:
            resultado = self.emprestimos.insert_one(emprestimo)
            emprestimo["_id"] = resultado.inserted_id

            return emprestimo

        except Exception:
            # Se ocorrer algum erro ao salvar o empréstimo,
            # devolvemos o exemplar ao estoque.
            self.livros.update_one(
                {"isbn": isbn},
                {
                    "$inc": {
                        "exemplares_disponiveis": 1
                    }
                },
            )

            raise

    # ============================================================
    # R5 - DEVOLVER LIVRO
    # ============================================================

    def devolver_livro(
        self,
        emprestimo_id,
        data_atual=None
    ):
        if data_atual is None:
            data_atual = datetime.now()

        emprestimo = self.emprestimos.find_one({
            "_id": emprestimo_id
        })

        if not emprestimo:
            raise EmprestimoNaoEncontrado(
                "Empréstimo não encontrado."
            )

        if emprestimo["data_devolucao"] is not None:
            raise EmprestimoJaDevolvido(
                "Este empréstimo já foi devolvido."
            )

        dias_atraso = 0

        if data_atual > emprestimo["data_prevista"]:
            diferenca = (
                data_atual - emprestimo["data_prevista"]
            )

            dias_atraso = diferenca.days

        # Multa de R$ 2,00 por dia.
        multa = dias_atraso * 2.0

        # data_devolucao=None no filtro também ajuda a impedir
        # que o mesmo empréstimo seja devolvido duas vezes.
        resultado = self.emprestimos.update_one(
            {
                "_id": emprestimo_id,
                "data_devolucao": None,
            },
            {
                "$set": {
                    "data_devolucao": data_atual,
                    "multa": multa,
                }
            },
        )

        if resultado.modified_count == 0:
            raise EmprestimoJaDevolvido(
                "Este empréstimo já foi devolvido."
            )

        # Devolve o exemplar ao estoque.
        self.livros.update_one(
            {"isbn": emprestimo["isbn"]},
            {
                "$inc": {
                    "exemplares_disponiveis": 1
                }
            },
        )

        return {
            "dias_atraso": dias_atraso,
            "multa": multa,
        }

    # ============================================================
    # R6 - RELATÓRIOS COM AGGREGATION PIPELINE
    # ============================================================

    def top_5_livros_mais_emprestados(self):
        pipeline = [
            {
                "$group": {
                    "_id": "$isbn",
                    "quantidade_emprestimos": {
                        "$sum": 1
                    },
                }
            },
            {
                "$lookup": {
                    "from": "livros",
                    "localField": "_id",
                    "foreignField": "isbn",
                    "as": "livro",
                }
            },
            {
                "$unwind": "$livro"
            },
            {
                "$project": {
                    "_id": 0,
                    "isbn": "$_id",
                    "titulo": "$livro.titulo",
                    "quantidade_emprestimos": 1,
                }
            },
            {
                "$sort": {
                    "quantidade_emprestimos": -1,
                    "titulo": 1,
                }
            },
            {
                "$limit": 5
            },
        ]

        return list(
            self.emprestimos.aggregate(pipeline)
        )

    def emprestimos_por_curso(self):
        pipeline = [
            {
                "$lookup": {
                    "from": "alunos",
                    "localField": "matricula",
                    "foreignField": "matricula",
                    "as": "aluno",
                }
            },
            {
                "$unwind": "$aluno"
            },
            {
                "$group": {
                    "_id": "$aluno.curso",
                    "quantidade": {
                        "$sum": 1
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "curso": "$_id",
                    "quantidade": 1,
                }
            },
            {
                "$sort": {
                    "quantidade": -1,
                    "curso": 1
                }
            },
        ]

        return list(
            self.emprestimos.aggregate(pipeline)
        )

    def alunos_com_emprestimos_atrasados(
        self,
        data_atual=None
    ):
        if data_atual is None:
            data_atual = datetime.now()

        pipeline = [
            {
                "$match": {
                    "data_devolucao": None,
                    "data_prevista": {
                        "$lt": data_atual
                    },
                }
            },
            {
                "$lookup": {
                    "from": "alunos",
                    "localField": "matricula",
                    "foreignField": "matricula",
                    "as": "aluno",
                }
            },
            {
                "$unwind": "$aluno"
            },
            {
                "$lookup": {
                    "from": "livros",
                    "localField": "isbn",
                    "foreignField": "isbn",
                    "as": "livro",
                }
            },
            {
                "$unwind": "$livro"
            },
            {
                "$addFields": {
                    "dias_atraso": {
                        "$dateDiff": {
                            "startDate": "$data_prevista",
                            "endDate": data_atual,
                            "unit": "day",
                        }
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "matricula": 1,
                    "nome": "$aluno.nome",
                    "isbn": 1,
                    "livro": "$livro.titulo",
                    "dias_atraso": 1,
                }
            },
            {
                "$sort": {
                    "dias_atraso": -1
                }
            },
        ]

        return list(
            self.emprestimos.aggregate(pipeline)
        )

    def total_arrecadado_multas(self):
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total": {
                        "$sum": "$multa"
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total": 1,
                }
            },
        ]

        resultado = list(
            self.emprestimos.aggregate(pipeline)
        )

        if not resultado:
            return 0.0

        return float(resultado[0]["total"])