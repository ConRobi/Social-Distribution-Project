from django.contrib import admin
from .models import (AdminApproval, Author, Post, FollowRequest,
    Comment, Like, InboxPost, Node )

# Register your models here.
@admin.register(AdminApproval)
class AdminSettings(admin.ModelAdmin):
    # Admin settings panel customization
    list_display = ("require_approval",)

    def has_add_permission(self, request):
        return not AdminApproval.objects.exists()  # Enforces singleton, prevents multiple instances

    def has_delete_permission(self, request, obj=None):
        return False  # Prevents deleting the setting

    def save_model(self, request, obj, form, change):
        if 'require_approval' in form.changed_data:
            obj.save()

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    # Admin panel for approving authors
    list_display = ("display_name","uuid", "is_approved")
    list_filter = ("is_approved",)
    exclude = ('first_name', 'last_name', 'email') # Exclude unneeded default fields
    actions = ["approve_authors"]

    def approve_authors(self, request, queryset):
        '''Allows admin to approve authors'''
        queryset.update(is_approved=True)
        self.message_user(request, "Selected authors approved!")
        
    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get('password'):
            obj.set_password(form.cleaned_data['password'])  # Hash password
        super().save_model(request, obj, form, change)
    
    class Meta:
        # Change button from default "User(s)" to "Approve User(s)"
        verbose_name = "Approve User"
        verbose_name_plural = "Approve Users"  # Change name in admin panel

    approve_authors.short_description = "Approve selected authors"

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'visibility', 'published')
    list_filter = ('visibility',)

@admin.register(FollowRequest)
class FollowRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'timestamp')
    list_filter = ('status',)
    search_fields = ('sender__display_name', 'receiver__display_name')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'published', 'contentType')
    list_filter = ('contentType', 'published')
    search_fields = ('author__display_name', 'post__title')

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'comment', 'published')
    search_fields = ('author__display_name',)

@admin.register(InboxPost)
class InboxPostAdmin(admin.ModelAdmin):
    list_display = ('receiver', 'post', 'received_at')
    search_fields = ('receiver__display_name', 'post__title',)

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'IPAddress', 'connection_enabled')
    list_filter = ('connection_enabled',)
    search_fields = ('name', 'IPAddress')
    actions = ['enable_connection', 'disable_connection']

    def enable_connection(self, request, queryset):
        '''Allows admin to enable connections to other Nodes'''
        queryset.update(connection_enabled=True)
        self.message_user(request, "Selected connections enabled!")

    def disable_connection(self, request, queryset):
        '''Allows admin to disable connections to other Nodes'''
        queryset.update(connection_enabled=False)
        self.message_user(request, "Selected connections disabled!")

    enable_connection.short_description = "Enable connections"
    disable_connection.short_description = "Disable connections"



