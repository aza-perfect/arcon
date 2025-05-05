# myapp/templatetags/custom_tags.py

from django import template
from django.urls import reverse
from datetime import date

from ..utils import *

register = template.Library()


@register.filter
def is_in_group(user, group_name):
    return user_group_is(user, group_name)


@register.filter
def is_seller_t(user):
    return is_seller(user)


@register.filter
def is_worker_t(user):
    return not (user_group_is(user, 'Quyuvchi') or user_group_is(user, 'Kraskachi'))


@register.filter
def is_quyuvchi(user):
    return not user_group_is(user, 'Quyuvchi')


@register.filter
def is_manager(user):
    return not user_group_is(user, 'Proizvodstvo rahbari')


@register.filter
def is_skladchi(user):
    return not user_group_is(user, 'Skladchi')


@register.filter
def url_n(request, test):
    # name, is_get = test.split(',')
    lst = test.split(',')
    name = lst[0]
    if len(lst) > 1:
        is_get = lst[1]
    else:
        is_get = 0

    if request.resolver_match.view_name == name:
        if not is_get and request.GET.get('stage') != '5':
            return "bg-indigo-100 text-indigo-700"
        if request.GET.get('stage') == '5' and is_get == '5':
            return "bg-indigo-100 text-indigo-700"
        return "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
    else:
        return "text-gray-600 hover:bg-gray-50 hover:text-gray-900"


@register.simple_tag(takes_context=True)
def active(context, view_name, stage=None):
    """
    Возвращает CSS-класс, если текущий view_name совпадает,
    и (опционально) GET-param 'stage' равен переданному.
    """
    req = context['request']
    current = req.resolver_match.view_name
    # если view_name не совпадает — ничего не делаем
    if current != view_name:
        return ''

    get = str(req.GET.get('stage', ''))
    if current == view_name and get == '5' and stage is None:
        return ''
    # если у нас ещё проверяется stage
    if stage is not None:
        if get == str(stage):
            return 'bg-indigo-100 text-indigo-700'
        return ''
    # просто совпадение view_name
    return 'bg-indigo-100 text-indigo-700'


@register.simple_tag(takes_context=True)
def is_filter_m(context):
    req = context['request']
    current = req.resolver_match.view_name
    # если view_name не совпадает — ничего не делаем
    print(current)
    print('test')
    if current == 'production:manager_dashboard':
        return False

    return True


@register.simple_tag
def deadline_class(deadline):
    """
    Возвращает CSS-класс в зависимости от оставшихся дней:
      4 → bg-red-100
      3 → bg-red-200
      2 → bg-red-300
      1 → bg-red-400
      0 или просрочено → bg-red-600 text-white
      None → пустую строку
    """
    if not deadline:
        return ""
    days = (deadline - date.today()).days
    if days >= 4:
        return "bg-red-100"
    elif days == 3:
        return "bg-red-200"
    elif days == 2:
        return "bg-red-300"
    elif days == 1:
        return "bg-red-400"
    else:  # days <= 0
        return "bg-red-600 text-white"
