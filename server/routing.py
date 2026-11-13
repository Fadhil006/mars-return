"""Grid routing and route metrics for a prepared region."""

import heapq
import math

from server.coordinates import pixel_to_xy, xy_to_pixel


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a, b, p):
    return abs(_orient(a, b, p)) < 1e-9 and min(a[0], b[0]) - 1e-9 <= p[0] <= max(a[0], b[0]) + 1e-9 and min(a[1], b[1]) - 1e-9 <= p[1] <= max(a[1], b[1]) + 1e-9


def _segments_intersect(a, b, c, d):
    o1, o2, o3, o4 = _orient(a, b, c), _orient(a, b, d), _orient(c, d, a), _orient(c, d, b)
    return (o1 * o2 < 0 and o3 * o4 < 0) or any((_on_segment(a, b, c), _on_segment(a, b, d), _on_segment(c, d, a), _on_segment(c, d, b)))


def _validated_polygons(polygons):
    result = []
    for polygon in polygons or []:
        if not isinstance(polygon, (list, tuple)) or len(polygon) < 3:
            raise ValueError("blocked polygons must contain at least three points")
        points = []
        for point in polygon:
            if not isinstance(point, (list, tuple)) or len(point) != 2 or not all(_number(v) for v in point):
                raise ValueError("polygon coordinates must be finite [x, y] pairs")
            points.append(tuple(point))
        if points[0] == points[-1]:
            points.pop()
        if len(set(points)) != len(points) or len(points) < 3:
            raise ValueError("blocked polygon vertices must be distinct")
        area = sum(points[i][0] * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * points[i][1] for i in range(len(points)))
        if abs(area) < 1e-9:
            raise ValueError("blocked polygon must have nonzero area")
        for i in range(len(points)):
            a, b = points[i], points[(i + 1) % len(points)]
            for j in range(i + 1, len(points)):
                if j in (i, (i + 1) % len(points)) or (j + 1) % len(points) == i:
                    continue
                if _segments_intersect(a, b, points[j], points[(j + 1) % len(points)]):
                    raise ValueError("blocked polygon must not self-intersect")
        result.append((points, (min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points))))
    return result


def _cell_blocked(row, col, region, polygons):
    if not region["mask"][row][col] or not _number(region["elevation"][row][col]) or not _number(region["slope"][row][col]):
        return True
    manifest = region["manifest"]
    x, y = pixel_to_xy(row, col, manifest)
    half = manifest["cellSizeM"] / 2
    box = [(x-half,y-half),(x+half,y-half),(x+half,y+half),(x-half,y+half)]
    for poly, bounds in polygons:
        if bounds[2] < x-half or bounds[0] > x+half or bounds[3] < y-half or bounds[1] > y+half:
            continue
        if any(px >= x-half and px <= x+half and py >= y-half and py <= y+half for px, py in poly):
            return True
        if any(_point_in_polygon(corner, poly) for corner in box):
            return True
        if any(_segments_intersect(box[i], box[(i+1)%4], poly[j], poly[(j+1)%len(poly)]) for i in range(4) for j in range(len(poly))):
            return True
    return False


def _point_in_polygon(p, poly):
    inside = False
    for i, (x1, y1) in enumerate(poly):
        x2, y2 = poly[(i+1) % len(poly)]
        if _on_segment((x1,y1),(x2,y2),p):
            return True
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2-x1)*(p[1]-y1)/(y2-y1)+x1:
            inside = not inside
    return inside


def _search(slopes, h, w, size, blocked, start, goal, mode, max_slope_deg):
    """Least-cost search from start. With goal=None it explores every reachable cell."""
    moves = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    distances, previous = {start: 0.0}, {}
    queue = [(0.0, start)]
    while queue:
        _, current = heapq.heappop(queue)
        if current == goal: break
        for dr, dc in moves:
            nxt = (current[0]+dr, current[1]+dc)
            r,c = nxt
            if not (0 <= r < h and 0 <= c < w) or blocked(r,c): continue
            if dr and dc and (blocked(current[0]+dr,current[1]) or blocked(current[0],current[1]+dc)): continue
            length = size * (math.sqrt(2) if dr and dc else 1)
            edge_slope = max(slopes[current[0]][current[1]], slopes[r][c])
            weight = length * (1 + 4*(edge_slope/max_slope_deg)**2) if mode == "slope_penalized" else length
            candidate = distances[current] + weight
            if candidate < distances.get(nxt, math.inf):
                distances[nxt], previous[nxt] = candidate, current
                heuristic = size * math.hypot(goal[0]-r, goal[1]-c) if goal else 0.0
                heapq.heappush(queue, (candidate+heuristic, nxt))
    return distances, previous


def return_field(region, origin_xy, mode="shortest", max_slope_deg=15, blocked_polygons=None):
    """Walking distance from every cell to origin along its least-cost path; None where unreachable.

    Edges are symmetric, so distance from the origin equals distance back to it.
    """
    if mode not in ("shortest", "slope_penalized") or not _number(max_slope_deg) or max_slope_deg <= 0:
        raise ValueError("unsupported route mode or slope limit")
    polygons = _validated_polygons(blocked_polygons)
    manifest, slopes = region["manifest"], region["slope"]
    h, w, size = manifest["height"], manifest["width"], manifest["cellSizeM"]
    start = tuple(xy_to_pixel(*origin_xy, manifest))
    cache = {}
    def blocked(r, c):
        if (r, c) not in cache:
            cache[(r, c)] = _cell_blocked(r, c, region, polygons) or slopes[r][c] > max_slope_deg
        return cache[(r, c)]
    if blocked(*start):
        raise ValueError("base position is blocked, over the slope limit, or has unavailable terrain data")
    costs, previous = _search(slopes, h, w, size, blocked, start, None, mode, max_slope_deg)
    grid = [[None] * w for _ in range(h)]
    grid[start[0]][start[1]] = 0.0
    for cell in sorted(previous, key=costs.get):  # parents always cost less, so they are filled first
        parent = previous[cell]
        step = size * (math.sqrt(2) if cell[0] != parent[0] and cell[1] != parent[1] else 1)
        grid[cell[0]][cell[1]] = grid[parent[0]][parent[1]] + step
    return grid


def route(region, start_xy, goal_xy, mode="shortest", max_slope_deg=15, blocked_polygons=None):
    """Find a cell-center path; endpoint cells are never silently snapped."""
    empty = {"status": "invalid_input", "pathXY": None, "distanceM": None, "ascentM": None, "maxSlopeDeg": None, "meanSlopeDeg": None, "profile": None, "cost": None,
             "requestedStartXY": start_xy, "requestedGoalXY": goal_xy, "effectiveStartXY": None, "effectiveGoalXY": None}
    try:
        if mode not in ("shortest", "slope_penalized") or not _number(max_slope_deg) or max_slope_deg <= 0:
            return empty
        polygons = _validated_polygons(blocked_polygons)
        manifest = region["manifest"]
        elev, slopes, mask = region["elevation"], region["slope"], region["mask"]
        h, w = manifest["height"], manifest["width"]
        if any(len(grid) != h or any(len(row) != w for row in grid) for grid in (elev, slopes, mask)):
            return empty
        start, goal = tuple(xy_to_pixel(*start_xy, manifest)), tuple(xy_to_pixel(*goal_xy, manifest))
        blocked_cells = {}
        def blocked(r, c):
            cell = (r, c)
            if cell not in blocked_cells:
                blocked_cells[cell] = _cell_blocked(r, c, region, polygons) or slopes[r][c] > max_slope_deg
            return blocked_cells[cell]
        start_xy_effective, goal_xy_effective = pixel_to_xy(*start, manifest), pixel_to_xy(*goal, manifest)
        if blocked(*start):
            return {**empty, "message": "start position is blocked, over the slope limit, or has unavailable terrain data"}
        if blocked(*goal):
            return {**empty, "message": "goal position is blocked, over the slope limit, or has unavailable terrain data"}
    except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError):
        return empty
    if start == goal:
        coords = [start_xy_effective]
        return {"status":"ok","pathXY":coords,"distanceM":0.0,"ascentM":0.0,"maxSlopeDeg":slopes[start[0]][start[1]],"meanSlopeDeg":slopes[start[0]][start[1]],"profile":[{"distanceM":0.0,"elevationM":elev[start[0]][start[1]],"slopeDeg":slopes[start[0]][start[1]]}],"cost":0.0,
                "requestedStartXY":start_xy,"requestedGoalXY":goal_xy,"effectiveStartXY":start_xy_effective,"effectiveGoalXY":goal_xy_effective}
    size = manifest["cellSizeM"]
    distances, previous = _search(slopes, h, w, size, blocked, start, goal, mode, max_slope_deg)
    if goal not in distances:
        return {**empty, "status":"no_path"}
    cells = [goal]
    while cells[-1] != start: cells.append(previous[cells[-1]])
    cells.reverse()
    path = [pixel_to_xy(r,c,manifest) for r,c in cells]
    profile, distance, ascent = [], 0.0, 0.0
    slopes_sampled = []
    weighted_slope, slope_distance = 0.0, 0.0
    for i,(r,c) in enumerate(cells):
        if i:
            pr,pc = cells[i-1]
            edge_distance = size * (math.sqrt(2) if r != pr and c != pc else 1)
            distance += edge_distance
            ascent += max(0.0, elev[r][c]-elev[pr][pc])
            edge_slope = max(slopes[pr][pc], slopes[r][c])
            weighted_slope += edge_slope * edge_distance
            slope_distance += edge_distance
        s = slopes[r][c]; slopes_sampled.append(s)
        profile.append({"distanceM":distance,"elevationM":elev[r][c],"slopeDeg":s})
    return {"status":"ok","pathXY":path,"distanceM":distance,"ascentM":ascent,"maxSlopeDeg":max(slopes_sampled),"meanSlopeDeg":weighted_slope/slope_distance if slope_distance else slopes_sampled[0],"profile":profile,"cost":distances[goal],
            "requestedStartXY":start_xy,"requestedGoalXY":goal_xy,"effectiveStartXY":path[0],"effectiveGoalXY":path[-1]}
