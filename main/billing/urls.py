from django.urls import path
from . import views

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('users/', views.UserListApiView.as_view()),
    path('users/<int:telegram_id>', views.UserDetailApiView.as_view()),
    path('peers/', views.PeerListAllApiView.as_view()),
    path('peers/<int:pk>', views.PeerDetailApiView.as_view()),
    path('peers_of_user/<str:telegram_id>', views.PeerListApiView.as_view()),
    path('dns/', views.DNSListApiView.as_view()),
    path('allowed_networks/', views.AllowedNetworksListApiView.as_view()),
]
