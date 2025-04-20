from django.urls import path
from django.contrib.auth import views as auth_views
from .views import dashboard_view,customer_list,collections_view,add_collection

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
      template_name="accounts/login.html",
      next_page="dashboard"
    ),name="login"),
    path('logout/', auth_views.LogoutView.as_view(next_page="login"),name="logout"),
    path('dashboard/',dashboard_view,name="dashboard"),
    path('customers/',customer_list,name="customer_list"),
    path('customers/colletions/',collections_view,name="collections"),
    path('customers/colletions/add',add_collection,name="add_collection"),
]
