from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver, Signal

from .models import User


new_order = Signal()

@receiver(new_order)
def send_new_order_email(sender, user_id, **kwargs):
    """
    Отправить письмо при изменении статуса заказа
    """
    user = User.objects.get(id=user_id)

    subject = "Обновление статуса заказа"
    message = f"Ваш заказ №{kwargs.get('order_id')} сформирован"
    from_email = settings.EMAIL_HOST_USER
    to_email = [user.email]

    msg = EmailMultiAlternatives(subject, message, from_email, to_email)
    msg.send()
