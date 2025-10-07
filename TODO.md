# TODO: Panel de Recepción con Reporte Diario en Excel

## Pasos a Completar

- [x] Instalar openpyxl para generar archivos Excel
- [x] Actualizar restaurant/models.py: Agregar 'recepcion' a opciones de rol en UserProfile y RegistrationPIN
- [x] Actualizar restaurant/views.py: Agregar redirección en home para 'recepcion'
- [x] Actualizar restaurant/views.py: Crear vista 'reception' para mostrar panel
- [x] Actualizar restaurant/views.py: Crear vista 'download_daily_report' para generar Excel
- [x] Actualizar restaurant/urls.py: Agregar rutas para recepción y descarga
- [x] Crear restaurant/templates/restaurant/reception.html
- [x] Ejecutar migraciones de Django si es necesario
- [x] Probar el panel de recepción y descarga del reporte
- [x] Arreglar carga de CSS en panel admin agregando extrastyle y STATICFILES_DIRS
