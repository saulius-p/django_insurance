from uuid import UUID

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpRequest
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import Q


from .models import Policyholder, Policy, Car, MTPLData, PropertyData, Risk, CASCOData, Claim
from .forms import UserUpdateForm, ProfileUpdateForm, PremiumCalculationFormProperty, \
    PremiumCalculationFormCasco, PremiumCalculationFormMtpl
from .pricing_functions import calculate_premium_for_mtpl, calculate_premium_for_property, calculate_premium_for_casco
from .helper_functions import check_passwordl, send_policy_email, validate_car_insurance_data

from datetime import datetime, date, timedelta
import os


def index(request):
    return render(request, "index.html")


def insure_policy(request):
    return render(request, "insure_policy.html")


@csrf_protect
def register_user(request: HttpRequest):
    """
        Handles user registration. Creates policyholder object in the database.

        Parameters:
        - request: HttpRequest object representing the current request.

        Returns:
        - HttpResponse: Renders the registration form page if the request method is not POST.
                      Redirects to the registration page with error messages if validation fails.
                      Redirects to the login page with a success message if registration is successful.
    """
    if request.method != "POST":
        return render(request, "registration/registration.html")

    # If POST, we take data from the form.
    username = request.POST["username"]
    email = request.POST["email"]
    tel_num = request.POST["tel_num"]
    password = request.POST["password"]
    password2 = request.POST["password2"]
    personal_code = request.POST["personal_code"]
    name = request.POST["name"]
    surname = request.POST["surname"]
    birth_date = request.POST["birth_date"]

    if password != password2:
        messages.error(request, "Passwords don't match!!!")

    if not check_passwordl(password):
        messages.error(request, "Password1 too short!!!")

    if User.objects.filter(username=username).exists():  # exists returns True or False
        messages.error(request, f"User {username} already exists!!!")

    if User.objects.filter(email=email).exists():
        messages.error(request, f"Email {email} already registered!!!")

    if messages.get_messages(request):
        return redirect("register-url")

    # Create the User object
    user = User.objects.create_user(username=username, email=email, password=password, first_name=name,
                                    last_name=surname)

    # Create the Policyholder object
    policyholder = Policyholder.objects.create(
        user=user,
        personal_code=personal_code,
        birth_date=birth_date,
        tel_num=tel_num
    )
    messages.success(request, f"User {username} created!!!")
    return redirect('login')


@login_required
def profile(request: HttpRequest):
    """
     View function for handling user profile updates.

     Parameters:
     - request: HttpRequest object representing the current request.

     Returns:
     - HttpResponse: Renders the user profile update page.
                       Updates the user profile if the request method is POST and form validations pass.
                       Redirects to the profile page with a success message if the profile is updated.
     """
    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Profilis atnaujintas!")
            return redirect('profilis-url')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'profile.html', context=context)


@login_required
def insure_mtpl(request):
    if request.method == 'POST':
        form = PremiumCalculationFormMtpl(request.POST)
        if form.is_valid():
            insurance_data = form.cleaned_data  # dictionary with cleaned, validated data

            # PRINT for TEST only.
            print(insurance_data)

            start_date = insurance_data["start_date"]
            end_date = insurance_data["end_date"]
            plate_number = insurance_data["plate_number"]
            driver_experience = insurance_data["driver_experience"]

            car, validation_result = validate_car_insurance_data(request, form)

            if validation_result:
                return validation_result

            # PRINTS for TEST only.
            print(plate_number)
            print(f"Plate number: {car.plate_number}.")
            print(f"Car make: {car.make}.")
            print(f"Car model: {car.model}.")

            policy_duration = (end_date - start_date).days

            premium = calculate_premium_for_mtpl(policy_duration, driver_experience, car.make)

            # If we need to serialize dates to JSON we need to convert them to str.
            insurance_data["start_date"] = str(start_date)
            insurance_data["end_date"] = str(end_date)

            # Let's also add policy_duration and premium, so that we wouldn't have to recalculate them.

            insurance_data["policy_duration"] = policy_duration
            insurance_data["premium"] = premium

            # We store data in the session for the use in next step.
            # request.session is dictionary-like object
            request.session["insurance_data"] = insurance_data

            # PRINTS for TEST only. Compare with the print above.
            print(request.session["insurance_data"])
            print(request.session)

            context = {"premium": premium,
                       "policy_duration": policy_duration}

            # Display the result on the page
            return render(request, 'premium_result.html', context=context)

    else:
        form = PremiumCalculationFormMtpl()

    return render(request, "premium_calculation.html", {"form": form})


@login_required
def buy_mtpl_policy(request):
    # Get the authenticated user
    user = request.user

    # Retrieve the associated Policyholder object
    policyholder = Policyholder.objects.get(user=user)

    # If the key is present, it returns the corresponding value. If the key is not present, it returns an empty
    # dictionary {} as the default value.
    insurance_data = request.session.get("insurance_data", {})

    start_date = datetime.strptime(insurance_data.get("start_date"), "%Y-%m-%d").date()
    end_date = datetime.strptime(insurance_data.get("end_date"), "%Y-%m-%d").date()
    policy_duration = insurance_data.get("policy_duration")
    plate_number = insurance_data.get("plate_number")
    driver_experience = insurance_data.get("driver_experience")
    premium = insurance_data.get("premium")

    new_policy = Policy.objects.create(
        policyholder=policyholder,
        start_date=start_date,
        end_date=end_date,
        policy_duration=policy_duration,
        policy_type="MTPL",
        insurance_premium=premium,
    )

    car = Car.objects.get(plate_number=plate_number)

    new_mtpl_record = MTPLData.objects.create(
        policy=new_policy,
        driver_experience=driver_experience,
        car=car,
    )

    # Call function that sends email
    send_policy_email(user.email, "mtpl_reference_doc.pdf")

    # If the user is authenticated, redirect to the "Thank You" page
    return render(request, 'thank_you.html', {
        'email': user.email,  # We use authenticated user's email
        'start_date': start_date,
    })


@login_required
def insure_casco(request):
    if request.method == 'POST':
        form = PremiumCalculationFormCasco(request.POST)
        if form.is_valid():
            insurance_data = form.cleaned_data  # dictionary with cleaned, validated data

            # PRINT for TEST only.
            print(insurance_data)

            start_date = insurance_data["start_date"]
            end_date = insurance_data["end_date"]
            plate_number = insurance_data["plate_number"]
            driver_experience = insurance_data["driver_experience"]
            alarm_system_ind_list = insurance_data['alarm_system_indicator']  # Can be empty list, if the car
            # doesn't have alarm.

            car, validation_result = validate_car_insurance_data(request, form)

            if validation_result:
                return validation_result

            # PRINTS for TEST only.
            print(plate_number)
            print(f"Plate number: {car.plate_number}.")
            print(f"Car make: {car.make}.")
            print(f"Car model: {car.model}.")

            policy_duration = (end_date - start_date).days

            # alarm_system_ind_list will be equivalent to False, if the list is empty. True otherwise.
            premium = calculate_premium_for_casco(policy_duration, driver_experience, car.make, alarm_system_ind_list)

            # If we need to serialize dates to JSON we need to convert them to str.
            insurance_data["start_date"] = str(start_date)
            insurance_data["end_date"] = str(end_date)

            # Let's also add policy_duration and premium, so that we wouldn't have to recalculate them.

            insurance_data["policy_duration"] = policy_duration
            insurance_data["premium"] = premium

            # We store data in the session for the use in next step.
            request.session["insurance_data"] = insurance_data

            # PRINTS for TEST only. Compare with the print above.
            print(request.session["insurance_data"])
            print(request.session)

            context = {"premium": premium,
                       "policy_duration": policy_duration}

            # Display the result on the page
            return render(request, 'premium_result.html', context=context)

    else:
        form = PremiumCalculationFormCasco()

    return render(request, 'premium_calculation.html', {'form': form})


@login_required
def buy_casco_policy(request):
    # Get the authenticated user
    user = request.user

    # Retrieve the associated Policyholder object
    policyholder = Policyholder.objects.get(user=user)

    # If the key is present, it returns the corresponding value. If the key is not present, it returns an empty
    # dictionary {} as the default value.
    insurance_data = request.session.get("insurance_data", {})

    start_date = datetime.strptime(insurance_data.get("start_date"), "%Y-%m-%d").date()
    end_date = datetime.strptime(insurance_data.get("end_date"), "%Y-%m-%d").date()
    plate_number = insurance_data["plate_number"]
    policy_duration = insurance_data.get("policy_duration")
    driver_experience = insurance_data.get("driver_experience")
    alarm_system_ind_list = insurance_data.get("alarm_system_indicator")
    premium = insurance_data.get("premium")

    if alarm_system_ind_list:
        car_alarm = True
    else:
        car_alarm = False

    new_policy = Policy.objects.create(
        policyholder=policyholder,
        start_date=start_date,
        end_date=end_date,
        policy_duration=policy_duration,
        policy_type="CASCO",
        insurance_premium=premium,
    )

    car = Car.objects.get(plate_number=plate_number)

    new_casco_record = CASCOData.objects.create(
        policy=new_policy,
        driver_experience=driver_experience,
        car_alarm=car_alarm,
        car=car,
    )

    # Call function that sends email
    send_policy_email(user.email, "casco_insurance_rules.pdf")

    # If the user is authenticated, redirect to the "Thank You" page
    return render(request, 'thank_you.html', {
        'email': request.user.email,  # We use authenticated user's email
        'start_date': start_date,
    })


@login_required
def insure_property(request):
    if request.method == 'POST':
        form = PremiumCalculationFormProperty(request.POST)
        if form.is_valid():
            insurance_data = form.cleaned_data  # dictionary with cleaned, validated data

            # PRINT for TEST only.
            print(insurance_data)

            start_date = insurance_data["start_date"]
            end_date = insurance_data["end_date"]
            construction = insurance_data["construction"]
            building_purpose = insurance_data['building_purpose']
            selected_risks = insurance_data['selected_risks']  # Will be not empty list because we require that at least
            # one risk must be chosen.

            if start_date >= end_date:
                messages.error(request, f"Attention! Policy end date must be bigger than policy start date.")
                return render(request, "premium_calculation.html", {"form": form})

            policy_duration = (end_date - start_date).days

            premium = calculate_premium_for_property(policy_duration, building_purpose, construction, selected_risks)

            # If we need to serialize dates to JSON we need to convert them to str.
            insurance_data["start_date"] = str(start_date)
            insurance_data["end_date"] = str(end_date)

            # Let's also add policy_duration and premium, so that we wouldn't have to recalculate them.

            insurance_data["policy_duration"] = policy_duration
            insurance_data["premium"] = premium

            # We store data in the session for the use in next step.
            request.session["insurance_data"] = insurance_data

            # PRINTS for TEST only. Compare with the print above.
            print(request.session["insurance_data"])
            print(request.session)

            context = {"premium": premium,
                       "policy_duration": policy_duration}

            # Display the result on the page
            return render(request, 'premium_result.html', context=context)

    else:
        form = PremiumCalculationFormProperty()

    return render(request, 'premium_calculation.html', {'form': form})


@login_required
def buy_property_policy(request):
    # Get the authenticated user
    user = request.user

    # Retrieve the associated Policyholder object
    policyholder = Policyholder.objects.get(user=user)

    # If the key is present, it returns the corresponding value. If the key is not present, it returns an empty
    # dictionary {} as the default value.
    insurance_data = request.session.get("insurance_data", {})

    start_date = datetime.strptime(insurance_data.get("start_date"), "%Y-%m-%d").date()
    end_date = datetime.strptime(insurance_data.get("end_date"), "%Y-%m-%d").date()
    policy_duration = insurance_data.get("policy_duration")
    construction = insurance_data.get("construction")
    building_purpose = insurance_data.get("building_purpose")
    selected_risks = insurance_data.get("selected_risks")  # Will be not empty list because we require that at least
    # one risk must be chosen.
    premium = insurance_data.get("premium")

    new_policy = Policy.objects.create(
        policyholder=policyholder,
        start_date=start_date,
        end_date=end_date,
        policy_duration=policy_duration,
        policy_type="PROPERTY",
        insurance_premium=premium,
    )

    new_property_record = PropertyData.objects.create(
        policy=new_policy,
        building_purpose=building_purpose,
        construction=construction,
    )

    for risk in selected_risks:
        risk_object, created = Risk.objects.get_or_create(property_risk=risk)
        new_property_record.risks.add(risk_object)

    # Call function that sends email
    send_policy_email(user.email, "property_insurance_rules.pdf")

    # If the user is authenticated, redirect to the "Thank You" page
    return render(request, 'thank_you.html', {
        'email': request.user.email,  # We use authenticated user's email
        'start_date': start_date,
    })


@login_required
def file_claim(request):

    user = request.user
    policyholder = Policyholder.objects.get(user=user)
    policies = Policy.objects.filter(policyholder=policyholder)

    context = {
        "policies": policies,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "personal_code": policyholder.personal_code,
        "email": user.email,
        "tel_num": policyholder.tel_num,
    }

    if request.method != "POST":
        return render(request, 'claim_form.html', context=context)

    # If POST, we take data from the claim form.
    incident_date = request.POST.get('incident_date')  # In case key was not found, the returned value would be None.
    description = request.POST.get('description')
    supporting_document = request.FILES.get('supporting_document')
    selected_policy = request.POST.get("selected_policy")

    # Only for TESTING
    print(incident_date)
    print(type(incident_date))
    print(description)
    print(supporting_document)
    print(selected_policy)
    print(type(selected_policy))
    print("POLICY OBJECT")
    policy = Policy.objects.get(policy_number=selected_policy)
    print(policy)
    ################################################################

    new_claim = Claim.objects.create(
        incident_date=incident_date,
        description_of_the_incident=description,
        supporting_document=supporting_document,
        policy=policy,
    )

    # Placeholder for saving info to the database.

    html_content = "<h1>Your claim has been successfully submitted. Our team will review the information provided, and you will receive further communication regarding the status of your claim in 24 hours.</h1>"
    return HttpResponse(html_content)


class PoliciesByUserListView(LoginRequiredMixin, generic.ListView):  # Subclass of the parent class ListView.
    model = Policy
    template_name = "user_policies.html"
    context_object_name = "policies_list"
    paginate_by = 4

    def get_queryset(self):
        user = self.request.user

        # Retrieve the associated Policyholder object
        policyholder = Policyholder.objects.get(user=user)
        return Policy.objects.filter(policyholder=policyholder)  # We can add .order_by().

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["today"] = date.today()
        return context


class SearchPoliciesView(UserPassesTestMixin, generic.TemplateView):
    template_name = "search_policies.html"

    def test_func(self):
        # Here we check if the user is in the group "Underwriters"
        return self.request.user.groups.filter(name="Underwriters").exists()

    def get(self, request, *args, **kwargs):
        # In case of GET request
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        # In case of POST request
        policy_type = request.POST.get("policy_type")
        last_name_fragment = request.POST.get("last_name", "")
        print(last_name_fragment)

        query = Q(policy_type=policy_type)

        if last_name_fragment:
            query &= Q(policyholder__user__last_name__icontains=last_name_fragment)
            query_2 = Q(policyholder__user__last_name__icontains=last_name_fragment)
        else:
            query_2 = Q()

        if policy_type == "ALL":
            search_results = Policy.objects.filter(query_2)
        else:
            search_results = Policy.objects.filter(query)

        return render(request, self.template_name, {"search_results": search_results})


class PolicyDetailView(LoginRequiredMixin, generic.DetailView):
    """
    Display detailed information about a policy for authenticated users.

    Attributes:
        model (class): The Django model class representing policies.
        context_object_name (str): The name used to identify the policy object in the template context.
        template_name (str): Name of the template, which is used to render details of the specific policy.

    Methods:
        get_context_data(**kwargs): Sends additional context data to the template.

    Mixins:
        LoginRequiredMixin: Ensures that only authenticated users can access the policy details.
    """
    model = Policy
    context_object_name = "policy"
    template_name = "policy_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["today"] = date.today()
        return context


# Think through if @login_required is needed
def cancel_policy(request: HttpRequest, policy_number: UUID) -> HttpResponse:
    """
    Cancel a policy based on the given policy number by changing its end date.

    Parameters:
    - request (HttpRequest): The HTTP request object.
    - policy_number (UUID): Unique policy number of the policy that is chosen for cancelation.

    Returns:
    - HttpResponse: A rendered HTML response with cancelation message.

    Raises:
    - Http404: If the specified policy number does not exist.
    """
    today = date.today()
    policy = get_object_or_404(Policy, policy_number=policy_number)

    if policy.start_date > today:
        policy.end_date = policy.start_date
    elif policy.start_date <= today <= policy.end_date:
        policy.end_date = today
    else:
        pass  # Policy already ended. We leave end date as it is.
    policy.save()
    return render(request, 'message_of_cancelation.html', {"policy": policy})
