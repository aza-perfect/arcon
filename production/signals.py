from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Zakaz, ZakazProizvodstvo, Proizvodstvo, Jarayon

@receiver(pre_save, sender=Zakaz)
def stamp_dates_on_status(sender, instance, **kwargs):
    if not instance.pk:
        return
    old = Zakaz.objects.get(pk=instance.pk)
    if old.status != instance.status:
        if instance.status == "Sotildi":
            instance.finished = timezone.now().date()
        elif instance.status == "Qisman Sotildi":
            instance.partial = timezone.now().date()

@receiver(post_save, sender=Zakaz)
def create_proizvodstvo_for_order(sender, instance, created, **kwargs):
    if created:
        ZakazProizvodstvo.objects.create(
            order=instance,
            created=instance.created,
            quantity=0
        )

@receiver(pre_save, sender=ZakazProizvodstvo)
def stamp_zp_dates(sender, instance, **kwargs):
    if instance.pk:
        old = ZakazProizvodstvo.objects.get(pk=instance.pk)
        if old.status != instance.status:
            if instance.status == "Bajarilmoqda":
                instance.started = timezone.now().date()
            elif instance.status == "Bajarildi":
                instance.finished = timezone.now().date()

# @receiver(post_save, sender=ZakazProizvodstvo)
# def kickoff_stages(sender, instance, **kwargs):
#     if instance.status == "Bajarilmoqda" and not Proizvodstvo.objects.filter(zp=instance).exists():
#         # create one Proizvodstvo per stage on start
#         for mj in instance.order.product.mahsulotjarayon_set.all():
#             Proizvodstvo.objects.create(
#                 zp=instance,
#                 jarayon=mj.jarayon,
#                 quantity=0
#             )

@receiver(pre_save, sender=Proizvodstvo)
def validate_pass_down(sender, instance, **kwargs):

    # Enforce quantity ≤ previous stage and ≤ order quantity, plus handle rerouting of brak.
    if instance.pk:
        old = Proizvodstvo.objects.get(pk=instance.pk)
        if instance.quantity > instance.zp.order.quantity:
            raise ValueError("Cannot process more than total ordered")
        # here you could also find the previous stage, compare instance.quantity + instance.brak, etc.

@receiver(pre_save, sender=Proizvodstvo)
def stamp_start_and_finish(sender, instance, **kwargs):
    # 1) Когда создаётся новый этап — ставим started, если ещё не стоит
    if instance._state.adding and not instance.started:
        instance.started = timezone.now().date()

    # 2) Логика finished:
    #    Считаем, что этап считается “завершённым”, когда
    #    (quantity + total_brak) достигает ожидаемого объёма для этой стадии.
    #    Предположим, что ожидаемый объём = старое значение quantity + старое значение brak
    #    (то есть incoming batch), либо хранится отдельно.
    #    Здесь для простоты возьмём incoming = old.quantity + old.brak.

    if not instance._state.adding:
        old = sender.objects.get(pk=instance.pk)

        # Если теперь выполнено всё, что было передано
        if instance.quantity == instance.zp.order.quantity:
            # и ранее не было finished
            if not old.finished:
                instance.finished = timezone.now().date()
        # Если появился новый брак — обнуляем finished
        if instance.total_brak > old.total_brak:
            instance.finished = None