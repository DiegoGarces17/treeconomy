from django.forms import ModelForm 
from django.urls import reverse
from django import forms
from .models import OrderItem, Project, Bill, Subscription
from accounts.models import ProjectByInvestor, User
from phonenumber_field.formfields import PhoneNumberField

class ProjectForm(forms.ModelForm):  
    class Meta:
        model = Project
        fields = "__all__"
        exclude = ('slug',)
        
class ProjectByInvestorForm(forms.ModelForm):  
    total_price = forms.FloatField(
        widget=forms.TextInput(attrs={'readonly':'readonly'})
    )
    unit_price = forms.FloatField(
        widget=forms.TextInput(attrs={'readonly':'readonly'})
    )
    class Meta:
        model = ProjectByInvestor
        fields = "__all__"

class AddToCartForm(forms.ModelForm):
    class Meta: 
        model = OrderItem
        fields = ['quantity', 'type_inversion']
    
    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id')
        project = Project.objects.get(name=project_id)
        super().__init__(*args, **kwargs)
        for field in ['type_inversion']:
            self.fields[field].widget.attrs['class'] = 'form-select'
        
class SubscriptionForm(forms.ModelForm):
    OPTIONS = (('Active', 'active'), ('Closed', 'closed'), ('On hold', 'On hold'))
    status = forms.ChoiceField(choices=OPTIONS, required=True) 

    class Meta:
        model = Subscription
        fields = ('user', 'n_projects')
    
    def clean_status(self):
        status = self.cleaned_data['status']
        if not status:
            raise forms.ValidationError('Tienes que especificar un estado para esta suscripción.')
        
        return status

class BillForm(forms.Form):
    
    #selected_billing_address = forms.ModelChoiceField(
    #    Bill.objects.none(), required=False,
    #    label="Seleccione un factura antigua:"
    #)
    comprador_nombre = forms.CharField(label="Comprador: Nombre completo")
    comprador_id = forms.CharField(label="Comprador: Identificación")
    comprador_email = forms.EmailField(label="Comprador: Correo electrónico")
    comprador_phone = PhoneNumberField(widget=forms.TextInput(), label="Comprador: Teléfono") 
    beneficiario_nombre = forms.CharField(label="Tercero de confianza: Nombre completo")
    beneficiario_id = forms.CharField(label="Tercero de confianza: Identificación")
    beneficiario_email = forms.EmailField(label="Tercero de confianza: Correo electrónico")
    beneficiario_phone = PhoneNumberField(widget=forms.TextInput(), label="Tercero de confianza: Teléfono")  
    billing_address_line_1 = forms.CharField(label="Dirección")
    billing_address_line_2 = forms.CharField(label="Casa, Apartamento, etc.")
    billing_zip_code = forms.CharField(label="Código postal")
    billing_city = forms.CharField(label="Ciudad")
    
      
    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')
        super().__init__(*args, **kwargs)
        if user_id:       
            user = User.objects.get(id=user_id)
            
            billing_address_qs = Bill.objects.filter(
                user=user,
                address_type='B'
            )
            
            #self.fields['selected_billing_address'].queryset = billing_address_qs
        
        