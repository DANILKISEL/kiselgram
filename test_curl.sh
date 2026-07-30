#!/bin/bash
BASE="http://127.0.0.1:8080"
AUTH="http://127.0.0.1:8081"
OK=0
FAIL=0

r() {
  local method=$1 url=$2 body=$3
  local opts="-s"
  if [ "$body" ]; then opts="$opts -H 'Content-Type: application/json' -d '$body'"; fi
  local resp=$(curl -s -X "$method" $opts "$url" 2>/dev/null)
  local status=$?
  if [ $status -ne 0 ]; then
    echo "  NET_ERR $method $url -> curl exit $status"
    FAIL=$((FAIL+1))
  else
    local firstline=$(echo "$resp" | head -c 120)
    echo "  OK $method $url -> $firstline"
    OK=$((OK+1))
  fi
  echo "$resp"
}

ar() {
  local method=$1 url=$2 body=$3
  local opts="-s -H 'Authorization: Bearer $TOKEN'"
  if [ "$body" ]; then opts="$opts -H 'Content-Type: application/json' -d '$body'"; fi
  local resp=$(curl -s -X "$method" $opts "$url" 2>/dev/null)
  local status=$?
  if [ $status -ne 0 ]; then
    echo "  NET_ERR $method $url -> curl exit $status"
    FAIL=$((FAIL+1))
  else
    local firstline=$(echo "$resp" | head -c 120)
    echo "  OK $method $url -> $firstline"
    OK=$((OK+1))
  fi
  echo "$resp"
}

echo "--- Health ---"
r "GET" "$BASE/health"

echo "--- Register ---"
REG=$(r "POST" "$AUTH/api/register" '{"username":"testplay","password":"test123","confirm_password":"test123"}')
TOKEN=$(echo "$REG" | grep -o '"token":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -z "$TOKEN" ]; then
  echo "  Login existing..."
  REG=$(r "POST" "$AUTH/api/login" '{"username":"testplay","password":"test123"}')
  TOKEN=$(echo "$REG" | grep -o '"token":"[^"]*"' | head -1 | cut -d'"' -f4)
fi
echo "  Token: ${TOKEN:0:30}..."

echo "--- Profile ---"
ar "GET" "$BASE/api/profile"
ar "PUT" "$BASE/api/profile" '{"first_name":"Test","last_name":"Play","bio":"Testing!"}'
ar "GET" "$BASE/api/profile/settings"
ar "PUT" "$BASE/api/profile/settings" '{"theme":"dark"}'
ar "PUT" "$BASE/api/profile/privacy" '{"show_status":false}'
ar "PUT" "$BASE/api/profile/notifications" '{"messages":true}'

echo "--- Sessions ---"
ar "GET" "$BASE/api/sessions"

echo "--- Contacts ---"
ar "GET" "$BASE/api/contacts"
ar "GET" "$BASE/api/blocked_users"

echo "--- Premium ---"
ar "GET" "$BASE/api/premium"
ar "POST" "$BASE/api/premium/subscribe" '{"plan":"monthly"}'

echo "--- Polls ---"
POLL=$(ar "POST" "$BASE/api/polls/create" '{"question":"Best lang?","options":["Java","Python","Kotlin"]}')
POLL_ID=$(echo "$POLL" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
if [ -n "$POLL_ID" ]; then
  ar "POST" "$BASE/api/polls/vote" "{\"poll_id\":$POLL_ID,\"option_index\":0}"
  ar "GET" "$BASE/api/polls/$POLL_ID/results"
fi

echo "--- Stories ---"
ar "GET" "$BASE/api/stories"
STORY=$(ar "POST" "$BASE/api/stories/upload" '{"file_path":"/test.jpg","type":"image"}')
STORY_ID=$(echo "$STORY" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
if [ -n "$STORY_ID" ]; then
  ar "POST" "$BASE/api/stories/$STORY_ID/reaction" '{"emoji":"🔥"}'
  ar "POST" "$BASE/api/stories/$STORY_ID/reply" '{"text":"Nice!"}'
  ar "GET" "$BASE/api/stories/$STORY_ID/stats"
  ar "DELETE" "$BASE/api/stories/$STORY_ID"
fi

echo "--- Pins ---"
ar "POST" "$BASE/api/messages/pin" '{"message_id":1}'
ar "GET" "$BASE/api/messages/pinned"
ar "POST" "$BASE/api/messages/pin/dismiss"

echo "--- Read Receipts ---"
ar "POST" "$BASE/api/messages/1/read"
ar "GET" "$BASE/api/messages/1/read_by"

echo "--- Group Permissions ---"
ar "GET" "$BASE/api/groups/1/permissions"

echo "--- Recent Searches ---"
ar "POST" "$BASE/api/recent_searches" '{"query":"hello"}'
ar "GET" "$BASE/api/recent_searches"
ar "DELETE" "$BASE/api/recent_searches"

echo "--- Referrals ---"
ar "GET" "$BASE/api/referrals/code"
ar "GET" "$BASE/api/referrals/count"

echo "--- Features ---"
ar "GET" "$BASE/api/features"

echo "--- Push ---"
ar "POST" "$BASE/api/push/subscribe" '{"endpoint":"https://ex.com/push","keys":{"p256dh":"key","auth":"auth"}}'
ar "GET" "$BASE/api/push/vapid_public_key"

echo "--- Preloaded ---"
ar "GET" "$BASE/api/preloaded/avatars"

echo "--- Favorites ---"
ar "GET" "$BASE/api/favorites"

echo "--- Calls ---"
ar "GET" "$BASE/api/calls"

echo "--- Invite Links ---"
ar "POST" "$BASE/api/groups/1/invites"
ar "GET" "$BASE/api/groups/1/invites"

echo ""
echo "=== RESULTS: $OK OK, $FAIL FAIL ==="
