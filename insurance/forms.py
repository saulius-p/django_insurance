from django import forms
from .models import Profile, User


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email')


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('picture',)


########################################################################################################################
# MTPL FORM
########################################################################################################################

class PremiumCalculationFormMtpl(forms.Form):
    start_date = forms.DateField(
        label="Policy Start Date",
        widget=forms.TextInput(attrs={"type": "date"}),
    )

    end_date = forms.DateField(
        label="Policy End Date",
        widget=forms.TextInput(attrs={"type": "date"}),
    )

    plate_number = forms.CharField(
        label="Car Plate No.",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "form-control car-plate-input"}),  # Style can be found in the template.
    )

    driver_experience = forms.IntegerField(
        label="Driver Experience (years)",
        min_value=0,
    )


########################################################################################################################
# CASCO FORM
########################################################################################################################

class PremiumCalculationFormCasco(forms.Form):
    start_date = forms.DateField(
        label="Policy Start Date",
        widget=forms.TextInput(attrs={"type": "date"}),
    )

    end_date = forms.DateField(
        label="Policy End Date",
        widget=forms.TextInput(attrs={"type": "date"}),
    )

    plate_number = forms.CharField(
        label="Car Plate No.",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "form-control car-plate-input"}),  # Style can be found in the template.
    )

    driver_experience = forms.IntegerField(
        label="Driver Experience (years)",
        min_value=0,
    )

    alarm_system_indicator = forms.MultipleChoiceField(
        label="Does your car have alarm system?",
        choices=[
            ("YES", "Car has alarm system"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,  # If the car doesn't have alarm system, the box won't be checked.
    )


########################################################################################################################
# PROPERTY FORM
########################################################################################################################

# Needed constants

CONSTRUCTION_CHOICES = [
    ("brick/concrete", "Brick/Concrete"),
    ("wood", "Wood"),
    ("logs", "Logs"),
    ("mixed", "Mixed"),
]

BUILDING_PURPOSE_CHOICES = [
    ("apartment", "Apartment"),
    ("garden house", "Garden House"),
    ("summerhouse", "Summerhouse"),
    ("house of other purpose", "House of Other Purpose"),
]


class PremiumCalculationFormProperty(forms.Form):
    start_date = forms.DateField(
        label="Policy Start Date",
        widget=forms.TextInput(attrs={"type": "date"}),
    )

    end_date = forms.DateField(
        label="Policy End Date",
        widget=forms.TextInput(attrs={"type": "date"}),
    )

    construction = forms.ChoiceField(
        label="Construction Type",
        choices=CONSTRUCTION_CHOICES,
    )

    building_purpose = forms.ChoiceField(
        label="Building Purpose",
        choices=BUILDING_PURPOSE_CHOICES,
    )

    selected_risks = forms.MultipleChoiceField(
        label="Selected Risks",
        choices=[
            ("Fire", "Fire"),
            ("Floods", "Floods"),
            ("Windstorms and Hail", "Windstorms and Hail"),
            ("Snow and Ice", "Snow and Ice"),
            ("Water Damage", "Water Damage"),
            ("Impact Damage", "Impact Damage"),
            ("Theft", "Theft"),
            ("Vandalism", "Vandalism"),
            ("Liability Coverage", "Liability Coverage"),
            ("Loss of Use", "Loss of Use"),
            ("Business-Related Risks", "Business-Related Risks"),
            ("Power Surge", "Power Surge"),
            ("Explosion", "Explosion"),
            ("Falling Objects", "Falling Objects"),
            ("Building Collapse", "Building Collapse"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=True,  # At least one box must be checked.
    )
