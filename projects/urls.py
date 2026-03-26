from django.urls import path
from . import views

urlpatterns = [
    path('', views.projects, name="projects"),
    path('for-you/', views.forYou, name="for-you"),
    path('saved/', views.savedProjects, name="saved-projects"),
    path('project-image/<str:pk>/', views.serve_project_image, name="serve-project-image"),
    path('project/<str:pk>/', views.project, name="project"),
    path('project/<str:pk>/vote/', views.voteProject, name='vote-project'),
    path('project/<str:pk>/comment/', views.commentProject, name='comment-project'),
    path('comment/<str:pk>/delete/', views.deleteComment, name='delete-comment'),
    path('project/<str:pk>/invite/', views.inviteCollaborator, name='invite-collaborator'),
    path('invite/<str:pk>/respond/', views.respondToInvite, name='respond-invite'),
    path('project/<str:pk>/remove-collaborator/<str:collab_id>/', views.removeCollaborator, name='remove-collaborator'),
    path('create-project/', views.createProject, name="create-project"),
    path('update-project/<str:pk>/', views.updateProject, name="update-project"),
    path('delete-project/<str:pk>/', views.deleteProject, name="delete-project"),
]               