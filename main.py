from bson import ObjectId

from db import inicializar_banco
from service import BibliotecaService
from exceptions import BibliotecaError


def linha():
    print("=" * 70)


def mostrar_livro(livro):
    print(
        f'ISBN: {livro["isbn"]} | '
        f'Título: {livro["titulo"]} | '
        f'Autor: {livro["autor"]} | '
        f'Categoria: {livro["categoria"]} | '
        f'Disponíveis: {livro["exemplares_disponiveis"]}/'
        f'{livro["exemplares_total"]}'
    )


def cadastrar_livro(service):
    print("\nCADASTRO DE LIVRO")

    isbn = input("ISBN: ").strip()
    titulo = input("Título: ").strip()
    autor = input("Autor: ").strip()
    ano = int(input("Ano: "))
    categoria = input("Categoria: ").strip()
    exemplares = int(input("Quantidade de exemplares: "))

    service.cadastrar_livro(
        isbn,
        titulo,
        autor,
        ano,
        categoria,
        exemplares
    )

    print("\nLivro cadastrado com sucesso!")


def buscar_livro_isbn(service):
    isbn = input("Digite o ISBN: ").strip()

    livro = service.buscar_livro_por_isbn(isbn)

    print()
    mostrar_livro(livro)


def listar_livros(service):
    livros = service.listar_livros()

    if not livros:
        print("\nNenhum livro cadastrado.")
        return

    print("\nLIVROS CADASTRADOS")

    for livro in livros:
        mostrar_livro(livro)


def atualizar_livro(service):
    isbn = input("ISBN do livro: ").strip()

    print("\nDeixe vazio o campo que não deseja alterar.")

    titulo = input("Novo título: ").strip()
    autor = input("Novo autor: ").strip()
    ano = input("Novo ano: ").strip()
    categoria = input("Nova categoria: ").strip()

    dados = {}

    if titulo:
        dados["titulo"] = titulo

    if autor:
        dados["autor"] = autor

    if ano:
        dados["ano"] = int(ano)

    if categoria:
        dados["categoria"] = categoria

    livro = service.atualizar_livro(isbn, dados)

    print("\nLivro atualizado com sucesso!")
    mostrar_livro(livro)


def remover_livro(service):
    isbn = input("ISBN: ").strip()

    service.remover_livro(isbn)

    print("\nLivro removido com sucesso!")


def cadastrar_aluno(service):
    print("\nCADASTRO DE ALUNO")

    matricula = input("Matrícula: ").strip()
    nome = input("Nome: ").strip()
    curso = input("Curso: ").strip()
    email = input("E-mail: ").strip()

    service.cadastrar_aluno(
        matricula,
        nome,
        curso,
        email
    )

    print("\nAluno cadastrado com sucesso!")


def buscar_aluno(service):
    matricula = input("Matrícula: ").strip()

    aluno = service.buscar_aluno_por_matricula(matricula)

    print(
        f'\nMatrícula: {aluno["matricula"]} | '
        f'Nome: {aluno["nome"]} | '
        f'Curso: {aluno["curso"]} | '
        f'E-mail: {aluno["email"]}'
    )


def pesquisar_livros(service):
    print("\nBUSCA DE LIVROS")

    termo = input(
        "Parte do título ou autor (Enter para ignorar): "
    ).strip()

    categoria = input(
        "Categoria (Enter para todas): "
    ).strip()

    livros = service.buscar_livros(
        termo=termo or None,
        categoria=categoria or None
    )

    if not livros:
        print("\nNenhum livro encontrado.")
        return

    print("\nRESULTADOS")

    for livro in livros:
        mostrar_livro(livro)


def emprestar(service):
    print("\nNOVO EMPRÉSTIMO")

    isbn = input("ISBN: ").strip()
    matricula = input("Matrícula: ").strip()

    emprestimo = service.emprestar_livro(
        isbn,
        matricula
    )

    print("\nEmpréstimo realizado com sucesso!")
    print(f'ID do empréstimo: {emprestimo["_id"]}')
    print(f'Data do empréstimo: {emprestimo["data_emprestimo"]}')
    print(f'Data prevista: {emprestimo["data_prevista"]}')


def devolver(service):
    print("\nDEVOLUÇÃO")

    id_emprestimo = input(
        "ID do empréstimo: "
    ).strip()

    resultado = service.devolver_livro(
        ObjectId(id_emprestimo)
    )

    print("\nDevolução realizada com sucesso!")
    print(
        f'Dias de atraso: {resultado["dias_atraso"]}'
    )
    print(
        f'Multa: R$ {resultado["multa"]:.2f}'
    )


def relatorios(service):
    while True:
        linha()
        print("RELATÓRIOS")
        linha()

        print("1 - Top 5 livros mais emprestados")
        print("2 - Quantidade de empréstimos por curso")
        print("3 - Alunos com empréstimos atrasados")
        print("4 - Total arrecadado em multas")
        print("0 - Voltar")

        opcao = input("\nEscolha uma opção: ").strip()

        try:
            if opcao == "1":
                resultados = (
                    service.top_5_livros_mais_emprestados()
                )

                print("\nTOP 5 LIVROS MAIS EMPRESTADOS")

                if not resultados:
                    print("Nenhum empréstimo encontrado.")

                for item in resultados:
                    print(
                        f'{item["titulo"]} | '
                        f'ISBN: {item["isbn"]} | '
                        f'Empréstimos: '
                        f'{item["quantidade_emprestimos"]}'
                    )

            elif opcao == "2":
                resultados = service.emprestimos_por_curso()

                print("\nEMPRÉSTIMOS POR CURSO")

                if not resultados:
                    print("Nenhum empréstimo encontrado.")

                for item in resultados:
                    print(
                        f'{item["curso"]}: '
                        f'{item["quantidade"]}'
                    )

            elif opcao == "3":
                resultados = (
                    service.alunos_com_emprestimos_atrasados()
                )

                print("\nEMPRÉSTIMOS ATRASADOS")

                if not resultados:
                    print("Nenhum empréstimo atrasado.")

                for item in resultados:
                    print(
                        f'Aluno: {item["nome"]} | '
                        f'Livro: {item["livro"]} | '
                        f'Dias de atraso: '
                        f'{item["dias_atraso"]}'
                    )

            elif opcao == "4":
                total = service.total_arrecadado_multas()

                print(
                    f"\nTotal arrecadado: R$ {total:.2f}"
                )

            elif opcao == "0":
                break

            else:
                print("\nOpção inválida.")

        except BibliotecaError as erro:
            print(f"\nERRO: {erro}")


def menu():
    db = inicializar_banco()
    service = BibliotecaService(db)

    while True:
        print()
        linha()
        print("SISTEMA DE EMPRÉSTIMO DE LIVROS")
        linha()

        print("1  - Cadastrar livro")
        print("2  - Buscar livro por ISBN")
        print("3  - Listar livros")
        print("4  - Atualizar livro")
        print("5  - Remover livro")
        print("6  - Cadastrar aluno")
        print("7  - Buscar aluno pela matrícula")
        print("8  - Pesquisar livros")
        print("9  - Emprestar livro")
        print("10 - Devolver livro")
        print("11 - Relatórios")
        print("0  - Sair")

        opcao = input(
            "\nEscolha uma opção: "
        ).strip()

        try:
            if opcao == "1":
                cadastrar_livro(service)

            elif opcao == "2":
                buscar_livro_isbn(service)

            elif opcao == "3":
                listar_livros(service)

            elif opcao == "4":
                atualizar_livro(service)

            elif opcao == "5":
                remover_livro(service)

            elif opcao == "6":
                cadastrar_aluno(service)

            elif opcao == "7":
                buscar_aluno(service)

            elif opcao == "8":
                pesquisar_livros(service)

            elif opcao == "9":
                emprestar(service)

            elif opcao == "10":
                devolver(service)

            elif opcao == "11":
                relatorios(service)

            elif opcao == "0":
                print("\nSistema encerrado.")
                break

            else:
                print("\nOpção inválida.")

        except BibliotecaError as erro:
            print(f"\nERRO: {erro}")

        except ValueError:
            print(
                "\nERRO: valor digitado inválido."
            )

        except Exception as erro:
            print(
                f"\nERRO inesperado: {erro}"
            )


if __name__ == "__main__":
    menu()