from collections import defaultdict
from datetime import timedelta, datetime
import requests
import json

from workdays import networkdays
from .import_service_items import import_service_items

from django.http.response import JsonResponse
from django.contrib.auth.decorators import login_required

from ..models import (
    Company,
    Proposal,
    Printer
)


def get_session(request):
    proposal = Proposal.objects.get(id=request.session['proposal_id'])
    company = Company.objects.get(id=proposal.sales_rep.company_id)

    api_key = company.dca_api_key
    user = company.dca_username
    password = company.dca_password
    url = company.dca_url

    session = requests.Session()
    session.auth = (user, password)
    session.headers.update({'X-API-KEY': api_key, 'content-type': 'application/json', 'accept': 'application/json'})

    request.session['printfleet_url'] = url

    return session


def parse_groups(groups):
    children = []

    for group in groups:
        children.append(parse_children(group, ['id', 'name']))

    return children


def parse_children(dict_input, keys):
    values = [dict_input.get(key, '') for key in keys]
    dict_response = dict(zip(keys, values))

    dict_response['children'] = [parse_children(child, keys) for child in dict_input.get('children', [])]
    return dict_response


def get(session, url):
    r = session.get(url)

    try:
        data = r.json()
    except Exception as e:
        print(e)
        print(r.text)
        data = []

    return data


@login_required
def groups(request, proposal_id):
    request.session['proposal_id'] = proposal_id
    session = get_session(request)

    group_url = request.session['printfleet_url'] + '/groups'
    groups_data = parse_groups(get(session, group_url))
    
    return JsonResponse(json.dumps(groups_data), safe=False)


@login_required
def devices(request, group_id):
    session = get_session(request)
    devices_url = request.session['printfleet_url'] + '/devices?groupId={group_id}'.format(group_id=group_id)
    devices_data = get(session, devices_url)

    unique_models = []
    devices = []

    for device in devices_data:
        model = device['name']
        devices.append({'id': device['id'], 'name': device['name'], 'is_color': device['modelMatch']['model']['isColor']})

        if model not in unique_models:
            unique_models.append(model)

    request.session['printfleet_devices'] = devices

    return JsonResponse(json.dumps(unique_models), safe=False)



@login_required
def group(request, group_id):
    session = get_session(request)
    group_url = request.session['printfleet_url'] + '/groups/{group_id}'.format(group_id=group_id)
    group_data = get(session, group_url)
    parsed_group = parse_children(group_data, ['id', 'name'])
    return JsonResponse(json.dumps(group_data), safe=False)

@login_required
def device_data(request, group_id):
    session = get_session(request)
    
    selected_devices = json.loads(request.body).get('devices', [])
    device_ids = [device['id'] for device in request.session['printfleet_devices'] if device['name'] in selected_devices]

    mono_url = request.session['printfleet_url'] + '/meters/LIFECOUNTMONO/history'
    color_url = request.session['printfleet_url'] + '/meters/LIFECOUNTCOLOR/history'

    start_date = str((datetime.today() - timedelta(days=60)).date())
    end_date = str(datetime.today().date())

    mono_meters = session.post(mono_url, json={'deviceIds': device_ids, 'startDate': start_date, 'endDate': end_date}).json()
    color_meters = session.post(color_url, json={'deviceIds': device_ids, 'startDate': start_date, 'endDate': end_date}).json()

    combined_meters = combine_meters_by_device(mono_meters, color_meters)

    if not combined_meters:
        message = "Unable to import. There have been no meter reads for the selected account in the last 60 days."
        return JsonResponse(json.dumps(message), safe=False)

    printfleet_items = defaultdict(lambda: defaultdict(lambda: 0))

    for device_id, meters in combined_meters.items():
        pf_devices = request.session['printfleet_devices']
        amv_calculations = calculateAMV(meters, device_id, pf_devices)

        if amv_calculations != "Invalid":
            device_name = next(item for item in pf_devices if item['id'] == device_id)['name']
            printfleet_items[device_name]['count'] += 1
            printfleet_items[device_name]['Mono AMV'] += amv_calculations["mono_amv"]
            printfleet_items[device_name]['Color AMV'] += amv_calculations["color_amv"]

    proposal_id = request.session['proposal_id']
    count = import_service_items(proposal_id, printfleet_items)
    message = "Successfully imported {} items!".format(count)

    return JsonResponse(json.dumps(message), safe=False)

def combine_meters_by_device(mono_meters, color_meters):
    combined_meters = {}

    for device in mono_meters:
        combined_meters[device['deviceId']] = { 'mono_meters': device['values'], 'color_meters': [] }

    for device in color_meters:
        if device['deviceId'] in combined_meters:
            combined_meters[device['deviceId']]['color_meters'] = device['values']
        else:
            combined_meters[device['deviceId']] = { 'mono_meters': [], 'color_meters': device['values'] }

    return combined_meters

def calculateAMV(meters, device_id, pf_devices):
    mono_meters = meters['mono_meters']
    color_meters = meters['color_meters']

    start_mono_meter = None if not mono_meters else min(mono_meters, key=lambda x:x['count'])
    end_mono_meter = None if not mono_meters else max(mono_meters, key=lambda x:x['count'])
    start_mono_date = None if not start_mono_meter else datetime.strptime(start_mono_meter['firstReportedAt'].split('T')[0], '%Y-%m-%d')
    end_mono_date = None if not end_mono_meter else datetime.strptime(end_mono_meter['firstReportedAt'].split('T')[0], '%Y-%m-%d')

    start_color_meter = None if not color_meters else min(color_meters, key=lambda x:x['count'])
    end_color_meter = None if not color_meters else max(color_meters, key=lambda x:x['count'])
    start_color_date = None if not start_color_meter else datetime.strptime(start_color_meter['firstReportedAt'].split('T')[0], '%Y-%m-%d')
    end_color_date = None if not end_color_meter else datetime.strptime(end_color_meter['firstReportedAt'].split('T')[0], '%Y-%m-%d')

    if all ([start_mono_date, end_mono_date, start_color_date, end_color_date]):
        start_date = min(start_mono_date, start_color_date)
        end_date = max(end_mono_date, end_color_date)
    else:
        start_date = start_mono_date or start_color_date
        end_date = end_mono_date or end_color_date

    if (not start_date or not end_date) or ((end_date - start_date).days < 30):
        return "Invalid"

    if end_mono_meter and start_mono_meter:
        mono_count = (end_mono_meter['count'] - start_mono_meter['count']) / networkdays(start_date, end_date)
        mono_count = 5 if mono_count == 0 else mono_count
    else:
        mono_count = 5

    is_color_device = next(item for item in pf_devices if item['id'] == device_id)['is_color']
        
    if start_color_meter and end_color_meter:
            color_count = (end_color_meter['count'] - start_color_meter['count']) / networkdays(start_date, end_date)
    elif is_color_device:
            color_count = 5
    else:
            color_count = 0

    amv_calculations = { "color_amv": round(color_count), "mono_amv": round(mono_count) }

    return amv_calculations