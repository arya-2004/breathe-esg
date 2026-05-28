from django.urls import path
from . import views

urlpatterns = [
    # auth
    path('api/login/', views.login_view),
    path('api/logout/', views.logout_view),

    # upload
    path('api/upload/sap/', views.upload_sap),
    path('api/upload/utility/', views.upload_utility),
    path('api/upload/travel/', views.upload_travel),

    # dashboard
    path('api/batches/', views.get_batches),
    path('api/records/', views.get_records),

    # review — analyst
    path('api/records/<int:record_id>/approve/', views.approve_record),
    path('api/records/<int:record_id>/reject/', views.reject_record),

    # batch management — admin only
    path('api/batches/<int:batch_id>/lock/', views.lock_batch),
    path('api/batches/<int:batch_id>/delete/', views.delete_batch),

    # user management — admin only
    path('api/users/', views.list_users),
    path('api/users/create/', views.create_user),
]