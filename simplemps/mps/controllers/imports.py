from csv import DictReader
from collections import defaultdict
from decimal import Decimal
from datetime import datetime
from distutils.util import strtobool
from io import StringIO
import sys

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

from ..forms import UploadForm
from ..models import (
    Accessory,
    Company,
    Developer,
    Drum,
    Gate,
    Make,
    PageCost,
    Printer,
    PrinterCost,
    Product,
    Proposal,
    ProposalServiceItem,
    Toner,
)
from .utils import extract_csv_data
from .import_service_items import import_service_items
from ..views import (
    get_scaled_toner_costs,
)

@login_required
def import_device_makeup(request):
    return validate_form_do_import(request, import_device_makeup_post) if request.method == 'POST' else get_import_form(request)

@login_required
def import_toners(request):
    return validate_form_do_import(request, import_printer_part, Toner) if request.method == 'POST' else get_import_form(request)

@login_required
def import_drums(request):
    return validate_form_do_import(request, import_printer_part, Drum) if request.method == 'POST' else get_import_form(request)

@login_required
def import_developers(request):
    return validate_form_do_import(request, import_printer_part, Developer) if request.method == 'POST' else get_import_form(request)

@login_required
def import_printers(request):
    return validate_form_do_import(request, import_printers_post) if request.method == 'POST' else get_import_form(request)

@login_required
def import_makes(request):
    return base_importer(request, Make, ['name']) if request.method == 'POST' else get_import_form(request)

@login_required
def import_printer_costs(request):
    return import_printer_costs_post(request) if request.method == 'POST' else get_import_form(request)

@login_required
def import_printer_costs_post(request):
    form = UploadForm(request.POST, request.FILES)

    if form.is_valid():
        file = request.FILES['file']

        fieldnames = [
            'part_name',
            'short_name',
            'long_model',
            'out_cost',
            'msrp_cost',
            'care_pack_cost',
        ]

        reader = extract_csv_data(file, fieldnames)

        # skip the header row
        iter_reader = iter(reader)
        next(iter_reader)

        s_count = 0
        e_count = 0
        had_errors = False
        for row in reader:
            part_name = str(row['part_name']).strip()
            short_name = str(row['short_name']).strip()
            long_model = str(row['long_model']).strip()
            out_cost = Decimal(str(row['out_cost']).strip().replace(",", ""))
            msrp_cost = Decimal(str(row['msrp_cost']).strip().replace(",", ""))
            care_pack_cost = Decimal(str(row['care_pack_cost']).strip().replace(",", ""))
            try:
                printer = Printer.objects.get(short_model=short_name)
            except Printer.DoesNotExist:
                continue
            try:
                pc = PrinterCost.objects.get(
                    long_model=long_model,
                    company=request.user.mps_user.company,
                )
                pc.product_id = part_name
                pc.printer = printer
                pc.out_cost = out_cost
                pc.msrp_cost = msrp_cost
                pc.care_pack_cost = care_pack_cost
                pc.save()
            except PrinterCost.DoesNotExist:
                PrinterCost.objects.create(
                    long_model=long_model,
                    company=request.user.mps_user.company,
                    product_id = part_name,
                    printer = printer,
                    out_cost = out_cost,
                    msrp_cost = msrp_cost,
                    care_pack_cost = care_pack_cost,
                )
            s_count += 1

        context = {
            'success': s_count > 0,
            's_count': s_count,
            'had_errors': had_errors,
            'e_count': e_count
        }

        return render(request, 'importResults.html', context)

@login_required
def import_accessories(request):
    return import_accessories_post(request) if request.method == 'POST' else get_import_form(request)

@login_required
def import_accessories_post(request):
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        file = request.FILES['file']

        fieldnames = [
            'part_number',
            'short_name',
            'description',
            'out_cost',
            'msrp_cost',
        ]

        reader = extract_csv_data(file, fieldnames)

         # skip the header row
        iter_reader = iter(reader)
        next(iter_reader)

        s_count = 0
        e_count = 0
        had_errors = False
        for row in reader:
            part_number = str(row['part_number']).strip()
            short_name = str(row['short_name']).strip()
            description = str(row['description']).strip()
            out_cost = Decimal(str(row['out_cost']).strip().replace(",", ""))
            msrp_cost = Decimal(str(row['msrp_cost']).strip().replace(",", ""))
            try:
                printer = Printer.objects.get(short_model=short_name)
            except Printer.DoesNotExist:
                continue
            a, created = Accessory.objects.get_or_create(
                printer=printer,
                company=request.user.mps_user.company,
                part_number=part_number,
                description=description,
                out_cost=out_cost,
                msrp_cost=msrp_cost,
            )
            a.save()
            s_count += 1

        context = {
            'success': s_count > 0,
            's_count': s_count,
            'had_errors': had_errors,
            'e_count': e_count
        }

        return render(request, 'importResults.html', context)

@login_required
def import_products(request):
    return import_products_post(request) if request.method == 'POST' else get_import_form(request)

@login_required
def import_products_post(request):
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        file = request.FILES['file']

        fieldnames = [
            'oem_number',
            'make',
            'product_type',
            'display_description',
            'long_description',
            'dca_description',
            'short_name',
            'colorant',
            'product_yield',
            'msrp',
            'currency',
            'compatible',
            'status'
        ]

        reader = extract_csv_data(file, fieldnames)

        s_count = 0
        e_count = 0
        had_errors = False
        for row in reader:
            oem_number = str(row['oem_number']).strip()
            make = str(row['make']).strip()
            product_type = str(row['product_type']).strip()
            display_description = str(row['display_description']).strip()
            long_description = str(row['long_description']).strip()
            dca_description = str(row['dca_description']).strip()
            short_name = str(row['short_name']).strip()
            colorant = str(row['colorant']).strip()
            product_yield = str(row['product_yield']).strip()
            msrp = Decimal(str(row['msrp']).strip().replace(",", ""))
            currency = str(row['currency']).strip()
            compatible = str(row['compatible']).strip()
            status = str(row['status']).strip()
            printer = Printer.objects.get(short_model=short_name)
            make = Make.objects.get(name=make)
            p, created = Product.objects.get_or_create(
                oem_number=oem_number,
                make=make,
                product_type=product_type,
                display_description=display_description,
                long_description=long_description,
                dca_description=dca_description,
                printer=printer,
                colorant=colorant,
                product_yield=product_yield,
                msrp=msrp,
                currency=currency,
                compatible=compatible,
                status=status,
                created_by=request.user.mps_user,
                updated_by=request.user.mps_user
            )
            p.save()
            s_count += 1

        context = {
            'success': s_count > 0,
            's_count': s_count,
            'had_errors': had_errors,
            'e_count': e_count
        }

        return render(request, 'importResults.html', context)

@login_required
def import_service(request):
    return import_service_post(request) if request.method == 'POST' else get_import_form(request)

@login_required
def import_service_post(request):
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        file = request.FILES['file']

        fieldnames = [
            'short_model',
            'source',
            'service_cpp',
            'currency',
            'def_base_volume_mono',
            'def_base_volume_color'
        ]

        reader = extract_csv_data(file, fieldnames)

         # skip the header row
        iter_reader = iter(reader)
        next(iter_reader)

        s_count = 0
        error_count = 0
        had_errors = False
        for row in reader:
            short_model = str(row['short_model']).strip()
            source = str(row['source']).strip()
            service_cpp = str(row['service_cpp']).strip()
            currency = str(row['currency']).strip()
            def_base_volume_mono = str(row['def_base_volume_mono']).strip()
            def_base_volume_color = str(row['def_base_volume_color']).strip()
            try:
                printer = Printer.objects.get(short_model=short_model)
            except Printer.DoesNotExist:
                continue
            service, created = PageCost.objects.get_or_create(
                printer=printer,
                company=request.user.mps_user.company,
                source=source,
                service_cpp=service_cpp,
                currency=currency,
                def_base_volume_mono=def_base_volume_mono,
                def_base_volume_color=def_base_volume_color,
                created_by=str(request.user.mps_user),
                updated_by=str(request.user.mps_user)
            )
            service.save()
            s_count += 1

        context = {
            'success': s_count > 0,
            's_count': s_count,
            'had_errors': had_errors,
            'error_count': error_count
        }

        return render(request, 'importResults.html', context)
            

@login_required
def get_import_form(request):
    form = UploadForm()
    return render(request, 'import.html', {'form': form})

@login_required
def validate_form_do_import(request, callback, param=None):
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        if param is None:
            return callback(request)
        return callback(request, param)
    return HttpResponse('There was a problem uploading the file to the server')

@login_required
def import_device_makeup_post(request):
    fieldnames = [
        'short_model',
        'mono_toner',
        'cyan_toner',
        'yellow_toner',
        'magenta_toner',
        'mono_drum',
        'cyan_drum',
        'yellow_drum',
        'magenta_drum',
        'mono_developer',
        'cyan_developer',
        'yellow_developer',
        'magenta_developer',
        'kit_1',
        'kit_2',
        'kit_3',
        'kit_4'
    ]
    reader = extract_csv_data(request.FILES['file'], fieldnames)

    #TODO: needs to also save makes, since that's what it validates on when creating
    printer_names = set()
    for printer in Printer.objects.all().values('short_model'):
        printer_names.add(printer['short_model'].strip())

    success_count = 0
    e_count = 0
    had_errors = False
    for row in reader:
        if row['short_model'] == 'short_model':
            #skip header row
            continue

        #TODO: needs to check if short_model + make combo exists
        if row['short_model'].strip() not in printer_names:
            had_errors = True
            e_count += 1
            continue

        row_vals = {}
        is_color = False
        for key in row.keys():
            if key == 'short_model':
                row_vals[key] = row[key]
            else:
                val = bool(strtobool(row[key]))
                row_vals[key] = val

                if 'mono' not in key and val:
                    is_color = True

        row_vals['is_color_device'] = is_color

        #TODO: needs to filter by make and short_model
        success_count += Printer.objects.filter(short_model=row['short_model'].strip()).update(**row_vals)

    context = {
        'success': success_count > 0,
        's_count': success_count,
        'had_errors': had_errors,
        'e_count': e_count
    }

    return render(request, 'importResults.html', context)

@login_required
def import_printer_part(request, part_model):
    fieldnames = ['part_id', 'description', 'printer_short_name', 'part_color', 'manufacturer', 'yield_amount', 'price']
    reader = extract_csv_data(request.FILES['file'], fieldnames)

    gate_list = list(Gate.objects.order_by('gate_max'))
    p_list = list(Printer.objects.all())
    printers = {}
    for printer in p_list:
        printers[printer.short_model] = printer

    had_errors = False
    e_count = 0
    success_count = 0
    for row in reader:
        try:
            if row['part_id'] == 'part_id':
                continue

            row['company'] = request.user.mps_user.company
            row['printer'] = printers[row['printer_short_name'].strip()]
            del row['printer_short_name']

            gate = gate_list[-1]
            for g in gate_list:
                if int(row['yield_amount']) <= g.gate_max:
                    gate = g
                    break
            row['gate'] = gate

            try:
                part_obj = part_model.objects.get(part_id=row['part_id'],
                                                  company=row['company'],
                                                  manufacturer=row['manufacturer'],
                                                  printer=row['printer'],
                                                  part_color=row['part_color'])
                for key, value in row.items():
                    setattr(part_obj, key, value)
            except (Toner.DoesNotExist, Drum.DoesNotExist, Developer.DoesNotExist):
                part_obj = part_model(**row)

            part_obj.full_clean()
            part_obj.save()
            success_count += 1
        except (ValidationError, KeyError):
            had_errors = True
            e_count += 1

    context = {
        'success': success_count > 0,
        's_count': success_count,
        'had_errors': had_errors,
        'e_count': e_count
    }

    return render(request, 'importResults.html', context)

@login_required
def import_printers_post(request):
    fieldnames = ['short_model', 'make', 'release_date', 'device_type', 'duty_cycle', 'display_description']
    reader = extract_csv_data(request.FILES['file'], fieldnames)

    makes = {}
    for make in Make.objects.all():
        makes[make.name.lower()] = make

    had_errors = False
    e_count = 0
    success_count = 0
    for row in reader:
        try:
            if row['make'] == 'make':
                continue

            if row['make'].strip() == '':
                continue

            row['short_model'] = row['short_model'].strip()
            row['make'] = makes[row['make'].lower()]    #need to check for None
            row['release_date'] = datetime.strptime(row['release_date'], '%m/%d/%Y')
            row['device_type'] = row['device_type'].lower()

            try:
                print_obj = Printer.objects.get(short_model=row['short_model'].strip(), make=row['make'])
                for key, value in row.items():
                    setattr(print_obj, key, value)
            except Printer.DoesNotExist:
                print_obj = Printer(**row)

            try:
                print_obj.full_clean()
            except ValidationError as e:
                #print(e.message_dict)
                had_erros = True
                e_count += 1
            else:
                print_obj.save()
                success_count += 1

        except ValidationError:
            had_errors = True
            e_count += 1

    context = {
        'success': success_count > 0,
        's_count': success_count,
        'had_errors': had_errors,
        'e_count': e_count
    }

    return render(request, 'importResults.html', context)

@login_required
def base_importer(request, modl, fieldnames):
    reader = extract_csv_data(request.FILES['file'], fieldnames)

    had_errors = False
    e_count = 0
    success_count = 0
    for row in reader:
        try:
            first_item = list(row.values())[0]
            if first_item == fieldnames[0]:
                continue

            obj = modl(**row)
            obj.full_clean()
            obj.save()
            success_count += 1
        except ValidationError:
            had_errors = True
            e_count += 1

    context = {
        'success': success_count > 0,
        's_count': success_count,
        'had_errors': had_errors,
        'e_count': e_count
    }

    return render(request, 'importResults.html', context)

@login_required
def import_dca_post(request, proposal_id):
    try:
        file = StringIO(initial_value=request.FILES['dcaFile'].read().decode('utf-8'), newline='\r\n')
        reader = DictReader(file)

        # read in DCA items, group all similar items
        dca_items = defaultdict(lambda: defaultdict(lambda: 0))
        for row in reader:
            device = row['Device'].lower()

            dca_items[device]['count'] += 1
            if row['Mono AMV']:
                dca_items[device]['Mono AMV'] += int(row['Mono AMV'])
            if row['Color AMV']:
                dca_items[device]['Color AMV'] += int(row['Color AMV'])

        count = import_service_items(proposal_id, dca_items)
    except Exception as e:
        return render(request, 'importDCAResults.html', { 'success': False, 'had_errors': True, 'error': e })

    context = {
        'proposal_id': proposal_id,
        's_count': count,
        'success': True,
    }
    return render(request, 'importDCAResults.html', context)


@login_required
def import_hw_data(request):
    return import_hw_data_post(request) if request.method == 'POST' else get_import_form(request)


@login_required
def import_supplies_data(request):
    return import_supplies_data_post(request) if request.method == 'POST' else get_import_form(request)


@login_required
def import_hw_data_post(request):
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        file = request.FILES['file']

        fieldnames = ['part_name/id','description', 'out_cost']

        reader = extract_csv_data(file, fieldnames)

         # skip the header row
        iter_reader = iter(reader)
        next(iter_reader)

        s_count = 0
        e_count = 0
        had_errors = False

        company = request.user.mps_user.company

        for row in reader:
            part_number = str(row['part_name/id']).strip()
            description = str(row['description']).strip()
            out_cost = Decimal(str(row['out_cost']).strip().replace(",", ""))

            accessory_updated = Accessory.objects.filter(part_number=part_number, company=company).update(
                description=description, out_cost=out_cost)
            printer_cost_updated = PrinterCost.objects.filter(product_id=part_number, company=company).update(
                long_model=description, out_cost=out_cost)
            
            if accessory_updated or printer_cost_updated:
                s_count += 1

        context = {
            'success': s_count > 0,
            's_count': s_count,
            'had_errors': had_errors,
            'e_count': e_count
        }

        return render(request, 'importResults.html', context)


@login_required
def import_supplies_data_post(request):
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
        file = request.FILES['file']

        fieldnames = ['part_id', 'manufacturer', 'yield_amount', 'price']

        reader = extract_csv_data(file, fieldnames)

         # skip the header row
        iter_reader = iter(reader)
        next(iter_reader)

        s_count = 0
        e_count = 0
        had_errors = False

        company = request.user.mps_user.company

        for row in reader:
            part_id = str(row['part_id']).strip()
            manufacturer = str(row['manufacturer']).strip()
            yield_amount = str(row['yield_amount']).strip()
            price = Decimal(str(row['price']).strip().replace(",", ""))

            toner_updated = Toner.objects.filter(part_id=part_id, company=company, manufacturer=manufacturer).update(
                yield_amount=yield_amount, price=price)
            drum_updated = Drum.objects.filter(part_id=part_id, company=company, manufacturer=manufacturer).update(
                yield_amount=yield_amount, price=price)
            developer_updated = Developer.objects.filter(part_id=part_id, company=company, manufacturer=manufacturer).update(
                yield_amount=yield_amount, price=price)
            
            if toner_updated or drum_updated or developer_updated:
                s_count += 1

        context = {
            'success': s_count > 0,
            's_count': s_count,
            'had_errors': had_errors,
            'e_count': e_count
        }

        return render(request, 'importResults.html', context)