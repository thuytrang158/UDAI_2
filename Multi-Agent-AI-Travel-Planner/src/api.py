"""
Phase 11: FastAPI Backend API for AI Travel Planner.
Exposes multi-agent workflows as structured REST endpoints.
"""
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Tools & Schemas
from src.tools.places import search_places_osm, retry_missing_coordinates, get_places_notice
from src.tools.routing import calculate_route
from src.tools.clustering import group_places_by_days
from src.tools.accommodation import search_accommodations
from src.tools.cost_calculator import calculate_trip_cost
from src.tools.modification import modify_selection_with_llm
from src.tools.currency import INR_TO_VND_RATE, inr_to_vnd, vnd_to_inr
from src.rag_retrieval import initialize_rag_index, rag_index_health, retrieve_rag_chunks


app = FastAPI(
    title="AI Travel Planner API",
    version="1.0.0",
    description="Multi-Agent Open-Source AI Travel Planner"
)


@app.on_event("startup")
def warm_bge_m3_rag_index():
    """Load BGE-M3 and prepare/reuse the persistent knowledge-base index."""
    try:
        status = initialize_rag_index()
        print(f"BGE-M3 RAG ready: {status['chunk_count']} chunks in Qdrant local store.")
    except Exception as error:
        # Keep Planner routes available; /api/rag/retrieve will retry and report 503.
        print(f"BGE-M3 RAG initialization deferred: {type(error).__name__}: {error}")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder for web UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ----------------------------------------------------------------------
# Request / Response Schemas
# ----------------------------------------------------------------------
class RequirementsRequest(BaseModel):
    destination: str = "Bengaluru"
    number_of_days: int = 3
    number_of_travelers: int = 2
    budget_per_day: str = "1.085.000 VND/ngày"
    transportation_preference: str = "Cab and Metro"
    interests: List[str] = Field(default_factory=list)


class GenerateItineraryRequest(BaseModel):
    destination: str
    number_of_days: int
    transportation_preference: str
    selected_places: List[dict]


class ModifyItineraryRequest(BaseModel):
    feedback: str
    available_places: List[dict]
    selected_places: List[dict]
    destination: str = "Bengaluru"
    number_of_days: int = 3
    transportation_preference: str = "Cab and Metro"


class SearchStaysRequest(BaseModel):
    destination: str
    stay_type: str = "Hotel"
    max_budget: int = 1356850
    preferred_area: str = "Quiet Area"


class FinalizeTripRequest(BaseModel):
    destination: str
    number_of_days: int
    number_of_travelers: int
    transportation_preference: str
    itinerary: dict
    selected_accommodation: dict
    routes: List[dict]
    selected_places: List[dict] = Field(default_factory=list)


class RagRetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1200)
    limit: int = Field(default=12, ge=1, le=30)


# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------
@app.get("/")
def serve_ui():
    """Serves the single-page application UI."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AI Travel Planner API running. Place index.html in src/static/."}


@app.get("/api/rag/health")
def rag_health():
    return rag_index_health()


@app.post("/api/rag/retrieve")
def retrieve_rag(req: RagRetrieveRequest):
    try:
        return retrieve_rag_chunks(req.query.strip(), req.limit)
    except Exception as error:
        print(f"BGE-M3 RAG retrieval failed: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=503,
            detail="BGE-M3 RAG chưa sẵn sàng. Kiểm tra log FastAPI và kết nối tải model.",
        ) from error


@app.post("/api/trip/initiate")
def initiate_trip(req: RequirementsRequest):
    """
    Step 1: Discovers Top attractions tailored to destination AND travel interests.
    """
    dest = req.destination.strip()
    places = search_places_osm(dest, limit=10, interests=req.interests)

    return {
        "destination": dest,
        "number_of_days": req.number_of_days,
        "number_of_travelers": req.number_of_travelers,
        "budget_per_day": req.budget_per_day,
        "transportation_preference": req.transportation_preference,
        "interests": req.interests,
        "available_places": places,
        "places_notice": get_places_notice() or ("" if places else "Không tìm thấy địa điểm phù hợp lúc này. Một hoặc nhiều nguồn dữ liệu có thể đang tạm thời không truy cập được."),
        "status": "PLACES_DISCOVERED"
    }


@app.post("/api/trip/generate-itinerary")
def generate_itinerary(req: GenerateItineraryRequest):
    """
    Steps 2 & 3: Calculates OSRM routes, clusters stops, and builds the timetable.
    """
    places = retry_missing_coordinates(req.selected_places, req.destination)
    if not places:
        raise HTTPException(status_code=400, detail="Vui lòng chọn ít nhất một địa điểm tham quan.")
    # 1. Calculate OSRM route legs
    routes = []
    for i in range(len(places) - 1):
        p1 = places[i]
        p2 = places[i + 1]
        if p1.get("latitude") is None or p1.get("longitude") is None or p2.get("latitude") is None or p2.get("longitude") is None:
            continue
        route_data = calculate_route(
            origin_lat=p1["latitude"], origin_lon=p1["longitude"],
            dest_lat=p2["latitude"], dest_lon=p2["longitude"]
        )
        routes.append({
            "origin_name": p1["name"],
            "destination_name": p2["name"],
            "distance_km": route_data["distance_km"],
            "duration_minutes": route_data["duration_minutes"],
            "source": route_data["source"]
        })

    itinerary = build_itinerary(places, req.number_of_days, req.transportation_preference, calculate_route)

    return {
        "selected_places": places,
        "routes": routes,
        "itinerary": {"destination": req.destination, "total_days": req.number_of_days, **itinerary}
    }


@app.post("/api/trip/modify")
def modify_itinerary(req: ModifyItineraryRequest):
    """
    Human-in-the-Loop modification handler.
    """
    feedback = req.feedback.lower()
    selected = modify_selection_with_llm(req.feedback, req.selected_places, req.available_places)
    available = req.available_places
    # Reject non-available IDs/names and locations without coordinates before routing.
    available_by_id = {p.get("id"): p for p in available if p.get("id")}
    if available_by_id:
        selected = [available_by_id[p.get("id")] for p in selected if p.get("id") in available_by_id]
    selected = retry_missing_coordinates(selected, req.destination)
    # Rebuild routes and schedule from the accepted place selection so that the
    # itinerary shown to the user and later included in the dossier stay aligned.
    routes = []
    for origin, destination in zip(selected, selected[1:]):
        if origin.get("latitude") is None or origin.get("longitude") is None or destination.get("latitude") is None or destination.get("longitude") is None:
            continue
        route_data = calculate_route(origin["latitude"], origin["longitude"], destination["latitude"], destination["longitude"])
        routes.append({
            "origin_name": origin["name"], "destination_name": destination["name"],
            "distance_km": route_data["distance_km"], "duration_minutes": route_data["duration_minutes"],
            "source": route_data["source"]
        })
    itinerary = build_itinerary(selected, req.number_of_days, req.transportation_preference, calculate_route)
    itinerary.update({"destination": req.destination, "total_days": req.number_of_days})
    return {"selected_places": selected, "itinerary": itinerary, "routes": routes}


def build_itinerary(places, number_of_days, transport_preference, route_calculator):
    """Create a Vietnamese schedule while preserving existing place/category values."""
    day_buckets = group_places_by_days(places, number_of_days)
    itinerary_days = []
    for day_num, day_places in enumerate(day_buckets, start=1):
        schedule = []
        # Preserve the original English value checks used by existing place data.
        has_trek = any("Trek" in p.get("category", "") or "Hills" in p.get("name", "") for p in day_places)
        theme = "Khám phá thiên nhiên và trekking trên đồi" if has_trek else "Di sản và vườn xanh trong thành phố"
        schedule.append({
            "time": "05:30" if has_trek else "09:00",
            "activity": "Khởi hành từ nơi lưu trú",
            "details": f"Bắt đầu hành trình bằng {transport_preference}."
        })
        current_hour = 6 if has_trek else 9
        for idx, place in enumerate(day_places):
            if idx > 0:
                prev = day_places[idx - 1]
                has_route_coordinates = all(prev.get(key) is not None and place.get(key) is not None for key in ("latitude", "longitude"))
                if has_route_coordinates:
                    leg = route_calculator(prev["latitude"], prev["longitude"], place["latitude"], place["longitude"])
                    travel_details = f"Quãng đường {leg['distance_km']} km, thời gian dự kiến {leg['duration_minutes']} phút."
                    current_hour += leg["duration_minutes"] // 60
                else:
                    travel_details = "Chưa có đủ tọa độ để ước tính quãng đường và thời gian di chuyển."
                schedule.append({
                    "time": f"{current_hour:02d}:30",
                    "activity": f"Di chuyển đến {place['name']}",
                    "details": travel_details
                })
            category = place.get("category", "Địa điểm tham quan")
            category_labels = {
                "Trekking & Adventure": "Leo núi và phiêu lưu", "Parks & Leisure": "Công viên và thư giãn",
                "Heritage & Architecture": "Di sản và kiến trúc", "Spiritual & Wellness": "Tâm linh và chăm sóc sức khỏe",
                "Food & Culinary": "Ẩm thực", "Shopping & Bazaars": "Mua sắm và chợ truyền thống",
            }
            schedule.append({
                "time": f"{current_hour:02d}:30",
                "activity": place["name"],
                "details": f"{category_labels.get(category, category)} — {place.get('description', 'Chưa có nội dung giới thiệu trong nguồn.')}" + (" — Chưa xác định được tọa độ." if place.get("latitude") is None or place.get("longitude") is None else ""),
                "place_id": place.get("id"), "sources": place.get("sources", []),
                "geocoding_status": place.get("geocoding_status", "unavailable"),
                "geocoding_reason": place.get("geocoding_reason"),
                "coordinate_source": place.get("coordinate_source"),
                "coordinate_reference_url": place.get("coordinate_reference_url"),
                "coordinate_attribution": place.get("coordinate_attribution")
            })
            current_hour += 2
            if current_hour in [12, 13, 14] and not any("Nghỉ trưa" in item["activity"] for item in schedule):
                schedule.append({"time": "13:30", "activity": "Nghỉ trưa và dùng bữa", "details": "Thưởng thức ẩm thực địa phương và nghỉ ngơi."})
                current_hour += 1
        schedule.append({"time": "18:00", "activity": "Trở về nơi lưu trú", "details": "Buổi tối tự do nghỉ ngơi và thư giãn."})
        itinerary_days.append({"day_number": day_num, "theme": theme, "schedule": schedule})
    return {"days": itinerary_days}


@app.post("/api/trip/stays")
def get_stays(req: SearchStaysRequest):
    """
    Step 4: Retrieves authentic properties filtered by user criteria.
    """
    options = search_accommodations(
        destination=req.destination,
        stay_type=req.stay_type,
        max_budget=vnd_to_inr(req.max_budget),
        preferred_area=req.preferred_area
    )
    for option in options:
        option["price_per_night"] = inr_to_vnd(option.get("price_per_night", 0))
        option["currency"] = "VND"
    return {"accommodation_options": options}


@app.post("/api/trip/finalize")
def finalize_trip(req: FinalizeTripRequest):
    """
    Step 5: Calculates deterministic costs and compiles the Master Dossier.
    """
    days = req.itinerary.get("days") if isinstance(req.itinerary, dict) else None
    if not isinstance(days, list) or len(days) != req.number_of_days or any(
        not isinstance(day, dict) or day.get("day_number") != index + 1
        or not isinstance(day.get("schedule"), list) or not day["schedule"]
        or any(not isinstance(item, dict) or not item.get("time") or not item.get("activity") or item.get("details") is None for item in day["schedule"])
        for index, day in enumerate(days)
    ):
        raise HTTPException(status_code=400, detail="Lịch trình chưa đầy đủ. Vui lòng quay lại bước Lịch trình để tạo và xác nhận lại.")
    stay = req.selected_accommodation
    # The stays API exposes VND amounts; cost assumptions remain internal INR.
    nightly_rate = vnd_to_inr(stay.get("price_per_night", inr_to_vnd(2200)))

    cost_data = calculate_trip_cost(
        number_of_days=req.number_of_days,
        number_of_travelers=req.number_of_travelers,
        nightly_rate=nightly_rate,
        routes=req.routes,
        transport_pref=req.transportation_preference
    )
    for key in ("accommodation_cost", "transportation_cost", "food_cost", "activities_cost", "miscellaneous_cost", "total_estimated_cost"):
        cost_data[key] = inr_to_vnd(cost_data[key])
    cost_data["currency"] = "VND"
    cost_data["exchange_rate_inr_to_vnd"] = INR_TO_VND_RATE
    cost_data["breakdown_notes"]["rate_per_km"] = inr_to_vnd(cost_data["breakdown_notes"]["rate_per_km"])
    stay["currency"] = "VND"

    return {
        "destination": req.destination,
        "duration_summary": f"{req.number_of_days} Days / {max(req.number_of_days - 1, 1)} Nights",
        "travelers": req.number_of_travelers,
        "selected_accommodation": stay,
        "selected_places": req.selected_places,
        "itinerary": req.itinerary,
        "cost_breakdown": cost_data,
        "exchange_rate_inr_to_vnd": INR_TO_VND_RATE,
        "status": "FINALIZED"
    }
