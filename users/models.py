from django.db import models
from django.db.models.functions import Lower
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property
from allauth.account.models import EmailAddress
from chat.models import Message


class User(AbstractUser):
    DELETED_USER_PREFIX = 'deleted_user_'

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
    
    def add_friend(self, friend):
        '''Add a user to this user's friends list'''
        self.friends.add(friend)
    
    def remove_friend(self, friend):
        '''Returns a tuple containing a boolean success flag (True if the friend is removed, False otherwise), and a message'''
        if not self.friends_mutual.contains(friend):
            return False, 'No such user in friends list'
        
        self.friends.remove(friend)
        friend.friends.remove(self)
        return True, 'Friend successfully removed'
    
    def handle_incoming_request(self, request_sender, action):
        '''Returns a tuple containing a boolean success flag (True if the incoming request is either rejected or accepted successfully, False otherwise), and a message'''
        if not self.get_incoming_requests().contains(request_sender):
            return False, 'No such friend request'

        if action == 'accept':
            self.friends.add(request_sender)
            message = 'Incoming friend request successfully accepted'
        elif action == 'reject':
            request_sender.friends.remove(self)
            message = 'Incoming friend request successfully rejected'
        else:
            return False, 'Invalid action'
        
        return True, message
    
    def cancel_outgoing_request(self, request_recipient):
        '''Returns a tuple containing a boolean success flag (True if the outgoing request is cancelled successfully, False otherwise), and a message'''
        if not self.get_outgoing_requests().contains(request_recipient):
            return False, 'No such friend request'

        self.friends.remove(request_recipient)
        return True, 'Outgoing friend request successfully cancelled'

    def delete_account(self):
        '''Delete a user's account, but keep the old user id in the database'''
        self.is_active = False
        self.username = f'{self.DELETED_USER_PREFIX}{self.id}'
        self.email = ''
        EmailAddress.objects.filter(user=self).delete()
        self.set_unusable_password()
        self.save()
        
        for friend in self.friends_mutual:
            self.friends.remove(friend)
            friend.friends.remove(self)

        self.remove_redundant_users()

    @classmethod
    def remove_redundant_users(cls):
        '''Remove all users from the database who have deleted their account and have no messages'''
        Message.remove_redundant_messages()
        deleted_users = cls.objects.filter(is_active=False)
        for user in deleted_users:
            if not Message.objects.filter(
                models.Q(sender=user) |
                models.Q(recipient=user)
            ).exists():
                user.delete()

    @classmethod
    def has_deleted_user_prefix(cls, username):
        '''Check if a username starts with the prefix used for deleted users' usernames'''
        return username.startswith(cls.DELETED_USER_PREFIX)