from ..models import OEM, OEM_SMP, REMAN


def get_part_helper(part_query, first_manf, next_manf=None):
    if hasattr(part_query.model, "original_part"):
        parts = part_query.filter(
            original_part__manufacturer=first_manf).order_by(
            '-original_part__yield_amount', 'new_price'
        )
        if not parts.exists():
            parts = part_query.filter(
                original_part__manufacturer=next_manf).order_by(
                '-original_part__yield_amount', 'new_price'
            )
            if not parts.exists():
                parts = part_query.filter(
                    original_part__manufacturer=OEM).order_by(
                    '-original_part__yield_amount', 'new_price'
                )
    else:
        parts = part_query.filter(
            manufacturer=first_manf).order_by(
            '-yield_amount', 'price'
        )
        if not parts.exists():
            parts = part_query.filter(
                manufacturer=next_manf).order_by(
                '-yield_amount', 'price'
            )
            if not parts.exists():
                parts = part_query.filter(
                    manufacturer=OEM).order_by(
                    '-yield_amount', 'price'
                )

    # (price * (1-rebate)) + freight
    # ((price * (1 + distro markup)) * (1 - rebate)) + freight

    # new_p / yield * effective_mono/color yield
    return parts[0]


def get_device_part(printer, part_model, part_color, proposal_manf_type,
                    manf_after_reman, manf_after_smp, company):
    if not getattr(printer, part_color + '_' + part_model().part_type):
        return None

    all_parts = part_model.objects.filter(printer=printer,
                                          part_color=part_color,
                                          company=company).select_related()
    if not all_parts.exists():
        return None

    if proposal_manf_type == OEM:
        return get_part_helper(all_parts, OEM)
    elif proposal_manf_type == OEM_SMP:
        return get_part_helper(all_parts, OEM_SMP, manf_after_smp)
    else:
        return get_part_helper(all_parts, REMAN, manf_after_reman)
