## All Endpoints — Full JSON Request/Response Contracts

---

### GET /api/chat_list

Response `200`:
```json
{
  "success": true,
  "data": {
    "chats": [
      {
        "chat_type": "personal",
        "peer": {
          "user_id": 42,
          "username": "alice",
          "avatar_url": "/media/avatars/alice.jpg",
          "is_online": true,
          "last_seen": "2026-05-26T14:25:00Z"
        },
        "last_message": {
          "message_id": 873,
          "content": "See you tomorrow!",
          "sender_id": 42,
          "timestamp": "2026-05-26T14:20:00Z",
          "is_read": false
        },
        "unread_count": 3
      },
      {
        "chat_type": "group",
        "group": {
          "group_id": 15,
          "name": "Work Team",
          "avatar_url": "/media/groups/work.jpg"
        },
        "last_message": {
          "message_id": 1201,
          "content": "Meeting at 3pm",
          "sender_id": 99,
          "sender_username": "bob",
          "timestamp": "2026-05-26T13:45:00Z"
        },
        "unread_count": 12
      },
      {
        "chat_type": "channel",
        "channel": {
          "channel_id": 7,
          "name": "News Updates",
          "avatar_url": "/media/channels/news.jpg"
        },
        "last_message": {
          "message_id": 5600,
          "content": "Breaking: major update released",
          "timestamp": "2026-05-26T14:10:00Z"
        },
        "unread_count": 0
      },
      {
        "chat_type": "saved",
        "label": "Saved Messages",
        "last_message": {
          "saved_id": 45,
          "content": "Meeting at 3pm",
          "saved_from": "Work Team",
          "timestamp": "2026-05-26T13:50:00Z"
        },
        "unread_count": 0
      }
    ]
  }
}
```

---

### GET /api/messages/<user_id>?after=<id>&limit=<n>

Response `200`:
```json
{
  "success": true,
  "data": {
    "peer": {
      "user_id": 42,
      "username": "alice",
      "avatar_url": "/media/avatars/alice.jpg",
      "is_online": true,
      "last_seen": "2026-05-26T14:25:00Z"
    },
    "messages": [
      {
        "message_id": 873,
        "sender_id": 42,
        "receiver_id": 1,
        "content": "See you tomorrow!",
        "reply_to_id": null,
        "file_path": null,
        "file_type": null,
        "is_read": true,
        "timestamp": "2026-05-26T14:20:00Z",
        "edited_at": null
      },
      {
        "message_id": 870,
        "sender_id": 1,
        "receiver_id": 42,
        "content": "Sounds good!",
        "reply_to_id": null,
        "file_path": null,
        "file_type": null,
        "is_read": true,
        "timestamp": "2026-05-26T14:19:00Z",
        "edited_at": "2026-05-26T14:19:30Z"
      }
    ],
    "pagination": {
      "after": null,
      "limit": 50,
      "has_more": false,
      "next_cursor": null
    }
  }
}
```

---

### GET /api/typing/<chat_type>/<chat_id>

Response `200`:
```json
{
  "success": true,
  "data": {
    "typing_users": [
      {
        "user_id": 42,
        "username": "alice",
        "started_at": "2026-05-26T14:30:05Z"
      }
    ]
  }
}
```

---

### GET /api/groups

Response `200`:
```json
{
  "success": true,
  "data": {
    "groups": [
      {
        "group_id": 15,
        "name": "Work Team",
        "description": "Daily standup and updates",
        "avatar_url": "/media/groups/work.jpg",
        "owner_id": 1,
        "is_public": false,
        "invite_link": "kiselgram.com/join/abc123",
        "member_count": 8,
        "my_role": "admin",
        "last_message": {
          "message_id": 1201,
          "content": "Meeting at 3pm",
          "sender_username": "bob",
          "timestamp": "2026-05-26T13:45:00Z"
        },
        "created_at": "2025-11-15T09:00:00Z"
      }
    ]
  }
}
```

---

### GET /api/groups/<id>

Response `200`:
```json
{
  "success": true,
  "data": {
    "group_id": 15,
    "name": "Work Team",
    "description": "Daily standup and updates",
    "avatar_url": "/media/groups/work.jpg",
    "owner_id": 1,
    "owner_username": "john_doe",
    "is_public": false,
    "invite_link": "kiselgram.com/join/abc123",
    "created_at": "2025-11-15T09:00:00Z",
    "member_count": 8,
    "members_url": "/api/groups/15/members"
  }
}
```

---

### GET /api/groups/<id>/members?offset=<n>&limit=<n>

Response `200`:
```json
{
  "success": true,
  "data": {
    "group_id": 15,
    "members": [
      {
        "user_id": 1,
        "username": "john_doe",
        "avatar_url": "/media/avatars/john.jpg",
        "role": "owner",
        "joined_at": "2025-11-15T09:00:00Z"
      },
      {
        "user_id": 42,
        "username": "alice",
        "avatar_url": "/media/avatars/alice.jpg",
        "role": "admin",
        "joined_at": "2025-11-16T10:30:00Z"
      }
    ],
    "pagination": {
      "offset": 0,
      "limit": 50,
      "has_more": false,
      "total": 8
    }
  }
}
```

---

### GET /api/group_messages/<id>?after=<id>&limit=<n>

Response `200`:
```json
{
  "success": true,
  "data": {
    "group_id": 15,
    "messages": [
      {
        "message_id": 1201,
        "sender_id": 99,
        "sender_username": "bob",
        "sender_avatar_url": "/media/avatars/bob.jpg",
        "content": "Meeting at 3pm",
        "reply_to_id": null,
        "file_path": null,
        "file_type": null,
        "timestamp": "2026-05-26T13:45:00Z",
        "edited_at": null
      }
    ],
    "pagination": {
      "after": 1201,
      "limit": 50,
      "has_more": true,
      "next_cursor": 1190
    }
  }
}
```

---

### GET /api/join_group/<invite_link>

Response `200`:
```json
{
  "success": true,
  "data": {
    "group": {
      "group_id": 20,
      "name": "Open Source Club",
      "description": "Contributing together",
      "avatar_url": "/media/groups/opensource.jpg",
      "owner_id": 55,
      "is_public": true,
      "member_count": 152,
      "my_role": "member",
      "joined_at": "2026-05-26T15:30:00Z"
    }
  }
}
```

---

### GET /api/channels/<id>

Response `200`:
```json
{
  "success": true,
  "data": {
    "channel_id": 7,
    "name": "News Updates",
    "description": "Official news and announcements",
    "avatar_url": "/media/channels/news.jpg",
    "owner_id": 1,
    "owner_username": "admin",
    "is_public": true,
    "invite_link": "kiselgram.com/channel/xyz789",
    "subscriber_count": 15420,
    "is_subscribed": true,
    "admins": [
      { "user_id": 1, "username": "admin" },
      { "user_id": 5, "username": "moderator_amy" }
    ],
    "created_at": "2025-06-01T12:00:00Z"
  }
}
```

---

### GET /api/channel_messages/<id>?after=<id>&limit=<n>

Response `200`:
```json
{
  "success": true,
  "data": {
    "channel_id": 7,
    "messages": [
      {
        "message_id": 5600,
        "sender_id": 1,
        "sender_username": "admin",
        "content": "Breaking: major update released",
        "reply_to_id": null,
        "file_path": null,
        "file_type": null,
        "timestamp": "2026-05-26T14:10:00Z",
        "edited_at": null
      }
    ],
    "pagination": {
      "after": 5600,
      "limit": 50,
      "has_more": true,
      "next_cursor": 5550
    }
  }
}
```

---

### GET /api/stories

Response `200`:
```json
{
  "success": true,
  "data": {
    "stories": [
      {
        "user_id": 42,
        "username": "alice",
        "avatar_url": "/media/avatars/alice.jpg",
        "stories": [
          {
            "story_id": 301,
            "media_path": "/media/stories/alice_story1.jpg",
            "media_type": "image",
            "caption": "Morning coffee ☕",
            "created_at": "2026-05-26T08:30:00Z",
            "expires_at": "2026-05-27T08:30:00Z",
            "is_viewed": false,
            "view_count": 12,
            "like_count": 3,
            "my_reaction": null
          },
          {
            "story_id": 302,
            "media_path": "/media/stories/alice_story2.mp4",
            "media_type": "video",
            "caption": "Workout time!",
            "created_at": "2026-05-26T07:15:00Z",
            "expires_at": "2026-05-27T07:15:00Z",
            "is_viewed": true,
            "view_count": 25,
            "like_count": 8,
            "my_reaction": "fire"
          }
        ]
      },
      {
        "user_id": 99,
        "username": "bob",
        "avatar_url": "/media/avatars/bob.jpg",
        "stories": [
          {
            "story_id": 310,
            "media_path": "/media/stories/bob_story1.jpg",
            "media_type": "image",
            "caption": "New project",
            "created_at": "2026-05-26T09:00:00Z",
            "expires_at": "2026-05-27T09:00:00Z",
            "is_viewed": false,
            "view_count": 5,
            "like_count": 1,
            "my_reaction": null
          }
        ]
      }
    ]
  }
}
```

---

### GET /api/stories/<id>/stats

Response `200`:
```json
{
  "success": true,
  "data": {
    "story_id": 301,
    "views": {
      "count": 12,
      "users": [
        { "user_id": 1, "username": "john_doe", "viewed_at": "2026-05-26T08:35:00Z" },
        { "user_id": 99, "username": "bob", "viewed_at": "2026-05-26T09:10:00Z" }
      ]
    },
    "likes": {
      "count": 3,
      "users": [
        { "user_id": 1, "username": "john_doe" },
        { "user_id": 5, "username": "moderator_amy" }
      ]
    },
    "reactions": [
      { "reaction": "heart", "count": 2, "users": ["john_doe", "moderator_amy"] },
      { "reaction": "fire", "count": 1, "users": ["bob"] }
    ]
  }
}
```

---

### GET /api/profile

Response `200`:
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "display_name": "John",
    "avatar_url": "/media/avatars/john.jpg",
    "bio": "Software developer | Coffee addict",
    "is_premium": true,
    "is_admin": false,
    "is_online": true,
    "last_seen": "2026-05-26T14:30:00Z",
    "created_at": "2025-01-10T08:00:00Z"
  }
}
```

---

### GET /api/profile/settings

Response `200`:
```json
{
  "success": true,
  "data": {
    "theme": "dark",
    "font_size": "medium",
    "colors": {
      "primary": "#4A90D9",
      "accent": "#F5A623",
      "background": "#1E1E2E",
      "chat_bubble_self": "#4A90D9",
      "chat_bubble_other": "#2E2E3E"
    }
  }
}
```

---

### GET /api/profile/privacy

Response `200`:
```json
{
  "success": true,
  "data": {
    "last_seen": "contacts_only",
    "profile_photo": "everyone",
    "calls": "contacts_only",
    "messages": "everyone"
  }
}
```

---

### GET /api/contacts

Response `200`:
```json
{
  "success": true,
  "data": {
    "contacts": [
      {
        "user_id": 42,
        "username": "alice",
        "display_name": "Alice W.",
        "avatar_url": "/media/avatars/alice.jpg",
        "custom_name": "Ally",
        "is_online": true,
        "last_seen": "2026-05-26T14:25:00Z",
        "added_at": "2025-03-15T10:00:00Z"
      },
      {
        "user_id": 99,
        "username": "bob",
        "display_name": "Bob",
        "avatar_url": "/media/avatars/bob.jpg",
        "custom_name": null,
        "is_online": false,
        "last_seen": "2026-05-26T12:00:00Z",
        "added_at": "2025-06-20T14:30:00Z"
      }
    ],
    "total": 2
  }
}
```

---

### GET /api/blocked_users

Response `200`:
```json
{
  "success": true,
  "data": {
    "blocked_users": [
      {
        "user_id": 200,
        "username": "spammer123",
        "avatar_url": "/media/avatars/default.jpg",
        "blocked_at": "2026-05-10T11:00:00Z"
      }
    ],
    "total": 1
  }
}
```

---

### GET /api/search/global?q=<query>

Response `200`:
```json
{
  "success": true,
  "data": {
    "query": "alice",
    "results": {
      "users": [
        {
          "user_id": 42,
          "username": "alice",
          "display_name": "Alice W.",
          "avatar_url": "/media/avatars/alice.jpg",
          "is_contact": true
        },
        {
          "user_id": 77,
          "username": "alice_dev",
          "display_name": "Alice Developer",
          "avatar_url": "/media/avatars/alice_dev.jpg",
          "is_contact": false
        }
      ],
      "groups": [
        {
          "group_id": 22,
          "name": "Alice Fans",
          "avatar_url": "/media/groups/alice_fans.jpg",
          "member_count": 150,
          "is_member": false
        }
      ],
      "channels": []
    }
  }
}
```

---

### GET /api/users?search=<query>

Response `200`:
```json
{
  "success": true,
  "data": {
    "query": "alice",
    "users": [
      {
        "user_id": 42,
        "username": "alice",
        "display_name": "Alice W.",
        "avatar_url": "/media/avatars/alice.jpg",
        "bio": "Designer & coffee lover",
        "is_online": true,
        "is_contact": true
      },
      {
        "user_id": 77,
        "username": "alice_dev",
        "display_name": "Alice Developer",
        "avatar_url": "/media/avatars/alice_dev.jpg",
        "bio": "Full-stack engineer",
        "is_online": false,
        "is_contact": false
      }
    ],
    "total": 2
  }
}
```

---

### GET /api/recent_searches

Response `200`:
```json
{
  "success": true,
  "data": {
    "searches": [
      {
        "search_id": 10,
        "query": "alice",
        "created_at": "2026-05-26T14:00:00Z"
      },
      {
        "search_id": 9,
        "query": "work team",
        "created_at": "2026-05-26T10:30:00Z"
      }
    ]
  }
}
```

---

### GET /api/reactions/<message_id>

Response `200`:
```json
{
  "success": true,
  "data": {
    "message_id": 873,
    "reactions": [
      {
        "reaction_type": "heart",
        "count": 3,
        "users": [
          { "user_id": 1, "username": "john_doe" },
          { "user_id": 42, "username": "alice" }
        ],
        "has_reacted": true
      },
      {
        "reaction_type": "laugh",
        "count": 1,
        "users": [
          { "user_id": 99, "username": "bob" }
        ],
        "has_reacted": false
      }
    ]
  }
}
```

---

### GET /api/saved_messages?after=<id>&limit=<n>

Response `200`:
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "saved_id": 45,
        "original_message": {
          "message_id": 873,
          "sender_id": 42,
          "sender_username": "alice",
          "content": "See you tomorrow!",
          "chat_type": "personal",
          "chat_name": "alice",
          "timestamp": "2026-05-26T14:20:00Z"
        },
        "saved_at": "2026-05-26T14:21:00Z",
        "note": null
      },
      {
        "saved_id": 44,
        "original_message": {
          "message_id": 1201,
          "sender_id": 99,
          "sender_username": "bob",
          "content": "Meeting at 3pm",
          "chat_type": "group",
          "chat_name": "Work Team",
          "timestamp": "2026-05-26T13:45:00Z"
        },
        "saved_at": "2026-05-26T13:50:00Z",
        "note": "Important reminder"
      }
    ],
    "pagination": {
      "after": 44,
      "limit": 50,
      "has_more": false,
      "next_cursor": null
    }
  }
}
```

---

### GET /api/calls/history

Response `200`:
```json
{
  "success": true,
  "data": {
    "calls": [
      {
        "call_id": 55,
        "call_type": "video",
        "peer": {
          "user_id": 42,
          "username": "alice",
          "avatar_url": "/media/avatars/alice.jpg"
        },
        "direction": "outgoing",
        "status": "ended",
        "duration_seconds": 320,
        "started_at": "2026-05-26T12:00:00Z",
        "ended_at": "2026-05-26T12:05:20Z"
      },
      {
        "call_id": 52,
        "call_type": "voice",
        "peer": {
          "user_id": 99,
          "username": "bob",
          "avatar_url": "/media/avatars/bob.jpg"
        },
        "direction": "incoming",
        "status": "missed",
        "duration_seconds": 0,
        "started_at": "2026-05-25T16:30:00Z",
        "ended_at": null
      }
    ]
  }
}
```

---

### GET /api/sessions

Response `200`:
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "session_token": "abc123def456",
        "device": "Chrome on Windows",
        "ip_address": "192.168.1.1",
        "location": "New York, US",
        "is_current": true,
        "last_active": "2026-05-26T14:30:00Z",
        "created_at": "2026-05-20T08:00:00Z"
      },
      {
        "session_token": "xyz789ghi012",
        "device": "Kiselgram iOS",
        "ip_address": "10.0.0.1",
        "location": "London, UK",
        "is_current": false,
        "last_active": "2026-05-25T22:00:00Z",
        "created_at": "2026-05-15T14:00:00Z"
      }
    ]
  }
}
```

---

### GET /api/check_username?username=<username>

Response `200`:
```json
{
  "success": true,
  "data": {
    "username": "alice",
    "available": false
  }
}
```

---

### POST /api/auth/login

Request:
```json
{
  "username": "john_doe",
  "password": "securepass123"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "display_name": "John",
      "avatar_url": "/media/avatars/john.jpg",
      "bio": "Software developer | Coffee addict",
      "is_premium": true,
      "is_admin": false,
      "is_online": true,
      "last_seen": "2026-05-26T14:30:00Z",
      "created_at": "2025-01-10T08:00:00Z"
    },
    "session_token": "abc123def456"
  }
}
```

Response `401`:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid username or password"
  }
}
```

---

### POST /api/auth/register

Request:
```json
{
  "username": "new_user",
  "email": "new@example.com",
  "password": "securepass123"
}
```

Response `201`:
```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": 500,
      "username": "new_user",
      "email": "new@example.com",
      "display_name": "new_user",
      "avatar_url": null,
      "bio": null,
      "is_premium": false,
      "is_admin": false,
      "is_online": true,
      "last_seen": "2026-05-26T14:30:00Z",
      "created_at": "2026-05-26T14:30:00Z"
    },
    "session_token": "new_session_xyz789"
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "fields": {
      "username": "Username already taken",
      "email": "Invalid email format",
      "password": "Password must be at least 8 characters"
    }
  }
}
```

---

### POST /api/auth/logout

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "message": "Logged out successfully"
  }
}
```

---

### POST /api/send_message

Request:
```json
{
  "receiver_id": 42,
  "content": "Hey, how are you?",
  "reply_to_id": null,
  "file_path": null
}
```

Response `201`:
```json
{
  "success": true,
  "data": {
    "message": {
      "message_id": 875,
      "sender_id": 1,
      "receiver_id": 42,
      "content": "Hey, how are you?",
      "reply_to_id": null,
      "file_path": null,
      "file_type": null,
      "is_read": false,
      "timestamp": "2026-05-26T14:31:00Z",
      "edited_at": null
    }
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "fields": {
      "receiver_id": "Receiver ID is required",
      "content": "Message content cannot be empty"
    }
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "USER_BLOCKED",
    "message": "You cannot send messages to this user"
  }
}
```

---

### POST /api/mark_read/<user_id>

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "marked_count": 3,
    "peer_user_id": 42
  }
}
```

---

### POST /api/messages/<message_id>/edit

Request:
```json
{
  "content": "Hey, how are you? *edited*"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "message": {
      "message_id": 875,
      "sender_id": 1,
      "receiver_id": 42,
      "content": "Hey, how are you? *edited*",
      "reply_to_id": null,
      "file_path": null,
      "file_type": null,
      "is_read": false,
      "timestamp": "2026-05-26T14:31:00Z",
      "edited_at": "2026-05-26T14:35:00Z"
    }
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You can only edit your own messages"
  }
}
```

---

### POST /api/typing/<chat_type>/<chat_id>

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "chat_type": "personal",
    "chat_id": "42",
    "is_typing": true,
    "expires_at": "2026-05-26T14:31:10Z"
  }
}
```

---

### POST /api/groups/create

Request:
```json
{
  "name": "Work Team",
  "description": "Daily standup and updates",
  "member_ids": [42, 99, 105]
}
```

Response `201`:
```json
{
  "success": true,
  "data": {
    "group": {
      "group_id": 16,
      "name": "Work Team",
      "description": "Daily standup and updates",
      "avatar_url": null,
      "owner_id": 1,
      "is_public": false,
      "invite_link": "kiselgram.com/join/def456",
      "member_count": 4,
      "created_at": "2026-05-26T14:32:00Z"
    }
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "fields": {
      "name": "Group name is required",
      "member_ids": "At least one member is required"
    }
  }
}
```

---

### POST /api/send_group_message

Request:
```json
{
  "group_id": 15,
  "content": "Meeting at 3pm everyone",
  "reply_to_id": null
}
```

Response `201`:
```json
{
  "success": true,
  "data": {
    "message": {
      "message_id": 1202,
      "sender_id": 1,
      "sender_username": "john_doe",
      "sender_avatar_url": "/media/avatars/john.jpg",
      "group_id": 15,
      "content": "Meeting at 3pm everyone",
      "reply_to_id": null,
      "file_path": null,
      "file_type": null,
      "timestamp": "2026-05-26T14:33:00Z",
      "edited_at": null
    }
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "NOT_MEMBER",
    "message": "You are not a member of this group"
  }
}
```

---

### POST /api/groups/<id>/update

Request:
```json
{
  "name": "Work Team Updated",
  "description": "Updated description"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "group": {
      "group_id": 15,
      "name": "Work Team Updated",
      "description": "Updated description",
      "avatar_url": "/media/groups/work.jpg",
      "owner_id": 1,
      "is_public": false,
      "invite_link": "kiselgram.com/join/abc123",
      "member_count": 8,
      "created_at": "2025-11-15T09:00:00Z"
    }
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Only owners and admins can update the group"
  }
}
```

---

### POST /api/groups/<id>/members/<user_id>/role

Request:
```json
{
  "role": "admin"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "group_id": 15,
    "user_id": 99,
    "username": "bob",
    "role": "admin",
    "updated_at": "2026-05-26T14:34:00Z"
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Role must be one of: admin, member"
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Only the owner can change member roles"
  }
}
```

---

### POST /api/leave_group/<id>

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "message": "Successfully left the group",
    "group_id": 15
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "OWNER_CANNOT_LEAVE",
    "message": "Owner cannot leave the group. Transfer ownership or delete the group."
  }
}
```

---

### POST /api/channels/create

Request:
```json
{
  "name": "Tech News",
  "description": "Latest technology updates"
}
```

Response `201`:
```json
{
  "success": true,
  "data": {
    "channel": {
      "channel_id": 10,
      "name": "Tech News",
      "description": "Latest technology updates",
      "avatar_url": null,
      "owner_id": 1,
      "is_public": true,
      "invite_link": "kiselgram.com/channel/abc999",
      "subscriber_count": 1,
      "created_at": "2026-05-26T14:35:00Z"
    }
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "fields": {
      "name": "Channel name is required"
    }
  }
}
```

---

### POST /api/send_channel_message

Request:
```json
{
  "channel_id": 7,
  "content": "New feature released today!"
}
```

Response `201`:
```json
{
  "success": true,
  "data": {
    "message": {
      "message_id": 5601,
      "sender_id": 1,
      "sender_username": "admin",
      "channel_id": 7,
      "content": "New feature released today!",
      "reply_to_id": null,
      "file_path": null,
      "file_type": null,
      "timestamp": "2026-05-26T14:36:00Z",
      "edited_at": null
    }
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Only admins can post to this channel"
  }
}
```

---

### POST /api/channels/<id>/subscribe

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "channel_id": 7,
    "is_subscribed": true,
    "subscriber_count": 15421,
    "subscribed_at": "2026-05-26T14:37:00Z"
  }
}
```

---

### POST /api/channels/<id>/unsubscribe

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "channel_id": 7,
    "is_subscribed": false,
    "subscriber_count": 15420
  }
}
```

---

### POST /api/channels/<id>/update

Request:
```json
{
  "name": "Tech News Updated",
  "description": "Updated channel description"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "channel": {
      "channel_id": 7,
      "name": "Tech News Updated",
      "description": "Updated channel description",
      "avatar_url": "/media/channels/news.jpg",
      "owner_id": 1,
      "is_public": true,
      "invite_link": "kiselgram.com/channel/xyz789",
      "subscriber_count": 15420,
      "created_at": "2025-06-01T12:00:00Z"
    }
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Only owners and admins can update the channel"
  }
}
```

---

### POST /api/channels/<id>/admins

Request:
```json
{
  "user_id": 99
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "channel_id": 7,
    "user_id": 99,
    "username": "bob",
    "role": "admin",
    "added_at": "2026-05-26T14:38:00Z"
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "ALREADY_ADMIN",
    "message": "User is already an admin of this channel"
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Only the owner can add admins"
  }
}
```

---

### POST /api/stories/create

Request: *(multipart)*
```
media: <file>
caption: "Morning coffee ☕"
privacy: "contacts_only"
```

Response `201`:
```json
{
  "success": true,
  "data": {
    "story": {
      "story_id": 305,
      "user_id": 1,
      "media_path": "/media/stories/john_story_305.jpg",
      "media_type": "image",
      "caption": "Morning coffee ☕",
      "privacy": "contacts_only",
      "created_at": "2026-05-26T14:39:00Z",
      "expires_at": "2026-05-27T14:39:00Z"
    }
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Media file is required"
  }
}
```

---

### POST /api/stories/<id>/view

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "story_id": 305,
    "viewed": true,
    "viewed_at": "2026-05-26T14:40:00Z"
  }
}
```

---

### POST /api/stories/<id>/like

Request: *(none)*

Response `200` *(liked)*:
```json
{
  "success": true,
  "data": {
    "story_id": 305,
    "liked": true,
    "like_count": 5
  }
}
```

Response `200` *(unliked)*:
```json
{
  "success": true,
  "data": {
    "story_id": 305,
    "liked": false,
    "like_count": 4
  }
}
```

---

### POST /api/stories/<id>/reaction

Request:
```json
{
  "reaction": "fire"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "story_id": 305,
    "reaction": "fire",
    "reaction_count": 3
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Reaction must be one of: heart, fire, laugh, wow, sad, angry"
  }
}
```

---

### POST /api/stories/<id>/reply

Request:
```json
{
  "reply_text": "Looks great!"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "message": {
      "message_id": 876,
      "sender_id": 1,
      "receiver_id": 42,
      "content": "Looks great!",
      "reply_to_story_id": 305,
      "timestamp": "2026-05-26T14:41:00Z"
    }
  }
}
```

---

### POST /api/profile/avatar

Request: *(multipart)*
```
avatar: <file>
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "avatar_url": "/media/avatars/john_new.jpg",
    "updated_at": "2026-05-26T14:42:00Z"
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Avatar must be a JPEG or PNG under 5MB"
  }
}
```

---

### POST /api/contacts

Request:
```json
{
  "contact_id": 42
}
```

Response `201`:
```json
{
  "success": true,
  "data": {
    "contact": {
      "user_id": 42,
      "username": "alice",
      "display_name": "Alice W.",
      "avatar_url": "/media/avatars/alice.jpg",
      "custom_name": null,
      "added_at": "2026-05-26T14:43:00Z"
    }
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "ALREADY_CONTACT",
    "message": "User is already in your contacts"
  }
}
```

---

### POST /api/contacts/rename

Request:
```json
{
  "contact_id": 42,
  "name": "Ally"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "user_id": 42,
    "custom_name": "Ally",
    "updated_at": "2026-05-26T14:44:00Z"
  }
}
```

---

### POST /api/block_user/<id>

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "blocked_user_id": 200,
    "username": "spammer123",
    "blocked_at": "2026-05-26T14:45:00Z"
  }
}
```

---

### POST /api/unblock_user/<id>

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "unblocked_user_id": 200,
    "username": "spammer123"
  }
}
```

---

### POST /api/search_in_chat

Request:
```json
{
  "chat_id": "42",
  "query": "meeting"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "chat_id": "42",
    "chat_type": "personal",
    "query": "meeting",
    "results": [
      {
        "message_id": 850,
        "sender_id": 42,
        "content": "Let's have a meeting tomorrow",
        "timestamp": "2026-05-25T10:00:00Z"
      },
      {
        "message_id": 830,
        "sender_id": 1,
        "content": "Meeting was productive",
        "timestamp": "2026-05-24T15:30:00Z"
      }
    ],
    "total": 2
  }
}
```

---

### POST /api/reactions/add

Request:
```json
{
  "message_id": 873,
  "reaction_type": "heart"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "message_id": 873,
    "reaction_type": "heart",
    "has_reacted": true,
    "reaction_count": 4
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Reaction type must be one of: heart, laugh, thumbs_up, thumbs_down, fire, crying"
  }
}
```

---

### POST /api/saved_messages

Request:
```json
{
  "message_id": 873,
  "note": "Important reminder"
}
```

Response `201`:
```json
{
  "success": true,
  "data": {
    "saved_id": 46,
    "original_message": {
      "message_id": 873,
      "sender_id": 42,
      "sender_username": "alice",
      "content": "See you tomorrow!",
      "chat_type": "personal",
      "chat_name": "alice",
      "timestamp": "2026-05-26T14:20:00Z"
    },
    "saved_at": "2026-05-26T14:50:00Z",
    "note": "Important reminder"
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "ALREADY_SAVED",
    "message": "Message already saved"
  }
}
```

---

### POST /api/saved_messages/<saved_id>/note

Request:
```json
{
  "note": "Updated reminder text"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "saved_id": 46,
    "note": "Updated reminder text",
    "updated_at": "2026-05-26T14:55:00Z"
  }
}
```

---

### POST /api/calls/make

Request:
```json
{
  "receiver_id": 42,
  "call_type": "video"
}
```

Response `201`:
```json
{
  "success": true,
  "data": {
    "call": {
      "call_id": 56,
      "call_type": "video",
      "caller_id": 1,
      "receiver_id": 42,
      "status": "ringing",
      "room_token": "room_abc123xyz",
      "started_at": "2026-05-26T14:47:00Z"
    }
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Call type must be voice or video"
  }
}
```

---

### POST /api/calls/answer

Request:
```json
{
  "call_id": 56
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "call": {
      "call_id": 56,
      "status": "active",
      "room_token": "room_abc123xyz",
      "answered_at": "2026-05-26T14:47:05Z"
    }
  }
}
```

Response `404`:
```json
{
  "success": false,
  "error": {
    "code": "CALL_NOT_FOUND",
    "message": "Call not found or already ended"
  }
}
```

---

### POST /api/calls/end

Request:
```json
{
  "call_id": 56,
  "duration": 320
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "call": {
      "call_id": 56,
      "status": "ended",
      "duration_seconds": 320,
      "ended_at": "2026-05-26T14:52:20Z"
    }
  }
}
```

---

### POST /api/video/create_room

Request:
```json
{
  "call_type": "video"
}
```

Response `201`:
```json
{
  "success": true,
  "data": {
    "room_token": "room_xyz789abc",
    "call_type": "video",
    "created_at": "2026-05-26T14:47:00Z",
    "expires_at": "2026-05-26T15:47:00Z"
  }
}
```

---

### POST /api/sessions/terminate

Request:
```json
{
  "session_token": "xyz789ghi012"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "message": "Session terminated successfully",
    "session_token": "xyz789ghi012"
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "CANNOT_TERMINATE_CURRENT",
    "message": "Cannot terminate your current session"
  }
}
```

---

### POST /api/sessions/terminate_all

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "message": "All other sessions terminated",
    "terminated_count": 2
  }
}
```

---

### POST /api/update_last_seen

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "last_seen": "2026-05-26T14:48:00Z",
    "is_online": true
  }
}
```

---

### PUT /api/profile/update

Request:
```json
{
  "display_name": "John D.",
  "username": "john_doe",
  "bio": "Senior dev | Open source contributor"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "display_name": "John D.",
      "avatar_url": "/media/avatars/john.jpg",
      "bio": "Senior dev | Open source contributor",
      "is_premium": true,
      "is_admin": false,
      "is_online": true,
      "last_seen": "2026-05-26T15:00:00Z",
      "created_at": "2025-01-10T08:00:00Z"
    }
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "fields": {
      "username": "Username already taken",
      "display_name": "Display name must be between 1 and 50 characters",
      "bio": "Bio must be under 500 characters"
    }
  }
}
```

---

### PUT /api/profile/settings

Request:
```json
{
  "theme": "light",
  "font_size": "large",
  "colors": {
    "primary": "#2E86AB",
    "accent": "#A23B72",
    "background": "#FFFFFF",
    "chat_bubble_self": "#2E86AB",
    "chat_bubble_other": "#F0F0F0"
  }
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "theme": "light",
    "font_size": "large",
    "colors": {
      "primary": "#2E86AB",
      "accent": "#A23B72",
      "background": "#FFFFFF",
      "chat_bubble_self": "#2E86AB",
      "chat_bubble_other": "#F0F0F0"
    },
    "updated_at": "2026-05-26T15:01:00Z"
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "fields": {
      "theme": "Theme must be light, dark, or system",
      "font_size": "Font size must be small, medium, or large"
    }
  }
}
```

---

### PUT /api/profile/privacy

Request:
```json
{
  "last_seen": "nobody",
  "profile_photo": "contacts_only",
  "calls": "contacts_only",
  "messages": "everyone"
}
```

Response `200`:
```json
{
  "success": true,
  "data": {
    "last_seen": "nobody",
    "profile_photo": "contacts_only",
    "calls": "contacts_only",
    "messages": "everyone",
    "updated_at": "2026-05-26T15:02:00Z"
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Each privacy setting must be one of: everyone, contacts_only, nobody"
  }
}
```

---

### DELETE /api/messages/<message_id>

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "message_id": 875,
    "deleted": true,
    "deleted_at": "2026-05-26T15:10:00Z"
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You can only delete your own messages"
  }
}
```

Response `404`:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Message not found or already deleted"
  }
}
```

---

### DELETE /api/groups/<id>

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "group_id": 15,
    "group_name": "Work Team",
    "deleted": true,
    "deleted_at": "2026-05-26T15:20:00Z"
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Only the owner can delete the group"
  }
}
```

Response `404`:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Group not found"
  }
}
```

---

### DELETE /api/groups/<id>/members/<user_id>

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "group_id": 15,
    "removed_user": {
      "user_id": 99,
      "username": "bob"
    },
    "removed_by": {
      "user_id": 1,
      "username": "john_doe"
    },
    "removed_at": "2026-05-26T15:11:00Z",
    "member_count": 7
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Only owners and admins can remove members"
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "CANNOT_REMOVE_OWNER",
    "message": "Cannot remove the group owner"
  }
}
```

Response `404`:
```json
{
  "success": false,
  "error": {
    "code": "NOT_MEMBER",
    "message": "User is not a member of this group"
  }
}
```

---

### DELETE /api/channels/<id>

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "channel_id": 7,
    "channel_name": "Tech News",
    "deleted": true,
    "deleted_at": "2026-05-26T15:21:00Z"
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Only the owner can delete the channel"
  }
}
```

Response `404`:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Channel not found"
  }
}
```

---

### DELETE /api/channels/<id>/admins/<user_id>

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "channel_id": 7,
    "removed_admin": {
      "user_id": 99,
      "username": "bob"
    },
    "removed_by": {
      "user_id": 1,
      "username": "admin"
    },
    "removed_at": "2026-05-26T15:12:00Z",
    "admin_count": 1
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Only the owner can remove admins"
  }
}
```

Response `400`:
```json
{
  "success": false,
  "error": {
    "code": "CANNOT_REMOVE_OWNER",
    "message": "Cannot remove the channel owner as admin"
  }
}
```

Response `404`:
```json
{
  "success": false,
  "error": {
    "code": "NOT_ADMIN",
    "message": "User is not an admin of this channel"
  }
}
```

---

### DELETE /api/stories/<id>

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "story_id": 305,
    "deleted": true,
    "deleted_at": "2026-05-26T15:13:00Z"
  }
}
```

Response `403`:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You can only delete your own stories"
  }
}
```

Response `404`:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Story not found or already expired"
  }
}
```

---

### DELETE /api/saved_messages/<saved_id>

Request: *(none)*

Response `200`:
```json
{
  "success": true,
  "data": {
    "message": "Saved message removed",
    "saved_id": 46
  }
}
```

Response `404`:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Saved message not found"
  }
}
```