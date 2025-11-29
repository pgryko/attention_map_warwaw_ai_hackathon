import { http, HttpResponse } from "msw";

// Mock data
export const mockUser = {
  id: 1,
  email: "test@example.com",
  is_staff: false,
  profile: {
    display_name: "Test User",
    reputation: 150,
  },
};

export const mockStaffUser = {
  id: 2,
  email: "staff@example.com",
  is_staff: true,
  profile: {
    display_name: "Staff User",
    reputation: 500,
  },
};

export const mockEvents = [
  {
    id: 1,
    category: "fire",
    status: "new",
    severity: 4,
    title: "Building Fire",
    description: "Smoke visible from apartment building",
    latitude: 52.2297,
    longitude: 21.0122,
    created_at: new Date().toISOString(),
    reporter_name: "Test User",
    media_urls: [],
  },
  {
    id: 2,
    category: "accident",
    status: "verified",
    severity: 3,
    title: "Car Accident",
    description: "Two vehicles involved at intersection",
    latitude: 52.231,
    longitude: 21.015,
    created_at: new Date(Date.now() - 3600000).toISOString(),
    reporter_name: "Another User",
    media_urls: [],
  },
  {
    id: 3,
    category: "infrastructure",
    status: "resolved",
    severity: 2,
    title: "Pothole",
    description: "Large pothole on main road",
    latitude: 52.228,
    longitude: 21.008,
    created_at: new Date(Date.now() - 86400000).toISOString(),
    reporter_name: "Citizen",
    media_urls: [],
  },
];

export const mockStats = {
  total: 156,
  new: 24,
  verified: 45,
  in_progress: 12,
  resolved: 75,
  today: 8,
};

export const mockUserStats = {
  reputation: 150,
  report_count: 12,
  verified_count: 8,
  badges: [
    {
      id: 1,
      name: "First Report",
      description: "Submit your first report",
      icon: "🎯",
    },
    {
      id: 2,
      name: "Verified Reporter",
      description: "Get 5 reports verified",
      icon: "✅",
    },
  ],
};

export const mockLeaderboard = [
  { id: 1, display_name: "TopReporter", reputation: 1250, badge_count: 12 },
  { id: 2, display_name: "ActiveCitizen", reputation: 980, badge_count: 8 },
  { id: 3, display_name: "Test User", reputation: 150, badge_count: 2 },
];

export const mockBadges = [
  {
    id: 1,
    name: "First Report",
    description: "Submit your first report",
    icon: "🎯",
    points: 10,
  },
  {
    id: 2,
    name: "Verified Reporter",
    description: "Get 5 reports verified",
    icon: "✅",
    points: 50,
  },
  {
    id: 3,
    name: "Fire Watcher",
    description: "Report 3 fire incidents",
    icon: "🔥",
    points: 30,
  },
];

// Token storage for test
let currentUser = null;

export const handlers = [
  // Auth endpoints
  http.post("/api/v1/auth/token/pair", async ({ request }) => {
    const body = await request.json();
    if (body.email === "test@example.com" && body.password === "password123") {
      currentUser = mockUser;
      return HttpResponse.json({
        access: "mock-access-token",
        refresh: "mock-refresh-token",
      });
    }
    if (body.email === "staff@example.com" && body.password === "password123") {
      currentUser = mockStaffUser;
      return HttpResponse.json({
        access: "mock-staff-access-token",
        refresh: "mock-staff-refresh-token",
      });
    }
    return HttpResponse.json(
      { detail: "Invalid credentials" },
      { status: 401 },
    );
  }),

  http.post("/api/v1/auth/token/refresh", async ({ request }) => {
    const body = await request.json();
    if (body.refresh) {
      return HttpResponse.json({
        access: "mock-refreshed-access-token",
      });
    }
    return HttpResponse.json({ detail: "Invalid token" }, { status: 401 });
  }),

  http.post("/api/v1/auth/register", async ({ request }) => {
    const body = await request.json();
    if (body.email && body.password) {
      return HttpResponse.json({
        id: 99,
        email: body.email,
        is_staff: false,
      });
    }
    return HttpResponse.json({ detail: "Invalid data" }, { status: 400 });
  }),

  http.get("/api/v1/auth/me", ({ request }) => {
    const authHeader = request.headers.get("Authorization");
    if (authHeader?.includes("mock-staff")) {
      return HttpResponse.json(mockStaffUser);
    }
    if (authHeader?.includes("mock")) {
      return HttpResponse.json(mockUser);
    }
    return HttpResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }),

  http.get("/api/v1/auth/me/stats", ({ request }) => {
    const authHeader = request.headers.get("Authorization");
    if (authHeader?.includes("mock")) {
      return HttpResponse.json(mockUserStats);
    }
    return HttpResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }),

  http.get("/api/v1/auth/leaderboard", () => {
    return HttpResponse.json(mockLeaderboard);
  }),

  http.get("/api/v1/auth/badges", () => {
    return HttpResponse.json(mockBadges);
  }),

  // Events endpoints
  http.get("/api/v1/events", ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get("status");
    const category = url.searchParams.get("category");

    let filtered = [...mockEvents];
    if (status) {
      filtered = filtered.filter((e) => e.status === status);
    }
    if (category) {
      filtered = filtered.filter((e) => e.category === category);
    }

    return HttpResponse.json({ events: filtered });
  }),

  http.get("/api/v1/events/:id", ({ params }) => {
    const event = mockEvents.find((e) => e.id === parseInt(params.id));
    if (event) {
      return HttpResponse.json(event);
    }
    return HttpResponse.json({ detail: "Not found" }, { status: 404 });
  }),

  http.post("/api/v1/events/upload", async ({ request }) => {
    // Simulate successful upload
    const newEvent = {
      id: Math.floor(Math.random() * 1000) + 100,
      category: "other",
      status: "new",
      severity: 2,
      title: "New Report",
      description: "User submitted report",
      latitude: 52.2297,
      longitude: 21.0122,
      created_at: new Date().toISOString(),
      reporter_name: "Test User",
      media_urls: ["/media/test.jpg"],
    };
    return HttpResponse.json(newEvent, { status: 201 });
  }),

  http.patch("/api/v1/events/:id/status", async ({ params, request }) => {
    const body = await request.json();
    const event = mockEvents.find((e) => e.id === parseInt(params.id));
    if (event) {
      return HttpResponse.json({
        ...event,
        status: body.status,
      });
    }
    return HttpResponse.json({ detail: "Not found" }, { status: 404 });
  }),

  // Stats endpoint
  http.get("/api/v1/stats/summary", () => {
    return HttpResponse.json(mockStats);
  }),

  // SSE endpoint (returns empty response for tests)
  http.get("/api/v1/events/stream", () => {
    return new HttpResponse(null, { status: 200 });
  }),
];

// Helper to reset current user
export const resetMockUser = () => {
  currentUser = null;
};
