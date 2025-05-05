from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views
from .forms import LoginForm

app_name = 'production'

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    # — Аутентификация —
    path('login/', auth_views.LoginView.as_view(template_name='production/login.html', authentication_form=LoginForm),
         name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('dashboard/', views.DashboardRedirect.as_view(), name='dashboard'),

    # — Дашборды по ролям —
    path('dashboard/seller/', views.SellerDashboard.as_view(), name='seller_dashboard'),
    path('dashboard/manager/', views.ManagerDashboard.as_view(), name='manager_dashboard'),
    path('dashboard/worker/', views.WorkerDashboard.as_view(), name='worker_dashboard'),
    path('dashboard/table/', views.Table.as_view(), name='table'),

    # — Старая часть: CRUD для базовых моделей —
    # Rang
    path('rangs/', views.RangList.as_view(), name='rang_list'),
    path('rangs/add/', views.RangCreate.as_view(), name='rang_add'),
    path('rangs/<int:pk>/edit/', views.RangUpdate.as_view(), name='rang_edit'),

    # Jarayon
    path('jarayon/', views.JarayonList.as_view(), name='jarayon_list'),
    path('jarayon/add/', views.JarayonCreate.as_view(), name='jarayon_add'),
    path('jarayon/<int:pk>/edit/', views.JarayonUpdate.as_view(), name='jarayon_edit'),

    # Zakaz Proizvodsto (orders)
    path('orders/add/', views.ZakazCreate.as_view(), name='zakaz_create'),
    path('orders/<int:pk>/', views.ZakazDetail.as_view(), name='zakaz_detail'),
    path('orders/<int:pk>/edit/', views.ZakazUpdate.as_view(), name='zakaz_edit'),

    # Production workflow
    path('orders/<int:zakaz_pk>/start/', views.ZakazStartProduction.as_view(), name='zakaz_start_production'),
    path('production/<int:zp_pk>/stage/<int:jarayon_pk>/',
         views.StageProcess.as_view(), name='stage_process'),

    # Production workflow
    path('orders/<int:pk>/sales/', views.ZakazSalesView.as_view(), name='zakaz_sales'),
    # Sklad
    path('stock/', views.SkladList.as_view(), name='sklad_list'),
    path('stock/<int:pk>/edit/', views.SkladUpdate.as_view(), name='sklad_edit'),

    # Подтвердить одну продажу
    path('sales/confirmations/', views.WarehouseConfirmList.as_view(), name='warehouse_confirmations'),
    path('sales/<int:pk>/confirm/', views.ConfirmSale.as_view(), name='confirm_sale'),

    path('sotuv/', views.SotuvList.as_view(), name='sotuv'),
    path('mijoz/', views.ClientDashboard.as_view(), name='mijoz'),
    path('zakaz_list/', views.ZakazList.as_view(), name='zakaz_list'),
    path('mijoz/add/', views.MijozCreate.as_view(), name='mijoz_create'),
    path('mijoz/<int:pk>/edit/', views.MijozUpdate.as_view(), name='mijoz_edit'),

    # Продукты
    path('products/', views.MahsulotList.as_view(), name='mahsulot_list'),
    path('products/add/', views.MahsulotCreate.as_view(), name='mahsulot_add'),
    path('products/<int:pk>/edit/', views.MahsulotUpdate.as_view(), name='mahsulot_edit'),
]
