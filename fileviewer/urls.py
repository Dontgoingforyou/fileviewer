from django.urls import path
from fileviewer.views import index, files, oauth_callback

urlpatterns = [
    path('', index, name='index'),
    path('files/', files, name='files'),
    path('oauth/callback/', oauth_callback, name='oauth_callback'),
]