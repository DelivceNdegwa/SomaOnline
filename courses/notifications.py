import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from courses import selectors


channel_layer = get_channel_layer()
logger = logging.getLogger(__name__)


def send_notification(video_id: int, message: str, success: bool):
    logger.info(f"-------NOTIFICATION={message}--------")
    video = selectors.get_specific_video({'id': video_id})
    video.processing_state = 'complete'
    video.save()

    async_to_sync(channel_layer.group_send)(
        'notifications',
        {
            'type': 'send_notification',
            'notification': message,
            'success': success
        }
    )