from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from .models import Profile,Skill,Message
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm
from .forms import ProfileForm
from .forms import SkillForm
from .forms import MessageForm
from django.db.models import Q
from .utils import searchProfiles, paginateProfiles
from django.db.models import F
from projects.models import Project

def loginUser(request):
    if request.user.is_authenticated:
        return redirect('profiles')
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "Username does not exist")
            return render(request, 'users/login_register.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next', 'profiles'))
        else:
            messages.error(request, "Password is incorrect")
    return render(request, 'users/login_register.html')

def logoutUser(request):
    logout(request)
    messages.info(request,"Logged out successfully")
    return redirect('login')

def registerUser(request):
    page = 'register'
    form = CustomUserCreationForm()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()

            messages.success(request, 'User account was created!')
            login(request,user)
            return redirect('edit-account')
        else:
            messages.error(request,'An error has occured during registration')

    context = {'page': page, 'form': form}
    return render(request, 'users/login_register.html', context)

def profiles(request):
    profiles, search_query = searchProfiles(request)

    if request.user.is_authenticated:
        profiles = profiles.exclude(user=request.user)

    custom_range, profiles = paginateProfiles(request, profiles, 6)
    context = {'profiles': profiles, 'search_query': search_query,
               'custom_range': custom_range}
    return render(request, 'users/profiles.html', context)

def userProfile(request,pk):
    profile = Profile.objects.get(id=pk)
    is_own_profile = request.user.is_authenticated and str(request.user.profile.id) == str(pk)
    if not is_own_profile:
        viewed_profiles = request.session.get('viewed_profiles', [])
        if str(pk) not in viewed_profiles:
            Profile.objects.filter(pk=pk).update(views=F('views') + 1)
            viewed_profiles.append(str(pk))
            request.session['viewed_profiles'] = viewed_profiles
        profile.refresh_from_db()
    show_views = not is_own_profile
    topSkills = profile.skill_set.exclude(description__exact="")
    otherSkills = profile.skill_set.filter(description="")

    is_following = False
    if request.user.is_authenticated:
        is_following = request.user.profile.following.filter(id=profile.id).exists()

    context = {
        'profile': profile,
        'topSkills': topSkills,
        'otherSkills': otherSkills,
        'is_following': is_following,
        'show_views': show_views,
    }
    return render(request, 'users/user-profile.html', context)

@login_required(login_url='login')
def userAccount(request):
    profile = request.user.profile
    skills = profile.skill_set.all()
    projects = profile.project_set.all()
    following_count = profile.following.count()
    context = {
        'profile': profile,
        'skills': skills,
        'projects': projects,
        'following_count': following_count,
    }
    return render(request, 'users/account.html',context)

@login_required(login_url='login')
def editAccount(request):
    profile = request.user.profile
    form = ProfileForm(instance=profile)
    if request.method == 'POST':
        form = ProfileForm(request.POST,request.FILES,instance=profile)
        if form.is_valid():
            form.save()
            return redirect('account')
    context = {'form': form}
    return render(request, 'users/profile_form.html',context)

@login_required(login_url='login')
def createSkill(request):
    profile = request.user.profile
    form = SkillForm()
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.owner = profile
            skill.save()
            messages.success(request, 'Skill was added successfully!')
            return redirect('account')  
    context = {'form': form}
    return render(request, 'users/skill_form.html', context)

@login_required(login_url='login')
def updateSkill(request, pk):
    profile = request.user.profile
    skill = profile.skill_set.get(id=pk)
    form = SkillForm(instance=skill)

    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Skill was updated successfully!')
            return redirect('account')

    context = {'form': form}
    return render(request, 'users/skill_form.html', context)


@login_required(login_url='login')
def deleteSkill(request, pk):
    profile = request.user.profile
    skill = profile.skill_set.get(id=pk)
    if request.method == 'POST':
        skill.delete()
        messages.success(request, 'Skill was deleted successfully!')
        return redirect('account')

    context = {'object': skill}
    return render(request, 'delete_template.html', context)


@login_required(login_url='login')
def inbox(request):
    profile = request.user.profile
    messageRequests = profile.messages.all()
    unreadCount = messageRequests.filter(is_read=False).count()
    context = {'messageRequests': messageRequests, 'unreadCount': unreadCount}
    return render(request, 'users/inbox.html', context)

@login_required(login_url='login')
def viewMessage(request, pk):
    profile = request.user.profile
    message = profile.messages.get(id=pk)
    if message.is_read == False:
        message.is_read = True
        message.save()
    context = {'message': message}
    return render(request, 'users/message.html', context)

@login_required(login_url='login')
def followUser(request, pk):
    target_profile = Profile.objects.get(id=pk)
    my_profile = request.user.profile

    if target_profile == my_profile:
        messages.error(request, "You cannot follow yourself.")
        return redirect('user-profile', pk=pk)

    if my_profile.following.filter(id=target_profile.id).exists():
        my_profile.following.remove(target_profile)
        messages.info(request, f"You unfollowed {target_profile.name}.")
    else:
        my_profile.following.add(target_profile)
        messages.success(request, f"You are now following {target_profile.name}.")

    return redirect('user-profile', pk=pk)


@login_required(login_url='login')
def followingList(request):
    profile = request.user.profile
    following = profile.following.all()
    context = {'following': following}
    return render(request, 'users/following.html', context)


@login_required(login_url='login')
def toggleBookmark(request, pk):
    project = Project.objects.get(id=pk)
    profile = request.user.profile
    if profile.bookmarks.filter(id=pk).exists():
        profile.bookmarks.remove(project)
        messages.info(request, 'Bookmark removed.')
    else:
        if project.owner == profile:
            messages.error(request, "You cannot bookmark your own project.")
            return redirect('project', pk=pk)
        profile.bookmarks.add(project)
        messages.success(request, 'Project bookmarked!')
    return redirect('project', pk=pk)


def createMessage(request,pk):
    recipient = Profile.objects.get(id=pk)
    form = MessageForm()
    try:
        sender = request.user.profile
    except:
        sender = None

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = sender
            message.recipient = recipient

            if sender:
                message.name = sender.name
                message.email = sender.email
            message.save()

            messages.success(request, 'Your message was successfully sent!')
            return redirect('user-profile', pk=recipient.id)

    context = {'recipient': recipient, 'form': form}
    return render(request, 'users/message_form.html', context)