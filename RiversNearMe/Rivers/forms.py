import registration.forms as RegForms

class RegistrationForm(RegForms.RegistrationForm):
    
    default_loc = forms.CharField(label=_("Default Location"))