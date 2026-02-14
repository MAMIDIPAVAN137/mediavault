from django import forms
from .models import MediaItem, Folder

class MediaEditForm(forms.ModelForm):
    class Meta:
        model = MediaItem
        fields = ['title', 'description', 'category', 'is_private']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'fluent-input', 'style': 'width: 100%; box-sizing: border-box;'}),
            'description': forms.Textarea(attrs={'class': 'fluent-input', 'rows': 4, 'style': 'width: 100%; box-sizing: border-box;'}),
            'category': forms.Select(attrs={'class': 'fluent-input', 'style': 'width: 100%; box-sizing: border-box;'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'fluent-checkbox'}),
        }

class FolderEditForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'is_private']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'fluent-input', 'style': 'width: 100%; box-sizing: border-box;'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'fluent-checkbox'}),
        }
