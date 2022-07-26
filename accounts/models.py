from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import datetime
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from projects.models import Project, Subscription, Pricing, SubscriptionElement
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_extensions.db.models import TimeStampedModel
from django.db.models import F
import stripe


DEFAULT_ACTIVATION_DAYS = getattr(settings, 'DEFAULT_ACTIVATION_DAYS', 7)
DAYS_PER_YEAR = 365
TREES_PER_HECTARE = 500
CO2_CONSUMPTION_PER_HECTARE_PER_YEAR = 35000
CO2_CONSUMPTION_PER_TREE_PER_YEAR = (CO2_CONSUMPTION_PER_HECTARE_PER_YEAR / TREES_PER_HECTARE)
CO2_CONSUMPTION_PER_TREE_PER_DAY = (CO2_CONSUMPTION_PER_TREE_PER_YEAR / DAYS_PER_YEAR)



class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50)
    # ROLES DE USUARIO 
    VISITOR = 1 ## Unicamente ve información y dahboard de ejemplo
    ONETIME_INVESTOR = 2 ## Es inversionista de pago único
    SUBSCRIPTION_INVESTOR = 3 # Es inversionista con subscripción
    ADMIN = 4 # Administrador

    ROLE_CHOICES = [
        (VISITOR , 'Visitor'),
        (ONETIME_INVESTOR, 'One Time Investment'), 
        (SUBSCRIPTION_INVESTOR, 'Subscription Investment'),
        (ADMIN , 'Admin'),
        ]
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, blank=True, null=True)
    ## Género
    GENDER_MALE = 1
    GENDER_FEMALE = 2
    GENDER_CHOICES = [(GENDER_MALE, 'Male'), (GENDER_FEMALE, 'Female'),]
   
    # Campos del perfil 
    
    #gender         = models.IntegerField(choices=GENDER_CHOICES, blank=True, null=True)
    country        = CountryField(default="Co")
    city           = models.CharField(max_length=50, blank=True, null=True, verbose_name = "Ciudad")
    state          = models.CharField(max_length=50, blank=True, null=True)
    adress         = models.CharField(max_length=50, blank=True, null=True)
    zipcode        = models.CharField(max_length=100, blank=True, null=True)
    phone          = PhoneNumberField(blank=True, null=True)
    date_of_birth  = models.DateField(blank=True, null=True)
    rut            = models.CharField(max_length=100, blank=True, null=True)
    tax_register   = models.CharField(max_length=50, blank=True, null=True)
    facebook       = models.URLField(max_length=200, blank=True, null=True)
    instagram      = models.URLField(max_length=200, blank=True, null=True)
    twitter        = models.URLField(max_length=200, blank=True, null=True)
    web_domine     = models.URLField(max_length=200, blank=True, null=True)
    photo          = models.ImageField(upload_to='images/users/%Y/%m/%d',blank=True, null=True)
    
    @receiver(post_save, sender=User) #add this
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User) #add this
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()
        
    def __str__(self):
        return f'Perfil para usuario {self.user.username}'
    
    
    
    class Meta:
        verbose_name_plural=u'Perfiles de Usuario'
        
class CommissionAgent(User):
    people_related = models.PositiveIntegerField()
    percentage_per_person = models.FloatField()

    class Meta:
        verbose_name = "Commission agent"
        verbose_name_plural = "Commission agents"

    def __str__(self):
        return self.name + " " + self.last_name

class ProjectByInvestorManager(models.Manager):
    def all(self):
        return self.get_queryset().active()
    
    def get_by_id(self, id):
        qs = self.get_queryset().filter(id=id) # Product.objects == self.get_queryset()
        if qs.count() == 1:
            return qs.first()
        return None

    def get_by_investor(self, investor_id):
        qs = self.get_queryset().select_related('project').filter(investor=investor_id) #filter(investor=investor_id)
        if qs.count() >= 1:
            return qs
        return None
    
    def get_by_project(self, project_id):
        qs = self.get_queryset().filter(investor=project_id)
        if qs.count() >= 1:
            return qs
        return None

class ProjectByInvestor(models.Model):
    investor         = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_investor")
    project          = models.ForeignKey(Project, on_delete=models.CASCADE)
    commission_agent = models.ForeignKey(CommissionAgent, null=True, blank=True, on_delete=models.CASCADE, related_name="user_commission_agent")
    n_trees_subscription = models.PositiveIntegerField()
    n_trees_one_payment = models.PositiveIntegerField()
    co2_consumption  = models.FloatField(validators=[MinValueValidator(0.0)], null=True, blank=True)
    active           = models.BooleanField(default=True)

    objects = ProjectByInvestorManager()

    class Meta:
        verbose_name = "Project by investor"
        verbose_name_plural = "Projects by investor"
    
    def n_trees(self):
        return self.n_trees_subscription + self.n_trees_one_payment


    def __str__(self):
        return str(self.pk) + "_" + self.investor.username + "_" + self.project.name


@receiver(post_save, sender=User)
def post_email_confirmed(sender, instance, created, **kwargs):
    print("entrooo")
    if created:
        user = instance
        subscription = Subscription.objects.create(
            user=user,
            status="trialing",
            n_projects=0
        )

        #Crear cliente en stripe
        stripe_customer = stripe.Customer.create(
            email=user.email, 
            name= user.first_name +' ' + user.last_name 
        )
        
        stripe_subscription = stripe.Subscription.create(
            customer=stripe_customer["id"],
            items=[{'price': settings.STRIPE_FREE_PRICE}],
            trial_period_days=20
        )

        subscription.status=stripe_subscription["status"]
        subscription.stripe_subscription_id = stripe_subscription["id"]
        subscription.save()
        profile = Profile.objects.get(user_id=user.id)
        profile.stripe_customer_id=stripe_customer["id"]
        profile.save()

