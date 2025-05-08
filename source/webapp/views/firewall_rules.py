from django.views.generic import TemplateView

from webapp.models import Connection


class FirewallRulesView(TemplateView):
    template_name = 'firewall_rules.html'


class AllRulesView(TemplateView):
    template_name = 'all_rules.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        # Все правила пользователя (ненулевые)
        connections = Connection.objects.filter(
            report__user=user,
            firewall_rule__isnull=False
        ).exclude(firewall_rule="")

        context['connections_with_rules'] = [
            {'id': t.connect_varchar_id, 'rule': t.firewall_rule}
            for t in connections if t.firewall_rule
        ]

        return context