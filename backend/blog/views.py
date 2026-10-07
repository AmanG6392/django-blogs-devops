import logging

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics

from .models import Author, Comment, Post
from .serializers import CommentSerializer, PostSerializer

logger = logging.getLogger("blog")


def _author_for(user):
    author, _ = Author.objects.get_or_create(
        user=user, defaults={"display_name": user.get_username()})
    return author


class PostListCreate(generics.ListCreateAPIView):
    queryset = Post.objects.select_related("author").all()
    serializer_class = PostSerializer

    def perform_create(self, serializer):
        post = serializer.save(author=_author_for(self.request.user))
        logger.info("post created id=%s user=%s", post.pk, self.request.user)


class CommentListCreate(generics.ListCreateAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        return Comment.objects.filter(post=post).select_related("author")

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        c = serializer.save(post=post, author=_author_for(self.request.user))
        logger.info("comment created id=%s post=%s user=%s", c.pk, post.pk,
                    self.request.user)


def health(request):
    return JsonResponse({"status": "ok"})


def readiness(request):
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
    except Exception:
        logger.exception("readiness check failed")
        return JsonResponse({"status": "not ready"}, status=503)
    return JsonResponse({"status": "ready"})
