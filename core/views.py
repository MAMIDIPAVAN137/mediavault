from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
import datetime

from .forms import (
    CustomUserCreationForm, EmailOrPhoneAuthenticationForm, ProfileUpdateForm, 
    AdminUserUpdateForm, UploadRequestForm, ReportProblemForm, UsernameUpdateForm
)
from .models import UploadRequest, ReportedProblem
from media.models import MediaItem, Folder, Category
from social.models import Follow, Like, Favorite, MediaView, Review
from django.contrib.auth import get_user_model

User = get_user_model()

def home(request):
    query = request.GET.get("q", "").strip()
    media_type = request.GET.get("type", "ALL")
    sort_by = request.GET.get("sort", "date_desc")
    date_filter = request.GET.get("date", "all")
    is_search = bool(query)

    # Base Querysets
    items_qs = MediaItem.objects.filter(is_hidden=False)
    folders_qs = Folder.objects.filter(is_hidden=False)
    
    # Ownership/Privacy rules
    if not (request.user.is_authenticated and request.user.is_superuser):
        if request.user.is_authenticated:
            # Can see: (Public items AND Public profile) OR (My items) OR (Followed items)
            followed_users = Follow.objects.filter(follower=request.user, is_accepted=True).values_list('followed_id', flat=True)
            
            items_qs = items_qs.filter(
                (Q(is_private=False) & Q(uploader__is_private=False)) | 
                Q(uploader=request.user) |
                Q(uploader_id__in=followed_users)
            )
            folders_qs = folders_qs.filter(
                (Q(is_private=False) & Q(owner__is_private=False)) | 
                Q(owner=request.user) |
                Q(owner_id__in=followed_users)
            )
        else:
            # Anonymous users only see Public items from Public profiles
            items_qs = items_qs.filter(is_private=False, uploader__is_private=False)
            folders_qs = folders_qs.filter(is_private=False, owner__is_private=False)

    # Apply Sidebar Filters
    if media_type != "ALL":
        items_qs = items_qs.filter(media_type=media_type)
    
    if date_filter != "all":
        now = timezone.now()
        if date_filter == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == "week":
            start_date = now - datetime.timedelta(days=7)
        elif date_filter == "month":
            start_date = now - datetime.timedelta(days=30)
        items_qs = items_qs.filter(created_at__gte=start_date)

    # Sorting
    if sort_by == "date_asc":
        items_qs = items_qs.order_by('created_at')
    elif sort_by == "views":
        items_qs = items_qs.order_by('-views_count')
    elif sort_by == "name_asc":
        items_qs = items_qs.order_by('title')
    elif sort_by == "name_desc":
        items_qs = items_qs.order_by('-title')
    else: # date_desc
        items_qs = items_qs.order_by('-created_at')

    search_users = User.objects.none()
    search_photos = MediaItem.objects.none()
    search_videos = MediaItem.objects.none()
    search_documents = MediaItem.objects.none()
    search_folders = Folder.objects.none()

    if is_search:
        search_users = User.objects.filter(
            Q(username__icontains=query) | Q(bio__icontains=query)
        ).distinct()
        
        search_photos = items_qs.filter(media_type='IMAGE').filter(
            Q(title__icontains=query) | Q(file__icontains=query)
        ).distinct()

        search_videos = items_qs.filter(media_type='VIDEO').filter(
            Q(title__icontains=query) | Q(file__icontains=query)
        ).distinct()
        
        search_documents = items_qs.filter(media_type='DOCUMENT').filter(
            Q(title__icontains=query) | Q(file__icontains=query)
        ).distinct()
        
        search_folders = folders_qs.filter(name__icontains=query).distinct()

    no_results = is_search and not (
        search_users.exists() or search_photos.exists() or 
        search_videos.exists() or search_documents.exists() or search_folders.exists()
    )

    featured = MediaItem.objects.filter(uploader__is_superuser=True, is_hidden=False, is_private=False)[:10]
    trending = items_qs.annotate(lc=Count('likes')).order_by('-lc')[:10]
    # Combine or pick one for Recommended
    recommended = (featured | trending).distinct()[:15]
    recent = items_qs.order_by('-created_at')[:20]

    context = {
        "is_search": is_search,
        "query": query,
        "selected_type": media_type,
        "selected_sort": sort_by,
        "selected_date": date_filter,
        "search_users": search_users,
        "search_photos": search_photos,
        "search_videos": search_videos,
        "search_documents": search_documents,
        "search_folders": search_folders,
        "no_results": no_results,
        "recommended": recommended,
        "recent": recent,
    }
    return render(request, "core/home.html", context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user, user=request.user)
        if form.is_valid():
            user = form.save()
            # Handle allowed downloaders
            allowed_ids = request.POST.getlist('allowed_downloaders')
            user.allowed_downloaders.set(allowed_ids)
            messages.success(request, "Profile updated.")
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user, user=request.user)
    
    context = {
        'form': form,
        'allowed_users': request.user.allowed_downloaders.all()
    }
    return render(request, 'core/edit_profile.html', context)

@login_required
def search_users(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'users': []})
    
    users = User.objects.filter(
        Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
    ).exclude(id=request.user.id)[:10]
    
    results = []
    for u in users:
        results.append({
            'id': u.id,
            'username': u.username,
            'full_name': f"{u.first_name} {u.last_name}",
            'avatar': u.profile_picture.url if u.profile_picture else None
        })
    return JsonResponse({'users': results})

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user; logout(request); user.delete(); messages.success(request, "Account deleted."); return redirect('home')
    return redirect('profile')

def profile(request, username=None):
    if username: user_obj = get_object_or_404(User, username=username)
    else:
        if not request.user.is_authenticated: return redirect('login')
        user_obj = request.user
    is_own = (request.user.is_authenticated and request.user == user_obj)
    is_admin = (request.user.is_authenticated and request.user.is_superuser)

    is_following = False
    is_follow_requested = False
    if request.user.is_authenticated and not is_own:
        follow_obj = Follow.objects.filter(follower=request.user, followed=user_obj).first()
        if follow_obj:
            is_following = follow_obj.is_accepted
            is_follow_requested = not follow_obj.is_accepted

    is_profile_private = user_obj.is_private and not is_own and not is_admin and not is_following
    
    uploads_all_files = MediaItem.objects.filter(uploader=user_obj, is_hidden=False)
    uploads_folders = Folder.objects.filter(owner=user_obj, parent__isnull=True, is_hidden=False)
    uploads_direct = MediaItem.objects.filter(uploader=user_obj, folder__isnull=True, is_hidden=False)
    favorites = MediaItem.objects.filter(favorited_by__user=user_obj).select_related('uploader')
    likes = MediaItem.objects.filter(likes__user=user_obj).select_related('uploader')
    comments = Review.objects.filter(user=user_obj).select_related('media_item')
    history = [v.media_item for v in MediaView.objects.filter(user=user_obj).select_related('media_item')[:20]]
    hidden_items = MediaItem.objects.filter(uploader=user_obj, is_hidden=True) if is_own or is_admin else []

    # Content Filtering
    if not is_own and not is_admin:
        if is_profile_private:
            # Profile is private and user doesn't follow: they see nothing
            uploads_all_files = uploads_all_files.none()
            uploads_folders = uploads_folders.none()
            uploads_direct = uploads_direct.none()
        else:
            # Profile is public OR user follows: they see public items
            uploads_all_files = uploads_all_files.filter(is_private=False)
            uploads_folders = uploads_folders.filter(is_private=False)
            uploads_direct = uploads_direct.filter(is_private=False)

    notifications = []
    pending_follow_requests = Follow.objects.none()
    if is_own:
        from social.models import Notification
        notifications = Notification.objects.filter(recipient=request.user, is_read=False)
        pending_follow_requests = Follow.objects.filter(followed=request.user, is_accepted=False).select_related('follower')
    
    followers_list = Follow.objects.filter(followed=user_obj, is_accepted=True).select_related('follower')
    following_list = Follow.objects.filter(follower=user_obj, is_accepted=True).select_related('followed')

    # Uploader Request Logic for Settings
    upload_request_form = None
    pending_upload_request = None
    if is_own and not user_obj.is_uploader:
        pending_upload_request = UploadRequest.objects.filter(user=user_obj, processed_at__isnull=True).first()
        if not pending_upload_request:
            upload_request_form = UploadRequestForm()

    return render(request, 'core/profile.html', {
        'profile_user': user_obj,
        'uploads_all_files': uploads_all_files,
        'uploads_folders': uploads_folders,
        'uploads_direct': uploads_direct,
        'favorites': favorites,
        'likes': likes,
        'comments': comments,
        'history': history,
        'hidden_items': hidden_items,
        'is_own': is_own,
        'is_admin': is_admin,
        'is_following': is_following,
        'is_follow_requested': is_follow_requested,
        'is_profile_private': is_profile_private,
        'followers_list': Follow.objects.filter(followed=user_obj, is_accepted=True).select_related('follower'),
        'following_list': Follow.objects.filter(follower=user_obj, is_accepted=True).select_related('followed'),
        'pending_follow_requests': pending_follow_requests,
        'upload_request_form': UploadRequestForm() if is_own and not user_obj.is_uploader else None,
        'pending_upload_request': UploadRequest.objects.filter(user=user_obj, processed_at__isnull=True).exists(),
        'report_problem_form': ReportProblemForm() if is_own else None,
    })

@login_required
def report_problem(request):
    if request.method == 'POST':
        form = ReportProblemForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()
            messages.success(request, "Your report has been submitted. Thank you!")
            return redirect('profile')
    return redirect('profile')

@login_required
@require_POST
def verify_password(request):
    password = request.POST.get('password')
    if request.user.check_password(password):
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': 'Incorrect password.'}, status=400)

@login_required
def update_username(request):
    if request.method == 'POST':
        form = UsernameUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Username updated successfully.")
        else:
            for error in form.errors.values():
                messages.warning(request, error)
    return redirect('profile')

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='core.backends.EmailOrPhoneBackend')
            return redirect('home')
    else: form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = EmailOrPhoneAuthenticationForm(request, data=request.POST)
        if form.is_valid(): login(request, form.get_user()); return redirect('home')
    else: form = EmailOrPhoneAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
def request_upload_access(request):
    if request.method == 'POST':
        form = UploadRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False); req.user = request.user; req.save()
            messages.success(request, "Request sent."); return redirect('/profile/?tab=settings')
    else: form = UploadRequestForm()
    return render(request, 'core/request_upload.html', {'form': form})

@login_required
def admin_upload_requests(request):
    if not request.user.is_superuser: return redirect('home')
    requests = UploadRequest.objects.filter(processed_at__isnull=True).order_by('-created_at').select_related('user')
    history = UploadRequest.objects.filter(processed_at__isnull=False).order_by('-processed_at')[:20].select_related('user')
    problems = ReportedProblem.objects.filter(is_resolved=False).order_by('-created_at').select_related('user')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'resolve_problem':
            p = get_object_or_404(ReportedProblem, id=request.POST.get('problem_id'))
            p.is_resolved = True
            p.resolved_at = timezone.now()
            p.save()
            messages.success(request, f"Problem from {p.user.username} marked as resolved.")
            return redirect('admin_upload_requests')
        
        r = get_object_or_404(UploadRequest, id=request.POST.get('request_id'))
        action = request.POST.get('action')
        r.is_approved = (action == 'approve')
        if r.is_approved:
            r.user.is_uploader = True
            r.user.save()
        r.processed_at = timezone.now()
        r.save()
        messages.success(request, f"Request from {r.user.username} {'approved' if r.is_approved else 'rejected'}.")
        return redirect('admin_upload_requests')
        
    return render(request, 'core/admin_requests.html', {
        'requests': requests,
        'history': history,
        'problems': problems,
        'uploader_count': User.objects.filter(is_uploader=True).count(),
        'media_count': MediaItem.objects.count()
    })

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser: return redirect('home')
    return render(request, 'core/admin_dashboard.html', {
        'user_count': User.objects.count(),
        'media_count': MediaItem.objects.count(),
        'uploader_count': User.objects.filter(is_uploader=True).count(),
        'pending_requests_count': UploadRequest.objects.filter(processed_at__isnull=True).count(),
        'reported_problems_count': ReportedProblem.objects.filter(is_resolved=False).count(),
        'recent_problems': ReportedProblem.objects.filter(is_resolved=False).order_by('-created_at')[:5].select_related('user')
    })

@login_required
def toggle_profile_privacy(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        password = data.get('password')
        if not request.user.check_password(password):
            return JsonResponse({'status': 'error', 'message': 'Incorrect password.'}, status=403)
        
        request.user.is_private = not request.user.is_private
        request.user.save()
        return JsonResponse({'is_private': request.user.is_private, 'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)
@login_required
def update_theme(request):
    if request.method == 'POST':
        theme = request.POST.get('theme')
        if theme in ['LIGHT', 'DARK']:
            request.user.theme_preference = theme
            request.user.save()
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def admin_edit_user(request, username):
    if not request.user.is_superuser:
        return redirect('home')
    user_to_edit = get_object_or_404(User, username=username)
    if request.method == 'POST':
        form = AdminUserUpdateForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            user = form.save()
            new_pwd = form.cleaned_data.get('new_password')
            if new_pwd:
                user.set_password(new_pwd)
                user.save()
            messages.success(request, f"Profile for {username} updated by admin.")
            return redirect('user_profile', username=username)
    else:
        form = AdminUserUpdateForm(instance=user_to_edit)
    return render(request, 'core/edit_profile.html', {
        'form': form, 
        'edit_user': user_to_edit,
        'is_admin_edit': True
    })

@login_required
def admin_user_list(request):
    if not request.user.is_superuser:
        return redirect('home')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'core/admin_user_list.html', {
        'users': users,
        'user_count': users.count(),
        'uploader_count': users.filter(is_uploader=True).count()
    })

@login_required
def admin_media_list(request):
    if not request.user.is_superuser:
        return redirect('home')
    media_items = MediaItem.objects.all().order_by('-created_at').select_related('uploader')
    return render(request, 'core/admin_media_list.html', {
        'media_items': media_items,
        'media_count': media_items.count(),
        'uploader_count': User.objects.filter(is_uploader=True).count()
    })
