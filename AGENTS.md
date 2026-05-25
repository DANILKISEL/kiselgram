# Kiselgram Development Guide

## Essential Commands

**Start Services (Python Version):**
- `python manage.py start` - Start main app (port 5000) + video server (port 5001)
- `python manage.py start --port 3000` - Custom port for main app
- `python manage.py start --no-video` - Main app only
- `python manage.py video start` - Video server only

**Build & Run (Java Version):**
- `./gradlew bootRun` - Start the Java application
- `./gradlew clean bootJar` - Build executable JAR
- `java -jar build/libs/kiselgram-0.0.1-SNAPSHOT.jar` - Run the built JAR
- `./gradlew test` - Run tests

**Database & Maintenance (Python Version):**
- `python manage.py setup` - Initial setup (run first)
- `python manage.py reset-db` - Delete all data (use with caution)
- `python manage.py clean` - Clear temp files
- `python manage.py test` - Run tests

**Service Management (Python Version):**
- `python manage.py stop` - Graceful shutdown
- `python manage.py status` - Check service status
- `python manage.py restart` - Restart services

## Project Structure

**Core Directories (Python Version):**
- `app/` - Main Flask application
  - `models.py` - SQLAlchemy database models
  - `routes/` - Feature blueprints (chats, groups, video_integration, api)
  - `templates/` - HTML templates
  - `uploads/` - User uploaded files
- `video_server/` - WebRTC signaling server
  - `app.py` - SocketIO + WebRTC signaling
  - `templates/video/` - Video room UIs
  - `static/js/` - WebRTC client logic
- `instance/` - SQLite database (`kiselgram.db`)
- `logs/` - Application logs

**Core Directories (Java Version):**
- `src/main/java/com/kiselgram/kiselgram/` - Main application code
  - `KiselgramApplication.java` - Spring Boot entry point
  - `config/` - Security and application configuration
  - `controller/` - REST API endpoints
  - `dto/` - Data Transfer Objects for API responses
  - `model/` - JPA entities/database models
  - `repository/` - Spring Data JPA repositories
  - `service/` - Business logic services
  - `util/` - Utility classes (file handling, media processing)
- `src/main/resources/` - Configuration and static resources
  - `application.properties` - Database, file upload, and JWT settings
  - `templates/` - Thymeleaf HTML templates (for future SSR)

## Key Integration Points

**Video Chat Flow:**
1. Chat → Video Icon → POST `/video/create-room`
2. Redirect → `http://localhost:5001/video/join/{room_id}`
3. WebRTC → `getUserMedia()` → SocketIO signaling → P2P streams
4. UI → `video_server/templates/video/room.html`

**File Uploads:**
- Storage: `app/uploads/` and `uploads/` directories
- Max size: 16MB for all file types
- Types: Images (png,jpg,gif,webp), Documents (pdf,docx,txt), Video (mp4,webm,mov), Audio (mp3,wav,m4a)

## Development Notes

**Environment (Python Version):**
- Python 3.10+ required
- Virtual environment recommended (`.venv`)
- Environment variables managed via `manage.py setup`

**Environment (Java Version):**
- Java 17+ required
- Application properties in src/main/resources/application.properties
- JWT secret and expiration configurable
- File upload directory configurable

**Testing (Python Version):**
- Run tests with `python manage.py test` (basic dependency check only)
- Run pytest with `.venv/bin/python -m pytest tests/ -v` (comprehensive)
- Run specific file: `.venv/bin/python -m pytest tests/test_models.py -v`
- Run specific test: `.venv/bin/python -m pytest tests/test_models.py::TestUserModel::test_create_user -v`
- Test coverage includes: all 32 models, auth flows (register/login/logout/verify), groups CRUD, channels CRUD, messaging (send/receive/reactions/search), stories (create/view/like/reply), contacts (add/rename/block), calls (make/answer/end), video rooms (create/join/end), profile (get/update/avatar/settings/privacy), global search, pinned chats, favorites, sessions, premium behavior

**Testing (Java Version):**
- Run tests with ./gradlew test
- Currently minimal test coverage (add more)

**Code Organization (Python Version):**
- Feature routes in `app/routes/` as blueprints
- Database models in `app/models.py`
- Video integration in `app/routes/video_integration.py`
- Template inheritance in `app/templates/`

**Code Organization (Java Version):**
- REST controllers in src/main/java/com/kiselgram/kiselgram/controller/
- JPA entities in src/main/java/com/kiselgram/kiselgram/model/
- Spring Data repositories in src/main/java/com/kiselgram/kiselgram/repository/
- Business services in src/main/java/com/kiselgram/kiselgram/service/
- Utility classes in src/main/java/com/kiselgram/kiselgram/util/

## Common Tasks

**View Nexgram app**
1. CD into ~/Downloads/nexgram-main
2. Here you are in the app

**View Sputnk app**
1. CD into ~/Downloads/sputnik-main
2. Here you are in the app


**Adding New Features (Python Version):**
1. Create/update models in `app/models.py` if needed
2. Add routes in appropriate file under `app/routes/`
3. Create templates in `app/templates/` or extend existing ones
4. Update navigation in base templates if needed
5. Test with `python manage.py test`

**Adding New Features (Java Version):**
1. Create/update JPA entities in model/ if needed
2. Create/update repository interfaces in repository/
3. Implement business logic in service/ layer
4. Create REST endpoints in controller/ layer
5. Add DTOs in dto/ for API responses if needed
6. Test with ./gradlew test

**Authentication (Java Version):**
- JWT tokens generated in AuthController.login()
- Token validation handled by JwtAuthenticationFilter
- User details loaded by UserDetailsServiceImpl
- Passwords encoded with BCrypt via AuthService

**File Handling (Java Version):**
- Uploads processed in MessageController.upload()
- Files stored using FileUtil.saveFile()
- Thumbnails created using MediaUtil.createThumbnail()
- File type detection via MediaUtil.getFileType()

**Video Features:**
1. Signaling logic in `video_server/app.py`
2. UI templates in `video_server/templates/video/`
3. Client logic in `video_server/static/js/`
4. Integration points in `app/routes/video_integration.py`