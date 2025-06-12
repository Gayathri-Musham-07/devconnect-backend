from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView 
from .serializers import UserProfileSerializer, UserRegistrationSerializer, CustomTokenObtainPairSerializer
from django.db.models import Count, Q

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        profile_serializer = UserProfileSerializer(user, context={'request': request})
        return Response({
            "user": profile_serializer.data,
            "message": "User registered successfully"
        }, status=status.HTTP_201_CREATED)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, 
            data=request.data, 
            partial=partial,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class UserDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserProfileSerializer
    lookup_field = 'username'
    queryset = User.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        return Response(serializer.data)

class UserFollowingView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        # Get users that the current user follows
        following_users = User.objects.filter(followers=self.request.user)
        return following_users.annotate(
            followers_count=Count('followers'),
            following_count=Count('following')
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "count": queryset.count(),
            "results": serializer.data
        })

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.all()
        
        if self.request.user.is_authenticated:
            # Annotate with followers and following counts
            queryset = queryset.annotate(
                followers_count=Count('followers'),
                following_count=Count('following')
            )
            
            # Add is_followed status
            for user in queryset:
                user.is_followed = user.followers.filter(pk=self.request.user.pk).exists()
        
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, pk=None):
        try:
            user_to_follow = get_object_or_404(User, pk=pk)
            
            if request.user == user_to_follow:
                return Response(
                    {"error": "You cannot follow yourself."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            is_following = user_to_follow.followers.filter(pk=request.user.pk).exists()
            
            if is_following:
                user_to_follow.followers.remove(request.user)
                following_status = "Unfollowed"
            else:
                user_to_follow.followers.add(request.user)
                following_status = "Followed"

            # Refresh both users to get updated counts
            user_to_follow.refresh_from_db()
            request.user.refresh_from_db()

            # Get updated counts
            followers_count = user_to_follow.followers.count()
            following_count = request.user.following.count()

            # Get updated serialized data
            serializer = UserProfileSerializer(
                user_to_follow, 
                context={'request': request}
            )

            return Response({
                "status": following_status,
                "followers_count": followers_count,
                "following_count": following_count,
                "is_followed": not is_following,
                "user": serializer.data
            })

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request, *args, **kwargs):
        # Exclude the requesting user from the list
        queryset = self.get_queryset().exclude(pk=request.user.pk)
        
        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            context={'request': request}
        )
        return Response(serializer.data)