from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..models import (Developer, Drum, PrinterPart, ProposalServiceItem,
                      StreetFighterDeveloper, StreetFighterDrum,
                      StreetFighterToner, Toner)
from ..views import get_device_part


def delete_existing_sf_items(proposal):
    StreetFighterToner.objects.filter(proposal=proposal).delete()
    StreetFighterDrum.objects.filter(proposal=proposal).delete()
    StreetFighterDeveloper.objects.filter(proposal=proposal).delete()

def create_street_fighter_items(proposal):
    assumpts = proposal.management_assumptions
    default_toner = proposal.default_toner_type
    after_reman = assumpts.toner_after_reman
    after_smp = assumpts.toner_after_oem_smp
    company = proposal.sales_rep.company

    service_items = ProposalServiceItem.objects.filter(proposal=proposal)
    for item in service_items:
        printer = item.printer

        if printer.is_color_device:
            for part_color, text in PrinterPart.COLOR_CHOICES:
                if not create_sf_parts_for_color(printer, part_color, default_toner, after_reman, after_smp, company, proposal):
                    return False
        else:
            if not create_sf_parts_for_color(printer, PrinterPart.MONO, default_toner, after_reman, after_smp, company, proposal):
                return False

    return True

def create_sf_parts_for_color(printer, color, default_toner, after_reman, after_smp, company, proposal):
    toner = get_device_part(printer, Toner, color, default_toner, after_reman, after_smp, company)
    if toner is not None:
        try:
            StreetFighterToner(proposal=proposal, company=company, printer=printer,
                               part_color=color, original_price=toner.price, original_part=toner).save()
        except IntegrityError:
            pass

    drum = get_device_part(printer, Drum, color, default_toner, after_reman, after_smp, company)
    if drum is not None:
        try:
            StreetFighterDrum(proposal=proposal, company=company, printer=printer,
                              part_color=color, original_price=drum.price, original_part=drum).save()
        except IntegrityError:
            pass

    dev = get_device_part(printer, Developer, color, default_toner, after_reman, after_smp, company)
    if dev is not None:
        try:
            StreetFighterDeveloper(proposal=proposal, company=company, printer=printer,
                                   part_color=color, original_price=dev.price, original_part=dev).save()
        except IntegrityError:
            pass

    return True

def get_sf_item_info_list(proposal, sf_model):
    sf_parts = sf_model.objects.filter(proposal=proposal).order_by('printer__short_model', 'part_color')

    parts = []
    for part in sf_parts:
        original_part = part.original_part
        parts.append({
            'part_id': original_part.part_id,
            'part_type': original_part.part_type,
            'desc': original_part.description,
            'current_cost': float(part.original_price),
            'req_cost': 0 if part.requested_price is None else float(part.requested_price),
            'new_cost': 0 if part.new_price is None else float(part.new_price)
        })

    return parts

def update_street_fighter_costs(item_info, sf_model, proposal_id):
    try:
        sf_item = sf_model.objects.get(proposal_id=proposal_id, original_part__part_id=item_info['part_id'])
        sf_item.requested_price = item_info['requested_price']
        sf_item.new_price = item_info['new_price']
        sf_item.full_clean()
        sf_item.save()
        return True
    except (sf_model.DoesNotExist, ValidationError):
        return False
