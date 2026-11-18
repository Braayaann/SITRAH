from django.urls import path
from tramites import views

urlpatterns = [
    path("api/health/", views.health),
    path("api/session/", views.session),
    path("api/login/", views.sign_in),
    path("api/logout/", views.sign_out),
    path("api/cases/", views.cases),
    path("api/cases/<int:pk>/", views.detail),
    path("api/cases/<int:pk>/correct/", views.correct),
    path("api/cases/<int:pk>/action/", views.action),
    path("api/cases/<int:pk>/documents/", views.upload),
    path("api/cases/<int:pk>/bundle/", views.bundle),
    path("api/documents/<int:pk>/", views.download),
]
