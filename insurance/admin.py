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


class ClaimAdmin(admin.ModelAdmin):
    list_display = ("incident_date", "get_policy_number", "get_policy_start", "get_policy_end", "get_policy_type",
                    "get_personal_code", "get_first_name", "get_last_name")
    list_filter = ("policy__policy_type",)
    search_fields = ("policy__policy_number",)

    def get_policy_number(self, obj):
        return obj.policy.policy_number

    get_policy_number.short_description = "Policy Number"

    def get_policy_start(self, obj):
        return obj.policy.start_date

    get_policy_start.short_description = "Policy Start Date"

    def get_policy_end(self, obj):
        return obj.policy.end_date

    get_policy_end.short_description = "Policy End Date"

    def get_policy_type(self, obj):
        return obj.policy.policy_type

    get_policy_type.short_description = "Policy Type"

    def get_personal_code(self, obj):
        return obj.policy.policyholder.personal_code

    get_personal_code.short_description = "Policyholder Personal Code"

    def get_first_name(self, obj):
        return obj.policy.policyholder.user.first_name

    get_first_name.short_description = "First Name"

    def get_last_name(self, obj):
        return obj.policy.policyholder.user.last_name

    get_last_name.short_description = "Last Name"


admin.site.register(Policyholder, PolicyholderAdmin)
admin.site.register(Car)
admin.site.register(Policy)
admin.site.register(MTPLData)
admin.site.register(CASCOData)
admin.site.register(Risk)
admin.site.register(PropertyData)
admin.site.register(Profile)
admin.site.register(Claim, ClaimAdmin)
