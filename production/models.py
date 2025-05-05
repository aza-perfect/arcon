from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

User = get_user_model()


class Rang(models.Model):
    name = models.CharField(max_length=50, unique=True)  # "Oq", "Qora", ...
    color = models.CharField(max_length=7, default="#fff")  # "#ffffff", etc.

    class Meta:
        verbose_name = "Rang"
        verbose_name_plural = "Ranglar"

    def __str__(self):
        return self.name


class Mijoz(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Komoliddin, …
    phone = models.CharField(max_length=100, unique=True)
    created = models.DateField(auto_now_add=True, blank=True)

    class Meta:
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"

    def __str__(self):
        return f"{self.name}"


class Jarayon(models.Model):
    name = models.CharField(max_length=100, unique=True)
    can_view = models.ManyToManyField(Group, related_name="jarayon_view")
    can_edit = models.ManyToManyField(Group, related_name="jarayon_edit")

    order = models.PositiveIntegerField(
        help_text="Controls global ordering if you ever list them in the app."
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "Jarayon"
        verbose_name_plural = "Jarayonlar"

    def __str__(self):
        return f"{self.name}"


class Mahsulot(models.Model):
    name = models.CharField(max_length=100, unique=True)
    style_colors = models.ManyToManyField(Rang, related_name="stylable_products", blank=True)
    padosh_colors = models.ManyToManyField(Rang, related_name="padoshable_products")
    rand_colors = models.ManyToManyField(Rang, related_name="randable_products", blank=True)
    jarayonlar = models.ManyToManyField(Jarayon, blank=True, related_name="mahsulotlar")
    chaxlash = models.BooleanField(default=False)
    lazer = models.BooleanField(default=False)
    # простая M2M связь с этапами:
    default_amount = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"

    def __str__(self):
        return self.name


class Zakaz(models.Model):
    STATUS_CHOICES = [
        ("Yangi", "Yangi"),
        ("Qisman Sotildi", "Qisman Sotildi"),
        ("Sotildi", "Sotildi"),
        ("Otmen", "Otmen"),
    ]

    seller = models.ForeignKey(User, on_delete=models.PROTECT, related_name="sales")
    client = models.ForeignKey(Mijoz, on_delete=models.PROTECT)
    created = models.DateField(auto_now_add=True)
    deadline = models.DateField(null=True, blank=True)
    finished = models.DateField(null=True, blank=True)
    partial = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Yangi")
    quantity = models.PositiveIntegerField()
    product = models.ForeignKey(Mahsulot, on_delete=models.PROTECT)

    # pick‐lists for this order:
    style_color = models.ForeignKey(Rang, on_delete=models.PROTECT, null=True, blank=True, related_name='zakaz_style')
    padosh_color = models.ForeignKey(Rang, on_delete=models.PROTECT, null=True, blank=True, related_name='zakaz_padosh')
    rand_color = models.ForeignKey(Rang, on_delete=models.PROTECT, null=True, blank=True, related_name='zakaz_rand')
    use_lazer = models.BooleanField(default=False)
    use_chaxlash = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Zakaz"
        verbose_name_plural = "Zakazlar"

    def __str__(self):
        return f"#{self.id} {self.product.name} x{self.quantity} for {self.client} by {self.seller.username}"


class Sotuv(models.Model):
    order = models.ForeignKey(Zakaz, on_delete=models.CASCADE)
    sold_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField()
    approved = models.BooleanField(default=False)
    approved_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Sotuv"
        verbose_name_plural = "Sotuvlar"

    def __str__(self):
        return f"Sotuv for {self.order} – {self.quantity}"

    # def clean(self):
    #     if self.quantity > self.order.quantity:
    #         raise ValidationError("Can’t sell more than was ordered.")


class Sklad(models.Model):
    produkt = models.ForeignKey(Mahsulot, on_delete=models.CASCADE)
    style_color = models.ForeignKey(Rang, on_delete=models.PROTECT, null=True, blank=True, related_name='sklad_style')
    padosh_color = models.ForeignKey(Rang, on_delete=models.PROTECT, related_name='sklad_padosh')
    rand_color = models.ForeignKey(Rang, on_delete=models.PROTECT, null=True, blank=True, related_name='sklad_rand')
    chaxlash = models.BooleanField(default=False)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [
            ("produkt", "style_color", "padosh_color", "rand_color", "chaxlash")
        ]
        verbose_name = "Sklad"
        verbose_name_plural = "Sklad"

    def __str__(self):
        return f"{self.produkt.name} [{self.padosh_color}] – {self.quantity}"


class ZakazProizvodstvo(models.Model):
    STATUS = [
        ("Yangi", "Yangi"),
        ("Bajarilmoqda", "Bajarilmoqda"),
        ("Bajarildi", "Bajarildi"),
    ]

    order = models.OneToOneField(Zakaz, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS, default="Yangi")
    created = models.DateField()
    started = models.DateField(null=True, blank=True)
    finished = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Zakaz Proizvodstvo"
        verbose_name_plural = "Zakaz Proizvodstvo"

    def __str__(self):
        return f"Proizvodstvo #{self.order.id} – {self.status}"


class Proizvodstvo(models.Model):
    zp = models.ForeignKey(ZakazProizvodstvo, on_delete=models.CASCADE)
    jarayon = models.ForeignKey(Jarayon, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    brak = models.PositiveIntegerField(default=0)
    total_brak = models.PositiveIntegerField(default=0)
    started = models.DateField(null=True, blank=True)
    finished = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("zp", "jarayon")
        verbose_name = "Proizvodstvo"
        verbose_name_plural = "Proizvodstvo"

    def __str__(self):
        return f"{self.zp} – {self.jarayon}: {self.quantity}/{self.brak}"
