"""As três tags que fazem os templates genéricos funcionarem.

coluna_valor e coluna_classe são o motor da tabela de crud/list.html: a view declara
as colunas como pares (rótulo, atributo) e estas tags resolvem cada célula, incluindo
os três casos que precisam de formatação (_preco, _duracao, _situacao). Sem elas,
cada entidade precisaria do seu próprio template de lista.
querystring existe para a paginação não perder a busca e o filtro ativos.
"""
from django import template

register = template.Library()


@register.simple_tag
def coluna_valor(obj, attr):
    """Renderiza o valor de uma coluna, tratando colunas especiais."""
    if attr == "_situacao":
        ativo = getattr(obj, "ativo", True)
        return "Ativo" if ativo else "Inativo"
    if attr == "_preco":
        return f"R$ {obj.preco:.2f}".replace(".", ",")
    if attr == "_duracao":
        return f"{obj.duracao_minutos} min"
    valor = getattr(obj, attr, "")
    return valor if valor not in (None, "") else "—"


@register.simple_tag
def coluna_classe(obj, attr):
    """Classe CSS extra para a célula (ex.: badge de situação)."""
    if attr == "_situacao":
        ativo = getattr(obj, "ativo", True)
        return "badge badge-success" if ativo else "badge badge-muted"
    return ""


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """Atualiza a querystring atual preservando os demais parâmetros.

    Existe porque `?page=2` cru apagaria a busca e o filtro de status que o usuário
    acabou de aplicar. Valor vazio remove o parâmetro em vez de deixá-lo pendurado.
    """
    request = context["request"]
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else ""
