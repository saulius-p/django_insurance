from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.conf import settings

from .models import Policyholder, Policy, Car, MTPLData, PropertyData, Risk, CASCOData
from .forms import UserUpdateForm, ProfileUpdateForm, PremiumCalculationFormProperty, \
    PremiumCalculationFormCasco, PremiumCalculationFormMtpl
from .pricing_functions import calculate_premium_for_mtpl, calculate_premium_for_property, calculate_premium_for_casco
from .helper_functions import check_passwordl

from datetime import datetime
import os


def index(request):
    # num_policyholders = Policyholder.objects.count()
    # context = {
    #     "num_policyholders": num_policyholders,
    # }
    return render(request, "index.html")


def policyholders(request):
    policyholders = Policyholder.objects.all()
    context = {
        "policyholders": policyholders,
    }
    return render(request, "policyholders.html", context=context)


def add(request):
    val1 = int(request.POST["num1"])
    val2 = int(request.POST["num2"])
    res = val1 + val2
    return render(request, "result.html", {"res": res})


def insure_policy(request):
    return render(request, "insure_policy.html")


@csrf_protect
def register_user(request):
    if request.method != "POST":
        return render(request, "registration/registration.html")

    # jeigu POST
    # paimam duomenis iš formos
    username = request.POST["username"]
    email = request.POST["email"]
    password = request.POST["password"]
    password2 = request.POST["password2"]

    if password != password2:
        messages.error(request, "Slaptažodžiai nesutampa!!!")

    if User.objects.filter(username=username).exists():  # exists atiduoda True arba False
        messages.error(request, f"Vartotojo vardas {username} užimtas!!!")

    if User.objects.filter(email=email).exists():
        messages.error(request, f"Emailas {email} jau registruotas!!!")

    if messages.get_messages(request):
        return redirect("register-url")

    User.objects.create_user(username=username, email=email, password=password)
    messages.success(request, f"Vartotojas vardu {username} sukurtas!!!")
    return redirect('login')


@login_required
def profile(request):
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

            try:
                car = Car.objects.get(plate_number=plate_number)
            except Car.DoesNotExist:
                messages.error(request, f"Car with plate number {plate_number} not found.")
                return render(request, "premium_calculation.html", {"form": form})

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

    # Logic for sending emails

    # Here we specify FULL path to the PDF file.
    pdf_file_path = os.path.join(settings.MEDIA_ROOT, "insurance_rules", "mtpl_reference_doc.pdf").replace("\\", "/")

    # FOR TESTING PURPOSES
    print("TEST")
    print(pdf_file_path)
    print("TEST")
    if os.path.exists(pdf_file_path):
        print("File exists!")
    else:
        print("File does not exist!")

    # Here we create EmailMessage class object.

    email_message = EmailMessage(
        "Thank You for Choosing Our Product",
        f"We attach all the necessary documents.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )

    email_message.attach_file(pdf_file_path)
    email_message.send(fail_silently=False)  # In short, "fail_silently=False" means, that errors will not be silenced.

    # If the user is authenticated, redirect to the "Thank You" page
    return render(request, 'thank_you.html', {
        'email': user.email,  # We use authenticated user's email
        'start_date': start_date,
    })


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

            # LINE JUST FOR TESTING.
            print(f"Alarm system indication: {alarm_system_ind_list}")

            try:
                car = Car.objects.get(plate_number=plate_number)
            except Car.DoesNotExist:
                messages.error(request, f"Car with plate number {plate_number} not found.")
                return render(request, "premium_calculation.html", {"form": form})

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

    # Logic for sending emails

    # Here we specify FULL path to the PDF file.
    pdf_file_path = os.path.join(settings.MEDIA_ROOT, "insurance_rules", "casco_insurance_rules.pdf").replace("\\", "/")

    # FOR TESTING PURPOSES
    print("TEST")
    print(pdf_file_path)
    print("TEST")
    if os.path.exists(pdf_file_path):
        print("File exists!")
    else:
        print("File does not exist!")

    # Here we create EmailMessage class object.

    email_message = EmailMessage(
        "Thank You for Choosing Our Product",
        f"We attach all the necessary documents.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )

    email_message.attach_file(pdf_file_path)
    email_message.send(fail_silently=False)  # In short, "fail_silently=False" means, that errors will not be silenced.

    # If the user is authenticated, redirect to the "Thank You" page
    return render(request, 'thank_you.html', {
        'email': request.user.email,  # We use authenticated user's email
        'start_date': start_date,
    })


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

    # Logic for sending emails

    # Here we specify FULL path to the PDF file.
    pdf_file_path = os.path.join(settings.MEDIA_ROOT, "insurance_rules", "property_insurance_rules.pdf").replace("\\",
                                                                                                                 "/")

    # FOR TESTING PURPOSES
    print("TEST")
    print(pdf_file_path)
    print("TEST")
    if os.path.exists(pdf_file_path):
        print("File exists!")
    else:
        print("File does not exist!")

    # Here we create EmailMessage class object.

    email_message = EmailMessage(
        "Thank You for Choosing Our Product",
        f"We attach all the necessary documents.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )

    email_message.attach_file(pdf_file_path)
    email_message.send(fail_silently=False)  # In short, "fail_silently=False" means, that errors will not be silenced.

    # If the user is authenticated, redirect to the "Thank You" page
    return render(request, 'thank_you.html', {
        'email': request.user.email,  # We use authenticated user's email
        'start_date': start_date,
    })


@csrf_protect
def register_user(request):
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
def file_claim(request):
    if request.method != "POST":
        return render(request, 'claim_form.html')

    # If POST, we take data from the claim form.
    incident_date = request.POST.get('incident_date')  # In case key was not found, the returned value would be None.
    description = request.POST.get('description')
    claimant_name = request.POST.get('claimant_name')
    claimant_email = request.POST.get('claimant_email')
    claimant_tel_num = request.POST.get('claimant_tel_num')
    supporting_documents = request.FILES.get('supporting_documents')

    # Placeholder for saving info to the database.

    html_content = "<h1>Your claim has been successfully submitted. Our team will review the information provided, and you will receive further communication regarding the status of your claim in 24 hours.</h1>"
    return HttpResponse(html_content)


class PoliciesByUserListView(LoginRequiredMixin, generic.ListView):  # Subclass of the parent class ListView.
    model = Policy
    template_name = "user_policies.html"
    context_object_name = "policies_list"

    def get_queryset(self):
        user = self.request.user

        # Retrieve the associated Policyholder object
        policyholder = Policyholder.objects.get(user=user)
        return Policy.objects.filter(policyholder=policyholder)  # We can add .order_by().


class PolicyDetailView(LoginRequiredMixin, generic.DetailView):
    model = Policy
    context_object_name = "policy"
    template_name = "policy_detail.html"



