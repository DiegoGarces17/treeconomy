from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views import generic
from .forms import ProjectForm, AddToCartForm, BillForm
from .models import Project, OrderItem, Bill
from rolepermissions.decorators import has_role_decorator
from billing.utils import get_or_set_order_session
from accounts import views 
from accounts.models import User
from django.contrib import messages

# Create your views here.
class ProjectListView(generic.ListView):
    model = Project
    template_name = 'project_list.html'

    def get_queryset(self):
        return Project.objects.get_queryset()

    def get_context_data(self, *args, **kwargs):
        context = super(ProjectListView, self).get_context_data(*args, **kwargs)
        context["name"] = 'List of all active projects'
        return context

class ProjectDetailListView(generic.FormView):
    model = Project
    template_name = 'project_detail.html'
    form_class = AddToCartForm
    
    def get_queryset(self):
        return Project.objects.get_queryset()
    
    def get_context_data(self, *args, **kwargs):
        context = super(ProjectDetailListView, self).get_context_data(*args, **kwargs)
        context["project"] = self.get_object()
        context["order"] = get_or_set_order_session(self.request)
        return context
    
    def get_object(self):
        return get_object_or_404(Project, slug = self.kwargs["slug"])
    
    def get_success_url(self):
        return reverse("summary")
    
    def get_form_kwargs(self):
        kwargs = super(ProjectDetailListView, self).get_form_kwargs()
        kwargs["project_id"] = self.get_object().name
        return kwargs
    
    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        
        project = self.get_object()
        type_inversion = form.cleaned_data['type_inversion']
        item_filter = order.items.filter(project = project, type_inversion= type_inversion)
        if item_filter.exists():
            item = item_filter.first()
            item.quantity += int(form.cleaned_data['quantity'])
            item.save()
        else: 
            new_item = form.save(commit=False)
            new_item.project = project
            new_item.order = order
            new_item.save()
        return super(ProjectDetailListView, self).form_valid(form)

class CartView(generic.TemplateView):
    template_name = 'cart.html'
    
    def get_context_data(self, *args, **kwargs):
        context = super(CartView, self).get_context_data(**kwargs)
        context["order"] = get_or_set_order_session(self.request)
        return context
   
class IncreaseQuantityCartView(generic.View):
    def get(self, request, *args, **kwargs):    
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.quantity += 1
        order_item.save()
        return redirect("summary")

class DecreaseQuantityCartView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        if order_item.quantity <= 1:
            order_item.delete()
        else: 
            order_item.quantity -= 1
            order_item.save()
        return redirect("summary")
    
class RemoveFromCartView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.delete()
        return redirect("summary")
 
class FacturacionView(generic.FormView): 
    template_name= 'facturacion.html' 
    form_class = BillForm  

    def get_success_url(self):
        return reverse("billing:checkout")

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        #selected_billing_address =form.cleaned_data.get('selected_billing_address')
        selected_billing_address = False
        if selected_billing_address:
            print("hay factura")
            order.bill = selected_billing_address
        else:
            bill = Bill.objects.create(
                address_type = 'B',
                user =self.request.user,
                comprador_nombre=form.cleaned_data['comprador_nombre'],
                comprador_id=form.cleaned_data['comprador_id'],
                comprador_email= form.cleaned_data['comprador_email'],
                comprador_phone= form.cleaned_data['comprador_phone'],
                beneficiario_nombre=form.cleaned_data['beneficiario_nombre'],
                beneficiario_id=form.cleaned_data['beneficiario_id'],
                beneficiario_email= form.cleaned_data['beneficiario_email'],
                beneficiario_phone= form.cleaned_data['beneficiario_phone'],
                address_line_1=form.cleaned_data['billing_address_line_1'],
                address_line_2=form.cleaned_data['billing_address_line_2'],
                zip_code=form.cleaned_data['billing_zip_code'],
                city=form.cleaned_data['billing_city']
            )
            bill.save()
            order.bill = bill
            
        order.save()
        messages.info(self.request, "Agregaste exitosamente tu información de facturación")
        return super(FacturacionView, self).form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super(FacturacionView, self).get_form_kwargs()
        kwargs['user_id'] = self.request.user.id
        return kwargs
    
    def get_context_data(self, *args, **kwargs):
        context = super(FacturacionView, self).get_context_data(**kwargs)
        context["order"] = get_or_set_order_session(self.request)
        last_bill = Bill.objects.filter(user=self.request.user.id).latest('id')
        dict = {
            'id': last_bill.id,
            'user_id': last_bill.user.id, 
            'comprador_nombre': last_bill.comprador_nombre, 
            'comprador_id': last_bill.comprador_id, 
            'comprador_email': last_bill.comprador_email, 
            'comprador_phone':   last_bill.comprador_phone,
            'beneficiario_nombre': last_bill.beneficiario_nombre, 
            'beneficiario_id': last_bill.beneficiario_id, 
            'beneficiario_email': last_bill.beneficiario_email, 
            'beneficiario_phone': last_bill.beneficiario_phone,
            'billing_address_line_1': last_bill.address_line_1, 
            'billing_address_line_2': last_bill.address_line_2, 
            'billing_address_type': last_bill.address_type, 
            'billing_city': last_bill.city, 
            'billing_zip_code': last_bill.zip_code
        }
        form = BillForm(user_id=self.request.user.id, initial = dict)
        print(last_bill.address_line_1)
        context["form"] = form
        print(context["form"])
        return context
   
@has_role_decorator('admin')   
def crear(request):
    #import pdb; pdb.set_trace()
    formulario = ProjectForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('/projects')
    return render(request, "create.html", {'formulario': formulario})

@has_role_decorator('admin')  
def eliminar(request, pk):
  project = Project.objects.get(pk=pk)
  #import pdb; pdb.set_trace() 
  project.delete()
  return redirect('projects')

@has_role_decorator('admin')  
def editar(request, pk):
    project = Project.objects.get(pk=pk)
    formulario = ProjectForm(request.POST or None, request.FILES or None, instance=project)
     
    if formulario.is_valid() and request.POST:
        formulario.save()
        return redirect('projects')
    else:
        errores = formulario.errors

    return render(request, "edit.html", {'formulario': formulario, 'errores': errores})
    

    
