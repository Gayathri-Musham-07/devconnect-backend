# serializers.py
from rest_framework import serializers
from .models import Post, Comment, Like
from django.contrib.auth import get_user_model

User = get_user_model()

class PostSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'image', 'created_at', 
                 'updated_at', 'likes_count', 'comments_count', 'is_liked']

    def get_author(self, obj):
        return {
            'id': obj.author.id,
            'username': obj.author.username,
            'profile_picture': obj.author.profile_picture.url if obj.author.profile_picture else None
        }

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at', 'updated_at', 
                 'parent_comment', 'replies']
        read_only_fields = ['author', 'replies']

    def get_author(self, obj):
        return {
            'id': obj.author.id,
            'username': obj.author.username,
            'profile_picture': obj.author.profile_picture.url if obj.author.profile_picture else None
        }

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []
