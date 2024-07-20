from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Message
from .consumers import ChatConsumer
from channels.layers import get_channel_layer


@receiver(pre_save, sender=Message)
def handle_read_field_change(sender, instance, **kwargs):
    if instance.pk is None:
        # A pk is assigned to a model instance when it is saved to the database
        # Hence, the model instance must represent a new message if the pk is None in this pre save signal handler
        return

    # Send message read event if read field changes from False to True
    old_instance = sender.objects.get(pk=instance.pk)
    if not old_instance.read and instance.read:
        channel_layer = get_channel_layer()
        group_name = ChatConsumer.get_group_name(instance.sender.id, instance.recipient.id)
        ChatConsumer.send_message_read_event(channel_layer, group_name, instance)