from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.utils.http import is_safe_url
from django.views import generic
from django.conf import settings
from requests import request
from django.views.generic.base import View
from accounts.models import Profile
from projects.models import OrderItem, Pricing, Subscription, Order
from .utils import get_or_set_order_session
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib import messages
from .models import BillingProfile, Card
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.template.loader import get_template
from .utils import render_to_pdf

import stripe

# pdf



stripe.api_key = settings.STRIPE_PRIVATE_KEY

def generatePdf(request,pk):
    pdf = render_to_pdf('billing/plantilla_bill.html',pk)
    return HttpResponse(pdf, content_type='application/pdf')

class PlantillaOrderView(generic.TemplateView):
    model = Order
    template_name = 'billing/plantilla_bill.html'
    
    def get_context_data(self, *args, **kwargs):
        context = super(PlantillaOrderView, self).get_context_data(**kwargs)
        context["order"] = self.get_object()
        return context
    
    def get_object(self):
        return get_object_or_404(Order, pk = self.kwargs["pk"])
    

class CarteraView(generic.TemplateView):
    template_name = 'billing/cartera.html'
    
    def get_context_data(self, *args, **kwargs):
        context = super(CarteraView, self).get_context_data(**kwargs)
        orders_list  = Order.objects.filter(user=self.request.user)
        context["orders_list"] = orders_list
        return context
    

def payment_method_view(request):
    #next_url = 
    # if request.user.is_authenticated():
    #     billing_profile = request.user.billingprofile
    #     my_customer_id = billing_profile.customer_id

    billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
    if not billing_profile:
        return redirect("/cart")
    next_url = None
    next_ = request.GET.get('next')
    #next_ = request.GET['next']
    print(next_)
    if is_safe_url(next_, request.get_host()):
        next_url = next_
    return render(request, 'billing/payment-method.html', {"publish_key": STRIPE_PUB_KEY, "next_url": next_url})

def payment_method_createview(request):
    
    if request.method == "POST" and request.is_ajax():
        print('im in create')
        billing_profile, billing_profile_created = BillingProfile.objects.new_or_get(request)
        if not billing_profile:
            return HttpResponse({"message": "Cannot find this user"}, status=401)
        token = request.POST.get("token")
        if token is not None:
            print('token is not none')
            Card.objects.add_new(billing_profile, token)
        return JsonResponse({"message": "Success! Your card was added."})
    
    return HttpResponse("error", status=401)

class CheckoutView(View):
    def get(self, request, *args, **kwargs):
        subscription =request.user.subscription

        order =  get_or_set_order_session(self.request)
        #item = order.items.all()[0]
        #pricing = get_object_or_404(Pricing, price=item.project.price.price)
        #if subscription.pricing == pricing and subscription.is_active:
        #    messages.info(request, "Actualmente ya cuentas con una suscripción activa del mismo projecto, puedes aumentar tu número de árboles por mes. ")
        #    return redirect("projects:cart")

        context={
            'order': order,
            "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY
        }

        #if subscription.is_active and subscription.pricing.stripe_price_id != "price_1LB5yVJUacQRIX890kzKsUYJ":
        #    return render(request, "billing/change.html", context)

        return render(request, 'billing/checkout.html', context)

class CreateSubscriptionView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        profile = Profile.objects.get(user_id=request.user.id)
        customer_id = profile.stripe_customer_id
        orden =  get_or_set_order_session(self.request)
        try:
            #vincular el metodo de pago al cliente
            stripe.PaymentMethod.attach(
                data['paymentMethodId'],
                customer=customer_id
            )

            #configuurar metodo de pago prederterminado del cliente
            iss= stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': data['paymentMethodId'],
                },
            )
            
            ## pagos unicos
            mis_cantidades = {}
            for item in orden.items.filter(type_inversion = 'O'):
                mis_cantidades[item.project.price_onepayment.stripe_price_id] = item.quantity 
                mis_precios = list(mis_cantidades.keys())
            
            
            for item in list(mis_cantidades.keys()): 
                domain_url = settings.DOMINIO_URL  
                #session = create_checkout_session(item, mis_cantidades, customer_id)
                try:
                    # Create a git  with the order amount and currency
                    monto = Pricing.objects.filter(stripe_price_id=item)[0].price * mis_cantidades[item]
                    print(monto)
                    intent = stripe.PaymentIntent.create(
                        amount= monto,
                        currency='usd',
                        customer=customer_id,
                        metadata = {
                            'price': item,
                            'quantity': mis_cantidades[item],   
                        },
                        automatic_payment_methods={
                            'enabled': True,
                        },
                    )
                    stripe.PaymentIntent.confirm(
                        intent.id,
                        payment_method=data['paymentMethodId'],
                       
                        return_url= domain_url + '/billing/success/',
                    )
                except Exception as e:
                    print(str(e))

            #crear suscripcion
            subscription = request.user.subscription
            print(subscription.status)
            stripe_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                expand=['latest_invoice.payment_intent'],
                trial_end="now"
            )
            
            subscription.status=stripe_subscription.status
            print(subscription.status)
            subscription.save()  
            
            
            # Buscamos los items de esa suscripcion de stripe
            items_existentes = stripe.SubscriptionItem.list(
                subscription = stripe_subscription.id
            )
            mis_cantidades = {}
            for item in orden.items.filter(type_inversion = 'M'):
                mis_cantidades[item.project.price_subscription.stripe_price_id] = item.quantity 
            mis_precios = list(mis_cantidades.keys())
            
            # Busca subscription Item o por el contrario la crea
            subidos= []
            for item in items_existentes:
                if item['price']["id"] in mis_precios:
                    new_quantity = mis_cantidades[item['price']["id"]]
                    actual_quantity = item['quantity']
                    stripe.SubscriptionItem.modify(
                        item.id,
                        quantity= actual_quantity + new_quantity
                    )
                    subidos.append(item['price']["id"])
            
            for k in subidos:
                mis_cantidades.pop(k)
            for item in list(mis_cantidades.keys()): 
                stripe.SubscriptionItem.create(
                    subscription=stripe_subscription.id,
                    price= item,
                    quantity= mis_cantidades[item]
                )
                
            
            datasub = {}
            datach = {}
            
            datasub.update(stripe_subscription)
            #datach.update(session)
            
            data= [datasub, datach]
            return Response(data)
        except Exception as e:
            return Response({
                "error": {'message': str(e)}
            })

class RetryInvoiceView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        profile = Profile.objects.get(user_id=request.user.id)
        customer_id = profile.profile.stripe_customer_id
        
        try:

            stripe.PaymentMethod.attach(
                data['paymentMethodId'],
                customer=customer_id,
            )
            # Set the default payment method on the customer
            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': data['paymentMethodId'],
                },
            )

            invoice = stripe.Invoice.retrieve(
                data['invoiceId'],
                expand=['payment_intent'],
            )
            data = {}
            data.update(invoice)

            return Response(data)
        except Exception as e:

            return Response({
                "error": {'message': str(e)}
            })

class ChangeSubscriptionView(APIView):
    def post(self, request, *args, **kwargs):
        
        subscription_id = request.user.subscription.stripe_subscription_id
        subscription = stripe.Subscription.retrieve(subscription_id)
        try:
            updatedSubscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': request.data["priceId"],
                }],
                proration_behavior="always_invoice"
            )

            data = {}
            data.update(updatedSubscription)
            return Response(data)
        except Exception as e:
            return Response({
                "error": {'message': str(e)}
            })

class PaymentSuccessView(generic.TemplateView):
    
    template_name = "billing/success.html"
    
    def get_context_data(self, *args, **kwargs):
            context = super(PaymentSuccessView, self). get_context_data(**kwargs)
            order =  get_or_set_order_session(self.request)
            order.ordered = True
            order.save()
            context["order"] = order
            self.request.session['order_id'] = None
            return context
        
class PaymentCancelledView(generic.TemplateView):
    template_name = "billing/cancelled.html"
 
class PaymentFailedView(generic.TemplateView):
    template_name = "billing/failed.html"
    def get_context_data(self, *args, **kwargs):
        context = super(PaymentFailedView, self). get_context_data(**kwargs)
        context["order"] = get_or_set_order_session(self.request)
        return context

class OrderHistoryListView(generic.TemplateView):
    pass

@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLIC_KEY}
        return JsonResponse(stripe_config, safe=False)

@csrf_exempt
def create_checkout_session(item, mis_cantidades, customer_id):
    domain_url = settings.DOMINIO_URL
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                    {
                    'price': item,
                    'quantity': mis_cantidades[item],
                    
                    },
                ],
                mode='payment',
                payment_method_types=['card',],
                customer=customer_id,
                success_url=domain_url + '/billing/success/',
                cancel_url=domain_url + '/billing/cancelled/',
        )
        return checkout_session
    except Exception as e:
        return JsonResponse({'error': str(e)})