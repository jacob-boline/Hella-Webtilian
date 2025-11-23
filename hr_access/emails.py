# hr_access/emails.py

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

def send_claim_email(request, user):
    """
    Sends a magic link to activate the shadow account of an email and set the password.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    url = request.build_absolute_url(f'/access/account/claim/{uidb64}/{token}/')
    ctx = {
        'user': user,
        'claim_url': url,
        'site_name': getattr(settings, 'SITE_NAME', 'Hella Reptilian!'),
    }
    subject = f"Finish setting up your {ctx['site_name']} account"
    text_body = render_to_string('hr_access/email/claim_account.txt', ctx)
    html_body = render_to_string('hr_access/email/claim_account.html', ctx)

    send_mail(
        subject=subject,
        message=text_body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        recipient_list=[user.email],
        html_message=html_body,
        fail_silently=False,
    )
