from django.contrib import admin
from django.urls import path, include
from charts import views

urlpatterns = [
    path('', views.home, name='home'),
    path('c/<str:token>/', views.public_chart, name='public-chart'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('health/live', views.live), path('health/ready', views.ready), path('robots.txt', views.robots),
    path('admin/clients/', views.clients, name='clients'),
    path('admin/clients/new/', views.editor, name='client-new'),
    path('admin/clients/<uuid:chart_id>/', views.detail, name='client-detail'),
    path('admin/clients/<uuid:chart_id>/edit/', views.editor, name='client-edit'),
    path('admin/clients/<uuid:chart_id>/link/', views.link, name='client-link'),
    path('admin/clients/<uuid:chart_id>/action/', views.action, name='client-action'),
    path('admin/places/', views.places, name='places'),
    path('admin/', views.admin_home, name='admin-home'),
    path('admin/system/', admin.site.admin_view(admin.site.index), name='system-admin'),
    path('admin/', admin.site.urls),
]
