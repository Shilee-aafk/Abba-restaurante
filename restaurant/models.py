from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField("Rol", max_length=20, choices=[
        ('garzon', 'Garzón'),
        ('cocinero', 'Cocinero'),
        ('admin', 'Administrador'),
        ('recepcion', 'Recepción'),
    ], default='garzon')
    pin = models.CharField("PIN", max_length=10, blank=True)  # Para autenticación rápida

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Table(models.Model):
    number = models.IntegerField("Número", unique=True)
    capacity = models.IntegerField("Capacidad", default=4)
    is_available = models.BooleanField("Disponible", default=True)

    class Meta:
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"

    def __str__(self):
        return f"Mesa {self.number}"

class MenuItem(models.Model):
    name = models.CharField("Nombre", max_length=100)
    description = models.TextField("Descripción", blank=True)
    price = models.DecimalField("Precio", max_digits=6, decimal_places=2)
    available = models.BooleanField("Disponible", default=True)

    class Meta:
        verbose_name = "Elemento del Menú"
        verbose_name_plural = "Elementos del Menú"

    def __str__(self):
        return self.name

class Order(models.Model):
    table = models.ForeignKey(Table, verbose_name="Mesa", on_delete=models.CASCADE)
    waiter = models.ForeignKey(User, verbose_name="Garzón", on_delete=models.CASCADE)
    created_at = models.DateTimeField("Fecha y Hora", default=timezone.now, db_index=True)
    status = models.CharField("Estado", max_length=20, choices=[
        ('not_taken', 'Pedido sin tomar'),
        ('preparing', 'En preparación'),
        ('ready', 'Listo'),
        ('delivered', 'Entregado'),
    ], default='not_taken', db_index=True)
    notes = models.TextField("Notas", blank=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def calculate_total(self):
        total = sum(item.quantity * item.menu_item.price for item in self.items.all())
        return total

    def __str__(self):
        fecha_formateada = self.created_at.strftime("%d-%m-%Y %H:%M")
        return f"Pedido #{self.id} en {self.table} ({fecha_formateada})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name="Pedido", related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, verbose_name="Elemento del Menú", on_delete=models.CASCADE)
    quantity = models.IntegerField("Cantidad", default=1)
    notes = models.TextField("Notas", blank=True)

    class Meta:
        verbose_name = "Artículo del Pedido"
        verbose_name_plural = "Artículos del Pedido"

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"

class RegistrationPIN(models.Model):
    pin = models.CharField("PIN", max_length=10, unique=True)
    role = models.CharField("Rol", max_length=20, choices=[
        ('garzon', 'Garzón'),
        ('cocinero', 'Cocinero'),
        ('admin', 'Administrador'),
        ('recepcion', 'Recepción'),
    ])
    created_by = models.ForeignKey(User, verbose_name="Creado por", on_delete=models.CASCADE)
    created_at = models.DateTimeField("Fecha de creación", default=timezone.now)
    uses = models.IntegerField("Usos", default=0)

    class Meta:
        verbose_name = "PIN de Registro"
        verbose_name_plural = "PINs de Registro"

    def __str__(self):
        return f"PIN {self.pin} - {self.role} - Usos: {self.uses}/2"

class AuditLog(models.Model):
    user = models.ForeignKey(User, verbose_name="Usuario", on_delete=models.CASCADE)
    action = models.CharField("Acción", max_length=100)
    timestamp = models.DateTimeField("Fecha y Hora", default=timezone.now)
    details = models.TextField("Detalles", blank=True)

    class Meta:
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, 'userprofile'):
            instance.userprofile.save()
