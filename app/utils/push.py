import json, logging
from pywebpush import webpush, WebPushException
from app import db
from app.models import PushSubscription, User

logger = logging.getLogger(__name__)

_VAPID_PRIVATE_KEY = None
_VAPID_PUBLIC_KEY = None

def init_vapid(app):
    global _VAPID_PRIVATE_KEY, _VAPID_PUBLIC_KEY
    _VAPID_PRIVATE_KEY = app.config.get('VAPID_PRIVATE_KEY', '')
    _VAPID_PUBLIC_KEY = app.config.get('VAPID_PUBLIC_KEY', '')
    if not _VAPID_PRIVATE_KEY or not _VAPID_PUBLIC_KEY:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from base64 import urlsafe_b64encode
        private_key = ec.generate_private_key(ec.SECP256R1())
        _VAPID_PRIVATE_KEY = urlsafe_b64encode(
            private_key.private_bytes(
                serialization.Encoding.DER,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()
            )
        ).decode().rstrip('=')
        _VAPID_PUBLIC_KEY = urlsafe_b64encode(
            private_key.public_key().public_bytes(
                serialization.Encoding.X962,
                serialization.PublicFormat.UncompressedPoint
            )
        ).decode().rstrip('=')
        app.config['VAPID_PRIVATE_KEY'] = _VAPID_PRIVATE_KEY
        app.config['VAPID_PUBLIC_KEY'] = _VAPID_PUBLIC_KEY

def get_vapid_claims():
    return {
        'sub': 'mailto:admin@kiselgram.ru',
    }

def send_push_to_user(user_id, title, body, url='/'):
    if not _VAPID_PRIVATE_KEY:
        logger.warning("VAPID not configured, skipping push")
        return
    subs = PushSubscription.query.filter_by(user_id=user_id).all()
    if not subs:
        return
    payload = json.dumps({'title': title, 'body': body, 'url': url, 'tag': 'kiselgram'})
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth}
                },
                data=payload,
                vapid_private_key=_VAPID_PRIVATE_KEY,
                vapid_claims=get_vapid_claims()
            )
        except WebPushException as e:
            if e.response and e.response.status_code in (404, 410):
                db.session.delete(sub)
                db.session.commit()
            else:
                logger.error(f"Push send error: {e}")
