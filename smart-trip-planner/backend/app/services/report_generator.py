"""行程报告生成服务"""
from typing import List
from app.models.trip import TripIntent, TripPlan, DayPlan, AttractionInDay, HotelRecommendation
from app.models.poi import POI


class ReportGenerator:
    def generate(
        self,
        intent: TripIntent,
        route: List[POI],
        segments: List[dict],
        hotels: List[POI] = [],
    ) -> TripPlan:
        day_plans = []
        attractions_per_day = max(1, len(route) // intent.days)

        for day in range(1, intent.days + 1):
            start_idx = (day - 1) * attractions_per_day
            end_idx = min(start_idx + attractions_per_day, len(route))
            day_attractions = route[start_idx:end_idx]

            attractions = []
            for i, poi in enumerate(day_attractions):
                arrival = 9 + i * 2
                attractions.append(AttractionInDay(
                    name=poi.name,
                    poi={"name": poi.name, "lat": poi.lat, "lng": poi.lng},
                    arrival_time=f"{arrival:02d}:00",
                    departure_time=f"{arrival+2:02d}:00",
                    duration_minutes=120,
                ))

            day_plans.append(DayPlan(
                day=day,
                attractions=attractions,
            ))

        hotel_recs = [
            HotelRecommendation(
                name=h.name,
                address=h.address,
                lat=h.lat,
                lng=h.lng,
                rating=h.rating,
                district=h.district,
                reason="周边景点密集，交通便利",
            )
            for h in hotels[:3]
        ]

        return TripPlan(
            intent=intent.model_dump(),
            city=intent.city,
            days=intent.days,
            day_plans=day_plans,
            hotels=hotel_recs,
            tips=[
                "建议提前预约热门景点门票",
                "携带身份证，部分景点需实名入场",
                "关注目的地天气，合理安排行程",
            ],
        )
