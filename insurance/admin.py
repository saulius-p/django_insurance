from django.contrib import admin

from .models import Policyholder, Car, Policy, MTPLData, CASCOData, Risk, PropertyData, Profile, Claim


class PolicyInline(admin.TabularInline):
    model = Policy
    extra = 0


class PolicyholderAdmin(admin.ModelAdmin):

    def get_first_name(self, obj):
        return obj.user.first_name if obj.user.first_name else None

    get_first_name.short_description = 'First name'

    def get_last_name(self, obj):
        return obj.user.last_name if obj.user.last_name else None

    get_last_name.short_description = 'Last name'

    def get_email(self, obj):
        return obj.user.email if obj.user.email else None

    get_email.short_description = 'email'

    list_display = ("get_first_name", "get_last_name", "user", "birth_date", "tel_num", "get_email")
    inlines = [PolicyInline, ]


admin.site.register(Policyholder, PolicyholderAdmin)
admin.site.register(Car)
admin.site.register(Policy)
admin.site.register(MTPLData)
admin.site.register(CASCOData)
admin.site.register(Risk)
admin.site.register(PropertyData)
admin.site.register(Profile)
admin.site.register(Claim)
