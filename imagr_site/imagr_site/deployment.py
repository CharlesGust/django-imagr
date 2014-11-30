import os

def setup_deployment():
    # SECURITY WARNING: don't run with debug turned on in production!
    os.environ['DEBUG'] = "False"
    os.environ['TEMPLATE_DEBUG'] = "False"

    # CMGTODO
    # may have to allow '*.amazonaws.com' hosts if DNS not settled
    # may have to allow '*' as host, but less secure
    os.environ['ALLOWED_HOSTS'] = "['imagr_app.charlesgust.me',]"

    # There is a risk that the greater security of setting
    #  these to True will not work unless we get an SSL
    #  certificate, and we don't know yet whether Amazon EC2
    #  will give us a certificate or let us use one of theirs

    os.environ['CSRF_COOKIE_SECURE'] = "True"

    os.environ['SESSION_COOKIE_SECURE'] = "True"

    # Performance Optimizations

    os.environ['CONN_MAX_AGE'] = "60"
    # TEMPLATE_LOADERS =

    # Error reporting
