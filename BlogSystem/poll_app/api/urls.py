from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from poll_app.api.views import (
    poll_detail,
    poll_list,
    poll_results,
    poll_statistics,
    poll_vote,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", poll_list, name="poll_list"),
    path("<int:poll_id>/", poll_detail, name="poll_detail"),
    path("statistics/", poll_statistics, name="poll_statistics"),
    path("<int:poll_id>/vote/", poll_vote, name="poll_vote"),
    path("<int:poll_id>/results/", poll_results, name="poll_results"),
]
