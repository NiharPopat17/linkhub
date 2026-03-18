from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q, F
from .models import Project, Tag
from .forms import ProjectForm, ReviewForm
from django.contrib.auth.decorators import login_required
from .utils import searchProjects, paginateProjects
from django.contrib import messages

def projects(request):
    projects, search_query = searchProjects(request)

    if not search_query:
        if request.user.is_authenticated:
            following_ids = list(request.user.profile.following.values_list('id', flat=True))
            projects = projects.filter(owner__id__in=following_ids).order_by('-created')
        else:
            projects = projects.order_by('-vote_ratio', '-vote_total')

    custom_range, projects = paginateProjects(request, projects, 6)
    context = {
        'projects': projects,
        'search_query': search_query,
        'custom_range': custom_range,
    }
    return render(request, 'projects/projects.html', context)

def project(request,pk):
    projectObj = Project.objects.get(id=pk)
    is_owner = request.user.is_authenticated and request.user.profile == projectObj.owner
    if not is_owner:
        viewed_projects = request.session.get('viewed_projects', [])
        if str(pk) not in viewed_projects:
            Project.objects.filter(pk=pk).update(views=F('views') + 1)
            viewed_projects.append(str(pk))
            request.session['viewed_projects'] = viewed_projects
        projectObj.refresh_from_db()
    show_views = not is_owner
    form = ReviewForm()
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, 'You must be logged in to leave a review.')
            return redirect('login')
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Prevent duplicate reviews
            if request.user.profile.id in projectObj.reviewers:
                messages.warning(request, 'You have already reviewed this project!')
                return redirect('project', pk=projectObj.id)
            review = form.save(commit=False)
            review.owner = request.user.profile
            review.project = projectObj
            review.save()
            projectObj.getVoteCount()
            messages.success(request, 'Your review was added successfully!')
            return redirect('project', pk=projectObj.id)    
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = request.user.profile.bookmarks.filter(id=pk).exists()
    return render(request, 'projects/single-project.html', {'project': projectObj, 'form': form, 'show_views': show_views, 'is_bookmarked': is_bookmarked})

@login_required(login_url='login')
def forYou(request):
    try:
        from ml.recommendations import get_project_recommendations
        projects = get_project_recommendations(request.user.profile, limit=50)
    except Exception:
        projects = []
    custom_range, projects = paginateProjects(request, projects, 6)
    context = {
        'projects': projects,
        'custom_range': custom_range,
    }
    return render(request, 'projects/for-you.html', context)

@login_required(login_url='login')
def createProject(request):
    profile = request.user.profile  
    form = ProjectForm()
    if request.method == 'POST':
        newtags = request.POST.get('newtags').replace(',',  " ").split()
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = profile
            project.save()
            for tag in newtags:
                tag, created = Tag.objects.get_or_create(name=tag)
                project.tags.add(tag)   
            return redirect('account')

    context = {'form': form}
    return render(request, 'projects/project_form.html', context)

@login_required(login_url='login')
def updateProject(request, pk):
    profile = request.user.profile
    project = profile.project_set.get(id=pk)
    form = ProjectForm(instance=project)
    if request.method == 'POST':
        newtags = request.POST.get('newtags').replace(',',  " ").split()
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            project = form.save(commit=False)
            project.save()
            for tag in newtags:
                tag, created = Tag.objects.get_or_create(name=tag)
                project.tags.add(tag)   
            return redirect('account')

    context = {'form': form, 'project': project}
    return render(request, 'projects/project_form.html', context)

@login_required(login_url='login')
def deleteProject(request, pk):
    profile = request.user.profile
    project = profile.project_set.get(id=pk)
    if request.method == 'POST':
        project.delete()
        return redirect('account')
    context = {'object': project}
    return render(request, 'delete_template.html', context)