"""Filtros e tags auxiliares de template."""
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
    """Atualiza a querystring atual preservando os demais parâmetros."""
    request = context["request"]
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else ""
