from django.urls import path
from fileviewer.views import index, files, oauth_callback, download_multuple_files

urlpatterns = [
    path('', index, name='index'),
    path('files/', files, name='files'),
    path('oauth/callback/', oauth_callback, name='oauth_callback'),
    path('download-multuple-files/', download_multuple_files, name='download_multuple_files'),
]