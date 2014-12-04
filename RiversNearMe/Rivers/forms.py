from operator import itemgetter
from django import forms
#from django.core.validators
from registration.forms import RegistrationForm as DefaultRegistrationForm
import registration.forms as RegForms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field, Fieldset
from crispy_forms.bootstrap import InlineField, PrependedText, StrictButton, FormActions, Alert
from Rivers.validators import validGauge

CLASSIFICATIONS = (('I','I'),
                   ('I+', 'I+'),
                   ('II-', 'II-'),
                   ('II', 'II'),
                   ('II+', 'II+'),
                   ('III-', 'III-'),
                   ('III', 'III'),
                   ('III+', 'III+'),
                   ('IV-', 'IV-'),
                   ('IV', 'IV'),
                   ('IV+', 'IV+'),
                   ('V-', 'V-'),
                   ('V', 'V'),
                   ('V+', 'V+'),
                   ('VI', 'VI'),)

STATES = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}

class PlacemarkForm(forms.Form):
    name = forms.RegexField(regex=r'^[\w.@+-]+$',
                            max_length = 50,
                            label = "River",
                            help_text = "Name of the river.",
                            error_messages={'invalid': "This value may contain only letters, numbers and @/./+/-/_ characters."}
                            )
    section = forms.RegexField(regex=r'^[\w\s.@+-]+$',
                               max_length = 50,
                               label = "Section",
                               help_text = "Name of the specific section of the river.",
                               error_messages={'invalid': "This value may contain only letters, numbers and @/./+/-/_ characters."}
                               )
    class_field = forms.ChoiceField(label="Class",
                                    choices=CLASSIFICATIONS,
                                    help_text = "Whitewater classification for standard lines and typical flows.",)
    description = forms.URLField(label = "URL",
                                 #initial = "Description Link",
                                 help_text = "URL Link to a web page describing the section.",
                                 error_messages={'invalid': "This value must contain a valid URL."},
                                 required=False)
    state = forms.ChoiceField(label = "State",
                              help_text = "Two-letter state abbreviation where the put-in is located.",
                              choices = sorted(STATES.items(),key=itemgetter(1)),
                              required=False,)
    lat = forms.DecimalField(label = "Latitude",
                           help_text = "Latitude in +/- decimal degrees.",
                           min_value=-90,
                           max_value=90,
                           max_digits=9,
                           decimal_places=6)
    lon = forms.DecimalField(label = "Longitude",
                           help_text = "Longitude in +/- decimal degrees.",
                           min_value=-180,
                           max_value=180,
                           max_digits=9,
                           decimal_places=6,)
    usgs_gauge = forms.RegexField(regex=r'^[0-9]+$',
                                  label = "USGS Gauge ID",
                                  help_text = '<a href="http://http://waterdata.usgs.gov/nwis/rt">USGS Gauge ID</a> for the section (if applicable).',
                                  validators = [validGauge],
                                  required=False,)
    flow_min = forms.IntegerField(label = "Flow Min",
                                  help_text = "Minimum runnable flow in CFS.",
                                  min_value=0,
                                  max_value=999999,
                                  required=False)
    flow_max = forms.IntegerField(label = "Flow Max",
                                  help_text = "Maximum runnable flow in CFS.",
                                  min_value=0,
                                  max_value=999999,
                                  required=False)
    stage_min = forms.DecimalField(label = "Stage Min",
                                 help_text = "Minimum runnable level in feet.",
                                 min_value=-99,
                                 max_value=1000,
                                required=False)
    stage_max = forms.DecimalField(label = "Stage Max",
                                 help_text = "Maximum runnable level in feet.",
                                 min_value=0,
                                 max_value=1000,
                                required=False)
    
    def __init__(self, *args, **kwargs):
        super(PlacemarkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_id = 'addRiverForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.helper.form_action = '/rivers/add_river/'
        self.helper.label_class = 'col-sm-2 control-label'
        self.helper.field_class = 'col-sm-5'
        self.helper.help_text_inline = False
        self.helper.layout = Layout(
            Field('name', placeholder='River Name'),
            Field('section', placeholder='River Section'),
            'state',
            'class_field',
            PrependedText('description','URL:',),
            Field('usgs_gauge', placeholder='01646500'),
            Fieldset('Coordinates',
                     Field('lat', placeholder='e.g. 38.8977332'),
                     Field('lon', placeholder='e.g. -77.0365305'),),
            Fieldset('Runnable Flows',
                     'flow_min',
                     'flow_max',),
            Fieldset('Runnable Levels',
                     'stage_min',
                     'stage_max',),
            Div(
                FormActions(
                        StrictButton('Close', data_dismiss="modal", css_class="btn btn-default"),
                        StrictButton('Save Changes', value='Submit', type='submit', css_class="btn btn-primary"),
                        ),
                css_class="modal-footer"
               ),
        )
        
class UserProfileForm(forms.Form):
    first_name = forms.RegexField(regex=r'^[\w\'\-]+$',
                            max_length = 20,
                            label = "First Name",
                            required = False,
                            error_messages={'invalid': "This value may contain only letters, numbers and [',-] characters."}
                            )
    last_name = forms.RegexField(regex=r'^[\w\'\-]+$',
                            max_length = 20,
                            label = "Last Name",
                            required = False,
                            error_messages={'invalid': "This value may contain only letters, numbers and [',-] characters."}
                            )
    default_loc = forms.CharField(label = "Default Location",
                                       max_length = 50,
                                       required = False,
                                       help_text = "Enter an address or Lat/Lon coordinates that will serve as your default location when you login.",
                                       error_messages={'invalid': "Unable to resolve this address."})
    default_lat = forms.DecimalField(label = "Default Latitude",
                                     required = False,
                                     help_text = "Default latitude in +/- decimal degrees.",
                                     min_value=-90,
                                     max_value=90,
                                     max_digits=9,
                                     decimal_places=7)
    default_lon = forms.DecimalField(label = "Default Longitude",
                                     required = False,
                                     help_text = "Default longitude in +/- decimal degrees.",
                                     min_value=-180,
                                     max_value=180,
                                     max_digits=9,
                                     decimal_places=7,)
    
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_id = 'userProfileForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.helper.form_action = '/rivers/user_profile/'
        self.helper.label_class = 'col-sm-2 control-label'
        self.helper.field_class = 'col-sm-4'
        self.helper.layout = Layout(
            Field('first_name', placeholder="First Name (optional)"),
            Field('last_name', placeholder="Last Name (optional)"),
            Field('default_loc', placeholder="123 Main St, Anytown, AL *or* 12.345, -54.321"),
            Field('default_lat', placeholder="e.g. 38.8977332"),
            Field('default_lon', placeholder="e.g. -77.0365305"),
            Div( FormActions(
                 StrictButton('Save Changes', value='Submit', type='submit', css_class="btn btn-primary")),
                 css_class = "col-sm-offset-2")
            )
    


#class RegistrationForm(RegForms.RegistrationForm):
#    
#    default_loc = forms.CharField(label=_("Default Location"))