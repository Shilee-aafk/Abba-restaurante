from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Table, MenuItem, Order, OrderItem, UserProfile, AuditLog, RegistrationPIN
from django.utils import timezone
import json
import random
import string
from openpyxl import Workbook
from datetime import date

@login_required
def home(request):
    # Ensure UserProfile exists
    UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'garzon'})
    # If superuser, redirect to Django admin
    if request.user.is_superuser:
        return redirect('/admin/')
    if request.user.userprofile.role == 'garzon':
        return redirect('select_table')
    elif request.user.userprofile.role == 'cocinero':
        return redirect('kitchen_queue')
    elif request.user.userprofile.role == 'admin':
        return redirect('admin_users')
    elif request.user.userprofile.role == 'recepcion':
        return redirect('reception')
    else:
        return render(request, 'restaurant/home.html', {'message': 'Rol no reconocido'})

@login_required
def select_table(request):
    if request.user.userprofile.role not in ['garzon', 'admin']:
        return redirect('home')  # Or appropriate redirect
    tables = Table.objects.all()
    return render(request, 'restaurant/select_table.html', {'tables': tables})

@login_required
def menu(request, table_id):
    if request.user.userprofile.role not in ['garzon', 'admin']:
        return redirect('home')
    table = get_object_or_404(Table, id=table_id)
    products = MenuItem.objects.filter(available=True)
    return render(request, 'restaurant/menu.html', {'table': table, 'products': products})

@login_required
def send_order(request, table_id):
    if request.user.userprofile.role not in ['garzon', 'admin']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    if request.method == 'POST':
        # Cambiar para obtener datos del formulario POST tradicional
        items = []
        notes = request.POST.get('order_notes', '')

        # Extraer items del POST (esperando campos como item_id, quantity, notes)
        for key in request.POST:
            if key.startswith('item_id_'):
                suffix = key[len('item_id_'):]
                try:
                    item_id = int(request.POST.get(f'item_id_{suffix}'))
                    quantity = int(request.POST.get(f'quantity_{suffix}', 1))
                    item_notes = request.POST.get(f'notes_{suffix}', '')
                    items.append({'id': item_id, 'quantity': quantity, 'notes': item_notes})
                except (ValueError, TypeError):
                    continue

        if not items:
            return JsonResponse({'error': 'No hay ítems en el pedido'}, status=400)

        table = get_object_or_404(Table, id=table_id)
        order = Order.objects.create(table=table, waiter=request.user, notes=notes)

        for item in items:
            menu_item = get_object_or_404(MenuItem, id=item['id'])
            OrderItem.objects.create(order=order, menu_item=menu_item, quantity=item['quantity'], notes=item.get('notes', ''))

        # Mark table as occupied
        table.is_available = False
        table.save()

        # Log audit
        AuditLog.objects.create(user=request.user, action='Crear pedido', details=f'Pedido {order.id} para mesa {table.number}')

        from django.shortcuts import redirect
        return redirect('select_table')

    # Agregar retorno explícito para otros métodos HTTP
    return JsonResponse({'error': 'Método no permitido'}, status=405)

from django.core import serializers
from django.views.decorators.http import require_GET
from django.http import JsonResponse

from collections import defaultdict

@login_required
def kitchen_queue(request):
    if request.user.userprofile.role not in ['cocinero', 'admin']:
        return redirect('home')
    orders = Order.objects.filter(status__in=['not_taken', 'preparing']).prefetch_related('items').order_by('created_at')

    # Agrupar items por producto y notas para cada pedido
    for order in orders:
        grouped_items = defaultdict(lambda: {'menu_item': None, 'quantity': 0, 'notes': ''})
        for item in order.items.all():
            key = (item.menu_item.id, item.notes.strip())
            if grouped_items[key]['menu_item'] is None:
                grouped_items[key]['menu_item'] = item.menu_item
                grouped_items[key]['notes'] = item.notes.strip()
            grouped_items[key]['quantity'] += item.quantity
        order.grouped_items = list(grouped_items.values())

    return render(request, 'restaurant/kitchen_queue.html', {'orders': orders})

    # Agregar retorno explícito para evitar None
    return HttpResponse(status=200)

@login_required
@require_GET
def kitchen_queue_data(request):
    if request.user.userprofile.role not in ['cocinero', 'admin']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    orders = Order.objects.filter(status__in=['not_taken', 'preparing']).prefetch_related('items').order_by('created_at')
    data = []
    from collections import defaultdict
    for order in orders:
        grouped_items = defaultdict(lambda: {'menu_item_name': '', 'quantity': 0, 'notes': ''})
        for item in order.items.all():
            key = (item.menu_item.id, item.notes.strip())
            if grouped_items[key]['menu_item_name'] == '':
                grouped_items[key]['menu_item_name'] = item.menu_item.name
                grouped_items[key]['notes'] = item.notes.strip()
            grouped_items[key]['quantity'] += item.quantity
        items = list(grouped_items.values())
        data.append({
            'id': order.id,
            'table_number': order.table.number,
            'created_at_date': order.created_at.strftime('%d/%m/%Y'),
            'created_at_time': order.created_at.strftime('%H:%M'),
            'status': order.status,
            'status_display': order.get_status_display(),
            'notes': order.notes,
            'items': items,
        })
    return JsonResponse({'orders': data})

@login_required
def update_order_status(request, order_id):
    if request.user.userprofile.role not in ['cocinero', 'admin']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    if request.method == 'POST':
        data = json.loads(request.body)
        new_status = data.get('status')
        if new_status not in ['preparing', 'ready']:
            return JsonResponse({'error': 'Estado inválido'}, status=400)

        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()

        # Log audit
        AuditLog.objects.create(user=request.user, action=f'Cambiar estado pedido a {new_status}', details=f'Pedido {order.id}')

        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def toggle_table_availability(request, table_id):
    if request.user.userprofile.role not in ['garzon', 'admin']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    if request.method == 'POST':
        table = get_object_or_404(Table, id=table_id)
        table.is_available = not table.is_available
        table.save()

        # Log audit
        status_text = 'disponible' if table.is_available else 'ocupada'
        AuditLog.objects.create(user=request.user, action=f'Marcar mesa como {status_text}', details=f'Mesa {table.number} marcada como {status_text}')

        return JsonResponse({'success': True, 'is_available': table.is_available})

    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def admin_users(request):
    if request.user.userprofile.role != 'admin':
        return redirect('home')
    users = UserProfile.objects.all()
    pins = RegistrationPIN.objects.all().order_by('-created_at')
    if request.method == 'POST':
        role = request.POST.get('role')
        if role in ['garzon', 'cocinero', 'admin', 'recepcion']:
            pin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            RegistrationPIN.objects.create(pin=pin, role=role, created_by=request.user)
            messages.success(request, f'PIN generado: {pin} para rol {role}')
            # Log audit
            AuditLog.objects.create(user=request.user, action='Generar PIN de registro', details=f'PIN {pin} para rol {role}')
        else:
            messages.error(request, 'Rol inválido')
        return redirect('admin_users')
    return render(request, 'restaurant/admin_users.html', {'users': users, 'pins': pins})

@login_required
def audit_log(request):
    if request.user.userprofile.role != 'admin':
        return redirect('home')
    logs = AuditLog.objects.all().order_by('-timestamp')
    return render(request, 'restaurant/audit_log.html', {'logs': logs})

from django.contrib.auth.models import User
from django.contrib.auth import login

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        pin = request.POST.get('pin')
        if not username or not password or not pin:
            messages.error(request, 'Todos los campos son requeridos')
            return render(request, 'restaurant/register.html')
        try:
            pin_obj = RegistrationPIN.objects.get(pin=pin, uses__lt=2)
        except RegistrationPIN.DoesNotExist:
            messages.error(request, 'PIN inválido o agotado')
            return render(request, 'restaurant/register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Usuario ya existe')
            return render(request, 'restaurant/register.html')
        user = User.objects.create_user(username=username, password=password)
        # Asignar rol según el PIN
        if pin_obj.role == 'garzon':
            user.userprofile.role = 'garzon'
        elif pin_obj.role == 'cocinero':
            user.userprofile.role = 'cocinero'
        elif pin_obj.role == 'admin':
            user.userprofile.role = 'admin'
        elif pin_obj.role == 'recepcion':
            user.userprofile.role = 'recepcion'
        else:
            user.userprofile.role = 'garzon'  # Valor por defecto
        user.userprofile.save()
        pin_obj.uses += 1
        pin_obj.save()
        # Log audit
        AuditLog.objects.create(user=user, action='Registro de usuario', details=f'Usuario {username} registrado con rol {user.userprofile.role}')
        messages.success(request, 'Usuario registrado exitosamente')
        login(request, user)
        return redirect('home')
    return render(request, 'restaurant/register.html')

@login_required
def reception(request):
    if request.user.userprofile.role != 'recepcion':
        return redirect('home')
    today = date.today()
    orders = Order.objects.filter(created_at__date=today).prefetch_related('items')
    for order in orders:
        order.total = sum(item.quantity * item.menu_item.price for item in order.items.all())
    total_general = sum(order.total for order in orders)
    return render(request, 'restaurant/reception.html', {'orders': orders, 'total_general': total_general})

@login_required
def download_daily_report(request):
    if request.user.userprofile.role != 'recepcion':
        return redirect('home')
    today = date.today()
    orders = Order.objects.filter(created_at__date=today)
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte Diario"
    # Headers
    ws['A1'] = 'ID Pedido'
    ws['B1'] = 'Mesa'
    ws['C1'] = 'Garzón'
    ws['D1'] = 'Hora'
    ws['E1'] = 'Estado'
    ws['F1'] = 'Total'
    row = 2
    total_general = 0
    for order in orders:
        total_order = sum(item.quantity * item.menu_item.price for item in order.items.all())
        total_general += total_order
        ws[f'A{row}'] = order.id
        ws[f'B{row}'] = order.table.number
        ws[f'C{row}'] = order.waiter.username
        ws[f'D{row}'] = order.created_at.strftime('%H:%M')
        ws[f'E{row}'] = order.get_status_display()
        ws[f'F{row}'] = float(total_order)
        row += 1
    # Total general
    ws[f'E{row}'] = 'Total General'
    ws[f'F{row}'] = float(total_general)
    # Response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=reporte_diario_{today}.xlsx'
    wb.save(response)
    return response
