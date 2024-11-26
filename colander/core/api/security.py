from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'
    """Some external requesters use 'Authorization: Bearer' preamble
    to authenticate and not the 'non standard' 'Token' one used by DRF.
    """
