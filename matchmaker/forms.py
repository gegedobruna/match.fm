import re
from django import forms

USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class MatchForm(forms.Form):
    username_a = forms.CharField(label="User A", max_length=50)
    username_b = forms.CharField(label="User B", max_length=50)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username_a"].widget.attrs.update(
            {"placeholder": "e.g. your_username", "autocomplete": "off"}
        )
        self.fields["username_b"].widget.attrs.update(
            {"placeholder": "e.g. friend_username", "autocomplete": "off"}
        )

    def clean_username_a(self):
        return self._clean_username("username_a")

    def clean_username_b(self):
        return self._clean_username("username_b")

    def _clean_username(self, field_name: str) -> str:
        value = self.cleaned_data.get(field_name, "").strip()
        if not value:
            raise forms.ValidationError("Username cannot be empty.")
        if not USERNAME_RE.match(value):
            raise forms.ValidationError("Only letters, numbers, underscores, and hyphens are allowed.")
        return value
