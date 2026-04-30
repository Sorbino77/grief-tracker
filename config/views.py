from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "home.html"


class DashboardView(TemplateView):
    template_name = "dashboard.html"


class PrivacyView(TemplateView):
    """Plain-language GDPR privacy notice. Linked from the register form."""
    template_name = "privacy.html"
