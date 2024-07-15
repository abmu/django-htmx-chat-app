from django.db import models
from django.db.models.functions import Lower
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property
from allauth.account.models import EmailAddress


class User(AbstractUser):
    friends = models.ManyToManyField('self', blank=True, symmetrical=False)

    @cached_property
    def friends_mutual(self):
        '''Returns a queryset of the users who are friended by this user, and have friended back'''
        return self.friends.filter(friends=self).order_by(Lower('username'))
    
    def get_outgoing_requests(self):
        '''Returns a queryset of the users who are friended by this user, but haven't friended back'''
        return self.friends.exclude(pk__in=self.friends_mutual).order_by(Lower('username'))
    
    def get_incoming_requests(self):
        '''Returns a queryset of the users who have friended this user, but this user hasn't friended back'''
        return User.objects.filter(friends=self).exclude(pk__in=self.friends_mutual).order_by(Lower('username'))
    
    def delete_account(self):
        '''Delete a user's account, but preserve the old user id in the database'''
        self.is_active = False
        self.username = f'deleted_user_{self.id}'
        self.email = ''
        EmailAddress.objects.filter(user=self).delete()
        self.set_unusable_password()
        self.save()
        
        for friend in self.friends_mutual:
            self.friends.remove(friend)
            friend.friends.remove(self)