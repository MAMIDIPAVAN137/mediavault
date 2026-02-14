from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from .models import MediaItem, Folder, Category
from .forms import MediaEditForm, FolderEditForm
from social.forms import ReviewForm
from social.models import Review, Like, MediaView, Favorite
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

def folder_detail(request, pk):
    folder = get_object_or_404(Folder, pk=pk)
    
    is_owner = (request.user.is_authenticated and folder.owner == request.user)
    is_admin = (request.user.is_authenticated and request.user.is_superuser)
    
    # Permission: Profile check
    is_following = False
    if request.user.is_authenticated and not is_owner:
        from social.models import Follow
        is_following = Follow.objects.filter(follower=request.user, followed=folder.owner, is_accepted=True).exists()

    if folder.owner.is_private and not is_owner and not is_admin and not is_following:
        messages.error(request, "This profile is private.")
        return redirect('home')

    # Permission: Folder check
    if folder.is_private and not is_owner and not is_admin and not is_following:
        messages.error(request, "This folder is private.")
        return redirect('home')

    subfolders = Folder.objects.filter(parent=folder)
    media_items = MediaItem.objects.filter(folder=folder)

    if not is_owner and not is_admin:
        subfolders = subfolders.filter(is_private=False, is_hidden=False)
        media_items = media_items.filter(is_private=False, is_hidden=False)
    
    return render(request, 'media/folder_detail.html', {
        'folder': folder, 
        'subfolders': subfolders, 
        'media_items': media_items,
        'is_owner': is_owner
    })

@login_required
def set_folder_cover(request, folder_pk, media_pk):
    folder = get_object_or_404(Folder, pk=folder_pk, owner=request.user)
    media = get_object_or_404(MediaItem, pk=media_pk, folder=folder)
    
    if media.media_type != 'IMAGE':
        messages.error(request, "Only images can be set as cover.")
        return redirect('folder_detail', pk=folder_pk)
    
    folder.cover_image = media.file
    folder.save()
    messages.success(request, "Folder cover updated.")
    return redirect('folder_detail', pk=folder_pk)

@login_required
def delete_media(request, pk):
    media = get_object_or_404(MediaItem, pk=pk, uploader=request.user)
    folder = media.folder
    media.delete()
    messages.success(request, "Deleted.")
    return redirect('folder_detail', pk=folder.id) if folder else redirect('profile')

@login_required
def delete_folder(request, pk):
    folder = get_object_or_404(Folder, pk=pk, owner=request.user)
    parent = folder.parent
    folder.delete()
    messages.success(request, "Deleted.")
    return redirect('folder_detail', pk=parent.id) if parent else redirect('profile')

@login_required
def edit_folder(request, pk):
    folder = get_object_or_404(Folder, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = FolderEditForm(request.POST, instance=folder)
        if form.is_valid():
            form.save(); messages.success(request, "Saved."); return redirect('folder_detail', pk=pk)
    else:
        form = FolderEditForm(instance=folder)
    return render(request, 'media/edit_folder.html', {'form': form, 'folder': folder})

# Keeping media_detail for completeness
def media_detail(request, pk):
    media = get_object_or_404(MediaItem, pk=pk)
    is_owner = (request.user.is_authenticated and media.uploader == request.user)
    is_admin = (request.user.is_authenticated and request.user.is_superuser)
    
    is_following = False
    if request.user.is_authenticated and not is_owner:
        from social.models import Follow
        is_following = Follow.objects.filter(follower=request.user, followed=media.uploader, is_accepted=True).exists()
    
    if (media.is_private or media.uploader.is_private) and not is_owner and not is_admin and not is_following:
        messages.error(request, "This item is private.")
        return redirect('login') if not request.user.is_authenticated else redirect('home')

    # Comment submission
    if request.method == 'POST' and 'comment_submit' in request.POST:
        if not request.user.is_authenticated:
            return redirect('login')
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.media_item = media
            review.save()
            messages.success(request, "Comment added.")
            return redirect('media-detail-page', pk=pk)
    
    comment_form = ReviewForm()
    comments = Review.objects.filter(media_item=media).select_related('user').order_by('-created_at')

    # Log View (Unique per session/user)
    view_key = f'viewed_media_{media.id}'
    if not request.session.get(view_key):
        if request.user.is_authenticated:
            viewed, created = MediaView.objects.get_or_create(user=request.user, media_item=media)
            if created:
                media.views_count += 1
                media.save()
        else:
            media.views_count += 1
            media.save()
        request.session[view_key] = True

    # Suggestions: Similar items (same category or same type)
    related_items = MediaItem.objects.filter(
        Q(category=media.category) | Q(media_type=media.media_type)
    ).exclude(id=media.id).filter(is_private=False, is_hidden=False)[:10]

    # Folder Items
    folder_items = []
    if media.folder:
        folder_items = MediaItem.objects.filter(folder=media.folder).exclude(id=media.id).order_by('created_at')[:10]

    # Recent Uploads for sidebar
    recent_uploads = MediaItem.objects.filter(is_private=False, is_hidden=False).order_by('-created_at')[:5]

    # Next/Prev logic
    next_item = None
    prev_item = None
    
    # Contextual order: within folder if available, otherwise global
    if media.folder:
        qs = MediaItem.objects.filter(folder=media.folder).order_by('id')
    else:
        qs = MediaItem.objects.filter(folder__isnull=True).order_by('id')
        
    # Security/Privacy filter for next/prev
    if not is_owner and not is_admin and not is_following:
        qs = qs.filter(is_private=False, is_hidden=False)

    next_item = qs.filter(id__gt=media.id).first()
    prev_item = qs.filter(id__lt=media.id).last()

    return render(request, 'media/detail.html', {
        'media': media, 'media_item': media, 'media_comments': comments, 'comment_form': comment_form, 
        'is_owner': is_owner, 'related_items': related_items,
        'folder_items': folder_items, 'recent_items': recent_uploads,
        'next_item': next_item, 'prev_item': prev_item,
        'is_liked': Like.objects.filter(user=request.user, media_item=media).exists() if request.user.is_authenticated else False,
        'is_favorited': Favorite.objects.filter(user=request.user, media_item=media).exists() if request.user.is_authenticated else False,
        'is_following': is_following
    })

@login_required
def edit_media(request, pk):
    media = get_object_or_404(MediaItem, pk=pk, uploader=request.user)
    if request.method == 'POST':
        form = MediaEditForm(request.POST, request.FILES, instance=media)
        if form.is_valid():
            form.save(); messages.success(request, "Media updated."); return redirect('media-detail-page', pk=pk)
    else:
        form = MediaEditForm(instance=media)
    return render(request, 'media/edit_media.html', {'form': form, 'media': media})

def all_media(request):
    media_type = request.GET.get('type', 'ALL')
    sort_by = request.GET.get('sort', 'date_desc')
    
    # Base Queryset
    items_qs = MediaItem.objects.filter(is_hidden=False)
    
    # Security/Privacy Filter
    if not (request.user.is_authenticated and request.user.is_superuser):
        if request.user.is_authenticated:
            from social.models import Follow
            followed_users = Follow.objects.filter(follower=request.user, is_accepted=True).values_list('followed_id', flat=True)
            items_qs = items_qs.filter(
                (Q(is_private=False) & Q(uploader__is_private=False)) | 
                Q(uploader=request.user) |
                Q(uploader_id__in=followed_users)
            )
        else:
            items_qs = items_qs.filter(is_private=False, uploader__is_private=False)

    if media_type != 'ALL':
        items_qs = items_qs.filter(media_type=media_type)

    if sort_by == 'views': items_qs = items_qs.order_by('-views_count')
    elif sort_by == 'name_asc': items_qs = items_qs.order_by('title')
    else: items_qs = items_qs.order_by('-created_at')

    # Infinite scroll handling (Initial load + AJAX loads)
    page = int(request.GET.get('page', 1))
    per_page = 24
    start = (page - 1) * per_page
    end = start + per_page
    
    items = items_qs[start:end]
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'media/media_grid_items.html', {'items': items})

    return render(request, 'media/all_media.html', {
        'items': items,
        'selected_type': media_type,
        'selected_sort': sort_by,
        'next_page': page + 1 if len(items) == per_page else None
    })

@login_required
def toggle_media_visibility(request, pk, action):
    m = get_object_or_404(MediaItem, pk=pk, uploader=request.user)
    if action == 'hide': m.is_hidden = True
    elif action == 'unhide': m.is_hidden = False
    elif action == 'private': m.is_private = True
    elif action == 'public': m.is_private = False
    m.save(); return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def toggle_folder_visibility(request, pk, action):
    f = get_object_or_404(Folder, pk=pk, owner=request.user)
    if action == 'hide': f.is_hidden = True
    elif action == 'unhide': f.is_hidden = False
    elif action == 'private': f.is_private = True
    elif action == 'public': f.is_private = False
    f.save(); return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
@require_POST
def bulk_delete(request):
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        
        media_ids = [item['id'] for item in items if item['type'] == 'media']
        folder_ids = [item['id'] for item in items if item['type'] == 'folder']
        
        # Security: Only delete items owned by the user
        deleted_media_count = MediaItem.objects.filter(id__in=media_ids, uploader=request.user).delete()[0]
        deleted_folder_count = Folder.objects.filter(id__in=folder_ids, owner=request.user).delete()[0]
        
        messages.success(request, f"Successfully deleted {deleted_media_count} files and {deleted_folder_count} folders.")
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
