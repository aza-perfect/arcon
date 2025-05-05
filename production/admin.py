from django.contrib import admin
from .models import *
from .forms import *
from django.contrib.auth.models import Group
from django.utils.html import format_html

admin.site.site_header = "Производство"  # Заголовок в шапке
admin.site.site_title = "Панель администратора"  # Заголовок вкладки браузера
admin.site.index_title = "Добро пожаловать в админку"  # Название главной страницы


@admin.register(Rang)
class RangAdmin(admin.ModelAdmin):
    form = RangForm
    list_display = ('name', 'color_display')

    def color_display(self, obj):
        return format_html(
            '<div style="width: 24px; height: 24px; border-radius: 50%; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )

    color_display.short_description = 'Color'


@admin.register(Mijoz)
class MijozAdmin(admin.ModelAdmin):
    form = MijozForm
    list_display = ['name']


@admin.register(Jarayon)
class JarayonAdmin(admin.ModelAdmin):
    form = JarayonForm
    list_display = ['name', 'order']
    filter_horizontal = ['can_view', 'can_edit']


@admin.register(Mahsulot)
class MahsulotAdmin(admin.ModelAdmin):
    form = MahsulotAdminForm
    list_display = ['name', 'chaxlash', 'lazer', 'default_amount']
    # filter_horizontal = ['style_colors','padosh_colors','rand_colors','jarayonlar']
    filter_horizontal = ['style_colors', 'padosh_colors', 'rand_colors']


@admin.register(Zakaz)
class ZakazAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'quantity', 'status', 'created', 'seller']
    list_filter = ['status', 'created']
    raw_id_fields = ['seller', 'client', 'product', 'style_color', 'padosh_color', 'rand_color']


@admin.register(Sotuv)
class SotuvAdmin(admin.ModelAdmin):
    list_display = ['order', 'quantity', 'approved', 'sold_date', 'approved_date']
    list_filter = ['approved']


@admin.register(Sklad)
class SkladAdmin(admin.ModelAdmin):
    list_display = ['produkt', 'padosh_color', 'style_color', 'rand_color', 'chaxlash', 'quantity']
    list_filter = ['produkt', 'chaxlash']


@admin.register(ZakazProizvodstvo)
class ZakazProizvodstvoAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'created', 'started', 'finished']
    list_filter = ['status']


@admin.register(Proizvodstvo)
class ProizvodstvoAdmin(admin.ModelAdmin):
    list_display = ['zp', 'jarayon', 'quantity', 'brak', 'total_brak']
    list_filter = ['jarayon']
