from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
# Import the required views here
from .views import UserProfileView, UserDetailView, UserViewSet, CustomTokenObtainPairView, UserRegistrationView, UserFollowingView

# Initialize DefaultRouter for UserViewSet
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Authentication Endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # User Registration
    path('users/register/', UserRegistrationView.as_view(), name='user-register'),

    # User Profile and Details
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    path('users/<str:username>/', UserDetailView.as_view(), name='user-detail'),

    # Endpoint for getting users that the logged-in user is following (me/following)
    path('users/me/following/', UserFollowingView.as_view(), name='user-following'),

    # Add this line for follow functionality on a specific user
    path('users/<int:pk>/follow/', UserViewSet.as_view({'post': 'follow'}), name='user-follow'),

    # Include router-generated URLs for UserViewSet (this will handle list and detail for users)
    path('', include(router.urls)),
]
