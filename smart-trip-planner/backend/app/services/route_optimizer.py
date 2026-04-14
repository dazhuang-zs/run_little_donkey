"""路径优化服务（贪心最近邻 + 2-opt）"""
from typing import List, Tuple
from app.models.poi import POI, DistanceInfo, DistanceMatrix, TransportMode
from app.services.poi_service import TencentMapService
from app.core.exceptions import RouteOptimizationError
import math


class RouteOptimizer:
    def __init__(self, map_service: TencentMapService, max_opt_iterations: int = 100):
        self.map_service = map_service
        self.max_opt_iterations = max_opt_iterations

    async def optimize(
        self,
        pois: List[POI],
        start_poi: POI = None,
        mode: TransportMode = TransportMode.DRIVING,
    ) -> Tuple[List[POI], List[dict]]:
        if not pois:
            return [], []
        if len(pois) == 1:
            return pois, []

        try:
            # 构建距离矩阵
            matrix = await self._build_matrix(pois, mode)
            # 贪心算法
            route = self._greedy(pois, matrix, start_poi)
            # 2-opt优化
            if len(route) >= 3:
                route = self._two_opt(route, matrix)
            # 构建段信息
            segments = await self._build_segments(route, mode)
            return route, segments
        except Exception as e:
            raise RouteOptimizationError(f"优化失败: {str(e)}")

    async def _build_matrix(self, pois: List[POI], mode) -> List[List[float]]:
        n = len(pois)
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    info = await self.map_service.get_distance(pois[i], pois[j], mode)
                    matrix[i][j] = info.distance_meters if info else float('inf')
        return matrix

    def _greedy(self, pois, matrix, start_poi):
        n = len(pois)
        visited = [False] * n
        route = []
        start_idx = pois.index(start_poi) if start_poi else 0
        route.append(start_idx)
        visited[start_idx] = True

        current = start_idx
        while len(route) < n:
            nearest = min(
                range(n),
                key=lambda x: matrix[current][x] if not visited[x] else float('inf')
            )
            route.append(nearest)
            visited[nearest] = True
            current = nearest
        return [pois[i] for i in route]

    def _two_opt(self, route, matrix):
        improved = True
        iterations = 0
        best = route[:]
        best_cost = self._calc_cost(best, matrix)

        while improved and iterations < self.max_opt_iterations:
            improved = False
            for i in range(1, len(best) - 2):
                for j in range(i + 1, len(best) - 1):
                    new_route = best[:i] + best[i:j+1][::-1] + best[j+1:]
                    new_cost = self._calc_cost(new_route, matrix)
                    if new_cost < best_cost:
                        best = new_route
                        best_cost = new_cost
                        improved = True
            iterations += 1
        return best

    def _calc_cost(self, route, matrix):
        return sum(matrix[route[i]][route[i+1]] for i in range(len(route)-1))

    async def _build_segments(self, route, mode):
        segments = []
        for i in range(len(route) - 1):
            info = await self.map_service.get_distance(route[i], route[i+1], mode)
            if info:
                segments.append({
                    "from": route[i].name,
                    "to": route[i+1].name,
                    "distance": info.distance_meters,
                    "duration": info.duration_seconds,
                })
        return segments
