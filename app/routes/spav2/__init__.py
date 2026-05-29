from flask import Blueprint

class Api2:
    def __init__(self, app=None,autoreg=True):
        self.spav2_bp = Blueprint("spav2_master", __name__, url_prefix="/api.v2")
        self.autoreg = autoreg
        if app is not None:
            self.app = app
            self.register(app)

    def init_app(self, app):
        self.app = app
        self.register(app)


    def register(self, app):
        from .auth import spav2_auth_bp
        from .chat import spav2_chat_bp
        from .groups import spav2_groups_bp
        from .channels import spav2_channels_bp
        from .contacts import spav2_contacts_bp
        from .stories import spav2_stories_bp
        from .profile import spav2_profile_bp
        from .calls import spav2_calls_bp
        from .search import spav2_search_bp
        from .sessions import spav2_sessions_bp
        from .messages import spav2_messages_bp
        from .saved import spav2_saved_bp
        from .music import spav2_music_bp
        from .ksettings import spav2_ksettings_bp

        # 1. Create a parent blueprint with the prefix
        spav2_bp=self.spav2_bp

        # 2. Nest your existing blueprints into the parent blueprint
        spav2_bp.register_blueprint(spav2_auth_bp)
        spav2_bp.register_blueprint(spav2_chat_bp)
        spav2_bp.register_blueprint(spav2_groups_bp)
        spav2_bp.register_blueprint(spav2_channels_bp)
        spav2_bp.register_blueprint(spav2_contacts_bp)
        spav2_bp.register_blueprint(spav2_stories_bp)
        spav2_bp.register_blueprint(spav2_profile_bp)
        spav2_bp.register_blueprint(spav2_calls_bp)
        spav2_bp.register_blueprint(spav2_search_bp)
        spav2_bp.register_blueprint(spav2_sessions_bp)
        spav2_bp.register_blueprint(spav2_messages_bp)
        spav2_bp.register_blueprint(spav2_saved_bp)
        spav2_bp.register_blueprint(spav2_music_bp)
        spav2_bp.register_blueprint(spav2_ksettings_bp)

        app.register_blueprint(self.spav2_bp)



