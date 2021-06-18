from .models import ( AccountSetting )

def co_branding_logo(request):
  if hasattr(request.user, 'mps_user'):
    company = request.user.mps_user.company
    account_settings, created = AccountSetting.objects.get_or_create(company=company)
    return {
      'co_branding_logo': account_settings.co_branding_logo.url
    }
  return {}