from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import AccessToken

class AccessTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.replace('Bearer ', '')
        
        try:
            access_token = AccessToken.objects.get(token=token)
            if access_token.is_expired():
                access_token.delete()
                raise AuthenticationFailed('Token已过期')
            
            # Wrap user to ensure it has required attributes for DRF
            user = access_token.user
            # Ensure user has is_authenticated attribute
            if not hasattr(user, 'is_authenticated'):
                user.is_authenticated = True
            
            return (user, token)
        except AccessToken.DoesNotExist:
            raise AuthenticationFailed('无效的token')