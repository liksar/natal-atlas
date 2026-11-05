from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from .models import Client, Chart
from .search import normalize

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['internal_name', 'open_client', 'created_at']
    search_fields = ['internal_name']
    def changelist_view(self,request,extra_context=None):
        return HttpResponseRedirect(reverse('clients'))
    def get_search_results(self,request,queryset,search_term):
        return queryset.filter(search_name__contains=normalize(search_term)),False
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    @admin.display(description='Atlas')
    def open_client(self, obj):
        return format_html('<a href="{}">Open</a>', reverse('client-detail', args=[obj.chart.pk]))

# Chart is deliberately not exposed as a raw ModelAdmin edit form.
