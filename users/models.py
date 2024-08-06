from django.db import models
from django.db.models.functions import Lower
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property
from uuid import uuid4
from allauth.account.models import EmailAddress
from chat.models import Message
from chat.utils import get_group_name, send_ws_message


class User(AbstractUser):
    DELETED_USER_PREFIX = 'deleted_user_'
    PLACEHOLDER_USERNAME = 'temp'

    username = models.CharField(max_length=150, unique=True)
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    friends = models.ManyToManyField('self', blank=True, symmetrical=False)

    
    class Meta:
        indexes = [
            models.Index(fields=['username'], name='username_idx')
        ]

    # NOTE: Using @cached_property here provides limited benefit since the method returns a queryset object, rather than
    # returning the result of a queryset being evaluated (which would cause a database access to be made and the result cached).
    @cached_property
    def friends_mutual(self):
        '''Returns a queryset of the users who are friended by this user, and have friended back'''
        return self.friends.filter(friends=self).order_by(Lower('username'))
    
    def get_incoming_requests(self):
        '''Returns a queryset of the users who have friended this user, but this user hasn't friended back'''
        return User.objects.filter(friends=self).exclude(pk__in=self.friends_mutual).order_by(Lower('username'))
    
    def get_outgoing_requests(self):
        '''Returns a queryset of the users who are friended by this user, but haven't friended back'''
        return self.friends.exclude(pk__in=self.friends_mutual).order_by(Lower('username'))
    
    def has_friend_mutual(self, user):
        '''Check if there is a mutual friendship between this user and the specified user'''
        return self.friends_mutual.contains(user)
    
    def has_incoming_request_from(self, user):
        '''Check if this user has received a friend request from the specified user'''
        return self.get_incoming_requests().contains(user)
    
    def has_outgoing_request_to(self, user):
        '''Check if this user has sent a friend request to the specified user'''
        return self.get_outgoing_requests().contains(user)
    
    def add_friend(self, friend):
        '''Add a user to this user's friends list'''
        if self.friends.contains(friend):
            return
        
        self.friends.add(friend)
        if self.has_friend_mutual(friend):
            group_name = get_group_name(friend)
            send_ws_message(group_name, {'type': 'friendship_created'})
    
    def remove_friend(self, friend):
        '''Returns a tuple containing a boolean success flag (True if the friend is removed, False otherwise), and a message'''
        if not self.has_friend_mutual(friend):
            return False, 'No such user in friends list'
        
        self.friends.remove(friend)
        friend.friends.remove(self)

        group_name = get_group_name(friend)
        send_ws_message(group_name, {'type': 'friendship_removed'})

        return True, 'Friend successfully removed'
    
    def handle_incoming_request(self, request_sender, action):
        '''Returns a tuple containing a boolean success flag (True if the incoming request is either rejected or accepted successfully, False otherwise), and a message'''
        if not self.has_incoming_request_from(request_sender):
            return False, 'No such incoming friend request'

        if action == 'accept':
            self.add_friend(request_sender)
            message = 'Incoming friend request successfully accepted'
        elif action == 'reject':
            request_sender.friends.remove(self)
            message = 'Incoming friend request successfully rejected'
        else:
            return False, 'Invalid action'
        
        return True, message
    
    def cancel_outgoing_request(self, request_recipient):
        '''Returns a tuple containing a boolean success flag (True if the outgoing request is cancelled successfully, False otherwise), and a message'''
        if not self.has_outgoing_request_to(request_recipient):
            return False, 'No such outgoing friend request'

        self.friends.remove(request_recipient)
        return True, 'Outgoing friend request successfully cancelled'

    def delete_account(self):
        '''Delete a user's account data, but keep the old user id in the database'''
        self.is_active = False
        self.username = f'{self.DELETED_USER_PREFIX}{self.uuid}'
        self.email = ''
        EmailAddress.objects.filter(user=self).delete()
        self.set_unusable_password()
        self.save()
        
        for friend in self.friends_mutual:
            group_name = get_group_name(friend)
            send_ws_message(group_name, {'type': 'friend_account_deleted'})

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
        return username.lower().startswith(cls.DELETED_USER_PREFIX)
    
    @classmethod
    def is_placeholder_username(cls, username):
        '''Check if the given username matches the reserved placeholder username'''
        return username.lower() == cls.PLACEHOLDER_USERNAME