from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property


class User(AbstractUser):
    friends = models.ManyToManyField('self', blank=True, symmetrical=False)

    @cached_property
    def friends_mutual(self):
        '''Returns a queryset of the users who are friended by this user, and have friended back'''
        return self.friends.filter(friends=self)
    
    def get_outgoing_requests(self):
        '''Returns a queryset of the users who are friended by this user, but haven't friended back'''
        return self.friends.exclude(pk__in=self.friends_mutual)
    
    def get_incoming_requests(self):
        '''Returns a queryset of the users who have friended this user, but this user hasn't friended back'''
        return User.objects.filter(friends=self).exclude(pk__in=self.friends_mutual)