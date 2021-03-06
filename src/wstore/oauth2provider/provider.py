# -*- coding: utf-8 -*-

# Copyright (c) 2013 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of WStore.

# WStore is free software: you can redistribute it and/or modify
# it under the terms of the European Union Public Licence (EUPL)
# as published by the European Commission, either version 1.1
# of the License, or (at your option) any later version.

# WStore is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# European Union Public Licence for more details.

# You should have received a copy of the European Union Public Licence
# along with WStore.
# If not, see <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>.

from django.http import HttpResponse

from wstore.oauth2provider.pyoauth2 import AuthorizationProvider
from wstore.oauth2provider.models import Application, Code, Token


class WstoreAuthorizationProvider(AuthorizationProvider):

    def _make_response(self, body='', headers=None, status_code=200):

        response = HttpResponse(body, status=status_code)
        for k, v in headers.iteritems():
            response[k] = v

        return response

    def get_client(self, client_id):
        return Application.objects.get(client_id=client_id)

    def validate_client_id(self, client_id):
        return Application.objects.filter(client_id=client_id).exists()

    def validate_client_secret(self, client_id, client_secret):
        return Application.objects.filter(client_id=client_id, client_secret=client_secret).exists()

    def validate_redirect_uri(self, client_id, redirect_uri):
        try:
            app = Application.objects.get(client_id=client_id)
        except:
            return False

        return app.redirect_uri == redirect_uri.split('?', 1)[0]

    def validate_access(self):
        return True

    def validate_scope(self, client_id, scope):
        return True

    def persist_authorization_code(self, user, client_id, code, scope):
        client = Application.objects.get(client_id=client_id)
        Code.objects.create(client=client, user=user, scope=scope, code=code)

    def persist_token_information(self, client_id, scope, access_token, token_type, expires_in, refresh_token, data):
        Token.objects.create(
            token=access_token,
            user_id=data['user_id'],
            token_type=token_type,
            client_id=client_id,
            scope=scope,
            expires_in=expires_in,
            refresh_token=refresh_token
        )

    def from_authorization_code(self, client_id, code, scope):
        try:
            client = Application.objects.get(client_id=client_id)
            code = Code.objects.get(client=client, scope=scope, code=code)
        except:
            return None

        return {
            'client_id': client_id,
            'scope': scope,
            'user_id': code.user.id
        }

    def discard_authorization_code(self, client_id, code):
        Code.objects.filter(client__client_id=client_id, code=code).delete()

    def from_refresh_token(self, client_id, refresh_token, scope):
        try:
            token = Token.objects.get(client__client_id=client_id, refresh_token=refresh_token, scope=scope)
        except:
            return None

        return {
            'scope': token.scope,
            'user_id': token.user.pk,
            'client_id': token.client.client_id
        }

    def discard_refresh_token(self, client_id, refresh_token):
        Token.objects.get(client__client_id=client_id, refresh_token=refresh_token).delete()
