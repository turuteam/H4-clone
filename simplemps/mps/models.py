import uuid
from decimal import Decimal, getcontext
from django.db import models
from django.db.models import Model
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

STATUS_TYPES = {
        'in-progress',
        'proposal_sent',
        'proposal_declined',
        'proposal_accepted',
        'contract_sent',
        'contract_signed',
        'contract_declined'
}

SERVICE_LEVELS = {
    'platinum',
    'gold',
    'silver'
}

SERVICE_TYPES = {
        'service_only',
        'supplies_only',
        'total'
}

SALE_TYPES = {
    'lease',
    'buy',
    'rent'
}

ROLES = {
    'manager',
    'rep'
}

DEVICE_TYPES = {
    'copier',
    'printer'
}

MANUFACTURERS = {
    'OEM',
    'REMAN',
    'OEM_SMP'
}

OEM = 'OEM'
OEM_SMP = 'OEM_SMP'
REMAN = 'REMAN'
MANUFACTURER_CHOICES = (
    (OEM, 'OEM'),
    (REMAN, 'Reman'),
    (OEM_SMP, 'OEM SMP')
)


class ServiceLevel(Model):
    name = models.CharField(max_length=20)
    responseTime = models.CharField(max_length=20)

    def __str__(self): 
        return self.name
        
def validate_service_types(service):
    base_validator(service, SERVICE_TYPES)

def validate_status_types(status):
    base_validator(status, STATUS_TYPES)

def validate_sale_types(status):
    base_validator(status, SALE_TYPES)

def validate_roles(role):
    base_validator(role, ROLES)

def validate_device_types(device):
    base_validator(device, DEVICE_TYPES)

def validate_manufacturers(manf):
    base_validator(manf, MANUFACTURERS)

def base_validator(item, validation_list):
    if item not in validation_list:
        raise ValidationError(f'{item} not in {validation_list}')

def validate_proportion(value):
    if value > 1 or value < 0:
        raise ValidationError(f'{value} is not a valid proportion, value must be between 0 and 1')

#Importer/Creator needed
class Company(Model):
    name = models.CharField(max_length=75)
    owner = models.CharField(max_length=50)
    email = models.EmailField()
    phone_number = models.CharField(max_length=30)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=2, null=True)
    country = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=15)
    dca_username = models.CharField(max_length=100, null=True, blank=True)
    dca_password = models.CharField(max_length=100, null=True, blank=True)
    dca_url = models.CharField(max_length=200, null=True, blank=True)
    dca_company = models.CharField(max_length=100, null=True, blank=True)
    currency = models.CharField(max_length=3, null=True, blank=True)
    dca_type = models.CharField(max_length=15, null=True, blank=True)
    dca_api_key = models.TextField(null=True, blank=True)
    self_service_key = models.UUIDField(blank=True, null=True, unique=True)

    def __str__(self):
        return self.name

#importer and updater created
class Client(Model):
    organization_name = models.CharField(max_length=75)
    contact = models.CharField(max_length=75)
    email = models.EmailField()
    city = models.CharField(max_length=50)
    address = models.CharField(max_length=200)
    state = models.CharField(max_length=2, null=True)
    zipcode = models.CharField(max_length=15)
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=30)
    rep_company = models.ForeignKey(Company, on_delete=models.CASCADE)
    currency = models.CharField(max_length=3, null=True, blank=True)

    def __str__(self):
        return self.organization_name

#TODO: need to update, but more involved than would like
class MPS_User(Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

class MPS_User_Anon(Model):
    user = models.OneToOneField(MPS_User, on_delete=models.CASCADE, null=True) 
    company = models.OneToOneField(Company, on_delete=models.CASCADE)

    class Meta: 
        verbose_name = 'Company anonymous representative'
        verbose_name_plural = 'Company Anon Rep\'s'

    def __str__(self): 
        return self.company.name

#Importer Created
class Make(Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
      return self.name

#Need Importer
class Gate(Model):
    gate_min = models.IntegerField()
    gate_max = models.IntegerField()
    us_rate = models.DecimalField(decimal_places=6, max_digits=7)

#Importer Created
class Printer(Model):
    #the way to check if a printer is color or mono is by using the device makeup info
    short_model = models.CharField(max_length=50)
    display_description = models.CharField(max_length=64, null=True)
    release_date = models.DateField()
    make = models.ForeignKey(Make, on_delete=models.CASCADE)
    device_type = models.CharField(max_length=20, validators=[validate_device_types])
    duty_cycle = models.IntegerField()

    #device make-up
    mono_toner = models.BooleanField(default=True)
    cyan_toner = models.BooleanField(default=False)
    yellow_toner = models.BooleanField(default=False)
    magenta_toner = models.BooleanField(default=False)

    mono_drum = models.BooleanField(default=False)
    cyan_drum = models.BooleanField(default=False)
    yellow_drum = models.BooleanField(default=False)
    magenta_drum = models.BooleanField(default=False)

    mono_developer = models.BooleanField(default=False)
    cyan_developer = models.BooleanField(default=False)
    yellow_developer = models.BooleanField(default=False)
    magenta_developer = models.BooleanField(default=False)

    kit_1 = models.BooleanField(default=False)
    kit_2 = models.BooleanField(default=False)
    kit_3 = models.BooleanField(default=False)
    kit_4 = models.BooleanField(default=False)
    # update these after importimg device make-up
    is_color_device = models.BooleanField(default=False)
    makeup_set = models.BooleanField(default=False)

    # oem standard average monthly volume
    avm_mono = models.IntegerField(default=0, null=True)
    avm_color = models.IntegerField(default=0, null=True)

    retail_mono = models.DecimalField(decimal_places=2, max_digits=7, default=0)
    retail_color = models.DecimalField(decimal_places=2, max_digits=7, default=0)

    def __str__(self):
      return self.display_description

    class Meta:
        constraints = [models.UniqueConstraint(fields=['make', 'short_model'], name='unique_printer')]


class ModelSpecification(Model):
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE)
    name = models.CharField(max_length=80, null=True)

    # Connectivity
    c_bluetooth = models.BooleanField(default=False)
    c_ethernet = models.BooleanField(default=False)
    c_usb = models.BooleanField(default=False)
    c_walk_up = models.BooleanField(default=False)
    c_wifi = models.BooleanField(default=False)

    # Page per month rating
    duty_cycle_max = models.IntegerField(default=0)
    duty_cycle_normal = models.IntegerField(default=0)

    # Features supported
    f_copy = models.BooleanField(default=False)
    f_fax = models.BooleanField(default=False)
    f_print = models.BooleanField(default=True)
    f_scan = models.BooleanField(default=False)

    # Manufacturer Model Info
    mfg_model_number = models.CharField(max_length=32, null=True)
    mfg_model_name = models.CharField(max_length=80, null=False)

    # Other features of interest
    o_adf_capacity = models.IntegerField(default=0)
    o_borderless = models.BooleanField(default=False)
    o_duplex = models.BooleanField(default=False)
    o_duplex_scan = models.BooleanField(default=False)
    o_staple = models.BooleanField(default=False)
    o_touchscreen = models.BooleanField(default=False)

    # Paper handling limits
    papersize_max = models.CharField(max_length=20, null=False)
    papersize_supported = models.CharField(max_length=200, null=True)

    # Pages per minute
    ppm_color = models.IntegerField(default=0)
    ppm_mono = models.IntegerField(default=0)

    print_technology = models.CharField(max_length=32, null=True) # toner, ink, thermal, LED, etc.
    available = models.BooleanField(default=True)  # is the device currently manufactured
    
    class Meta:
        constraints = [models.UniqueConstraint(fields=['mfg_model_name'], name='unique_model_name')]

    def __str__(self):
      return self.printer.display_description

    # removed price property because we are pulling data from cost table.
    # @property
    # def price(self):
    #     try:
    #         printer_cost = PrinterCost.objects.get(printer=self.printer, company=self.company)
    #         management_assumption = ManagementAssumption.objects.get(company=self.company)
    #         value = (printer_cost.out_cost * (1 + management_assumption.equipment_inflate)) / (
    #             1 - management_assumption.target_margin_equipment)
            
    #         return '${0:f}'.format(round(value, 2))
    #     except:
    #         return 'N/A'

    def get_item_price(self, company):
        try: 
            printer_cost = PrinterCost.objects.get(printer=self.printer, company=company)
            management_assumption = ManagementAssumption.objects.get(company=company)
            value = (printer_cost.out_cost * (1 + management_assumption.equipment_inflate)) / (
                1 - management_assumption.target_margin_equipment)
            return ('${0:f}'.format(round(value, 2)), printer_cost.id)
        except:
            return ('N/A', 'N/A')
            
    @property
    def purchase_heading(self):
        heading = self.printer.display_description
        if self.mfg_model_name:
            heading += ' {}'.format(self.mfg_model_name)
        if self.mfg_model_number:
            heading += ' {}'.format(self.mfg_model_number)
        return '{} Printer'.format(heading)

    @property
    def new_purchase_specification(self):
        representation = self.printer.make.name
        if self.f_print:
            representation += ', Print'
        if self.f_copy:
            representation += ', Copy'
        if self.f_scan:
            representation += ', Scan'
        if self.f_fax:
            representation += ', Fax'
        if self.printer.is_color_device:
            representation += ', Color'
        else:
            representation += ', Black'
        if self.c_bluetooth:
            representation += ', Bluetooth'
        if self.c_ethernet:
            representation += ', Ethernet'
        if self.c_usb:
            representation += ', USB'
        if self.c_walk_up:
            representation += ', Walk-Up'
        if self.c_wifi:
            representation += ', Wireless'
        if self.ppm_mono:
            representation += ', {} (mono) ppm'.format(self.ppm_mono)
        if self.ppm_color:
            representation += ', {} (color) ppm'.format(self.ppm_color)
        if self.o_duplex:
            representation += ', Duplex'
        if self.o_adf_capacity:
            representation += ', ADF ({}) sheets'.format(self.o_adf_capacity)
        if self.papersize_max:
            representation += ', {} (Max)'.format(self.papersize_max)
        return representation

    def as_json(self): 
        return dict(
            id = self.id,
            printer_id = self.printer.id,
            short_model = self.printer.short_model,
            purchase_heading = self.purchase_heading,
            new_purchase_specification = self.new_purchase_specification,
            is_color_device = self.printer.is_color_device,
            mfg_model_number = self.mfg_model_number
        )

class Product(Model):
    oem_number = models.CharField(max_length=100, null=True)
    make = models.ForeignKey(Make, on_delete=models.CASCADE)
    product_type = models.CharField(max_length=16)
    display_description = models.CharField(max_length=64, null=True)
    long_description = models.CharField(max_length=250)
    dca_description = models.CharField(max_length=128, null=True)
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE, null=True)
    colorant = models.CharField(max_length=25, null=True)
    product_yield = models.IntegerField(null=True)
    msrp = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    currency = models.CharField(max_length=32, null=True)
    compatible = models.BooleanField(default=False)
    status = models.CharField(max_length=8)
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(MPS_User, on_delete=models.CASCADE, related_name='product_created')
    updated_date = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(MPS_User, on_delete=models.CASCADE, related_name='product_updated')

# Harry imports this data
# listed under "Models" heading on My Account page
class PrinterCost(Model):
    product_id = models.CharField(max_length=50)
    long_model = models.CharField(max_length=400)
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    out_cost = models.DecimalField(decimal_places=4, max_digits=9, null=True) # this is the only thing they need to edit
    msrp_cost = models.DecimalField(decimal_places=4, max_digits=9, null=True)
    care_pack_cost = models.DecimalField(decimal_places=4, max_digits=10, null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['long_model', 'company'], name='unique_printer_cost')]

    @property
    def price(self):
        try:
            management_assumption = ManagementAssumption.objects.get(company=self.company)
            value = (self.out_cost * (1 + management_assumption.equipment_inflate)) / (
                1 - management_assumption.target_margin_equipment)
            
            return '${:0,.2f}'.format(round(value, 2))
        except:
            return 'N/A'

#split into company accessory table and accessory table, company will have company and cost
#Allows us to just import a ton of parts without having companies
class Accessory(Model):
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE)
    description = models.CharField(max_length=400)
    part_number = models.CharField(max_length=40)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    out_cost = models.DecimalField(decimal_places=4, max_digits=9)
    msrp_cost = models.DecimalField(decimal_places=4, max_digits=9, null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['printer', 'part_number', 'company'], name='unique_accessory')]

class ManagementAssumption(Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    # supplies
    target_margin_toner = models.DecimalField(decimal_places=5, max_digits=12, default=0.3, validators=[validate_proportion])
    effective_mono_yield = models.DecimalField(decimal_places=5, max_digits=12, default=0.9, validators=[validate_proportion])
    effective_color_yield = models.DecimalField(decimal_places=5, max_digits=12, default=0.9, validators=[validate_proportion])
    reman_rebate = models.DecimalField(decimal_places=5, max_digits=12, default=0)
    oem_smp_rebate = models.DecimalField(decimal_places=5, max_digits=12, default=-0.04)
    oem_rebate = models.DecimalField(decimal_places=5, max_digits=12, default=0)
    toner_shipping_price = models.DecimalField(decimal_places=5, max_digits=12, default=5)
    distro_markup = models.DecimalField(decimal_places=5, max_digits=12, default=0.03, validators=[validate_proportion])
    supplies_only = models.DecimalField(decimal_places=5, max_digits=12, default=0.05, validators=[validate_proportion])
    cpc_toner_only = models.BooleanField(default=True)

    # non network
    annual_mono_cartridges = models.IntegerField(default=3)
    maintenance_kit_replaced_years = models.IntegerField(default=2)
    percentage_color = models.DecimalField(decimal_places=5, max_digits=12, default=0.3, validators=[validate_proportion])
    non_network_margin = models.DecimalField(decimal_places=5, max_digits=12, default=0.5, validators=[validate_proportion])

    # commissions
    FLAT_MARGIN = 'flat_margin'
    FLAT_REVENUE = 'flat_revenue'
    BLENDED_MARGIN = 'blended_margin'
    BLENDED_REVENUE = 'blended_revenue'
    COMMISSION_CHOICES = (
        (FLAT_MARGIN, 'Flat % of Margin'),
        (FLAT_REVENUE, 'Flat % of Revenue'),
        (BLENDED_MARGIN, '% of Margin - Blended Printer & Copier Rate'),
        (BLENDED_REVENUE, '% of Revenue - Blended Printer & Copier Rate')
    )
    commission_type = models.CharField(max_length=40, choices=COMMISSION_CHOICES, default=FLAT_MARGIN)
    percent_margin_flat_rate = models.DecimalField(decimal_places=5, max_digits=12, default=0.1, validators=[validate_proportion])
    percentage_revenue_flat_rate = models.DecimalField(decimal_places=5, max_digits=12, default=0.02, validators=[validate_proportion])
    margin_rate_printers = models.DecimalField(decimal_places=5, max_digits=12, default=0.1, validators=[validate_proportion])
    margin_rate_copiers = models.DecimalField(decimal_places=5, max_digits=12, default=0.1, validators=[validate_proportion])
    revenue_rate_printers = models.DecimalField(decimal_places=5, max_digits=12, default=0.02, validators=[validate_proportion])
    revenue_rate_copiers = models.DecimalField(decimal_places=5, max_digits=12, default=0.02, validators=[validate_proportion])

    NON_NETWORK_COMMISSION_CHOICES = (
        (True, 'Same as Commission Structure'),
        (False, 'None')
    )
    pay_non_network_commission = models.BooleanField(choices=NON_NETWORK_COMMISSION_CHOICES, default=True)

    # service
    target_margin_service = models.DecimalField(decimal_places=5, max_digits=12, default=0.3, validators=[validate_proportion])
    gold_service = models.DecimalField(decimal_places=5, max_digits=12, default=0.05, validators=[validate_proportion])
    platinum_service = models.DecimalField(decimal_places=5, max_digits=12, default=0.35, validators=[validate_proportion])
    service_only = models.DecimalField(decimal_places=5, max_digits=12, default=0.05, validators=[validate_proportion])
    inflate_older_than = models.IntegerField(default=5)
    old_inflate_percent = models.DecimalField(decimal_places=5, max_digits=12, default=0.35, validators=[validate_proportion])
    inflate_out_of_area = models.DecimalField(decimal_places=5, max_digits=12, default=0.2, validators=[validate_proportion])
    outside_mma = models.DecimalField(decimal_places=5, max_digits=12, default=0.2, validators=[validate_proportion])
    tier2_inflate = models.DecimalField(decimal_places=5, max_digits=12, default=0.2, validators=[validate_proportion])
    tier3_inflate = models.DecimalField(decimal_places=5, max_digits=12, default=0.3, validators=[validate_proportion])

    # equipment
    equipment_inflate = models.DecimalField(decimal_places=5, max_digits=12, default=0.15, validators=[validate_proportion])
    accessory_inflate = models.DecimalField(decimal_places=5, max_digits=12, default=0.15, validators=[validate_proportion])
    target_margin_equipment  = models.DecimalField(decimal_places=5, max_digits=12, default=0.3, validators=[validate_proportion])

    # misc
    toner_after_reman = models.CharField(max_length=10, choices=MANUFACTURER_CHOICES, default=OEM_SMP)
    toner_after_oem_smp = models.CharField(max_length=10, choices=MANUFACTURER_CHOICES, default=OEM)
    min_mono_margin = models.DecimalField(decimal_places=5, max_digits=12, default=0.1, validators=[validate_proportion])
    min_color_margin = models.DecimalField(decimal_places=5, max_digits=12, default=0.1, validators=[validate_proportion])
    min_mono_on_color_margin = models.DecimalField(decimal_places=5, max_digits=12, default=0.1, validators=[validate_proportion])
    change_device_price_base = models.BooleanField(default=True)
    managed_cartridge_inflate = models.DecimalField(decimal_places=4, max_digits=7, default=0.00)

    # tiers
    bw1_cpp = models.DecimalField(decimal_places=5, max_digits=12, default=0.015)
    bw2_cpp = models.DecimalField(decimal_places=5, max_digits=12, default=0.02)
    bw3_cpp = models.DecimalField(decimal_places=5, max_digits=12, default=0.04)
    bw4_cpp = models.DecimalField(decimal_places=5, max_digits=12, default=9999)
    color1_cpp = models.DecimalField(decimal_places=5, max_digits=12, default=0.06)
    color2_cpp = models.DecimalField(decimal_places=5, max_digits=12, default=0.1)
    color3_cpp = models.DecimalField(decimal_places=5, max_digits=12, default=9999)

    #not needed?
    exchange_entire_model = models.DecimalField(decimal_places=5, max_digits=12, default=1)
    exchange_service_to_currency = models.DecimalField(decimal_places=5, max_digits=12, default=1)

    # features
    allow_cartridge_pricing = models.BooleanField(default=False)
    allow_leasing = models.BooleanField(default=True)
    allow_reman = models.BooleanField(default=True)
    allow_tiered = models.BooleanField(default=True)
    allow_term_offsets = models.BooleanField(default=False)
    allow_tco = models.BooleanField(default=True)
    allow_flat_rate = models.BooleanField(default=False)
    allow_rental = models.BooleanField(default=False)
    allow_self_service = models.BooleanField(default=False)
    sells_hardware = models.BooleanField(default=True)
    
    # contract term cost management
    cost_offset_12month = models.DecimalField(decimal_places=5, max_digits=12, default=0.0)
    cost_offset_24month = models.DecimalField(decimal_places=5, max_digits=12, default=0.0)
    cost_offset_36month = models.DecimalField(decimal_places=5, max_digits=12, default=0.0)
    cost_offset_48month = models.DecimalField(decimal_places=5, max_digits=12, default=0.0)
    cost_offset_60month = models.DecimalField(decimal_places=5, max_digits=12, default=0.0)

    # self_service
    self_service_term = models.IntegerField(default=12)
    self_service_service_type = models.CharField(max_length=40, default='supplies_only')
    self_service_toner_type = models.CharField(max_length=10, choices=MANUFACTURER_CHOICES, default='OEM')
    self_service_proposal_type = models.CharField(max_length=32, default='cpc')
    self_service_default_sales_rep = models.IntegerField(null=True, blank=True)

    # equipment commissions
    EQ_FLAT_MARGIN = 'eq_flat_margin'
    EQ_FLAT_REVENUE = 'eq_flat_revenue'
    EQ_BLENDED_MARGIN = 'eq_blended_margin'
    EQ_BLENDED_REVENUE = 'eq_blended_revenue'
    EQ_COMMISSION_CHOICES = (
        (EQ_FLAT_MARGIN, 'EQ Flat % of Margin'),
        (EQ_FLAT_REVENUE, 'EQ Flat % of Revenue'),
        (EQ_BLENDED_MARGIN, 'EQ % of Margin - Blended Printer & Copier Rate'),
        (EQ_BLENDED_REVENUE, 'EQ % of Revenue - Blended Printer & Copier Rate')
    )
    eq_commission_type = models.CharField(max_length=40, choices=EQ_COMMISSION_CHOICES, default=EQ_FLAT_MARGIN)
    eq_percent_margin_flat_rate = models.DecimalField(decimal_places=5, max_digits=12, default=0.1, validators=[validate_proportion])
    eq_percentage_revenue_flat_rate = models.DecimalField(decimal_places=5, max_digits=12, default=0.02, validators=[validate_proportion])
    eq_margin_rate_printers = models.DecimalField(decimal_places=5, max_digits=12, default=0.1, validators=[validate_proportion])
    eq_margin_rate_copiers = models.DecimalField(decimal_places=5, max_digits=12, default=0.1, validators=[validate_proportion])
    eq_revenue_rate_printers = models.DecimalField(decimal_places=5, max_digits=12, default=0.02, validators=[validate_proportion])
    eq_revenue_rate_copiers = models.DecimalField(decimal_places=5, max_digits=12, default=0.02, validators=[validate_proportion])


class Proposal(Model):
    status = models.CharField(max_length=40, validators=[validate_status_types])
    term = models.IntegerField(default=0)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True)
    sales_rep = models.ForeignKey(MPS_User, on_delete=models.CASCADE)
    management_assumptions = models.ForeignKey(ManagementAssumption, on_delete=models.CASCADE)
    contract_service_type = models.CharField(max_length=40, validators=[validate_service_types], null=True)
    contract_service_level = models.ForeignKey(ServiceLevel, on_delete=models.CASCADE, null=True)
    default_toner_type = models.CharField(max_length=10, choices=MANUFACTURER_CHOICES, default=OEM_SMP)
    proportion_fleet_offsite = models.DecimalField(decimal_places=5, max_digits=12, default=0)
    expiration_date = models.DateTimeField(null=True)
    signed_date = models.DateTimeField(null=True)
    create_date = models.DateTimeField()
    zone_01 = models.DecimalField(decimal_places=5, max_digits=12, default=0)
    zone_02 = models.DecimalField(decimal_places=5, max_digits=12, default=0)
    zone_03 = models.DecimalField(decimal_places=5, max_digits=12, default=0)
    auto_populate_base_info = models.BooleanField(default=True)
    description= models.CharField(max_length=128, null=True, blank=True)
    original_proposal_id = models.IntegerField(null=True, blank=True)
    #TODO: add date created, date edited, and date sent,

    NO_SF = 0
    PENDING = 1
    APPROVED = 2
    DECLINED = 3
    SF_STATUS_CHOICES = (
        (NO_SF, 'No Street Fighter'),
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (DECLINED, 'Declined')
    )
    street_fighter_status = models.IntegerField(choices=SF_STATUS_CHOICES, default=NO_SF)
    margin_issue = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    bln_base_volume_mono = models.IntegerField(null=True, blank=True)
    bln_base_rate_mono = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    bln_rcmd_price_mono = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    bln_proposed_price_mono = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    bln_base_volume_mono_on_color = models.IntegerField(null=True, blank=True)
    bln_base_rate_mono_on_color = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    bln_rcmd_price_mono_on_color = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    bln_proposed_price_mono_on_color = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    bln_base_volume_color = models.IntegerField(null=True, blank=True)
    bln_base_rate_color = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    bln_rcmd_price_color = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    bln_proposed_price_color = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    proposal_type = models.CharField(max_length=32, default='cpp')
    mps_price = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True, default=0)
    monthly_lease = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True, default=0)
    signature_image = models.ImageField(upload_to='signature_image/', null=True, blank=True)

    def __str__(self):
      return str(self.id)

    @property
    def get_company(self): 
        return Company.objects.get(pk=self.sales_rep.company.id)

#TODO: need to check
class ManagerAlert(Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    STREET_FIGHTER = 'street_fighter'
    MARGIN = 'margin'
    ALERT_TYPE_CHOICES = (
        (STREET_FIGHTER, 'Street Fighter'),
        (MARGIN, 'Margin')
    )
    alert_type = models.CharField(choices=ALERT_TYPE_CHOICES, max_length=25)
    resolved_by = models.ForeignKey(MPS_User, on_delete=models.PROTECT, null=True, blank=True) #Users should be marked as inactive/deleted, not actually removed
    was_approved = models.BooleanField(null=True)
    create_date = models.DateField()
    resolve_date = models.DateField(null=True, blank=True)

class TieredValue(Model):
    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE)
    bw1_proposed_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    bw1_overage_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    bw2_proposed_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    bw2_overage_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    bw3_proposed_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    bw3_overage_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    bw4_proposed_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    bw4_overage_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    color1_proposed_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    color1_overage_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    color2_proposed_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    color2_overage_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    color3_proposed_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)
    color3_overage_cpp = models.DecimalField(decimal_places=5, max_digits=12, null=True)

class ProposalPrinterItem(Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE)
    estimated_commission = models.DecimalField(decimal_places=5, max_digits=12)
    class Meta:
        abstract = True

class ProposalPurchaseItem(ProposalPrinterItem):
    buy_or_lease = models.CharField(max_length=40, validators=[validate_sale_types])

    proposed_cost = models.DecimalField(max_length=40, max_digits=10, decimal_places=2)
    number_printers_purchased = models.IntegerField()
    duty_cycle = models.IntegerField()
    long_model = models.CharField(max_length=200,)
    out_cost = models.DecimalField(decimal_places=4, max_digits=9, )
    msrp_cost = models.DecimalField(decimal_places=4, max_digits=9, )
    care_pack_cost = models.DecimalField(decimal_places=4, max_digits=10, null=True)
    lease_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    lease_term = models.IntegerField(default=0)
    lease_buyout = models.DecimalField(decimal_places=2, max_digits=9, default=0.00)
    bundled_cpp = models.DecimalField(decimal_places=2, max_digits=9, default=0.00)
    lease_type = models.CharField(max_length=100, null=True, blank=True)

class PrinterProposalAccessory(Model):
    purchase_printer = models.ForeignKey(ProposalPurchaseItem, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    cost = models.IntegerField()

class ProposalServiceItem(ProposalPrinterItem):
    number_printers_serviced = models.IntegerField()

    rcmd_cpp_mono = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    rcmd_cpp_color = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    proposed_cpp_mono = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    proposed_cpp_color = models.DecimalField(max_digits=10, decimal_places=8, null=True , blank=True)

    calculated_cpp_mono = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    calculated_cpp_color = models.DecimalField(max_digits=10, decimal_places=8, null=True , blank=True)

    recommended_cost_per_cartridge_mono = models.DecimalField(max_digits=10, decimal_places=4, null=True , blank=True, default=0.0000)
    recommended_cost_per_cartridge_color = models.DecimalField(max_digits=10, decimal_places=4, null=True , blank=True, default=0.0000)
    proposed_cost_per_cartridge_mono = models.DecimalField(max_digits=10, decimal_places=4, null=True , blank=True, default=0.0000)
    proposed_cost_per_cartridge_color = models.DecimalField(max_digits=10, decimal_places=4, null=True , blank=True, default=0.0000)

    base_volume_mono = models.IntegerField(null=True, blank=True)
    base_rate_mono = models.DecimalField(decimal_places=5, max_digits=12, null=True, blank=True)
    base_volume_color = models.IntegerField(null=True, blank=True)
    base_rate_color = models.DecimalField(decimal_places=5, max_digits=12, null=True, blank=True)
    total_mono_pages = models.IntegerField(null=True, blank=True)
    total_color_pages = models.IntegerField(null=True, blank=True)
    mono_coverage = models.DecimalField(decimal_places=5, max_digits=12, null=True, blank=True)
    color_coverage = models.DecimalField(decimal_places=5, max_digits=12, null=True, blank=True)
    mono_toner_price = models.DecimalField(decimal_places=5, max_digits=12, null=True, blank=True)
    color_toner_price = models.DecimalField(decimal_places=5, max_digits=12, null=True, blank=True)

    service_cost = models.DecimalField(decimal_places=5, max_digits=12, null=True, blank=True)

    is_non_network = models.BooleanField(default=False)
    non_network_cost = models.DecimalField(decimal_places=5, max_digits=12, null=True, blank=True)

    tier_level_mono = models.CharField(max_length=10, null=True, blank=True)
    tier_level_color = models.CharField(max_length=10, null=True, blank=True)

    proposal_purchase_item = models.OneToOneField(ProposalPurchaseItem, on_delete=models.CASCADE, blank=True, null=True)

    schedule = models.CharField(max_length=8, null=True, blank=True)
    transfer_id = models.IntegerField(null=True, blank=True)
    transfer_pages = models.IntegerField(null=True, blank=True)
    transfer_mono_pages = models.IntegerField(null=True, blank=True)
    transfer_color_pages = models.IntegerField(null=True, blank=True)
    IP_address = models.CharField(max_length=20, null=True, blank=True)
    serial = models.CharField(max_length=20, null=True, blank=True)
    building = models.CharField(max_length=64, null=True, blank=True)
    floor = models.CharField(max_length=16, null=True, blank=True)
    room = models.CharField(max_length=64, null=True, blank=True)
    address = models.CharField(max_length=256, null=True, blank=True)
    city = models.CharField(max_length=64, null=True, blank=True)
    state = models.CharField(max_length=4, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    location_remarks = models.CharField(max_length=128, null=True, blank=True)
    asset_id = models.CharField(max_length=32, null=True, blank=True)

    # TODO put the scaled toner calculation on the instance eventually

    # TODO incorporate management assumptions (set to 0 if service only)
    def set_recommended_mono_toner_price(self, scaled_mono_toner_cpp):
        self.mono_toner_price = Decimal(self.total_mono_pages * Decimal(scaled_mono_toner_cpp) * Decimal(self.mono_coverage) / Decimal(0.05))

    def set_recommended_color_toner_price(self, scaled_color_toner_cpp):
        self.color_toner_price = Decimal(self.total_color_pages * scaled_color_toner_cpp * Decimal(self.color_coverage) / Decimal(0.05))

    # TODO incorporate management assumptions (set to 0 if supplies only)
    def set_service_price(self, scaled_service_cost):
        self.service_cost = Decimal((self.total_mono_pages + self.total_color_pages) * scaled_service_cost)

    # TODO round to 4 decimal places
    def set_recommended_mono_cpp(self):
        self.rcmd_cpp_mono = 0.00 if self.total_mono_pages == 0 else round((self.mono_toner_price + (self.service_cost * self.total_mono_pages / (self.total_mono_pages + self.total_color_pages))) / self.total_mono_pages, 4)

    def set_recommended_color_cpp(self):
        self.rcmd_cpp_color = 0.00 if self.total_color_pages == 0 else round((self.color_toner_price + (self.service_cost * Decimal(self.total_color_pages / (self.total_mono_pages + self.total_color_pages)))) / self.total_color_pages, 4)

    # NOTE This isn't really very efficient, but it's what we're going with
    # for now.
    #TO DO --need to look at management assumption order for toners rather than hard coded
    def set_recommended_mono_cost_per_cartridge(self):
        if self.proposal.default_toner_type == 'OEM_SMP':
            toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='mono', manufacturer='OEM_SMP').first()
            if toner == None:
                toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='mono', manufacturer='REMAN').first()
                if toner == None:
                    toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='mono', manufacturer='OEM').first()
        elif self.proposal.default_toner_type == 'REMAN':
            toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='mono', manufacturer='REMAN').first()
            if toner == None:
                toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='mono', manufacturer='OEM_SMP').first()
                if toner == None:
                    toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='mono', manufacturer='OEM').first()
        else:
            toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='mono', manufacturer='OEM').first()

        if self.printer.mono_toner and toner and self.mono_toner_price:
            self.recommended_cost_per_cartridge_mono = round(
                (Decimal(toner.price) * Decimal((1 + self.proposal.management_assumptions.managed_cartridge_inflate))) / (
                    Decimal(1 - self.proposal.management_assumptions.target_margin_toner)), 2)
        else:
            self.recommended_cost_per_cartridge_mono = Decimal('0.0000')
    #TO DO --need to look at management assumption order for toners rather than hard coded
    def set_recommended_color_cost_per_cartridge(self):
        if self.proposal.default_toner_type == 'OEM_SMP':
            toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='cyan', manufacturer='OEM_SMP').first()
            if toner == None:
                toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='cyan', manufacturer='REMAN').first()
                if toner == None:
                    toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='cyan', manufacturer='OEM').first()
        elif self.proposal.default_toner_type == 'REMAN':
            toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='cyan', manufacturer='REMAN').first()
            if toner == None:
                toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='cyan', manufacturer='OEM_SMP').first()
                if toner == None:
                    toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='cyan', manufacturer='OEM').first()
        else:
            toner = Toner.objects.filter(company_id=self.proposal.sales_rep.company_id, printer_id=self.printer_id,
                                         part_color='cyan', manufacturer='OEM').first()

        if self.printer.cyan_toner and toner and self.color_toner_price:
            self.recommended_cost_per_cartridge_color = round(
                (Decimal(toner.price) * Decimal(
                    (1 + self.proposal.management_assumptions.managed_cartridge_inflate))) / (
                    Decimal(1 - self.proposal.management_assumptions.target_margin_toner)), 2)
        else:
            self.recommended_cost_per_cartridge_color = Decimal('0.0000')

    # TODO calculate the commission (uses monthly price which is calculated on front end but not stored)
    def set_commission(self):
        pass

    def set_tiers(self, management_assumptions):
        if not self.is_non_network:
            self.non_network_cost = None
            cpp_mono = float(self.proposed_cpp_mono) if self.proposed_cpp_mono else float(self.rcmd_cpp_mono)
            cpp_color = float(self.proposed_cpp_color) if self.proposed_cpp_color else float(self.rcmd_cpp_color)

        if self.is_non_network:
            tier_level_mono = None
        elif cpp_mono <= management_assumptions.bw1_cpp:
            tier_level_mono = 'bw1'
        elif cpp_mono <= management_assumptions.bw2_cpp:
            tier_level_mono = 'bw2'
        elif cpp_mono <= management_assumptions.bw3_cpp:
            tier_level_mono = 'bw3'
        else:
            tier_level_mono = 'bw4'

        if not self.printer.is_color_device or self.is_non_network:
            tier_level_color = None
        elif cpp_color <= management_assumptions.color1_cpp:
            tier_level_color = 'color1'
        elif cpp_color <= management_assumptions.color2_cpp:
            tier_level_color = 'color2'
        else:
            tier_level_color = 'color3'
            # where is tier 4 for color? It's a mystery.

        self.tier_level_mono = tier_level_mono
        self.tier_level_color = tier_level_color


class ProposalTCO(Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    contract_service_type = models.CharField(max_length=40, validators=[validate_service_types], null=True)
    total_supply_spend = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    total_service_spend = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    total_lease_spend = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    est_transaction_overhead = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True, default=60)
    total_sales_orders = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    total_service_orders = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)

class ProposalTCOItem(Model):
    proposalTCO = models.ForeignKey(ProposalTCO, on_delete=models.CASCADE)
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE)
    proposalserviceitem_id = models.IntegerField(null=True, blank=True)
    number_printers_serviced = models.IntegerField(null=True, blank=True, default=1)
    
    total_mono_pages = models.IntegerField(null=True, blank=True)
    total_color_pages = models.IntegerField(null=True, blank=True)

    current_cpp_mono = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    current_cpp_color = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)

    rcmd_cpp_mono = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    rcmd_cpp_color = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)

    mono_toner_price = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    color_toner_price = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    service_cost = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)

    base_volume_mono = models.IntegerField(null=True, blank=True)
    base_rate_mono = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)
    base_volume_color = models.IntegerField(null=True, blank=True)
    base_rate_color = models.DecimalField(max_digits=12, decimal_places=5, null=True, blank=True)

    monthly_lease_payment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    schedule = models.CharField(max_length=8, null=True, blank=True)
    IP_address = models.CharField(max_length=20, null=True, blank=True)
    serial = models.CharField(max_length=20, null=True, blank=True)
    building = models.CharField(max_length=64, null=True, blank=True)
    floor = models.CharField(max_length=16, null=True, blank=True)
    room = models.CharField(max_length=64, null=True, blank=True)
    address = models.CharField(max_length=256, null=True, blank=True)
    city = models.CharField(max_length=64, null=True, blank=True)
    state = models.CharField(max_length=4, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    location_remarks = models.CharField(max_length=128, null=True, blank=True)
    asset_id = models.CharField(max_length=32, null=True, blank=True)

class PrinterPart(Model):
    part_id = models.CharField(max_length=100)
    description = models.CharField(max_length=250, default='', blank=True)
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    MONO = 'mono'
    CYAN = 'cyan'
    YELLOW = 'yellow'
    MAGENTA = 'magenta'
    COLOR_CHOICES = (
        (MONO, 'Black'),
        (CYAN, 'Cyan'),
        (YELLOW, 'Yellow'),
        (MAGENTA, 'Magenta')
    )
    part_color = models.CharField(max_length=25, choices=COLOR_CHOICES)
    gate = models.ForeignKey(Gate, on_delete=models.CASCADE)
    manufacturer = models.CharField(max_length=100, validators=[validate_manufacturers])
    yield_amount = models.IntegerField(default=0)
    price = models.DecimalField(decimal_places=5, max_digits=10, default=0)

    @property
    def cost_per_page(self):
        return self.price / self.yield_amount

    class Meta:
        abstract = True

class Toner(PrinterPart):

    @property
    def part_type(self):
        return 'toner'

    class Meta:
        constraints = [models.UniqueConstraint(fields=['part_id', 'company', 'manufacturer', 'printer', 'part_color'], name='unique_toner')]

class Drum(PrinterPart):

    @property
    def part_type(self):
        return 'drum'

    class Meta:
        constraints = [models.UniqueConstraint(fields=['part_id', 'company', 'manufacturer', 'printer', 'part_color'], name='unique_drum')]

class Developer(PrinterPart):

    @property
    def part_type(self):
        return 'developer'

    class Meta:
        constraints = [models.UniqueConstraint(fields=['part_id', 'company', 'manufacturer', 'printer', 'part_color'], name='unique_developer')]

class StreetFighterItem(Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE)
    part_color = models.CharField(max_length=25)

    # including original price in case we want to freeze the original price after requesting
    original_price = models.DecimalField(decimal_places=5, max_digits=10, default=0)
    requested_price = models.DecimalField(decimal_places=5, max_digits=10, null=True, default=None, blank=True)
    new_price = models.DecimalField(decimal_places=5, max_digits=10, null=True, default=None, blank=True)

    class Meta:
        abstract = True

class StreetFighterToner(StreetFighterItem):
    #TODO: should this actually cascade on delete? why would toners be getting deleted?
    original_part = models.ForeignKey(Toner, on_delete=models.CASCADE)

    @property
    def part_type(self):
        return 'toner'

    class Meta:
        constraints = [models.UniqueConstraint(fields=['proposal', 'company', 'printer', 'part_color'], name='unique_sf_toner')]

class StreetFighterDrum(StreetFighterItem):
    original_part = models.ForeignKey(Drum, on_delete=models.CASCADE)

    @property
    def part_type(self):
        return 'drum'

    class Meta:
        constraints = [models.UniqueConstraint(fields=['proposal', 'company', 'printer', 'part_color'], name='unique_sf_drum')]

class StreetFighterDeveloper(StreetFighterItem):
    original_part = models.ForeignKey(Developer, on_delete=models.CASCADE)

    @property
    def part_type(self):
        return 'developer'

    class Meta:
        constraints = [models.UniqueConstraint(fields=['proposal', 'company', 'printer', 'part_color'], name='unique_sf_developer')]

# class StreetFighterPrinter(StreetFighterItem):
#     original_printer = models.ForeignKey(Printer, on_delete=models.CASCADE)

# class StreetFighterAccessory(StreetFighterItem):
#     original_accessory = models.ForeignKey(Accessory, on_delete=models.CASCADE)

class Kit(Model):
    # Could be initialized differently depending on which kit it is?
    kit_type_number = models.IntegerField()
    name = models.CharField(max_length=20)
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE,)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    kit_cost = models.DecimalField(max_digits=6, decimal_places=2)

    #Toner
    mono_toner = models.ForeignKey(Toner, null=True, on_delete=models.CASCADE, related_name='mono_toner')
    mono_toner_cost = models.IntegerField(null=True)

    cyan_toner = models.ForeignKey(Toner, on_delete=models.CASCADE, related_name='cyan_toner')
    cyan_toner_cost = models.IntegerField(null=True)

    yellow_toner = models.ForeignKey(Toner, on_delete=models.CASCADE, related_name='yellow_toner')
    yellow_toner_cost = models.IntegerField(null=True)

    magenta_toner = models.ForeignKey(Toner, on_delete=models.CASCADE, related_name='magenta_toner')
    magenta_toner_cost = models.IntegerField(null=True)

    #Drum
    mono_drum = models.ForeignKey(Drum, on_delete=models.CASCADE, related_name='mono_drum', null=True)
    mono_drum_cost = models.IntegerField(null=True)

    cyan_drum = models.ForeignKey(Drum, on_delete=models.CASCADE, related_name='cyan_drum', null=True)
    cyan_drum_cost = models.IntegerField(null=True)

    yellow_drum = models.ForeignKey(Drum, on_delete=models.CASCADE, related_name='yellow_drum', null=True)
    yellow_drum_cost = models.IntegerField(null=True)

    magenta_drum = models.ForeignKey(Drum, on_delete=models.CASCADE, related_name='magenta_drum', null=True)
    magenta_drum_cost = models.IntegerField(null=True)

    #Developer
    mono_developer = models.ForeignKey(Developer, on_delete=models.CASCADE, related_name='mono_developer', null=True)
    mono_developer_cost = models.IntegerField(null=True)

    cyan_developer = models.ForeignKey(Developer, on_delete=models.CASCADE, related_name='cyan_developer', null=True)
    cyan_developer_cost = models.IntegerField(null=True)

    yellow_developer = models.ForeignKey(Developer, on_delete=models.CASCADE, related_name='yellow_developer', null=True)
    yellow_developer_cost = models.IntegerField(null=True)

    magenta_developer = models.ForeignKey(Developer, on_delete=models.CASCADE, related_name='magenta_developer', null=True)
    magneta_developer_cost = models.IntegerField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['name', 'company', 'printer'], name='unique_kit')]

class LeasingCompany(Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    leasing_company = models.CharField(max_length=100, unique=False)

class LeasingInfo(Model):
    leasing_company = models.ForeignKey(LeasingCompany, on_delete=models.CASCADE)
    lease_type = models.CharField(max_length=100)
    lease_term = models.IntegerField()
    lease_start_range = models.DecimalField(max_digits=12, decimal_places=4)
    lease_end_range = models.DecimalField(max_digits=12, decimal_places=4)
    lease_rate = models.DecimalField(max_digits=10, decimal_places=5)

class PageCost(Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE)

    FIXED = 'fixed'
    LOCAL = 'local'
    SOURCE_CHOICES = (
        (FIXED, 'Fixed'),
        (LOCAL, 'Local')
    )
    source = models.CharField(max_length=8, choices=SOURCE_CHOICES)

    service_cpp = models.DecimalField(max_digits=10, decimal_places=4)
    service_cpp_cmp = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    supply_cpp_oem_mono = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    supply_cpp_oem_color = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    supply_cpp_smp_mono = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    supply_cpp_smp_color = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    supply_cpp_cmp_mono = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    supply_cpp_cmp_color = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    currency = models.CharField(max_length=32)
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=128)
    updated_date = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=128)
    def_base_volume_mono = models.IntegerField(null=True, blank=True)
    def_base_rate_mono = models.DecimalField(decimal_places=5, max_digits=12, null=True, blank=True)
    def_base_volume_color = models.IntegerField(null=True, blank=True)
    def_base_rate_color = models.DecimalField(decimal_places=5, max_digits=12, null=True, blank=True)


class AccountSetting(Model):
    company = models.OneToOneField(Company, on_delete=models.CASCADE)
    logo = models.ImageField(upload_to='logos/', default='logos/logo1.png')
    co_branding_logo = models.ImageField(upload_to='logos/', default='logos/logo1.png')
