from django.db.models import Sum, F, Q, Value, Count, IntegerField
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, FormView, RedirectView, TemplateView
)
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormMixin
from django.views import View
from django.contrib.auth import get_user_model
from .models import (
    Rang, Mijoz, Jarayon, Mahsulot,
    Zakaz, Sotuv, Sklad,
    ZakazProizvodstvo, Proizvodstvo
)
from .forms import (
    RangForm, MijozForm, JarayonForm,
    MahsulotForm, ZakazForm,
    SkladForm, StageProcessForm, SotuvForm
)
from django.contrib import messages
from .utils import *
from django.core.exceptions import PermissionDenied

User = get_user_model()
valid_groups = ['Sotuvchi', 'Skladchi', 'Proizvodstvo rahbari']


def global_context(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    jarayons = Jarayon.objects.all()
    worker = True
    for i in user_groups:
        if i in valid_groups:
            worker = False
            break
    if request.user.is_superuser: worker = False
    return {
        'is_worker': worker,
        'is_admin': request.user.is_superuser,
        'user_groups': user_groups,
        'jarayons': jarayons,
    }


def to_int_list(a):
    try:
        return list(map(int, a))
    except ValueError:
        return []


# — DASHBOARD REDIRECT —
class DashboardRedirect(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        user = request.user
        # Проверяем группу и редиректим
        if is_seller(user) or user.is_superuser:
            return redirect('production:seller_dashboard')
        elif user_group_is(user, 'Proizvodstvo rahbari'):
            return redirect('production:manager_dashboard')
        elif user_group_is(user, 'Skladchi'):
            return HttpResponseRedirect(f"{reverse('production:worker_dashboard')}?stage=5")
        # Если никому не подошли — на логин
        return redirect('production:worker_dashboard')


class SellerDashboard(LoginRequiredMixin, ListView):
    model = Zakaz
    template_name = 'production/seller.html'
    context_object_name = 'data'

    def get_queryset(self):
        qs = Zakaz.objects.select_related('client', 'product', 'seller', 'zakazproizvodstvo')

        # 2) Только свои, если не суперпользователь
        if not self.request.user.is_superuser:
            qs = qs.filter(seller=self.request.user)

        # 3) Применяем GET-фильтры
        clients = self.request.GET.getlist('client')
        products = self.request.GET.getlist('product')
        seller_ids = self.request.GET.getlist('seller')

        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if clients:
            qs = qs.filter(client_id__in=clients)
        if products:
            qs = qs.filter(product_id__in=products)
        if seller_ids:
            qs = qs.filter(seller_id__in=seller_ids)
        if date_from:
            qs = qs.filter(created__gte=date_from)
        if date_to:
            qs = qs.filter(created__lte=date_to)

        # 4) Аннотируем sold, produced и вычисляем received = produced − sold
        qs = qs.annotate(
            sold=Coalesce(
                Sum('sotuv__quantity', filter=Q(sotuv__approved=True)),
                Value(0),
                output_field=IntegerField(),
            ),
            produced=Coalesce(
                F('zakazproizvodstvo__quantity'),
                Value(0),
                output_field=IntegerField(),
            )
        ).annotate(
            received=F('produced') - F('sold')
        )

        # 5) Убираем те, что уже полностью проданы
        qs = qs.filter(~Q(sold=F('quantity')))

        # 6) Сортируем по ID
        return qs.order_by('id')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Списки для фильтров
        ctx['clients'] = Mijoz.objects.order_by('name')
        ctx['products'] = Mahsulot.objects.order_by('name')
        ctx['sellers'] = User.objects.filter(groups__name='Sotuvchi').order_by('username')
        # Текущие GET-параметры, чтобы сохранить выбранные значения
        ctx['filter'] = {
            k: self.request.GET.get(k, '')
            for k in ('client', 'product', 'seller', 'date_from', 'date_to')
        }
        queryset = ctx['data']

        ctx['selected_clients'] = to_int_list(self.request.GET.getlist('client'))
        ctx['selected_products'] = to_int_list(self.request.GET.getlist('product'))
        ctx['selected_sellers'] = to_int_list(self.request.GET.getlist('seller'))

        totals = queryset.aggregate(
            zakaz_count=Count('id'),
            total_received=Sum('received'),
            total_sold=Sum('sold'),
            total_quantity=Sum('quantity'),
        )
        ctx['totals'] = totals
        return ctx


class SotuvList(LoginRequiredMixin, TemplateView):
    template_name = 'production/sotuv_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if is_seller(user):
            data = Sotuv.objects.filter(order__seller=user).order_by('-sold_date')
        else:
            data = Sotuv.objects.filter().order_by('-sold_date')

        context['data'] = data
        return context


class ManagerDashboard(LoginRequiredMixin, TemplateView):
    template_name = 'production/manager.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Показываем все заказы, или фильтр по status="Yangi"
        # 3) Применяем GET-фильтры
        data = Zakaz.objects.exclude(status='Otmen').filter(zakazproizvodstvo__finished=None)
        products = self.request.GET.getlist('product')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if products:
            data = data.filter(product_id__in=products)
        if date_from:
            data = data.filter(created__gte=date_from)
        if date_to:
            data = data.filter(created__lte=date_to)

        ctx['data'] = data.order_by('id')
        ctx['clients'] = None
        ctx['products'] = Mahsulot.objects.order_by('name')
        ctx['sellers'] = None
        ctx['selected_products'] = to_int_list(self.request.GET.getlist('product'))

        return ctx


# production/views.py
class WorkerDashboard(LoginRequiredMixin, TemplateView):
    template_name = 'production/worker.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user_groups = self.request.user.groups.all()
        stage_id = self.request.GET.get('stage')
        if not stage_id:
            jar = Jarayon.objects.filter(can_edit__in=user_groups)
            stage_id = jar[0].id
            ctx['name_j'] = jar[0].name
        else:
            ctx['name_j'] = Jarayon.objects.filter(id=stage_id)[0].name

        # Общий QuerySet
        procs = Proizvodstvo.objects.filter(
            zp__status='Bajarilmoqda',
            jarayon_id=stage_id,
        ).select_related('zp__order', 'jarayon').order_by('zp__order__id')

        tasks = []
        for proc in procs:
            order = proc.zp.order
            name = proc.jarayon.name

            # Сразу отключаем ненужные этапы:
            if name == 'Lazer' and not order.use_lazer:
                continue
            if name == 'Chaxlash' and not order.use_chaxlash:
                continue
            if name == 'Rand' and not order.rand_color:
                continue

            # Теперь расчёты как раньше:
            done = proc.quantity
            total = order.quantity
            remaining = total - done
            if remaining == 0: continue

            # rework choices: тоже берём только релевантные
            stages = list(order.product.jarayonlar.all())
            idx1 = stages.index(proc.jarayon)

            valid_stages = []
            valid_stages2 = []
            for s in stages[: idx1 + 1]:
                if s.name == 'Lazer' and not order.use_lazer:    continue
                if s.name == 'Chaxlash' and not order.use_chaxlash: continue
                if s.name == 'Rand' and not order.rand_color:   continue
                valid_stages.append((s.pk, s.name))
                valid_stages2.append(s)
            idx = valid_stages2.index(proc.jarayon)
            # incoming
            if idx > 0:
                prev = valid_stages[idx - 1]
                prev_proc = Proizvodstvo.objects.get(zp=proc.zp, jarayon=prev)
                incoming = prev_proc.quantity
                if incoming == 0 or incoming == done: continue
                incoming -= done
            else:
                incoming = 0

            form = StageProcessForm(stages=valid_stages)

            tasks.append({
                'proc': proc,
                'incoming': incoming,
                'done': done,
                'remaining': remaining,
                'total': total,
                'form': form,
            })

        ctx['tasks'] = tasks
        return ctx


class RangList(LoginRequiredMixin, ListView):
    model = Rang
    template_name = 'production/rang_list.html'


class RangCreate(LoginRequiredMixin, CreateView):
    model = Rang
    form_class = RangForm
    template_name = 'production/rang_form.html'
    success_url = reverse_lazy('production:rang_list')


class RangUpdate(LoginRequiredMixin, UpdateView):
    model = Rang
    form_class = RangForm
    template_name = 'production/rang_form.html'
    success_url = reverse_lazy('production:rang_list')


class MijozUpdate(LoginRequiredMixin, UpdateView):
    model = Mijoz
    form_class = MijozForm
    template_name = 'production/mijoz_form.html'
    success_url = reverse_lazy('production:mijoz_list')


class JarayonList(LoginRequiredMixin, ListView):
    model = Jarayon
    template_name = 'production/jarayon_list.html'


class JarayonCreate(LoginRequiredMixin, CreateView):
    model = Jarayon
    form_class = JarayonForm
    template_name = 'production/jarayon_form.html'
    success_url = reverse_lazy('production:jarayon_list')


class JarayonUpdate(LoginRequiredMixin, UpdateView):
    model = Jarayon
    form_class = JarayonForm
    template_name = 'production/jarayon_form.html'
    success_url = reverse_lazy('production:jarayon_list')


class SkladList(LoginRequiredMixin, ListView):
    model = Sklad
    template_name = 'production/sklad_list.html'


class SkladCreate(LoginRequiredMixin, CreateView):
    model = Sklad
    form_class = SkladForm
    template_name = 'production/sklad_form.html'
    success_url = reverse_lazy('production:sklad_list')


class SkladUpdate(LoginRequiredMixin, UpdateView):
    model = Sklad
    form_class = SkladForm
    template_name = 'production/sklad_form.html'
    success_url = reverse_lazy('production:sklad_list')


class ZakazCreate(LoginRequiredMixin, CreateView):
    model = Zakaz
    form_class = ZakazForm
    template_name = 'production/zakaz_form.html'
    success_url = reverse_lazy('production:seller_dashboard')

    def form_valid(self, form):
        # seller = текущий пользователь
        form.instance.seller = self.request.user
        return super().form_valid(form)


class ZakazDetail(LoginRequiredMixin, DetailView):
    model = Zakaz
    template_name = 'production/zakaz_detail.html'
    context_object_name = 'zakaz'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        zakaz = self.object

        # Попробуем достать связанное производство
        try:
            zp = zakaz.zakazproizvodstvo
        except ZakazProizvodstvo.DoesNotExist:
            zp = None
        ctx['zp'] = zp

        # Если оно есть — вытянем все этапы
        if zp:
            ctx['stages'] = stages = (
                zp.proizvodstvo_set
                .select_related('jarayon')
                .order_by('jarayon__order')
            )
            total = 0
            for i in stages:
                total += i.total_brak
            ctx['brak_total'] = total
        else:
            ctx['stages'] = []
            ctx['brak_total'] = 0

        ctx['sales'] = zakaz.sotuv_set.order_by('sold_date')

        return ctx


class ZakazUpdate(LoginRequiredMixin, UpdateView):
    model = Zakaz
    form_class = ZakazForm
    template_name = 'production/zakaz_form.html'
    success_url = reverse_lazy('production:zakaz_list')


class ZakazStartProduction(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        zakaz = get_object_or_404(Zakaz, pk=kwargs['zakaz_pk'])
        zp = get_object_or_404(ZakazProizvodstvo, order=zakaz)

        if not (user_group_is(self.request.user, 'Proizvodstvo rahbari') or self.request.user.is_superuser):
            # если нет — сразу 403
            raise PermissionDenied("У вас нет прав.")

        # только если ещё не начали
        if zp.status == 'Yangi':
            zp.status = 'Bajarilmoqda'
            zp.started = timezone.now().date()
            zp.save()

            # Создаём только первый этап:
            first_stage = zakaz.product.jarayonlar.first()
            Proizvodstvo.objects.create(
                zp=zp,
                jarayon=first_stage,
                started=timezone.now().date(),
                quantity=0,
                brak=0,
                total_brak=0
            )
        # после запуска показываем деталь
        return reverse('production:manager_dashboard')


class StageProcess(LoginRequiredMixin, FormView):
    template_name = 'production/stage_form.html'
    form_class = StageProcessForm

    def dispatch(self, request, *args, **kwargs):
        self.zp, self.stage = None, None
        self.zp = get_object_or_404(ZakazProizvodstvo, pk=kwargs['zp_pk'])
        self.stage = get_object_or_404(Jarayon, pk=kwargs['jarayon_pk'])
        # создаём или получаем текущий этап
        self.proc, _ = Proizvodstvo.objects.get_or_create(
            zp=self.zp, jarayon=self.stage,
            defaults={'quantity': 0, 'brak': 0, 'total_brak': 0}
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        all_stages = list(self.zp.order.product.jarayonlar.all())
        # отфильтруем ненужные для всего этого заказа
        order = self.zp.order
        stages = [
            s for s in all_stages
            if not (s.name == 'Lazer' and not order.use_lazer)
               and not (s.name == 'Chaxlash' and not order.use_chaxlash)
               and not (s.name == 'Rand' and not order.rand_color)
        ]

        idx = stages.index(self.stage)
        # передаём только предыдущие релевантные
        kwargs['stages'] = [(s.pk, s.name) for s in stages[: idx + 1]]
        kwargs['request'] = self.request
        return kwargs

    def get_form(self, form_class=None):

        form = super().get_form(form_class)
        # привязываем proc к форме
        form.instance = self.proc
        return form

    def form_invalid(self, form):
        # выводим ошибки через сообщения и редиректим
        for field, errs in form.errors.items():
            label = form.fields[field].label if field in form.fields else ''
            for e in errs:
                messages.error(self.request, f"{e}")

        referer = self.request.META.get('HTTP_REFERER')

        # Если есть, то редиректим на неё
        if referer:
            return redirect(referer)

        # Если нет, редиректим на главную страницу (или на другой URL по умолчанию)
        return redirect('production:dashboard')

    def form_valid(self, form):
        qty = form.cleaned_data['quantity']
        brak = form.cleaned_data['brak'] or 0
        rerpk = form.cleaned_data.get('rework_stage')

        # обновляем накопленные значения
        self.proc.quantity += qty
        self.proc.total_brak += brak
        self.proc.save()

        # передаём qty на следующий этап
        stages = list(self.zp.order.product.jarayonlar.all())
        # список уже отфильтрованных этапов
        all_stages = [s for s in list(self.zp.order.product.jarayonlar.all())
                      if not (s.name == 'Lazer' and not self.zp.order.use_lazer)
                      and not (s.name == 'Chaxlash' and not self.zp.order.use_chaxlash)
                      and not (s.name == 'Rand' and not self.zp.order.rand_color)
                      ]
        idx = all_stages.index(self.stage)
        # следующий этап
        if qty > 0 and idx + 1 < len(all_stages):
            nxt = all_stages[idx + 1]
            next_proc, _ = Proizvodstvo.objects.get_or_create(
                zp=self.zp, jarayon=nxt,
                defaults={'quantity': 0, 'brak': 0, 'total_brak': 0}
            )
            next_proc.save()

        if self.stage == stages[-1]:
            self.zp.quantity = self.proc.quantity
            if self.proc.quantity == self.zp.order.quantity:
                self.zp.finished = timezone.now().date()
                self.zp.status = 'Bajarildi'
            self.zp.save()

        # возвращаем brak на выбранный этап
        if brak and rerpk:
            rer_stage = get_object_or_404(Jarayon, pk=rerpk)
            for i in range(rer_stage.id, self.stage.id):
                rer_proc, _ = Proizvodstvo.objects.get_or_create(
                    zp=self.zp, jarayon=stages[i - 1],
                    defaults={'quantity': 0, 'brak': 0, 'total_brak': 0}
                )
                rer_proc.quantity -= brak
                rer_proc.finished = None
                rer_proc.save()

        return super().form_valid(form)

    def get_success_url(self):
        referer = self.request.META.get('HTTP_REFERER')
        if referer:
            return referer
        return reverse('production:worker_dashboard')


class ZakazSalesView(LoginRequiredMixin, FormMixin, DetailView):
    model = Zakaz
    template_name = 'production/sotuv.html'
    context_object_name = 'zakaz'
    form_class = SotuvForm

    def get_success_url(self):
        return reverse('production:zakaz_sales', args=[self.object.pk])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # передаём заказ в форму, чтобы clean_quantity работал правильно
        kwargs['order'] = self.get_object()
        kwargs['request'] = self.request
        return kwargs

    def post(self, request, *args, **kwargs):
        # обязательно установить self.object до работы с FormMixin
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        # super() здесь уже отработает DetailView.get_context_data
        ctx = super().get_context_data(**kwargs)
        zakaz = self.object
        ctx['sales'] = zakaz.sotuv_set.order_by('sold_date')
        ctx['total'] = total = zakaz.sotuv_set.aggregate(total=Sum('quantity'))['total'] or 0
        ctx['incoming'] = zakaz.zakazproizvodstvo.quantity - total
        ctx['remaining'] = zakaz.quantity - total
        return ctx


class WarehouseConfirmList(LoginRequiredMixin, ListView):
    model = Sotuv
    template_name = 'production/sklad_check.html'
    context_object_name = 'sales'

    def get_queryset(self):
        queryset = Sotuv.objects.filter(approved=False) \
            .select_related('order__client', 'order__product', 'order__seller') \
            .order_by('sold_date')

        for sale in queryset:
            # Добавляем атрибут вручную
            sale.remaining = sale.order.quantity - sale.quantity

        return queryset


class ConfirmSale(LoginRequiredMixin, View):

    def post(self, request, pk):
        sale = get_object_or_404(Sotuv, pk=pk, approved=False)

        if not (user_group_is(request.user, 'Skladchi') or request.user.is_superuser):
            # если нет — сразу 403
            raise PermissionDenied("У вас нет прав для подтверждения продажи.")

        sale.approved = True
        sale.approved_date = timezone.now().date()
        sale.save()

        # 4) Обновляем связанный заказ
        zakaz = sale.order

        # Считаем, сколько уже всего продано (approved=True)
        total_sold = zakaz.sotuv_set.filter(
            approved=True
        ).aggregate(total=Sum('quantity'))['total'] or 0

        # Если продано ровно столько, сколько заказано — ставим «Sotildi»
        if total_sold >= zakaz.quantity:
            zakaz.status = 'Sotildi'
            zakaz.finished = timezone.now().date()
        # Если хоть что-то продано, но меньше всего заказа — «Qisman Sotildi»
        elif total_sold > 0:
            # переводим в Qisman Sotildi только если ещё был «Yangi»
            if zakaz.status == 'Yangi':
                zakaz.status = 'Qisman Sotildi'
                zakaz.partial = timezone.now().date()
        # Иначе — оставляем статус без изменений (например, если все продажи отменены)

        zakaz.save()
        # total = zakaz.sotuv_set.aggregate(total=Sum('quantity'))['total'] or 0

        return redirect('production:warehouse_confirmations')


class Table(LoginRequiredMixin, FormView):
    template_name = 'production/table.html'
    form_class = StageProcessForm


class ClientDashboard(LoginRequiredMixin, ListView):
    model = Mijoz
    template_name = 'production/client.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        qs = Mijoz.objects.all()

        qs = qs.annotate(
            total_orders=Count('zakaz', distinct=True),
            completed_orders=Count(
                'zakaz',
                filter=Q(
                    zakaz__sotuv__approved=True,
                ),
                distinct=True
            ),
            total_qty=Coalesce(Sum('zakaz__quantity'), Value(0), output_field=IntegerField()),
            sold_qty=Coalesce(
                Sum('zakaz__sotuv__quantity', filter=Q(zakaz__sotuv__approved=True)),
                Value(0),
                output_field=IntegerField()
            )
        )

        # Если хотите только клиентов с хотя бы одним заказом:
        # qs = qs.filter(total_orders__gt=0)

        return qs.order_by('id')


class ZakazList(LoginRequiredMixin, ListView):
    model = Zakaz
    template_name = 'production/zakaz_list.html'
    context_object_name = 'data'

    def get_queryset(self, *args, **kwargs):
        qs = Zakaz.objects.all()
        # Фильтр по продукту из GET
        product_id = self.request.GET.get('product')
        client_id = self.request.GET.get('client')
        if product_id:
            qs = qs.filter(product__pk=product_id)
        if client_id:
            qs = qs.filter(client__pk=client_id)

        return qs.order_by('id')


class MijozCreate(LoginRequiredMixin, CreateView):
    model = Mijoz
    form_class = MijozForm
    template_name = 'production/mijoz_form.html'
    success_url = reverse_lazy('production:mijoz')

    def dispatch(self, request, *args, **kwargs):
        # пропускаем только admin и группу «Sotuvchi»
        seller = request.user.groups.filter(name='Sotuvchi').exists()
        if not (request.user.is_superuser or seller):
            raise PermissionDenied("У вас нет прав для добавления клиента.")
        return super().dispatch(request, *args, **kwargs)


class MijozUpdate(LoginRequiredMixin, UpdateView):
    model = Mijoz
    form_class = MijozForm
    template_name = 'production/mijoz_form.html'
    success_url = reverse_lazy('production:mijoz')

    def dispatch(self, request, *args, **kwargs):
        # только superuser или Sotuvchi
        is_seller = request.user.groups.filter(name='Sotuvchi').exists()
        if not (request.user.is_superuser or is_seller):
            raise PermissionDenied("У вас нет прав на редактирование клиента.")
        return super().dispatch(request, *args, **kwargs)


# 1) Список продуктов
class MahsulotList(LoginRequiredMixin, TemplateView):
    template_name = "production/mahsulot_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        products = Mahsulot.objects.all()
        stats = []

        for p in products:
            # все заказы на этот продукт
            qs_orders = Zakaz.objects.filter(product=p)

            # 1) Всего заказов (по количеству записей Zakaz)
            order_count = qs_orders.count()

            # 2) Сколько из них уже «завершены» (например, когда произведено ≥ заказанного)
            completed_orders = qs_orders.filter(finished__isnull=False).count()

            # 3) Суммы по количествам, как было:
            total_ordered = qs_orders.aggregate(sum=Sum("quantity"))["sum"] or 0
            total_produced = qs_orders.aggregate(sum=Sum("zakazproizvodstvo__quantity"))["sum"] or 0
            total_sold = Sotuv.objects.filter(
                order__product=p, approved=True
            ).aggregate(sum=Sum("quantity"))["sum"] or 0

            # 4) Сколько у него уникальных клиентов
            unique_clients = qs_orders.values("client").distinct().count()

            # 5) Разбивка по продавцам (sold/ordered)
            sellers = (
                qs_orders.values("seller")
                .distinct()
                .order_by("seller")
                .annotate(
                    ordered=Sum("quantity"),
                    sold=Sum(
                        F("sotuv__quantity"),
                        filter=F("sotuv__approved") == True
                    )
                )
            )

            seller_stats = []
            for s in sellers:
                user = User.objects.get(pk=s["seller"])
                seller_stats.append({
                    "name": user.get_full_name() or user.username,
                    "ordered": s["ordered"] or 0,
                    "sold": s["sold"] or 0,
                })

            stats.append({
                "product": p,
                "order_count": order_count,
                "completed_orders": completed_orders,
                "total_ordered": total_ordered,
                "total_produced": total_produced,
                "total_sold": total_sold,
                "unique_clients": unique_clients,
                "seller_stats": seller_stats,
                # по аналогии можно и клиентские продажи/заказы на уровне клиента
            })

        ctx["stats"] = stats
        return ctx


# 2) Создание — только для админа ИЛИ группы «Rukovoditel»
class MahsulotCreate(LoginRequiredMixin, CreateView):
    model = Mahsulot
    form_class = MahsulotForm
    template_name = 'production/mahsulot_form.html'
    success_url = reverse_lazy('production:mahsulot_list')

    def dispatch(self, request, *args, **kwargs):
        # is_manager = request.user.groups.filter(name='Rukovoditel').exists()
        # if not (request.user.is_superuser or is_manager):
        #     raise PermissionDenied("У вас нет прав для добавления продукта.")
        return super().dispatch(request, *args, **kwargs)


# 3) Редактирование — те же права
class MahsulotUpdate(LoginRequiredMixin, UpdateView):
    model = Mahsulot
    form_class = MahsulotForm
    template_name = 'production/mahsulot_form.html'
    success_url = reverse_lazy('production:mahsulot_list')

    def dispatch(self, request, *args, **kwargs):
        # is_manager = request.user.groups.filter(name='Rukovoditel').exists()
        # if not (request.user.is_superuser or is_manager):
        #     raise PermissionDenied("У вас нет прав для редактирования продукта.")
        return super().dispatch(request, *args, **kwargs)
