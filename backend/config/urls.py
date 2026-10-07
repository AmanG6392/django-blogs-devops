from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from blog import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("posts/", views.PostListCreate.as_view(), name="post-list"),
    path("posts/<int:post_id>/comments/", views.CommentListCreate.as_view(),
         name="comment-list"),
    path("health/", views.health, name="health"),
    path("readiness/", views.readiness, name="readiness"),
    path("", include("django_prometheus.urls")),  # exposes /metrics
]
