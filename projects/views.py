from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q, F
from .models import Project, Tag, CollaborationInvite, Review, ProjectComment
from .forms import ProjectForm
from django.contrib.auth.decorators import login_required
from .utils import searchProjects, paginateProjects
from django.contrib import messages
from users.models import Profile

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

def project(request, pk):
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

    user_vote = None
    if request.user.is_authenticated:
        existing = Review.objects.filter(owner=request.user.profile, project=projectObj).first()
        if existing:
            user_vote = existing.value

    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = request.user.profile.bookmarks.filter(id=pk).exists()

    comments = projectObj.comments.select_related('owner').order_by('-created')

    return render(request, 'projects/single-project.html', {
        'project': projectObj,
        'show_views': show_views,
        'is_bookmarked': is_bookmarked,
        'user_vote': user_vote,
        'comments': comments,
    })


@login_required(login_url='login')
def voteProject(request, pk):
    """POST-only. Toggle or change vote on a project."""
    projectObj = get_object_or_404(Project, id=pk)

    if request.user.profile == projectObj.owner:
        messages.error(request, 'You cannot vote on your own project.')
        return redirect('project', pk=pk)

    if request.method == 'POST':
        value = request.POST.get('value', '')
        if value not in ('up', 'down'):
            messages.error(request, 'Invalid vote.')
            return redirect('project', pk=pk)

        review, created = Review.objects.get_or_create(
            owner=request.user.profile,
            project=projectObj,
            defaults={'value': value}
        )
        if not created:
            if review.value == value:
                review.delete()
            else:
                review.value = value
                review.save()

        projectObj.getVoteCount()

    return redirect('project', pk=pk)


@login_required(login_url='login')
def commentProject(request, pk):
    """POST-only. Add a comment to a project."""
    projectObj = get_object_or_404(Project, id=pk)

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            ProjectComment.objects.create(
                owner=request.user.profile,
                project=projectObj,
                body=body,
            )
            messages.success(request, 'Comment added.')
        else:
            messages.warning(request, 'Comment cannot be empty.')

    return redirect('project', pk=pk)


@login_required(login_url='login')
def deleteComment(request, pk):
    """POST-only. Project owner deletes a comment."""
    comment = get_object_or_404(ProjectComment, id=pk)
    project_pk = comment.project.id

    if request.user.profile != comment.project.owner:
        messages.error(request, 'Only the project owner can delete comments.')
        return redirect('project', pk=project_pk)

    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Comment deleted.')

    return redirect('project', pk=project_pk)

@login_required(login_url='login')
def savedProjects(request):
    profile = request.user.profile
    # Order by the M2M through-table id (highest = most recently bookmarked)
    through = profile.bookmarks.through
    ordered_ids = list(
        through.objects.filter(profile=profile)
        .order_by('-id')
        .values_list('project_id', flat=True)
    )
    project_map = {p.id: p for p in Project.objects.filter(id__in=ordered_ids)}
    bookmarks = [project_map[pid] for pid in ordered_ids if pid in project_map]

    custom_range, projects = paginateProjects(request, bookmarks, 6)
    context = {
        'projects': projects,
        'custom_range': custom_range,
    }
    return render(request, 'projects/saved.html', context)

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

    context = {'form': form, 'is_update': False}
    return render(request, 'projects/project_form.html', context)

@login_required(login_url='login')
def updateProject(request, pk):
    profile = request.user.profile
    # Allow both owner and collaborators to edit
    project = get_object_or_404(
        Project.objects.filter(Q(owner=profile) | Q(collaborators=profile)).distinct(),
        id=pk
    )
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

    context = {'form': form, 'project': project, 'is_update': True}
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


@login_required(login_url='login')
def inviteCollaborator(request, pk):
    """POST-only. Project owner invites a user by username."""
    project = get_object_or_404(Project, id=pk)
    
    # Only the owner can invite collaborators
    if request.user.profile != project.owner:
        messages.error(request, 'Only the project owner can invite collaborators.')
        return redirect('project', pk=pk)
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        
        if not username:
            messages.error(request, 'Please enter a username.')
            return redirect('project', pk=pk)
        
        # Find the recipient profile by username
        try:
            recipient = Profile.objects.get(user__username=username)
        except Profile.DoesNotExist:
            messages.error(request, f'User "{username}" not found.')
            return redirect('project', pk=pk)
        
        # Can't invite yourself
        if recipient == request.user.profile:
            messages.error(request, 'You cannot invite yourself.')
            return redirect('project', pk=pk)
        
        # Can't invite someone who is already a collaborator
        if project.collaborators.filter(id=recipient.id).exists():
            messages.warning(request, f'{recipient.name or username} is already a collaborator.')
            return redirect('project', pk=pk)
        
        # Can't send a duplicate pending invite
        if CollaborationInvite.objects.filter(project=project, recipient=recipient, status='pending').exists():
            messages.warning(request, f'An invite is already pending for {recipient.name or username}.')
            return redirect('project', pk=pk)
        
        # Delete any old declined invites so unique_together doesn't block re-invites
        CollaborationInvite.objects.filter(project=project, recipient=recipient).exclude(status='pending').delete()
        
        CollaborationInvite.objects.create(
            project=project,
            sender=request.user.profile,
            recipient=recipient,
            status='pending',
        )
        messages.success(request, f'Invitation sent to {recipient.name or username}!')
        return redirect('project', pk=pk)
    
    return redirect('project', pk=pk)


@login_required(login_url='login')
def respondToInvite(request, pk):
    """POST-only. Recipient accepts or declines an invite."""
    invite = get_object_or_404(CollaborationInvite, id=pk)
    
    # Only the recipient can respond
    if request.user.profile != invite.recipient:
        messages.error(request, 'You are not the recipient of this invite.')
        return redirect('account')
    
    if invite.status != 'pending':
        messages.warning(request, 'This invite has already been responded to.')
        return redirect('account')
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'accept':
            invite.status = 'accepted'
            invite.save()
            invite.project.collaborators.add(invite.recipient)
            messages.success(request, f'You are now a collaborator on "{invite.project.title}"!')
        elif action == 'decline':
            invite.status = 'declined'
            invite.save()
            messages.info(request, f'You declined the invite to "{invite.project.title}".')
        else:
            messages.error(request, 'Invalid action.')
    
    return redirect('account')


@login_required(login_url='login')
def removeCollaborator(request, pk, collab_id):
    """POST-only. Project owner removes a collaborator."""
    project = get_object_or_404(Project, id=pk)

    if request.user.profile != project.owner:
        messages.error(request, 'Only the project owner can remove collaborators.')
        return redirect('project', pk=pk)

    if request.method == 'POST':
        collaborator = get_object_or_404(Profile, id=collab_id)
        project.collaborators.remove(collaborator)
        messages.success(request, f'{collaborator.name or collaborator.username} has been removed from the project.')

    return redirect('project', pk=pk)