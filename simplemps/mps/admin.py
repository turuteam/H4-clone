from django.contrib import admin

# Register your models here.
from .models import (
    Client,
    Company,
    Developer,
    Drum,
    Gate,
    Kit,
    Make,
    ManagementAssumption,
    MPS_User,
    MPS_User_Anon,
    PageCost,
    Printer,
    PrinterCost,
    Proposal,
    ProposalServiceItem,
    ServiceLevel,
    StreetFighterDeveloper,
    StreetFighterDrum,
    StreetFighterToner,
    Toner,
    ManagerAlert,
    Accessory,
    TieredValue,
    ProposalTCO,
    ProposalTCOItem, 
    ModelSpecification
)

class AccessoryAdmin(admin.ModelAdmin):
  search_fields = ['description']
  list_display = ('printer', 'company', 'description', 'part_number', 'out_cost', 'msrp_cost')
  list_filter = ['company']

class PrinterCostAdmin(admin.ModelAdmin):
  list_display = ('product_id', 'long_model', 'company', 'out_cost', 'msrp_cost', 'care_pack_cost')
  list_filter = ['company']
  search_fields = ['long_model', 'product_id']

class TonerAdmin(admin.ModelAdmin):
  list_display = ('part_id', 'description', 'company', 'manufacturer', 'yield_amount', 'price')
  list_filter = ['company', 'manufacturer']
  search_fields = ['part_id']

class DrumAdmin(admin.ModelAdmin):
  list_display = ('part_id', 'description', 'company', 'manufacturer', 'yield_amount', 'price')
  list_filter = ['company', 'manufacturer']
  search_fields = ['part_id']

class DeveloperAdmin(admin.ModelAdmin):
  list_display = ('part_id', 'description', 'company', 'manufacturer', 'yield_amount', 'price')
  list_filter = ['company', 'manufacturer']
  search_fields = ['part_id']

class ManagementAssumptionAdmin(admin.ModelAdmin):
  list_display = ['company']
  list_filter = ['company']

class ProposalAdmin(admin.ModelAdmin):
  list_display = ('status', 'client', 'term', 'sales_rep', 'id')
  list_filter = ('client', 'sales_rep')

class PageCostAdmin(admin.ModelAdmin):
  list_display = ('company', 'printer', 'source', 'service_cpp', 'service_cpp_cmp')
  list_filter = ['company', 'printer']

class Anon(admin.ModelAdmin):
  list_display = ['user', 'company']
  
  def get_form(self, request, obj=None, **kwargs):
        form = super(Anon, self).get_form(request, obj, **kwargs)
        form.base_fields['user'].label_from_instance = lambda obj: "{} | {}".format(obj.user.username, obj.company.name)
        return form


admin.site.register(Company)
admin.site.register(Client)
admin.site.register(MPS_User)
admin.site.register(MPS_User_Anon, Anon)
admin.site.register(Make)
admin.site.register(Gate)
admin.site.register(Printer)
admin.site.register(PrinterCost, PrinterCostAdmin)
admin.site.register(ManagementAssumption, ManagementAssumptionAdmin)
admin.site.register(Toner, TonerAdmin)
admin.site.register(Drum, DrumAdmin)
admin.site.register(Developer, DeveloperAdmin)
admin.site.register(Kit)
admin.site.register(PageCost, PageCostAdmin)
admin.site.register(Proposal, ProposalAdmin)
admin.site.register(ServiceLevel)
admin.site.register(ProposalServiceItem)
admin.site.register(StreetFighterDeveloper)
admin.site.register(StreetFighterDrum)
admin.site.register(StreetFighterToner)
admin.site.register(ManagerAlert)
admin.site.register(Accessory, AccessoryAdmin)
admin.site.register(TieredValue)
admin.site.register(ProposalTCO)
admin.site.register(ProposalTCOItem)
admin.site.register(ModelSpecification)
