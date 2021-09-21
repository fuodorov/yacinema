from django.urls import path, include

from api.v1.urls import router_v1

urlpatterns = [
    path('v1/', include(router_v1.urls))
]
