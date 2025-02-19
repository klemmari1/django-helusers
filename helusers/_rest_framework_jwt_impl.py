from django.conf import settings
from django.utils.translation import ugettext as _
from rest_framework import exceptions
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.settings import api_settings

from .user_utils import get_or_create_user


def patch_jwt_settings():
    """Patch rest_framework_jwt authentication settings from allauth"""
    defaults = api_settings.defaults
    defaults['JWT_PAYLOAD_GET_USER_ID_HANDLER'] = (
        __name__ + '.get_user_id_from_payload_handler')

    if 'allauth.socialaccount' not in settings.INSTALLED_APPS:
        return

    from allauth.socialaccount.models import SocialApp
    try:
        app = SocialApp.objects.get(provider='helsinki')
    except SocialApp.DoesNotExist:
        return

    defaults['JWT_SECRET_KEY'] = app.secret
    defaults['JWT_AUDIENCE'] = app.client_id

# Disable automatic settings patching for now because it breaks Travis.
# patch_jwt_settings()


class JWTAuthentication(JSONWebTokenAuthentication):
    def authenticate_credentials(self, payload):
        try:
            user = get_or_create_user(payload)
        except ValueError as e:
            raise exceptions.AuthenticationFailed(str(e)) from e

        if user and not user.is_active:
            msg = _('User account is disabled.')
            raise exceptions.AuthenticationFailed(msg)

        return user


def get_user_id_from_payload_handler(payload):
    return payload.get('sub')
