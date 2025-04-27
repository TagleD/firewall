from django.views.generic import TemplateView


class FirewallRulesView(TemplateView):
    template_name = 'firewall_rules.html'