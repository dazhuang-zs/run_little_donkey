"""行程规划 API"""
from fastapi import APIRouter
import time
from app.models.trip import TripGenerationRequest, TripGenerationResponse
from app.models.response import APIResponse
from app.services.ai_parser import AIParserService
from app.services.poi_service import TencentMapService
from app.services.route_optimizer import RouteOptimizer
from app.services.report_generator import ReportGenerator
from app.core.exceptions import TripPlannerException

router = APIRouter(prefix="/api/v1", tags=["行程规划"])


@router.post("/trip/generate", response_model=TripGenerationResponse)
async def generate_trip(req: TripGenerationRequest) -> TripGenerationResponse:
    start = time.time()
    try:
        # 1. AI 解析意图
        ai = AIParserService()
        intent = await ai.parse(req.user_input)

        if req.confirm_intent:
            intent = req.confirm_intent

        # 2. POI 搜索
        map_svc = TencentMapService()
        pois = []
        for attr in intent.attractions:
            results = await map_svc.search_poi(attr, intent.city, "景点")
            if results:
                pois.append(results[0])

        if not pois:
            return TripGenerationResponse(success=False, error="未找到任何景点", processing_time_ms=0)

        # 3. 路径优化
        optimizer = RouteOptimizer(map_svc)
        route, segments = await optimizer.optimize(pois, mode=intent.transport_mode)

        # 4. 生成报告
        gen = ReportGenerator()
        trip_plan = gen.generate(intent, route, [], [])

        ms = int((time.time() - start) * 1000)
        return TripGenerationResponse(
            success=True,
            trip_plan=trip_plan,
            intent=intent,
            processing_time_ms=ms,
        )

    except TripPlannerException as e:
        return TripGenerationResponse(success=False, error=str(e), processing_time_ms=0)
    except Exception as e:
        return TripGenerationResponse(success=False, error=f"系统错误: {str(e)}", processing_time_ms=0)
