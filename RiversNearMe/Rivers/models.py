# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines for those models you wish to give write DB access
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.
from __future__ import unicode_literals

from django.db import models

class AuthGroup(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=80)
    class Meta:
        managed = False
        db_table = 'auth_group'

class AuthGroupPermissions(models.Model):
    id = models.IntegerField(primary_key=True)
    group_id = models.IntegerField()
    permission = models.ForeignKey('AuthPermission')
    class Meta:
        managed = False
        db_table = 'auth_group_permissions'

class AuthPermission(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    content_type_id = models.IntegerField()
    codename = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'auth_permission'

class AuthUser(models.Model):
    id = models.IntegerField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField()
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=30)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.CharField(max_length=75)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    default_loc = models.TextField(blank=True, null=True)
    default_lat = models.FloatField(blank=True, null=True)
    default_lon = models.FloatField(blank=True, null=True)
    placemarks = models.ManyToManyField('Placemarks')
    class Meta:
        managed = False
        db_table = 'auth_user'

class AuthUserGroups(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    group = models.ForeignKey(AuthGroup)
    class Meta:
        managed = False
        db_table = 'auth_user_groups'

class AuthUserUserPermissions(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    permission = models.ForeignKey(AuthPermission)
    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'

class DjangoAdminLog(models.Model):
    id = models.IntegerField(primary_key=True)
    action_time = models.DateTimeField()
    user_id = models.IntegerField()
    content_type_id = models.IntegerField(blank=True, null=True)
    object_id = models.TextField(blank=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    class Meta:
        managed = False
        db_table = 'django_admin_log'

class DjangoContentType(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'django_content_type'

class DjangoSession(models.Model):
    session_key = models.CharField(unique=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'django_session'

class Placemarks(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField(blank=True) # This field type is a guess.
    class_field = models.TextField(db_column='class', blank=True) # Field renamed because it was a Python reserved word. This field type is a guess.
    description = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True) # This field type is a guess.
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    section = models.TextField(blank=True) # This field type is a guess.
    usgs_gauge = models.ForeignKey('Gauges', to_field='usgs_gauge', db_column='usgs_gauge', blank=True)
    flow_min = models.FloatField(blank=True, null=True)
    flow_max = models.FloatField(blank=True, null=True)
    stage_min = models.FloatField(blank=True, null=True)
    stage_max = models.FloatField(blank=True, null=True)
    class Meta:
        #managed = False
        db_table = 'placemarks'
        
    def __unicode__(self):
        return self.name+"-"+self.section

class Gauges(models.Model):
    usgs_gauge = models.TextField(unique=True)
    flow = models.FloatField(blank=True, null=True)
    stage = models.FloatField(blank=True, null=True)
    water_temp = models.FloatField(blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)
    flow_delta = models.FloatField(blank=True, null=True)
    stage_delta = models.FloatField(blank=True,null=True)
    temp_delta = models.FloatField(blank=True, null=True)
    
    class Meta:
        #managed = False
        db_table = 'gauges'
        
    def __unicode__(self):
        return self.usgs_gauge

