import os
import json
from app import db
from app.models import PushSubscription, User
from flask import current_app

try:
    from pywebpush import webpush, WebPushException
except ImportError:
    webpush = None

    class WebPushException(Exception):
        pass

def get_vapid_claims():
    return {
        'sub': 'mailto:auth@kiselgram.ru',
    }

def send_push_notification(user_id, title, body, url='/'):
    if webpush is None:
        current_app.logger.warning('pywebpush not installed – skipping push')
        return False
    subs = PushSubscription.query.filter_by(user_id=user_id).all()
    if not subs:
        return False
    private_key = current_app.config.get('VAPID_PRIVATE_KEY', '')
    public_key = current_app.config.get('VAPID_PUBLIC_KEY', '')
    if not private_key or not public_key:
        current_app.logger.warning('VAPID keys not configured – skipping push')
        return False
    payload = json.dumps({'title': title, 'body': body, 'url': url, 'tag': 'kiselgram'})
    removed = []
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth}
                },
                data=payload,
                vapid_private_key=private_key,
                vapid_claims=get_vapid_claims()
            )
        except WebPushException as ex:
            if ex.response and ex.response.status_code in (410, 404):
                removed.append(sub)
            else:
                current_app.logger.error(f'Push send error: {ex}')
        except Exception as ex:
            current_app.logger.error(f'Push send error: {ex}')
    for sub in removed:
        db.session.delete(sub)
    if removed:
        db.session.commit()
    return True
