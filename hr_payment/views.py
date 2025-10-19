import json
import pprint

import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from stripe.error import SignatureVerificationError

from hr_payment.forms import PrePaymentEntryForm, PaymentEntryForm
from hr_shop.cart import Cart
from hr_shop.models import Price, Product

stripe.api_key = settings.STRIPE_API_KEY


@require_POST
def create_payment_intent(request) -> JsonResponse:
    cart = Cart(request)
    cart_subtotal = cart.get_cart_subtotal()

    try:
        data = json.loads(request.body)

        print('in create_payment_intent')
        print(f'data = {data}')

        intent = stripe.PaymentIntent.create(
            amount=cart_subtotal,
            currency='usd',
            automatic_payment_methods={
                'enabled': True,
            },
        )
        return JsonResponse({
            'clientSecret': intent['client_Secret']
        })
    except Exception as e:
        return JsonResponse({}, error=str(e), status=403)


def pre_payment_entry(request, cart):
    if request.method == 'POST':
        form = PrePaymentEntryForm(request.POST)
        if form.is_valid():
            shipping_address = form.extract_address()
            email = form.confirmed_email()
            payment_intent = stripe.PaymentIntent.create(
                amount=cart.get_cart_subtotal(),
                currency='usd',
                automatic_payment_methods={
                    'enabled': True,
                },
                payment_method_types=['card', ],
                receipt_email=email,
                shipping={
                    'address': {
                        'city': shipping_address.city,
                        'country': shipping_address.country,
                        'line1': shipping_address.street_address,
                        'line2': shipping_address.unit,
                        'postal_code': shipping_address.index,
                        'state': shipping_address.subdivision
                    },
                    'name': form.compile_name()
                }
            )
            if payment_intent:
                form = PaymentEntryForm()
                client_secret = payment_intent['client_secret']
                return redirect(request, 'payment_entry', {'form': form, 'client_secret': client_secret, 'cart': cart})

        if request.method == 'GET':
            form = PrePaymentEntryForm()
            return render(request, 'hr_payment/pre_payment_entry.html', {'form': form})


def payment_entry(request, cart):
    cart_subtotal = cart.get_cart_subtotal()
    payment_intent = stripe.PaymentIntent.create(
        amount=cart_subtotal,
        currency='usd',
        automatic_payment_methods={
            'enabled': True,
        },
        payment_method_types=['card', ]
    )
    if payment_intent:
        clientSecret = payment_intent['client_secret']


class StripeIntentView(View):
    def post(self, request, *args, **kwargs):
        try:
            req_json = json.loads(request.body)
            customer = stripe.Customer.create(email=req_json['email'])
            price = Price.objects.get(id=self.kwargs['pk'])
            intent = stripe.PaymentIntent.create(
                amount=price.price,
                currency='usd',
                customer=customer['id'],
                metadata={
                    'price_id': price.id
                }
            )
            return JsonResponse({
                'clientSecret': intent['client_scret']
            })
        except Exception as e:
            return JsonResponse({'error': str(e)})


class CreateCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        if build_cart_line_items:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=request.session.line_items,
                mode='payment',
                success_url=reverse('checkout_success'),
                cancel_url=reverse('checkout_cancel'),
            )
            return redirect(checkout_session.url)
        else:
            raise AttributeError


class SuccessView(TemplateView):
    template_name = "hr_payment/success.html"


class CancelView(TemplateView):
    template_name = 'hr_payment/cancel.html'


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.DJSTRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)

    except SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session['customer_details']['email']
        line_items = stripe.checkout.Session.list_line_items(session['id'])
        pprint.pprint(line_items)

        stripe_price_id = line_items['data'][0]['price']['id']
        price = Price.objects.get(stripe_price_id=stripe_price_id)
        product = price.product

        send_mail(
            subject="Your Purchase from Hella Reptilian!",
            message=f"Thank you for supporting the Reptilian Leadership of Today's Tomorrow with your recent purchase. Cold Blood Reigns! Download Link - {product.url}",
            recipient_list=[customer_email],
            from_email='foobar.zan'
        )
    elif event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        stripe_customer_id = intent['customer']
        stripe_customer = stripe.Customer.retrieve(stripe_customer_id)
        customer_email = stripe_customer['email']
        price_id = intent['metadata']['price_id']
        price = Price.objects.get(id=price_id)
        product = price.product

        send_mail(
            subject='Here is your product',
            message=f"Aye, a good trade. Have this link: {product.url}",
            recipient_list=[customer_email],
            from_email='admin@hellareptilian.com'
        )
    return HttpResponse(status=200)


class CustomPaymentView(TemplateView):

    template_name = "hr_payment/custom_payment.html"

    def get_context_data(self, **kwargs):
        product = Product.objects.get(name="Test Product")
        prices = Price.objects.filter(product=product)
        context = super(CustomPaymentView, self).get_context_data(**kwargs)
        context.update({
            'product': product,
            'prices': prices,
            'STRIPE_PUBLIC_KEY': settings.STRIPE_TEST_PUBLIC_KEY
        })
        return context

