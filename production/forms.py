from .models import Rang, Mijoz, Jarayon, Mahsulot, Zakaz, Sotuv, Sklad, ZakazProizvodstvo, Proizvodstvo
from django.contrib.admin import widgets
from django.core.exceptions import ValidationError
from .models import Zakaz, Rang, Mahsulot
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.db.models import Sum


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring focus:border-blue-500',
            'placeholder': 'Имя пользователя',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring focus:border-blue-500',
            'placeholder': 'Пароль',
        })
    )


class RangForm(forms.ModelForm):
    class Meta:
        model = Rang
        fields = ['name', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }
        labels = {
            'name': 'Nomi',
            'color': 'Rangi',
        }


class MijozForm(forms.ModelForm):
    class Meta:
        model = Mijoz
        fields = ['name', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border rounded'}),
            'phone': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border rounded'}),
        }
        labels = {
            'name': 'Ismi',
            'phone': 'Telefon',
        }


class JarayonForm(forms.ModelForm):
    class Meta:
        model = Jarayon
        fields = ['name', 'order', 'can_view', 'can_edit']
        labels = {
            'name': 'Nomi',
            'order': 'Ketmaketligi',
            'can_view': 'Koraoladi',
            'can_edit': 'Ozgartiraoladi',
        }
        widgets = {
            'can_view': forms.CheckboxSelectMultiple,
            'can_edit': forms.CheckboxSelectMultiple,
        }


class MahsulotAdminForm(forms.ModelForm):
    class Meta:
        model = Mahsulot
        fields = [
            'name', 'style_colors', 'padosh_colors', 'rand_colors', 'jarayonlar',
            'chaxlash', 'lazer', 'default_amount',
        ]
        widgets = {
            'style_colors': widgets.FilteredSelectMultiple('Ranglar', is_stacked=False),
            'padosh_colors': widgets.FilteredSelectMultiple('Ranglar', is_stacked=False),
            'rand_colors': widgets.FilteredSelectMultiple('Ranglar', is_stacked=False),
            'jarayonlar': widgets.FilteredSelectMultiple('Jarayonlar', is_stacked=False),
        }


class MahsulotForm(forms.ModelForm):
    class Meta:
        model = Mahsulot
        fields = [
            'name',
            'style_colors',
            'padosh_colors',
            'rand_colors',
            'chaxlash',
            'lazer',
            'jarayonlar',
            # 'default_amount',
        ]
        labels = {
            'name': 'Nomi',
            'style_colors': 'Stilka Ranglari',
            'padosh_colors': 'Padosh Ranglari',
            'rand_colors': 'Rand Ranglari',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-500',
                'placeholder': 'Nomi',
            }),
            'style_colors': forms.SelectMultiple(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-500',
            }),
            'padosh_colors': forms.SelectMultiple(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-500',
            }),
            'rand_colors': forms.SelectMultiple(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-500',
            }),
            'chaxlash': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 rounded focus:ring-blue-500',
            }),
            'lazer': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 rounded focus:ring-blue-500',
            }),
        }


class ZakazForm(forms.ModelForm):
    class Meta:
        model = Zakaz
        # Убрали из полей seller — его задаём в форме-valid
        fields = [
            'client', 'product', 'quantity',
            'style_color', 'padosh_color', 'rand_color',
            'use_lazer', 'use_chaxlash', 'deadline'
        ]
        widgets = {
            'client': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border rounded'
            }),
            'product': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border rounded'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border rounded'
            }),
            'style_color': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border rounded'
            }),
            'padosh_color': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border rounded'
            }),
            'rand_color': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border rounded'
            }),
            'use_lazer': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600'
            }),
            'use_chaxlash': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600'
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'block w-full px-4 py-2 border rounded mt-1 focus:outline-none focus:ring focus:border-blue-500',
                'type': 'date',
                'placeholder': 'dd.mm.YYYY',
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Логика динамической подгрузки цветов по продукту остаётся без изменений...
        # (оставляем ваш текущий __init__, где фильтруются style/padosh/rand)
        if 'product' in self.data:
            try:
                product_id = int(self.data.get('product'))
                self.fields['style_color'].queryset = Rang.objects.filter(
                    id__in=Mahsulot.style_colors.through.objects.filter(
                        mahsulot_id=product_id
                    ).values('rang_id')
                )
                self.fields['padosh_color'].queryset = Rang.objects.filter(
                    id__in=Mahsulot.padosh_colors.through.objects.filter(
                        mahsulot_id=product_id
                    ).values('rang_id')
                )
                self.fields['rand_color'].queryset = Rang.objects.filter(
                    id__in=Mahsulot.rand_colors.through.objects.filter(
                        mahsulot_id=product_id
                    ).values('rang_id')
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            product_id = self.instance.product_id
            self.fields['style_color'].queryset = Rang.objects.filter(
                id__in=Mahsulot.style_colors.through.objects.filter(
                    mahsulot_id=product_id
                ).values('rang_id')
            )
            self.fields['padosh_color'].queryset = Rang.objects.filter(
                id__in=Mahsulot.padosh_colors.through.objects.filter(
                    mahsulot_id=product_id
                ).values('rang_id')
            )
            self.fields['rand_color'].queryset = Rang.objects.filter(
                id__in=Mahsulot.rand_colors.through.objects.filter(
                    mahsulot_id=product_id
                ).values('rang_id')
            )

    def clean(self):
        cleaned = super().clean()
        style = cleaned.get('style_color')
        padosh = cleaned.get('padosh_color')
        # проверяем, что выбран ровно один из двух
        if bool(style) == bool(padosh):
            raise ValidationError("1 tasini tanlang padosh yoki stilka")
        return cleaned


class SkladForm(forms.ModelForm):
    class Meta:
        model = Sklad
        fields = ['produkt', 'style_color', 'padosh_color', 'rand_color', 'chaxlash', 'quantity']


# You can add custom clean() or validation methods to enforce inter-stage constraints.

# === StageProcessForm ===
class StageProcessForm(forms.Form):
    quantity = forms.IntegerField(min_value=0, label="Выполнено")
    brak = forms.IntegerField(min_value=0, label="Брак", required=False)
    rework_stage = forms.ChoiceField(choices=[], required=False, label="Куда вернуть брак")

    def __init__(self, *args, request=None, **kwargs):
        stages = kwargs.pop('stages', [])
        super().__init__(*args, **kwargs)
        self.fields['rework_stage'].choices = stages
        self.fields['quantity'].initial = None
        self.fields['brak'].initial = None
        self.request = request

    def clean(self):
        cleaned = super().clean()
        inc_qty = cleaned.get('quantity') or 0
        inc_brak = cleaned.get('brak') or 0
        proc = getattr(self, 'instance', None)

        if proc:
            order = proc.zp.order
            # список всех этапов для этого продукта
            stages = list(order.product.jarayonlar.all())
            idx1 = stages.index(proc.jarayon)
            if not (
                    self.request.user.is_superuser
                    or self.request.user.groups.filter(
                pk__in=stages[idx1].can_edit.values_list('pk', flat=True)).exists()
            ):
                raise forms.ValidationError("Siz buni ozgartira olmaysiz")
            valid_stages = []
            valid_stages2 = []
            for s in stages[: idx1 + 1]:
                if s.name == 'Lazer' and not order.use_lazer:    continue
                if s.name == 'Chaxlash' and not order.use_chaxlash: continue
                if s.name == 'Rand' and not order.rand_color:   continue
                valid_stages.append((s.pk, s.name))
                valid_stages2.append(s)
            idx = valid_stages2.index(proc.jarayon)

            if idx == 0:
                remaining = proc.zp.order.quantity
            else:
                prev = valid_stages[idx - 1]
                prev_proc = Proizvodstvo.objects.get(zp=proc.zp, jarayon=prev)
                remaining = prev_proc.quantity

            remaining -= proc.quantity
            if inc_qty + inc_brak > remaining:
                raise forms.ValidationError(
                    f"Bajarilganlani va braklani soni yig'indisi  ({inc_qty + inc_brak}) "
                    f"kelgan sondan kop bolishi mumkun emas ({remaining})."
                )
        return cleaned


class SotuvForm(forms.ModelForm):
    class Meta:
        model = Sotuv
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'min': 1,
                'class': 'mt-1 block w-full px-3 py-2 border rounded focus:ring focus:border-green-500'
            }),
        }
        labels = {
            'quantity': 'Soni'
        }

    def __init__(self, *args, request=None, order=None, **kwargs):
        # примем request и order из view
        self.request = request
        self.order = order
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        sold_total = self.order.sotuv_set.aggregate(
            total=Sum('quantity')
        )['total'] or 0
        # print(self.request.user)
        # print(self.order.seller)
        # if not (self.request.user != self.order.seller or self.request.user.is_superuser):
        #     raise forms.ValidationError(
        #         f"Bu sizni Zakazingiz emas"
        #     )
        if self.order.zakazproizvodstvo.quantity < qty:
            raise forms.ValidationError(
                f"Kiritilgan Son Ishlab Chiqilgan Sondan Kop"
            )
        remaining = self.order.zakazproizvodstvo.quantity - sold_total
        if qty > remaining:
            raise forms.ValidationError(
                f"Qolgan Sondan Kop Sotib Bolmaydi: {remaining}"
            )
        return qty

    def save(self, commit=True):
        inst = super().save(commit=False)
        inst.order = self.order
        # если дата ещё не проставлена
        if not inst.sold_date:
            inst.sold_date = timezone.now().date()
        if commit:
            inst.save()
        return inst


class ConfirmSaleForm(forms.ModelForm):
    class Meta:
        model = Sotuv
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'min': 1,
                'class': 'mt-1 block w-full px-3 py-2 border rounded focus:ring focus:border-green-500'
            }),
        }
        labels = {
            'quantity': 'Soni'
        }

    def __init__(self, *args, request=None, order=None, **kwargs):
        # примем request и order из view
        self.request = request
        self.order = order
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        sold_total = self.order.sotuv_set.aggregate(
            total=Sum('quantity')
        )['total'] or 0
        if self.request.user != self.order.seller:
            raise forms.ValidationError(
                f"Bu sizni Zakazingiz emas"
            )
        if self.order.zakazproizvodstvo.quantity < qty:
            raise forms.ValidationError(
                f"Kiritilgan Son Ishlab Chiqilgan Sondan Kop"
            )
        remaining = self.order.zakazproizvodstvo.quantity - sold_total
        if qty > remaining:
            raise forms.ValidationError(
                f"Qolgan Sondan Kop Sotib Bolmaydi: {remaining}"
            )
        return qty

    def save(self, commit=True):
        inst = super().save(commit=False)
        inst.order = self.order
        # если дата ещё не проставлена
        if not inst.sold_date:
            inst.sold_date = timezone.now().date()
        if commit:
            inst.save()
        return inst
