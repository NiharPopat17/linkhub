from django.urls import path
from . import views

urlpatterns = [
    path('login/',views.loginUser,name= "login"),
    path('logout/',views.logoutUser,name= "logout"),
    path('register/',views.registerUser,name= "register"),

    path('', views.home, name="home"),
    path('developers/', views.profiles, name="profiles"),
    path('profile/<str:pk>/', views.userProfile, name="user-profile"),
    path('account/', views.userAccount, name="account"),
    path('edit-account/', views.editAccount, name="edit-account"),
    path('create-skill/', views.createSkill, name="create-skill"),
    path('update-skill/<str:pk>/', views.updateSkill, name="update-skill"),
    path('delete-skill/<str:pk>/', views.deleteSkill, name="delete-skill"),
    path('follow/<str:pk>/', views.followUser, name="follow-user"),
    path('following/', views.followingList, name="following-list"),
    path('bookmark/<str:pk>/', views.toggleBookmark, name='bookmark-project'),
    path('inbox/', views.inbox, name="inbox"),
    path('inbox/thread/<str:pk>/', views.conversationThread, name="conversation"),
    path('create-message/<str:pk>/', views.createMessage, name="create-message"),
    path('profile-image/<str:pk>/', views.serve_profile_image, name="serve-profile-image"),

]