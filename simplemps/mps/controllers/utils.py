import csv
from django.http import HttpResponse
from django.contrib import messages
from decimal import Decimal


def extract_csv_data(file, fieldnames):
    if not file.name.endswith('.csv'):
        return False, HttpResponse("Error, File is not CSV type.")
    if file.multiple_chunks():
        return False, HttpResponse("Error, File is too large.")

    from io import BytesIO, TextIOWrapper
    byte_ar = BytesIO(file.open().read())
    file_txt = TextIOWrapper(byte_ar)
    reader = csv.DictReader(file_txt, fieldnames=fieldnames)
    return reader

def convert_class_to_primitives(data={}):
    t_data = data.copy()
    for key, value in data.items():
        if isinstance(value, Decimal):
            t_data[key] = float(value)
    return t_data

def get_flat_rate(proposal_service_item):
    item = proposal_service_item
    flat_mono = 0
    flat_color = 0
    if (item.base_rate_mono or 0) == 0 and (item.proposed_cpp_mono or 0) == 0:
        flat_mono = (item.rcmd_cpp_mono or 0) * (item.total_mono_pages or 0)

    if (item.base_rate_mono or 0) == 0 and (item.proposed_cpp_mono or 0) > 0:
        flat_mono = item.proposed_cpp_mono * item.total_mono_pages

    if (item.base_rate_mono or 0) > 0 and (item.proposed_cpp_mono or 0) > 0:
        flat_mono = item.base_rate_mono + ((item.total_mono_pages - item.base_volume_mono) * item.proposed_cpp_mono)

    if (item.base_rate_mono or 0) > 0 and (item.proposed_cpp_mono or 0) == 0:
        flat_mono = item.base_rate_mono + ((item.total_mono_pages - item.base_volume_mono) * item.rcmd_cpp_mono)

    if (item.base_rate_color or 0) == 0 and (item.proposed_cpp_color or 0) == 0:
        flat_color = (item.rcmd_cpp_color or 0) * (item.total_color_pages or 0)

    if (item.base_rate_color or 0) == 0 and (item.proposed_cpp_color or 0) > 0:
        flat_color = item.proposed_cpp_color * item.total_color_pages

    if (item.base_rate_color or 0) > 0 and (item.proposed_cpp_color or 0) > 0:
        flat_color = item.base_rate_color + (
                (item.total_color_pages - item.base_volume_color) * item.proposed_cpp_color)

    if (item.base_rate_color or 0) > 0 and (item.proposed_cpp_color or 0) == 0:
        flat_color = item.base_rate_color + ((item.total_color_pages - item.base_volume_color) * item.rcmd_cpp_color)

    flat_rate = flat_mono + flat_color

    return flat_rate
