from django.contrib import admin
from .models import AdminApproval, Author

# Register your models here.
@admin.register(AdminApproval)
class AdminSettings(admin.ModelAdmin):
    # Admin settings panel customization
    list_display = ("require_approval",)

    def has_add_permission(self, request):
        return not AdminApproval.objects.exists()  # Enforces singleton, prevents multiple instances

    def has_delete_permission(self, request, obj=None):
        return False  # Prevents deleting the setting

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    # Admin panel for approving authors
    list_display = ("display_name","uuid", "is_approved")
    list_filter = ("is_approved",)
    actions = ["approve_authors"]

    def approve_authors(self, request, queryset):
        '''Allows admin to approve authors'''
        queryset.update(is_approved=True)
        self.message_user(request, "Selected authors approved!")
    
    class Meta:
        # Change button from default "User(s)" to "Approve User(s)"
        verbose_name = "Approve User"
        verbose_name_plural = "Approve Users"  # Change name in admin panel

    approve_authors.short_description = "Approve selected authors"