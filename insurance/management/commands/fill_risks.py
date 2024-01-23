from django.core.management.base import BaseCommand
from insurance.models import Risk


class Command(BaseCommand):
    """
    Class Command defines objects, that are specific commands, that are run. In this case
    it is dedicated to filling table insurance_risk with a predefined list of risks.

    Usage:
    python manage.py fill_risks

    Description:
    This command fills the table insurance_risk with a predefined list of risks.
    If a risk already exists in the database, it will not be duplicated.

    Example:
    python manage.py fill_risks
    """
    help = "Fill the Risk model with risks."

    def handle(self, *args, **options):
        property_risks = [
            "Fire",
            "Floods",
            "Windstorms and Hail",
            "Snow and Ice",
            "Water Damage",
            "Impact Damage",
            "Theft",
            "Vandalism",
            "Liability Coverage",
            "Loss of Use",
            "Business-Related Risks",
            "Power Surge",
            "Explosion",
            "Falling Objects",
            "Building Collapse",
        ]

        for risk in property_risks:
            # _ is an object of class Risk; created has a boolean type;
            _, created = Risk.objects.get_or_create(property_risk=risk)

            if created:  # If we created line object, method returns true.
                self.stdout.write(self.style.SUCCESS(f'Successfully added risk: {risk}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Risk already exists: {risk}'))