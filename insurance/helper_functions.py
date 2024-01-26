from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
import os

from .models import Car


def check_passwordl(password):
    return len(password) >= 4


def send_policy_email(user_email: str, pdf_file_name: str) -> None:
    """
    Function sends an email with the policy confirmation and attaches the PDF file.
    """

    # Here we specify FULL path to the PDF file.
    pdf_file_path = os.path.join(settings.MEDIA_ROOT, "insurance_rules", pdf_file_name).replace("\\",
                                                                                                "/")
    print("TEST")
    print(pdf_file_path)
    print("TEST")
    if os.path.exists(pdf_file_path):
        print("File exists!")
    else:
        print("File does not exist!")

    # Create EmailMessage class object.
    email_message = EmailMessage(
        "Thank You for Choosing Our Product",
        """        We attach all the necessary documents.
        To start your insurance coverage, transfer the insurance bonus to this account LT888800000000000000001.""",
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
    )

    email_message.attach_file(pdf_file_path)
    email_message.send(fail_silently=False)


def validate_car_insurance_data(request, form):
    """
    Validates car insurance data common to both insure_mtpl and insure_casco functions.

    Parameters:
    - request: HttpRequest object representing the current request.
    - form: The PremiumCalculationForm to be validated.

    Returns:
    - Tuple[Car | None, HttpResponse | None]: A tuple containing the Car object (if found) and an HttpResponse
                                           if validation fails.
    """
    insurance_data = form.cleaned_data  # dictionary with cleaned, validated data
    start_date = insurance_data["start_date"]
    end_date = insurance_data["end_date"]
    plate_number = insurance_data["plate_number"]

    if start_date >= end_date:
        messages.error(request, f"Attention! Policy end date must be bigger than policy start date.")
        return None, render(request, "premium_calculation.html", {"form": form})

    try:
        car = Car.objects.get(plate_number=plate_number)
    except Car.DoesNotExist:
        messages.error(request, f"Car with plate number {plate_number} not found.")
        return None, render(request, "premium_calculation.html", {"form": form})

    user = request.user

    # PRINT LINES ONLY FOR TEST
    print("USER TEST")
    print(car.owner_personal_code)
    print(user.policyholder.personal_code)

    if car.owner_personal_code != user.policyholder.personal_code:
        messages.error(request, f"You are not the owner of this car. Did you enter plate number correctly?")
        return None, render(request, "premium_calculation.html", {"form": form})

    return car, None
