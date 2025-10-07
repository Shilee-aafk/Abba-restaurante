from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('select-table/', views.select_table, name='select_table'),
    path('menu/<int:table_id>/', views.menu, name='menu'),
    path('send-order/<int:table_id>/', views.send_order, name='send_order'),
    path('toggle-table/<int:table_id>/', views.toggle_table_availability, name='toggle_table'),
    path('kitchen-queue/', views.kitchen_queue, name='kitchen_queue'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('admin-users/', views.admin_users, name='admin_users'),
    path('audit-log/', views.audit_log, name='audit_log'),
    path('register/', views.register, name='register'),
    path('reception/', views.reception, name='reception'),
    path('download-daily-report/', views.download_daily_report, name='download_daily_report'),
]
