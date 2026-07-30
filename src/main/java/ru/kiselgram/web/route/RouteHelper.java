package ru.kiselgram.web.route;

import org.hibernate.Session;

import java.util.List;
import java.util.Map;

public class RouteHelper {

    @SuppressWarnings("unchecked")
    public static List<Map<String, Object>> listMaps(Session s, String sql, Object... params) {
        var q = s.createNativeQuery(sql, Map.class);
        for (int i = 0; i < params.length; i += 2) q.setParameter((String) params[i], params[i + 1]);
        return (List<Map<String, Object>>) (List) q.list();
    }

    public static Map<String, Object> ok(Object data) {
        return Map.of("success", true, "data", data);
    }

    public static Map<String, Object> err(String code, Object msg) {
        return Map.of("success", false, "error", Map.of("code", code, "message", msg));
    }
}
