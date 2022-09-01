import re
import pandas as pd
import numpy as np
import json
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.shortcuts import render
from projects.models import Project, Order
from accounts.models import ProjectByInvestor
from django.core import serializers
from django.template import loader
from django.http import JsonResponse
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pandas import json_normalize



def invest_json(request):
    usuario = request.user
    pbi= ProjectByInvestor.objects.filter(investor=usuario)
    projects_id= list(map(lambda x: x.project_id, pbi))
    api = {}
    resumen = {}
    inv_general = 0
    cap_general = 0
    rentabilidad= 0.0094
    for project_id in projects_id:
        
        fecha = Project.objects.get(pk=project_id).plantation_date
        hoy = datetime.today().date()
        api_fecha = {}
        total_trees = 0
        cap = 0
        cap_tot = 0
        n= 0
        
        cap_final = 0
        while fecha < hoy:
            fechafin = fecha + relativedelta(months=1)
            ordenes = Order.objects.filter(ordered_date__gte=fecha, ordered_date__lt= fechafin, user=usuario)
            fechas_ordenes = list(map(lambda x: str(x.ordered_date.date()), ordenes))
            #print(fecha)
            #print(fecha + relativedelta(months=1))
            #print(ordenes.count())
            new_trees = 0
            for orden in ordenes:
                if orden.ordered:
                    order_items = orden.items.filter(project=project_id)
                    new_trees += sum(list(map(lambda x: x.quantity, order_items )))
            total_trees += new_trees
            price = Project.objects.get(pk=project_id).price_onepayment.price
            valor_invertido = total_trees * price
            vi = "{:.2f}".format(int(valor_invertido or 0) /100)
            rent_acu = ((rentabilidad+1)**n)-1
            utilidad = rent_acu * cap
            rent = "{:.2f}".format(rentabilidad* 100)
            util_str = "{:.4f}".format(utilidad)
            cap_tot = utilidad + (valor_invertido/100)
            cap_tot__str = "{:.3f}".format(cap_tot)
            inversion = {'new_trees': new_trees, 'total_trees': total_trees, 'valor_invertido': vi, 'rentabilidad': rent, 'utilidad': util_str, 'capital': cap_tot__str}
            api_fecha[str(fecha)] = inversion
            fecha =fecha + relativedelta(months=1)
            cap = cap_tot
            n += 1
        api[Project.objects.get(pk=project_id).name] = api_fecha
        proyecto  = Project.objects.get(pk=project_id).name
        resumen[proyecto] = api[proyecto][list(api[proyecto].keys())[-1]]
        
    return [api, resumen]

def invest_api(request):
    datos = invest_json(request)[0]
    return JsonResponse(datos)


def invest(request): 
    datos = invest_api(request)
    
    #df = json_normalize(datos)
    print(type(datos))
    return render(request, 'invest.html',{
            'table': "dat",
        })

def dashboard(request):
    projects = Project.objects.all()
    invest = invest_json(request)
    datos = invest[0]
    resumen = invest[1]
    ## Gráfca inversion
    user_projects = Project.objects.filter(name__in= list(datos.keys()))
    ## Gráfica torta y  ## Grafica árboles
    suma_inversion = 0
    suma_utilidad = 0
    suma_capital = 0
    suma_arboles_acumulados= 0
    print(resumen)
    
    
    for key in resumen:
        suma_inversion += float(resumen[key]['valor_invertido'])
        suma_utilidad += float(resumen[key]['utilidad'])
        suma_capital += float(resumen[key]['capital'])
        #suma_arboles_nuevos += float(resumen[key]['new_trees'])
        suma_arboles_acumulados += resumen[key]['total_trees']
    
    print(suma_inversion)
    suma_inversion_str = "{:.2f}".format(suma_inversion)
    suma_utilidad_str = "{:.2f}".format(suma_utilidad)
    suma_capital_str = "{:.2f}".format(suma_capital)
    #suma_arboles_nuevos = "{:.2f}".format(suma_arboles_nuevos)
    #suma_arboles_acumulados = "{:.2f}".format(suma_arboles_acumulados) 
    resumen_general = [suma_inversion_str, suma_utilidad_str, suma_capital_str]
    return render(request, 'argon.html',{
        'projects': projects,
        'user_projects': user_projects,
        'datos': datos,
        'resumen_general': resumen_general,
        'resumen_dict': resumen,
        'inversion_total': resumen_general[0],
        'utilidad_total': resumen_general[1],
        'capital_total': resumen_general[2],
        'arboles_total': suma_arboles_acumulados,
        'rentabilidad': '0.94 %',
        
    })
    

