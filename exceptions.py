class BibliotecaError(Exception):
    """Classe base para os erros de negócio da biblioteca."""
    pass


class LivroNaoEncontrado(BibliotecaError):
    pass


class LivroDuplicado(BibliotecaError):
    pass


class LivroComEmprestimoAberto(BibliotecaError):
    pass


class LivroIndisponivel(BibliotecaError):
    pass


class AlunoNaoEncontrado(BibliotecaError):
    pass


class AlunoDuplicado(BibliotecaError):
    pass


class EmailInvalido(BibliotecaError):
    pass


class LimiteEmprestimos(BibliotecaError):
    pass


class AlunoComAtraso(BibliotecaError):
    pass


class EmprestimoNaoEncontrado(BibliotecaError):
    pass


class EmprestimoJaDevolvido(BibliotecaError):
    pass


class DadosInvalidos(BibliotecaError):
    pass