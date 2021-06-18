import zeep
import json
import requests

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, timedelta
from collections import defaultdict
from workdays import networkdays

from .import_service_items import import_service_items
from ..models import (
    Company,
    Proposal
)

@login_required
def accounts(request, proposal_id):
  proposal = Proposal.objects.get(id=proposal_id)
  company = Company.objects.get(id=proposal.sales_rep.company_id)

  if not all([company.dca_username, company.dca_password, company.dca_company, company.dca_url]):
    message = "FMAudit information has not been provided. Unable to authenticate."
    return JsonResponse(json.dumps(message), status=401, safe=False)

  url = company.dca_url
  history = zeep.plugins.HistoryPlugin()

  try:
    client = zeep.Client(wsdl=url, plugins=[history])
    client.service.Authenticate(company.dca_username, company.dca_password)
    request.session['dca_cookie'] = history.last_received['http_headers']['Set-Cookie']
    request.session['dca_url'] = url
    request.session['ticket'] = client.service.GetAuthTicket(company.dca_username, company.dca_password)
  except:
    message = "Unable to authenticate with FMAudit."
    return JsonResponse(json.dumps(message), status=401, safe=False)

  request.session['proposal_id'] = proposal_id

  accounts_request = client.service.GetAccountsInfo(company.dca_company)

  accounts_info = zeep.helpers.serialize_object(accounts_request)

  accounts_info_sorted = sorted(accounts_info["Accounts"]["FMAAccount"], key=lambda k: k['Name'])

  return JsonResponse(json.dumps(accounts_info_sorted), safe=False)

@login_required
def device_info(request, account_id):
  url = request.session['dca_url']
  history = zeep.plugins.HistoryPlugin()
  client = zeep.Client(wsdl=url, plugins=[history])
  cookie = request.session['dca_cookie']

  client.transport.session.headers.update({'Cookie': cookie})

  devices_response = client.service.GetDevicesForAccount(account_id)

  device_info = zeep.helpers.serialize_object(devices_response)

  unique_models = {}

  if device_info['Devices']:
    for device in device_info['Devices']['FMADevice']:
      if device.get('Model') and device.get('Manufacturer') and device.get('DeviceID'):
        if device['Model'] not in unique_models:
          unique_models[device["Manufacturer"] + " " + device['Model']] = [device["DeviceID"]]
        else:
          [device["Manufacturer"] + " " + device["Model"]].append(device["DeviceID"])

  request.session['dca_device_info'] = unique_models

  return JsonResponse(json.dumps(unique_models, cls=DjangoJSONEncoder), safe=False)

@login_required
def device_data(request, account_id):
  url = request.session['dca_url']
  history = zeep.plugins.HistoryPlugin()
  client = zeep.Client(wsdl=url, plugins=[history])
  cookie = request.session['dca_cookie']
  client.transport.session.headers.update({'Cookie': cookie})

  start_date = datetime.today() - timedelta(days=60)
  end_date = datetime.today()

  unique_models = request.session['dca_device_info']
  proposal_id = request.session['proposal_id']
  meter_response = client.service.GetAllMetersDataForAccountID(request.session['ticket'], account_id, start_date, end_date)
  device_data = zeep.helpers.serialize_object(meter_response)

  # read in DCA items, group all similar items
  dca_items = defaultdict(lambda: defaultdict(lambda: 0))

  if (device_data['Devices'] and device_data['Devices']['Device']):
    for device in device_data['Devices']['Device']:
      if (device["Meters"] and device["Meters"]["Meter"]):
        device_model = device.get("Manufacturer", "") + " " + device.get("Model", "")

        if device_model in unique_models:
          amv_calculations = calculateAMV(device["Meters"]["Meter"])

          if amv_calculations != "Invalid":
            device_name = (device["Manufacturer"] + " " + device['Model']).lower()
            dca_items[device_name]['count'] += 1
            dca_items[device_name]['Mono AMV'] += amv_calculations["mono_amv"]
            dca_items[device_name]['Color AMV'] += amv_calculations["color_amv"]

  count = import_service_items(proposal_id, dca_items)

  if (count == 0):
    message = "Unable to import. There have been no meter reads for the selected account in the last 60 days."
    return JsonResponse(json.dumps(message), safe=False)

  message = "Successfully imported {} items!".format(count)

  return JsonResponse(json.dumps(message), safe=False)

def calculateAMV(meter):
  start_date = None
  end_date = None

  start_mono_count = 0
  end_mono_count = 0
  start_color_count = None
  end_color_count = None

  for reading in meter:
    date = reading["Date"]
    if start_date == None or date <= start_date:
      start_date = date

      if reading["Name"] == "MonoPages":
        start_mono_count = reading["Reading"]

      if reading["Name"] == "ColorPages":
        start_color_count = reading["Reading"]

    if end_date == None or date >= end_date:
      end_date = date

      if reading["Name"] == "MonoPages":
        end_mono_count = reading["Reading"]

      if reading["Name"] == "ColorPages":
        end_color_count = reading["Reading"]

  if (len(meter) == 0 or end_date == start_date):
    return "Invalid"

  date_diff = end_date - start_date

  mono_count = (end_mono_count - start_mono_count) / networkdays(start_date, end_date)

  # TODO: fix the edit page, it breaks if this is 0
  mono_count = 5 if mono_count == 0 else mono_count

  color_count = 0
  if start_color_count is not None and end_color_count is not None:
    color_count = (end_color_count - start_color_count) / networkdays(start_date, end_date)
    color_count = 5 if color_count == 0 else color_count

  amv_calculations = { "color_amv": round(color_count), "mono_amv": round(mono_count) }

  return amv_calculations
