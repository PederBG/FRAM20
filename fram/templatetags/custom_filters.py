from django import template

register = template.Library()

@register.filter
def rem(self):
    return self.replace("-", "")
