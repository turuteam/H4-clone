from decimal import Decimal
from django.db import transaction

import sys

from ..views import (
    get_scaled_toner_costs,
)

from ..models import (
    Company,
    Proposal,
    ProposalServiceItem,
    Product,
    Printer,
    PageCost
)

def import_service_items(proposal_id, dca_items):
  # create service items in the database for each device group
  proposal = Proposal.objects.get(id=proposal_id)
  company = Company.objects.get(id=proposal.sales_rep.company_id)
  management_assumptions = proposal.management_assumptions
  proposal_service_items = []
  count = 0
  unknown_devices = []
  duplicate_devices = []

  try:
    for device_group, data in dca_items.items():
      product = Product.objects.filter(dca_description__iexact=device_group).first()

      if product:
        printer = Printer.objects.get(id=product.printer.id)
        page_costs = PageCost.objects.get(printer__id=product.printer.id, company=company)

        total_mono_pages = data['Mono AMV']
        total_color_pages = data['Color AMV']

        mono_coverage = 0.05 if total_mono_pages > 0 else 0.00
        color_coverage = 0.05 if total_color_pages > 0 else 0.00

        toner_costs = get_scaled_toner_costs(management_assumptions, proposal, printer, company, page_costs)

        proposal_service = ProposalServiceItem(
            number_printers_serviced=data['count'],
            proposed_cpp_mono=Decimal(0.00),
            proposed_cpp_color=Decimal(0.00),
            base_volume_mono=Decimal(0.00),
            base_rate_mono=Decimal(0.00),
            base_volume_color=Decimal(0.00),
            base_rate_color=Decimal(0.00),
            total_mono_pages=total_mono_pages,
            total_color_pages=total_color_pages,
            mono_coverage=mono_coverage,
            color_coverage=color_coverage,
            mono_toner_price=Decimal(0.00),
            color_toner_price=Decimal(0.00),
            service_cost=Decimal(0.00),
            is_non_network=False,
            proposal=proposal,
            printer=printer,
            estimated_commission=Decimal(0.00)
        )
        proposal_service.set_recommended_mono_toner_price(toner_costs['scaled_mono_cost'])
        proposal_service.set_recommended_color_toner_price(toner_costs['scaled_color_cost'])
        proposal_service.set_service_price(toner_costs['scaled_service_cost'])
        proposal_service.set_recommended_mono_cpp()
        proposal_service.set_recommended_color_cpp()
        proposal_service.set_recommended_mono_cost_per_cartridge()
        proposal_service.set_recommended_color_cost_per_cartridge()
        proposal_service.set_tiers(management_assumptions)

        proposal_service_items.append(proposal_service)
        count += 1

      else:
        unknown_devices.append(device_group)
    
    with transaction.atomic():
      ProposalServiceItem.objects.bulk_create(proposal_service_items)

      # TODO: send email with list of unkonwn/duplicate devices
  except Exception as e:
    raise Exception("Bulk import failed with error:", e)

  return count
