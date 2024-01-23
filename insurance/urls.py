from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("policyholders/", views.policyholders, name="policyholders-all"),
    path("insurepolicy/", views.insure_policy, name="insure-policy"),
    path("fileclaim/", views.file_claim, name="file-claim"),
    path("insurepolicy/mtpl/", views.insure_mtpl, name="insure-mtpl"),
    path("insurepolicy/casco/", views.insure_casco, name="insure-casco"),
    path("insurepolicy/property/", views.insure_property, name="insure-property"),
    path("buy-mtpl-policy/", views.buy_mtpl_policy, name="buy-mtpl-policy"),
    path("buy-casco-policy/", views.buy_casco_policy, name="buy-casco-policy"),
    path("buy-property-policy/", views.buy_property_policy, name="buy-property-policy"),
    path("add/", views.add, name="add-path"),

    path("register/", views.register_user, name="register-url"),
    path("profile/", views.profile, name="profile-url"),
    path("my-policies/", views.PoliciesByUserListView.as_view(), name="my-policies"),
    path("my-policies/<uuid:pk>", views.PolicyDetailView.as_view(), name="policy-one"),
]
